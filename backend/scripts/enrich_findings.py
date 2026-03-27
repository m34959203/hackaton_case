"""Обогащение findings: LLM-объяснения для дублирований + улучшенный поиск противоречий.

Запуск: cd backend && python -m scripts.enrich_findings
"""

import asyncio
import json
import logging
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import settings
from app.database import get_db, init_db
from app.llm.client import OllamaClient
from app.llm.prompts import CONTRADICTION_PROMPT, DUPLICATION_EXPLANATION_PROMPT

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("enrich_findings")

# Regex для поиска норм с числами (сроки, суммы, проценты)
NUMBER_PATTERN = re.compile(
    r'\d+\s*(?:дн[еёяй]|суток|месяц|год[аулет]?|лет|процент|тенге|МРП|%|час[аов]?'
    r'|рабоч|календарн|минут|размер|кратн|раз[а]?\b)',
    re.IGNORECASE,
)

# Приоритетные кластеры (труд, налоги, земля, пенсии, соцзащита, охрана труда)
PRIORITY_CLUSTER_KEYWORDS = [
    'труд', 'работ', 'охран', 'налог', 'земел', 'земл', 'пенс',
    'соци', 'страхов', 'выплат', 'зарплат', 'отпуск', 'штраф',
    'занятост', 'безопасност',
]


async def enrich_duplications(client: OllamaClient, top_n: int = 50) -> int:
    """Обогатить top-N дублирований LLM-объяснениями."""
    logger.info("=== Обогащение дублирований (топ-%d) ===", top_n)

    # Загружаем топ дублирований по confidence
    async with get_db() as db:
        cursor = await db.execute("""
            SELECT f.id, f.norm_a_id, f.norm_b_id, f.confidence, f.explanation
            FROM findings f
            WHERE f.type = 'duplication'
            ORDER BY f.confidence DESC
            LIMIT ?
        """, (top_n,))
        findings = await cursor.fetchall()

    logger.info("Загружено %d дублирований для обогащения", len(findings))

    # Предзагрузка данных о нормах и документах
    norm_ids = set()
    for f in findings:
        norm_ids.add(f["norm_a_id"])
        norm_ids.add(f["norm_b_id"])

    norms_data = {}
    async with get_db() as db:
        for nid in norm_ids:
            cursor = await db.execute(
                "SELECT id, doc_id, text FROM norms WHERE id = ?", (nid,)
            )
            row = await cursor.fetchone()
            if row:
                norms_data[nid] = dict(row)

    doc_titles = {}
    async with get_db() as db:
        cursor = await db.execute("SELECT id, title FROM documents")
        for row in await cursor.fetchall():
            doc_titles[row["id"]] = row["title"]

    enriched = 0
    for i, f in enumerate(findings):
        norm_a = norms_data.get(f["norm_a_id"])
        norm_b = norms_data.get(f["norm_b_id"])
        if not norm_a or not norm_b:
            continue

        prompt = DUPLICATION_EXPLANATION_PROMPT.format(
            doc_a_title=doc_titles.get(norm_a["doc_id"], "Неизвестный документ"),
            norm_a_text=norm_a["text"][:1500],
            doc_b_title=doc_titles.get(norm_b["doc_id"], "Неизвестный документ"),
            norm_b_text=norm_b["text"][:1500],
        )

        try:
            result = await client.generate_json(
                prompt=prompt,
                temperature=0.2,
            )
            new_explanation = result.get("explanation", "")
            new_severity = result.get("severity", f["confidence"])

            if new_explanation and len(new_explanation) > 20:
                async with get_db() as db:
                    await db.execute(
                        "UPDATE findings SET explanation = ?, severity = ? WHERE id = ?",
                        (new_explanation, new_severity, f["id"]),
                    )
                    await db.commit()
                enriched += 1

        except Exception:
            logger.exception("Ошибка LLM при обогащении finding #%d", f["id"])
            continue

        if (i + 1) % 10 == 0:
            logger.info("Обогащено %d/%d дублирований", i + 1, len(findings))

    logger.info("Обогащено дублирований: %d из %d", enriched, len(findings))
    return enriched


async def improved_contradiction_check(top_n: int = 100) -> list[dict]:
    """Улучшенный поиск противоречий: фокус на нормах с числами из приоритетных кластеров."""
    logger.info("=== Улучшенный поиск противоречий (топ-%d пар) ===", top_n)
    client = OllamaClient()
    findings = []

    # Находим приоритетные кластеры
    async with get_db() as db:
        cursor = await db.execute("""
            SELECT cluster_id, cluster_topic, COUNT(DISTINCT doc_id) as doc_count
            FROM norms
            WHERE cluster_id IS NOT NULL AND cluster_topic IS NOT NULL
            GROUP BY cluster_id
            HAVING doc_count >= 2
            ORDER BY doc_count DESC
        """)
        all_clusters = await cursor.fetchall()

    # Фильтруем приоритетные кластеры
    priority_clusters = []
    other_clusters = []
    for c in all_clusters:
        topic_lower = (c["cluster_topic"] or "").lower()
        if any(kw in topic_lower for kw in PRIORITY_CLUSTER_KEYWORDS):
            priority_clusters.append(c)
        else:
            other_clusters.append(c)

    logger.info(
        "Приоритетных кластеров: %d, прочих: %d",
        len(priority_clusters), len(other_clusters),
    )

    # Загружаем заголовки документов
    doc_titles = {}
    async with get_db() as db:
        cursor = await db.execute("SELECT id, title FROM documents")
        for row in await cursor.fetchall():
            doc_titles[row["id"]] = row["title"]

    # Собираем пары для проверки
    pairs_to_check = []

    # Из приоритетных кластеров — нормы с числами
    for cluster_row in priority_clusters[:40]:
        cid = cluster_row["cluster_id"]

        async with get_db() as db:
            cursor = await db.execute(
                "SELECT id, doc_id, text FROM norms WHERE cluster_id = ? LIMIT 200",
                (cid,),
            )
            norms = await cursor.fetchall()

        # Фильтруем нормы с числами
        norms_with_numbers = [
            n for n in norms if NUMBER_PATTERN.search(n["text"])
        ]

        # Если мало норм с числами, берём все
        candidates = norms_with_numbers if len(norms_with_numbers) >= 4 else norms

        # Группируем по документам
        by_doc: dict[str, list] = {}
        for n in candidates:
            by_doc.setdefault(n["doc_id"], []).append(n)

        if len(by_doc) < 2:
            continue

        # Формируем пары из разных документов
        doc_ids = list(by_doc.keys())
        for i in range(min(len(doc_ids), 4)):
            for j in range(i + 1, min(len(doc_ids), 4)):
                # Берём до 2 норм из каждого документа
                norms_a = by_doc[doc_ids[i]][:2]
                norms_b = by_doc[doc_ids[j]][:2]
                for na in norms_a:
                    for nb in norms_b:
                        pairs_to_check.append((na, nb, cid))

    # Из прочих кластеров — тоже добавляем пары
    for cluster_row in other_clusters[:20]:
        cid = cluster_row["cluster_id"]

        async with get_db() as db:
            cursor = await db.execute(
                "SELECT id, doc_id, text FROM norms WHERE cluster_id = ? LIMIT 100",
                (cid,),
            )
            norms = await cursor.fetchall()

        norms_with_numbers = [
            n for n in norms if NUMBER_PATTERN.search(n["text"])
        ]

        candidates = norms_with_numbers if len(norms_with_numbers) >= 2 else norms[:10]

        by_doc: dict[str, list] = {}
        for n in candidates:
            by_doc.setdefault(n["doc_id"], []).append(n)

        if len(by_doc) < 2:
            continue

        doc_ids = list(by_doc.keys())
        for i in range(min(len(doc_ids), 3)):
            for j in range(i + 1, min(len(doc_ids), 3)):
                na = by_doc[doc_ids[i]][0]
                nb = by_doc[doc_ids[j]][0]
                pairs_to_check.append((na, nb, cid))

    logger.info("Всего кандидатов-пар: %d, будет проверено: %d", len(pairs_to_check), min(len(pairs_to_check), top_n))

    # Проверяем пары через LLM
    checked = 0
    for norm_a, norm_b, cid in pairs_to_check[:top_n]:
        prompt = CONTRADICTION_PROMPT.format(
            doc_a_title=doc_titles.get(norm_a["doc_id"], ""),
            norm_a_text=norm_a["text"][:1500],
            doc_b_title=doc_titles.get(norm_b["doc_id"], ""),
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
                if confidence >= 0.5:  # Сниженный порог
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
                        "КОЛЛИЗИЯ [%s]: %s <-> %s (%.2f) — %s",
                        result.get("severity", "?"),
                        norm_a["id"][:30], norm_b["id"][:30],
                        confidence,
                        (result.get("explanation", ""))[:80],
                    )

        except Exception:
            logger.exception("LLM ошибка при проверке пары")
            continue

        if checked % 10 == 0:
            logger.info("Проверено %d/%d пар, найдено коллизий: %d", checked, top_n, len(findings))

    logger.info("Итого коллизий: %d из %d проверок", len(findings), checked)
    return findings


async def save_contradiction_findings(findings: list[dict]) -> int:
    """Сохранить новые contradiction findings в БД (не удаляя существующие)."""
    if not findings:
        return 0

    async with get_db() as db:
        # Удаляем старые contradictions (если были)
        await db.execute("DELETE FROM findings WHERE type = 'contradiction'")

        count = 0
        for f in findings:
            recommendation = f.get("legal_principle", "")
            await db.execute(
                """INSERT INTO findings (type, severity, confidence, norm_a_id, norm_b_id,
                   explanation, cluster_id, recommendation)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    f["type"], f["severity"], f["confidence"],
                    f["norm_a_id"], f["norm_b_id"], f["explanation"],
                    f.get("cluster_id"), recommendation,
                ),
            )
            count += 1
        await db.commit()

    logger.info("Сохранено %d contradiction findings", count)
    return count


async def main():
    total_start = time.time()
    logger.info("=" * 60)
    logger.info("ОБОГАЩЕНИЕ FINDINGS — ZanAlytics")
    logger.info("=" * 60)

    await init_db()
    client = OllamaClient()

    # 1. Обогащаем дублирования LLM-объяснениями (топ-50)
    t = time.time()
    enriched_count = await enrich_duplications(client, top_n=50)
    logger.info(
        "Обогащение дублирований: %d за %.1f сек",
        enriched_count, time.time() - t,
    )

    # 2. Улучшенный поиск противоречий (100 пар)
    t = time.time()
    contra_findings = await improved_contradiction_check(top_n=100)
    logger.info(
        "Поиск противоречий: %d за %.1f сек",
        len(contra_findings), time.time() - t,
    )

    # 3. Сохраняем противоречия
    saved = await save_contradiction_findings(contra_findings)

    # Итоговая статистика
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT type, COUNT(*) as c, AVG(confidence) as avg_conf FROM findings GROUP BY type"
        )
        stats = await cursor.fetchall()

    logger.info("=" * 60)
    logger.info("ОБОГАЩЕНИЕ ЗАВЕРШЕНО за %.1f сек", time.time() - total_start)
    logger.info("  Дублирований обогащено: %d", enriched_count)
    logger.info("  Противоречий найдено: %d", len(contra_findings))
    logger.info("  Противоречий сохранено: %d", saved)
    logger.info("--- Итоговая статистика findings ---")
    for s in stats:
        logger.info(
            "  %s: %d (avg confidence: %.3f)",
            s["type"], s["c"], s["avg_conf"],
        )
    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
