"""Расширенный поиск противоречий: 300 пар с фокусом на нормы с числами из разных документов.

Стратегия:
1. Находим кластеры с нормами из 2+ документов, содержащие числовые данные.
2. Сортируем пары по embedding-сходству (ChromaDB) — проверяем наиболее похожие первыми.
3. Пропускаем уже проверенные пары и пары из одного документа.
4. Проверяем 300 пар через LLM с порогом confidence >= 0.5.
5. Дописываем новые findings в SQLite (не удаляя существующие).
6. Пересобираем граф.

Запуск: cd backend && python -m scripts.find_more_contradictions
"""

import asyncio
import logging
import re
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import settings
from app.database import get_chroma_collection, get_db, init_db
from app.llm.client import OllamaClient
from app.llm.prompts import CONTRADICTION_PROMPT
from app.pipeline.graph_builder import GraphBuilder

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("find_more_contradictions")

# Regex для норм с числовыми данными (сроки, суммы, проценты, возраст)
NUMBER_PATTERN = re.compile(
    r'\d+\s*(?:дн[еёяй]|суток|месяц[аеов]*|год[аулет]*|лет'
    r'|процент[аов]*|тенге|МРП|%|раз[а]?\b|час[аов]*'
    r'|рабоч|календарн|минут|размер[аеов]*|кратн)',
    re.IGNORECASE,
)

# Приоритетные домены
PRIORITY_KEYWORDS = [
    'труд', 'работ', 'охран', 'налог', 'земел', 'земл', 'пенс',
    'соци', 'страхов', 'выплат', 'зарплат', 'отпуск', 'штраф',
    'занятост', 'безопасност', 'здоров', 'медицин', 'лиценз',
    'предприниматель', 'собствен', 'аренд', 'сроки', 'возраст',
]

TARGET_CHECKS = 300
MIN_NORM_LENGTH = 50


async def load_existing_pairs() -> set[tuple[str, str]]:
    """Загрузить уже проверенные пары (существующие findings)."""
    pairs = set()
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT norm_a_id, norm_b_id FROM findings WHERE type = 'contradiction'"
        )
        rows = await cursor.fetchall()
        for row in rows:
            pair = tuple(sorted([row["norm_a_id"], row["norm_b_id"]]))
            pairs.add(pair)
    logger.info("Уже проверенных пар (contradictions): %d", len(pairs))
    return pairs


async def load_multi_doc_clusters() -> list[dict]:
    """Загрузить кластеры с нормами из 2+ разных документов."""
    async with get_db() as db:
        cursor = await db.execute("""
            SELECT cluster_id, cluster_topic, COUNT(DISTINCT doc_id) as doc_count,
                   COUNT(*) as norm_count
            FROM norms
            WHERE cluster_id IS NOT NULL AND cluster_topic IS NOT NULL
            GROUP BY cluster_id
            HAVING doc_count >= 2
            ORDER BY doc_count DESC
        """)
        rows = await cursor.fetchall()
    clusters = [dict(r) for r in rows]
    logger.info("Всего кластеров с 2+ документами: %d", len(clusters))
    return clusters


def score_cluster(cluster: dict) -> float:
    """Оценить приоритет кластера: выше для приоритетных доменов."""
    topic = (cluster.get("cluster_topic") or "").lower()
    priority_bonus = sum(2.0 for kw in PRIORITY_KEYWORDS if kw in topic)
    # Больше документов -> больше шансов на противоречие, но не слишком широкие
    doc_factor = min(cluster["doc_count"], 20) / 20.0
    return priority_bonus + doc_factor


async def load_norms_for_cluster(cluster_id: int) -> list[dict]:
    """Загрузить нормы кластера с числовыми данными."""
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT id, doc_id, text FROM norms WHERE cluster_id = ?",
            (cluster_id,),
        )
        rows = await cursor.fetchall()
    all_norms = [dict(r) for r in rows]

    # Фильтруем по длине
    all_norms = [n for n in all_norms if len(n["text"]) >= MIN_NORM_LENGTH]

    # Отдельно нормы с числами
    with_numbers = [n for n in all_norms if NUMBER_PATTERN.search(n["text"])]

    # Если хватает норм с числами — возвращаем их, иначе все
    if len(with_numbers) >= 4:
        return with_numbers
    return all_norms


def cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """Косинусное сходство двух векторов."""
    a = np.array(vec_a, dtype=np.float32)
    b = np.array(vec_b, dtype=np.float32)
    dot = np.dot(a, b)
    norm = np.linalg.norm(a) * np.linalg.norm(b)
    if norm == 0:
        return 0.0
    return float(dot / norm)


async def get_embeddings_from_chroma(norm_ids: list[str]) -> dict[str, list[float]]:
    """Получить embedding-ы норм из ChromaDB."""
    if not norm_ids:
        return {}
    collection = get_chroma_collection("norms")
    result = {}
    # ChromaDB get() may fail for missing IDs, so batch carefully
    batch_size = 100
    for i in range(0, len(norm_ids), batch_size):
        batch = norm_ids[i:i + batch_size]
        try:
            data = collection.get(ids=batch, include=["embeddings"])
            if data and data["ids"] and data["embeddings"]:
                for nid, emb in zip(data["ids"], data["embeddings"]):
                    if emb is not None:
                        result[nid] = emb
        except Exception:
            logger.debug("ChromaDB get failed for batch starting at %d", i)
    return result


async def generate_smart_pairs(
    clusters: list[dict],
    existing_pairs: set[tuple[str, str]],
    max_pairs: int = 500,
) -> list[tuple[dict, dict, int]]:
    """Генерировать пары норм с числами из разных документов, отсортированные по сходству."""
    logger.info("Генерация пар из %d кластеров (лимит: %d пар)...", len(clusters), max_pairs)

    # Сортируем кластеры по приоритету
    clusters_sorted = sorted(clusters, key=score_cluster, reverse=True)

    raw_pairs: list[tuple[dict, dict, int, float]] = []  # (norm_a, norm_b, cluster_id, similarity)

    doc_titles = {}
    async with get_db() as db:
        cursor = await db.execute("SELECT id, title FROM documents")
        for row in await cursor.fetchall():
            doc_titles[row["id"]] = row["title"]

    clusters_processed = 0
    for cluster in clusters_sorted:
        if len(raw_pairs) >= max_pairs * 2:
            break

        cid = cluster["cluster_id"]
        norms = await load_norms_for_cluster(cid)

        # Группируем по документу
        by_doc: dict[str, list[dict]] = {}
        for n in norms:
            by_doc.setdefault(n["doc_id"], []).append(n)

        if len(by_doc) < 2:
            continue

        # Получаем embeddings для норм этого кластера
        all_norm_ids = [n["id"] for n in norms]
        embeddings = await get_embeddings_from_chroma(all_norm_ids)

        # Генерируем пары из разных документов
        doc_ids = list(by_doc.keys())
        for i in range(len(doc_ids)):
            for j in range(i + 1, len(doc_ids)):
                # Берём до 3 норм с числами из каждого документа
                norms_a = [n for n in by_doc[doc_ids[i]] if NUMBER_PATTERN.search(n["text"])][:3]
                if not norms_a:
                    norms_a = by_doc[doc_ids[i]][:2]
                norms_b = [n for n in by_doc[doc_ids[j]] if NUMBER_PATTERN.search(n["text"])][:3]
                if not norms_b:
                    norms_b = by_doc[doc_ids[j]][:2]

                for na in norms_a:
                    for nb in norms_b:
                        pair_key = tuple(sorted([na["id"], nb["id"]]))
                        if pair_key in existing_pairs:
                            continue

                        # Вычисляем сходство через embeddings
                        sim = 0.5  # default
                        if na["id"] in embeddings and nb["id"] in embeddings:
                            sim = cosine_similarity(embeddings[na["id"]], embeddings[nb["id"]])

                        raw_pairs.append((na, nb, cid, sim))

        clusters_processed += 1
        if clusters_processed % 20 == 0:
            logger.info(
                "Обработано кластеров: %d, собрано пар: %d",
                clusters_processed, len(raw_pairs),
            )

    # Сортируем по similarity (DESC) — наиболее похожие нормы из разных документов
    # Высокое сходство + разные документы = высокий шанс противоречия
    raw_pairs.sort(key=lambda x: x[3], reverse=True)

    # Берём top max_pairs, убираем дубли пар
    seen = set()
    result = []
    for na, nb, cid, sim in raw_pairs:
        pair_key = tuple(sorted([na["id"], nb["id"]]))
        if pair_key in seen:
            continue
        seen.add(pair_key)
        result.append((na, nb, cid))
        if len(result) >= max_pairs:
            break

    logger.info(
        "Итого уникальных пар для проверки: %d (из %d кандидатов)",
        len(result), len(raw_pairs),
    )
    return result


async def check_pairs_for_contradictions(
    pairs: list[tuple[dict, dict, int]],
    max_checks: int = TARGET_CHECKS,
) -> list[dict]:
    """Проверить пары через LLM на противоречия."""
    client = OllamaClient()
    findings = []

    # Загружаем заголовки документов
    doc_titles = {}
    async with get_db() as db:
        cursor = await db.execute("SELECT id, title FROM documents")
        for row in await cursor.fetchall():
            doc_titles[row["id"]] = row["title"]

    checked = 0
    errors = 0
    start_time = time.time()

    for norm_a, norm_b, cid in pairs[:max_checks]:
        prompt = CONTRADICTION_PROMPT.format(
            doc_a_title=doc_titles.get(norm_a["doc_id"], "Неизвестный документ"),
            norm_a_text=norm_a["text"][:1500],
            doc_b_title=doc_titles.get(norm_b["doc_id"], "Неизвестный документ"),
            norm_b_text=norm_b["text"][:1500],
        )

        try:
            result = await client.generate_json(
                prompt=prompt,
                temperature=settings.LLM_TEMPERATURE_ANALYSIS,
            )
            checked += 1

            if result.get("is_contradiction"):
                confidence = float(result.get("confidence", 0.5))
                if confidence >= 0.5:
                    findings.append({
                        "type": "contradiction",
                        "severity": result.get("severity", "medium"),
                        "confidence": confidence,
                        "norm_a_id": norm_a["id"],
                        "norm_b_id": norm_b["id"],
                        "explanation": result.get("explanation", "Коллизия обнаружена LLM"),
                        "cluster_id": cid,
                        "legal_principle": result.get("legal_principle", ""),
                    })
                    logger.info(
                        ">>> КОЛЛИЗИЯ #%d [%s, %.2f]: %s <-> %s — %s",
                        len(findings),
                        result.get("severity", "?"),
                        confidence,
                        norm_a["id"][:35],
                        norm_b["id"][:35],
                        (result.get("explanation", ""))[:100],
                    )

        except Exception as exc:
            errors += 1
            if errors <= 5:
                logger.warning("LLM ошибка при проверке пары: %s", str(exc)[:200])
            continue

        if checked % 10 == 0:
            elapsed = time.time() - start_time
            rate = checked / elapsed if elapsed > 0 else 0
            eta_min = (max_checks - checked) / rate / 60 if rate > 0 else 0
            logger.info(
                "Проверено %d/%d пар | Найдено коллизий: %d | Ошибок: %d | "
                "Скорость: %.1f пар/мин | ETA: %.1f мин",
                checked, max_checks, len(findings), errors,
                rate * 60, eta_min,
            )

    elapsed_total = time.time() - start_time
    logger.info(
        "Проверка завершена: %d пар за %.1f мин, найдено %d коллизий, %d ошибок",
        checked, elapsed_total / 60, len(findings), errors,
    )
    return findings


async def save_new_findings(findings: list[dict]) -> int:
    """Сохранить новые findings в БД (дописать, не удалять существующие)."""
    if not findings:
        logger.info("Нет новых findings для сохранения")
        return 0

    async with get_db() as db:
        # Загружаем существующие пары, чтобы не дублировать
        cursor = await db.execute(
            "SELECT norm_a_id, norm_b_id FROM findings WHERE type = 'contradiction'"
        )
        existing = set()
        for row in await cursor.fetchall():
            existing.add(tuple(sorted([row["norm_a_id"], row["norm_b_id"]])))

        count = 0
        for f in findings:
            pair_key = tuple(sorted([f["norm_a_id"], f["norm_b_id"]]))
            if pair_key in existing:
                logger.debug("Пропуск дубля: %s <-> %s", f["norm_a_id"], f["norm_b_id"])
                continue

            await db.execute(
                """INSERT INTO findings (type, severity, confidence, norm_a_id, norm_b_id,
                   explanation, cluster_id, recommendation)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    f["type"], f["severity"], f["confidence"],
                    f["norm_a_id"], f["norm_b_id"], f["explanation"],
                    f.get("cluster_id"), f.get("legal_principle", ""),
                ),
            )
            existing.add(pair_key)
            count += 1

        await db.commit()

    logger.info("Сохранено %d новых contradiction findings (из %d)", count, len(findings))
    return count


async def regenerate_graph() -> None:
    """Пересобрать граф после добавления новых findings."""
    logger.info("Пересборка графа...")
    builder = GraphBuilder()
    await builder.build_graph()
    graph_path = str(Path(settings.DB_PATH).parent / "graph.json")
    builder.save_json(graph_path)
    logger.info("Граф пересобран и сохранён: %s", graph_path)


async def main() -> None:
    total_start = time.time()
    logger.info("=" * 70)
    logger.info("РАСШИРЕННЫЙ ПОИСК ПРОТИВОРЕЧИЙ — ZanAlytics")
    logger.info("Цель: %d проверок, порог confidence >= 0.5", TARGET_CHECKS)
    logger.info("=" * 70)

    await init_db()

    # 1. Загружаем существующие пары
    existing_pairs = await load_existing_pairs()

    # 2. Загружаем кластеры
    clusters = await load_multi_doc_clusters()

    # 3. Генерируем умные пары
    pairs = await generate_smart_pairs(clusters, existing_pairs, max_pairs=TARGET_CHECKS + 100)

    if not pairs:
        logger.warning("Не удалось сгенерировать пары для проверки!")
        return

    # 4. Проверяем пары через LLM
    new_findings = await check_pairs_for_contradictions(pairs, max_checks=TARGET_CHECKS)

    # 5. Сохраняем новые findings
    saved = await save_new_findings(new_findings)

    # 6. Пересобираем граф
    await regenerate_graph()

    # Итоговая статистика
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT type, COUNT(*) as c, AVG(confidence) as avg_conf FROM findings GROUP BY type"
        )
        stats = await cursor.fetchall()

    elapsed = time.time() - total_start
    logger.info("=" * 70)
    logger.info("РАСШИРЕННЫЙ ПОИСК ЗАВЕРШЁН за %.1f мин", elapsed / 60)
    logger.info("  Проверено пар: %d", min(len(pairs), TARGET_CHECKS))
    logger.info("  Найдено новых коллизий: %d", len(new_findings))
    logger.info("  Сохранено в БД: %d", saved)
    logger.info("--- Итоговая статистика findings ---")
    for s in stats:
        logger.info(
            "  %s: %d (avg confidence: %.3f)",
            s["type"], s["c"], s["avg_conf"],
        )
    logger.info("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
