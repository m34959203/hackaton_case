"""Быстрый анализ — embedding-only дублирование + точечные LLM-проверки.

Запуск: cd backend && python -m scripts.quick_analyze
"""

import asyncio
import json
import logging
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import settings
from app.database import get_chroma_collection, get_db, init_db
from app.llm.client import OllamaClient
from app.llm.prompts import CONTRADICTION_PROMPT, DUPLICATION_PROMPT
from app.pipeline.graph_builder import GraphBuilder

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("quick_analyze")


async def embedding_based_dedup() -> list[dict]:
    """Найти дублирования только по cosine similarity (без LLM)."""
    logger.info("=== Embedding-based дублирование ===")
    collection = get_chroma_collection("norms")

    async with get_db() as db:
        cursor = await db.execute(
            "SELECT DISTINCT cluster_id FROM norms WHERE cluster_id IS NOT NULL"
        )
        cluster_rows = await cursor.fetchall()
    cluster_ids = [r[0] for r in cluster_rows]
    logger.info("Кластеров: %d", len(cluster_ids))

    findings = []
    for cid in cluster_ids:
        # Получаем нормы кластера
        async with get_db() as db:
            cursor = await db.execute(
                "SELECT id, doc_id, text FROM norms WHERE cluster_id = ?", (cid,)
            )
            norms = await cursor.fetchall()

        if len(norms) < 2:
            continue

        norm_ids = [n["id"] for n in norms]
        # Берём эмбеддинги из ChromaDB
        result = collection.get(ids=norm_ids[:100], include=["embeddings"])
        if result["embeddings"] is None or len(result["embeddings"]) < 2:
            continue

        # Считаем pairwise cosine similarity
        import numpy as np
        embs = np.array(result["embeddings"])
        norms_data = {n["id"]: n for n in norms}

        for i in range(len(result["ids"])):
            for j in range(i + 1, len(result["ids"])):
                a_id = result["ids"][i]
                b_id = result["ids"][j]
                # Cosine similarity
                dot = np.dot(embs[i], embs[j])
                mag = np.linalg.norm(embs[i]) * np.linalg.norm(embs[j])
                sim = float(dot / mag) if mag > 0 else 0

                if sim >= 0.92:  # Высокий порог для embedding-only
                    a_data = norms_data.get(a_id)
                    b_data = norms_data.get(b_id)
                    if not a_data or not b_data:
                        continue
                    # Пропускаем нормы из одного документа и одной статьи
                    if a_data["doc_id"] == b_data["doc_id"]:
                        a_art = a_id.split("_art")[1].split("_")[0] if "_art" in a_id else ""
                        b_art = b_id.split("_art")[1].split("_")[0] if "_art" in b_id else ""
                        if a_art == b_art:
                            continue
                    findings.append({
                        "type": "duplication",
                        "severity": "high" if sim >= 0.96 else "medium",
                        "confidence": round(sim, 3),
                        "norm_a_id": a_id,
                        "norm_b_id": b_id,
                        "explanation": f"Cosine similarity = {sim:.3f}. Нормы семантически идентичны.",
                        "cluster_id": cid,
                    })

    # Дедупликация и сортировка
    seen = set()
    unique = []
    for f in sorted(findings, key=lambda x: -x["confidence"]):
        key = tuple(sorted([f["norm_a_id"], f["norm_b_id"]]))
        if key not in seen:
            seen.add(key)
            unique.append(f)

    logger.info("Embedding-based дублирований: %d", len(unique))
    return unique[:200]  # Max 200


async def llm_contradiction_check(top_n: int = 50) -> list[dict]:
    """Проверить топ-N кандидатов на противоречие через LLM."""
    logger.info("=== LLM проверка противоречий (топ-%d кандидатов) ===", top_n)
    client = OllamaClient()
    findings = []

    # Берём кластеры с нормами из РАЗНЫХ документов
    async with get_db() as db:
        cursor = await db.execute("""
            SELECT cluster_id, COUNT(DISTINCT doc_id) as doc_count
            FROM norms WHERE cluster_id IS NOT NULL
            GROUP BY cluster_id
            HAVING doc_count >= 2
            ORDER BY doc_count DESC
            LIMIT 100
        """)
        clusters = await cursor.fetchall()

    logger.info("Кластеров с 2+ документами: %d", len(clusters))

    doc_titles = {}
    async with get_db() as db:
        cursor = await db.execute("SELECT id, title FROM documents")
        for row in await cursor.fetchall():
            doc_titles[row["id"]] = row["title"]

    checked = 0
    for cluster_row in clusters:
        if checked >= top_n:
            break

        cid = cluster_row["cluster_id"]
        async with get_db() as db:
            cursor = await db.execute(
                "SELECT id, doc_id, text FROM norms WHERE cluster_id = ? LIMIT 50",
                (cid,),
            )
            norms = await cursor.fetchall()

        # Группируем по документам
        by_doc: dict[str, list] = {}
        for n in norms:
            by_doc.setdefault(n["doc_id"], []).append(n)

        if len(by_doc) < 2:
            continue

        # Берём по 1 норме из каждого документа, формируем пары
        doc_ids = list(by_doc.keys())
        pairs_to_check = []
        for i in range(min(len(doc_ids), 3)):
            for j in range(i + 1, min(len(doc_ids), 3)):
                norm_a = by_doc[doc_ids[i]][0]
                norm_b = by_doc[doc_ids[j]][0]
                pairs_to_check.append((norm_a, norm_b))

        for norm_a, norm_b in pairs_to_check[:2]:
            if checked >= top_n:
                break

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
                    confidence = float(result.get("confidence", 0.7))
                    if confidence >= 0.6:
                        findings.append({
                            "type": "contradiction",
                            "severity": result.get("severity", "medium"),
                            "confidence": confidence,
                            "norm_a_id": norm_a["id"],
                            "norm_b_id": norm_b["id"],
                            "explanation": result.get("explanation", "Противоречие обнаружено LLM"),
                            "cluster_id": cid,
                        })
                        logger.info(
                            "Противоречие: %s <-> %s (%.2f, %s)",
                            norm_a["id"], norm_b["id"],
                            confidence, result.get("severity"),
                        )
            except Exception:
                logger.exception("LLM ошибка")
                continue

            if checked % 10 == 0:
                logger.info("Проверено %d/%d пар", checked, top_n)

    logger.info("Противоречий найдено: %d из %d проверок", len(findings), checked)
    return findings


async def find_outdated() -> list[dict]:
    """Найти устаревшие нормы по статусу документа."""
    logger.info("=== Поиск устаревших норм ===")
    findings = []

    async with get_db() as db:
        cursor = await db.execute("""
            SELECT n.id as norm_id, n.doc_id, n.text, d.title, d.status
            FROM norms n JOIN documents d ON n.doc_id = d.id
            WHERE d.status = 'expired'
            LIMIT 100
        """)
        expired_norms = await cursor.fetchall()

    for n in expired_norms:
        findings.append({
            "type": "outdated",
            "severity": "high",
            "confidence": 0.95,
            "norm_a_id": n["norm_id"],
            "norm_b_id": None,
            "explanation": f"Норма из документа '{n['title']}' со статусом 'утратил силу'.",
            "cluster_id": None,
        })

    logger.info("Устаревших норм: %d", len(findings))
    return findings[:100]


async def save_findings(findings: list[dict]) -> int:
    """Сохранить findings в SQLite."""
    async with get_db() as db:
        await db.execute("DELETE FROM findings")
        count = 0
        for f in findings:
            await db.execute(
                """INSERT INTO findings (type, severity, confidence, norm_a_id, norm_b_id,
                   explanation, cluster_id) VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (f["type"], f["severity"], f["confidence"],
                 f["norm_a_id"], f["norm_b_id"], f["explanation"], f.get("cluster_id")),
            )
            count += 1
        await db.commit()
    return count


async def main():
    total_start = time.time()
    logger.info("=" * 60)
    logger.info("БЫСТРЫЙ АНАЛИЗ ZanAlytics")
    logger.info("=" * 60)

    await init_db()

    # 1. Embedding-based дублирование (быстро)
    t = time.time()
    dup_findings = await embedding_based_dedup()
    logger.info("Дублирование: %d за %.1f сек", len(dup_findings), time.time() - t)

    # 2. LLM-проверка противоречий (50 пар)
    t = time.time()
    contra_findings = await llm_contradiction_check(top_n=50)
    logger.info("Противоречия: %d за %.1f сек", len(contra_findings), time.time() - t)

    # 3. Устаревшие нормы (по статусу)
    t = time.time()
    outdated_findings = await find_outdated()
    logger.info("Устаревшие: %d за %.1f сек", len(outdated_findings), time.time() - t)

    # Сохраняем
    all_findings = dup_findings + contra_findings + outdated_findings
    saved = await save_findings(all_findings)
    logger.info("Сохранено findings: %d", saved)

    # 4. Граф
    t = time.time()
    graph_builder = GraphBuilder()
    await graph_builder.build_graph()
    graph_path = str(Path(settings.DB_PATH).parent / "graph.json")
    graph_builder.save_json(graph_path)
    logger.info("Граф построен за %.1f сек: %s", time.time() - t, graph_path)

    logger.info("=" * 60)
    logger.info("АНАЛИЗ ЗАВЕРШЁН за %.1f сек", time.time() - total_start)
    logger.info("  Дублирований: %d", len(dup_findings))
    logger.info("  Противоречий: %d", len(contra_findings))
    logger.info("  Устаревших: %d", len(outdated_findings))
    logger.info("  Всего: %d", saved)
    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
