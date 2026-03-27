"""CLI-скрипт полного аналитического пайплайна.

Запуск:
    cd backend && python -m scripts.analyze

Порядок:
    1. Эмбеддинг норм → ChromaDB
    2. Кластеризация (UMAP + HDBSCAN)
    3. Поиск дублирований
    4. Поиск противоречий
    5. Поиск устаревших норм
    6. Построение графа → graph.json
"""

import asyncio
import logging
import sys
import time
from pathlib import Path

# Добавляем backend/ в sys.path для корректных импортов
_backend_dir = str(Path(__file__).resolve().parent.parent)
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

from app.config import settings
from app.database import get_db, init_db
from app.pipeline.clusterer import NormClusterer
from app.pipeline.contradiction import ContradictionDetector
from app.pipeline.dedup import DuplicationDetector
from app.pipeline.embedder import NormEmbedder
from app.pipeline.graph_builder import GraphBuilder
from app.pipeline.outdated import OutdatedDetector

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("analyze")


async def save_findings(findings: list) -> int:
    """Сохранить findings в SQLite. Возвращает количество сохранённых."""
    if not findings:
        return 0

    async with get_db() as db:
        count = 0
        for f in findings:
            await db.execute(
                """
                INSERT INTO findings (type, severity, confidence, norm_a_id, norm_b_id,
                                      explanation, cluster_id, recommendation)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    f.type,
                    f.severity,
                    f.confidence,
                    f.norm_a_id,
                    f.norm_b_id,
                    f.explanation,
                    f.cluster_id,
                    f.recommendation,
                ),
            )
            count += 1
        await db.commit()
    return count


async def run_pipeline() -> None:
    """Запуск полного аналитического пайплайна."""
    total_start = time.time()

    logger.info("=" * 60)
    logger.info("ЗАПУСК АНАЛИТИЧЕСКОГО ПАЙПЛАЙНА ZanAlytics")
    logger.info("=" * 60)

    # Инициализация БД
    await init_db()

    # Проверяем наличие норм
    async with get_db() as db:
        cursor = await db.execute("SELECT COUNT(*) as cnt FROM norms")
        row = await cursor.fetchone()
        norms_count = row["cnt"] if row else 0

    if norms_count == 0:
        logger.error("В БД нет норм. Сначала выполните парсинг документов.")
        return

    logger.info("В БД найдено %d норм для анализа", norms_count)

    # Очищаем предыдущие findings
    async with get_db() as db:
        await db.execute("DELETE FROM findings")
        await db.commit()
    logger.info("Предыдущие findings очищены")

    # ------------------------------------------------------------------
    # 1. Эмбеддинг
    # ------------------------------------------------------------------
    stage_start = time.time()
    logger.info("[1/6] Эмбеддинг норм...")

    embedder = NormEmbedder()
    await embedder.embed_all()

    logger.info("[1/6] Эмбеддинг завершён за %.1f сек", time.time() - stage_start)

    # ------------------------------------------------------------------
    # 2. Кластеризация
    # ------------------------------------------------------------------
    stage_start = time.time()
    logger.info("[2/6] Кластеризация норм...")

    clusterer = NormClusterer()
    clusters = await clusterer.cluster_norms()

    logger.info(
        "[2/6] Кластеризация завершена за %.1f сек: %d кластеров",
        time.time() - stage_start,
        len(clusters),
    )

    # ------------------------------------------------------------------
    # 3. Дублирование
    # ------------------------------------------------------------------
    stage_start = time.time()
    logger.info("[3/6] Поиск дублирований...")

    dedup = DuplicationDetector()
    dup_findings = await dedup.detect_duplications()
    dup_saved = await save_findings(dup_findings)

    logger.info(
        "[3/6] Дублирования завершены за %.1f сек: %d обнаружено",
        time.time() - stage_start,
        dup_saved,
    )

    # ------------------------------------------------------------------
    # 4. Противоречия
    # ------------------------------------------------------------------
    stage_start = time.time()
    logger.info("[4/6] Поиск противоречий...")

    contradiction = ContradictionDetector()
    contra_findings = await contradiction.detect_contradictions()
    contra_saved = await save_findings(contra_findings)

    logger.info(
        "[4/6] Противоречия завершены за %.1f сек: %d обнаружено",
        time.time() - stage_start,
        contra_saved,
    )

    # ------------------------------------------------------------------
    # 5. Устаревшие нормы
    # ------------------------------------------------------------------
    stage_start = time.time()
    logger.info("[5/6] Поиск устаревших норм...")

    outdated = OutdatedDetector()
    outdated_findings = await outdated.detect_outdated()
    outdated_saved = await save_findings(outdated_findings)

    logger.info(
        "[5/6] Устаревшие нормы завершены за %.1f сек: %d обнаружено",
        time.time() - stage_start,
        outdated_saved,
    )

    # ------------------------------------------------------------------
    # 6. Построение графа
    # ------------------------------------------------------------------
    stage_start = time.time()
    logger.info("[6/6] Построение графа...")

    graph_builder = GraphBuilder()
    await graph_builder.build_graph()

    graph_path = str(Path(settings.DB_PATH).parent / "graph.json")
    graph_builder.save_json(graph_path)

    logger.info("[6/6] Граф построен за %.1f сек", time.time() - stage_start)

    # ------------------------------------------------------------------
    # Итого
    # ------------------------------------------------------------------
    total_findings = dup_saved + contra_saved + outdated_saved
    total_time = time.time() - total_start

    logger.info("=" * 60)
    logger.info("ПАЙПЛАЙН ЗАВЕРШЁН за %.1f сек", total_time)
    logger.info("  Кластеров: %d", len(clusters))
    logger.info("  Дублирований: %d", dup_saved)
    logger.info("  Противоречий: %d", contra_saved)
    logger.info("  Устаревших: %d", outdated_saved)
    logger.info("  Всего findings: %d", total_findings)
    logger.info("  Граф: %s", graph_path)
    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(run_pipeline())
