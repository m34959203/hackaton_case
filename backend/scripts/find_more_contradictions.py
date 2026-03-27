"""Расширенный поиск противоречий: 300 пар с фокусом на нормы с числами из разных документов.

Стратегия:
1. Находим все нормы с числовыми данными (сроки, суммы, проценты).
2. Для каждой нормы ищем семантически похожие нормы из ДРУГИХ документов через ChromaDB.
3. Фильтруем: обе нормы должны содержать числа, similarity 0.7-0.95 (не дубликаты).
4. Проверяем 300 лучших пар через LLM с порогом confidence >= 0.5.
5. Дописываем новые findings в SQLite (не удаляя существующие).
6. Пересобираем граф.

Запуск: cd backend && python -m scripts.find_more_contradictions
"""

import asyncio
import logging
import random
import re
import sys
import time
from pathlib import Path

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

TARGET_CHECKS = 300
MIN_NORM_LENGTH = 80
# Similarity range: high enough to be same topic, low enough to not be duplicate
SIM_MIN = 0.70
SIM_MAX = 0.96


async def load_existing_pairs() -> set[tuple[str, str]]:
    """Загрузить уже проверенные пары (существующие contradiction findings)."""
    pairs = set()
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT norm_a_id, norm_b_id FROM findings WHERE type = 'contradiction'"
        )
        rows = await cursor.fetchall()
        for row in rows:
            pair = tuple(sorted([row["norm_a_id"], row["norm_b_id"]]))
            pairs.add(pair)
    logger.info("Уже проверенных пар (contradictions в БД): %d", len(pairs))
    return pairs


async def load_norms_with_numbers() -> dict[str, dict]:
    """Загрузить все нормы с числовыми данными (>80 символов)."""
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT id, doc_id, text, cluster_id FROM norms WHERE LENGTH(text) > ?",
            (MIN_NORM_LENGTH,),
        )
        rows = await cursor.fetchall()

    norms = {}
    for r in rows:
        if NUMBER_PATTERN.search(r["text"]):
            norms[r["id"]] = {
                "id": r["id"],
                "doc_id": r["doc_id"],
                "text": r["text"],
                "cluster_id": r["cluster_id"],
            }
    logger.info("Норм с числами (>%d символов): %d", MIN_NORM_LENGTH, len(norms))
    return norms


def get_embeddings_for_norms(norm_ids: list[str]) -> dict[str, list[float]]:
    """Получить embeddings норм из ChromaDB (синхронно)."""
    collection = get_chroma_collection("norms")
    result = {}
    batch_size = 200
    for i in range(0, len(norm_ids), batch_size):
        batch = norm_ids[i:i + batch_size]
        try:
            data = collection.get(ids=batch, include=["embeddings"])
            if data and data.get("ids") and data.get("embeddings") is not None:
                for j, nid in enumerate(data["ids"]):
                    emb = data["embeddings"][j]
                    if emb is not None and len(emb) > 0:
                        result[nid] = list(emb)
        except Exception as exc:
            logger.warning("ChromaDB get failed for batch at %d: %s", i, str(exc)[:100])
    logger.info("Получено embeddings: %d из %d", len(result), len(norm_ids))
    return result


def find_cross_doc_similar_pairs(
    norms: dict[str, dict],
    embeddings: dict[str, list[float]],
    existing_pairs: set[tuple[str, str]],
    max_pairs: int = 500,
    sample_size: int = 400,
) -> list[tuple[dict, dict, float]]:
    """Для выборки норм найти наиболее похожие нормы из ДРУГИХ документов через ChromaDB."""
    collection = get_chroma_collection("norms")

    # Берём случайную выборку норм с embeddings
    norm_ids_with_emb = [nid for nid in norms if nid in embeddings]
    if len(norm_ids_with_emb) > sample_size:
        sample_ids = random.sample(norm_ids_with_emb, sample_size)
    else:
        sample_ids = norm_ids_with_emb

    logger.info("Выборка для поиска пар: %d норм", len(sample_ids))

    raw_pairs: list[tuple[str, str, float]] = []
    seen_pairs: set[tuple[str, str]] = set()

    for i in range(0, len(sample_ids), 20):
        batch_ids = sample_ids[i:i + 20]
        batch_embs = [embeddings[nid] for nid in batch_ids]

        try:
            results = collection.query(
                query_embeddings=batch_embs,
                n_results=15,
                include=["distances"],
            )
        except Exception:
            logger.debug("ChromaDB query failed for batch at %d", i)
            continue

        for idx, qid in enumerate(batch_ids):
            if idx >= len(results["ids"]):
                break
            q_doc = norms[qid]["doc_id"]

            for j, rid in enumerate(results["ids"][idx]):
                if rid == qid:
                    continue
                # Должна быть норма с числами
                if rid not in norms:
                    continue
                # Должна быть из другого документа
                if norms[rid]["doc_id"] == q_doc:
                    continue

                dist = results["distances"][idx][j]
                sim = 1.0 - dist  # cosine distance -> similarity

                # Фильтр по similarity range
                if sim < SIM_MIN or sim > SIM_MAX:
                    continue

                pair_key = tuple(sorted([qid, rid]))
                if pair_key in seen_pairs or pair_key in existing_pairs:
                    continue
                seen_pairs.add(pair_key)

                raw_pairs.append((qid, rid, sim))

        if (i + 20) % 100 == 0:
            logger.info(
                "ChromaDB query: обработано %d/%d, найдено пар: %d",
                min(i + 20, len(sample_ids)), len(sample_ids), len(raw_pairs),
            )

    # Сортируем по сходству (DESC) — наиболее похожие нормы с числами из разных документов
    raw_pairs.sort(key=lambda x: x[2], reverse=True)

    # Конвертируем в нужный формат
    result = []
    for qid, rid, sim in raw_pairs[:max_pairs]:
        result.append((norms[qid], norms[rid], sim))

    logger.info(
        "Итого пар для проверки: %d (из %d кандидатов, диапазон sim: %.2f-%.2f)",
        len(result), len(raw_pairs), SIM_MIN, SIM_MAX,
    )
    return result


async def check_pairs_for_contradictions(
    pairs: list[tuple[dict, dict, float]],
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

    for norm_a, norm_b, sim in pairs[:max_checks]:
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
                        "cluster_id": norm_a.get("cluster_id"),
                        "legal_principle": result.get("legal_principle", ""),
                        "similarity": sim,
                    })
                    logger.info(
                        ">>> КОЛЛИЗИЯ #%d [%s, %.2f, sim=%.3f]: %s <-> %s — %s",
                        len(findings),
                        result.get("severity", "?"),
                        confidence,
                        sim,
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
    logger.info("Similarity range: %.2f - %.2f", SIM_MIN, SIM_MAX)
    logger.info("=" * 70)

    await init_db()

    # 1. Загружаем существующие пары
    existing_pairs = await load_existing_pairs()

    # 2. Загружаем нормы с числами
    norms = await load_norms_with_numbers()
    if not norms:
        logger.warning("Нет норм с числами!")
        return

    # 3. Получаем embeddings из ChromaDB
    embeddings = get_embeddings_for_norms(list(norms.keys()))

    # 4. Находим cross-doc пары через similarity search
    pairs = find_cross_doc_similar_pairs(
        norms, embeddings, existing_pairs,
        max_pairs=TARGET_CHECKS + 100,
        sample_size=500,
    )

    if not pairs:
        logger.warning("Не удалось найти пары для проверки!")
        return

    # 5. Проверяем пары через LLM
    new_findings = await check_pairs_for_contradictions(pairs, max_checks=TARGET_CHECKS)

    # 6. Сохраняем новые findings
    saved = await save_new_findings(new_findings)

    # 7. Пересобираем граф
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
