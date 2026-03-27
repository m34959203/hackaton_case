"""Выявление дублирования норм."""

import logging

from app.config import settings
from app.database import get_chroma_collection, get_db
from app.llm.client import OllamaClient
from app.llm.prompts import DUPLICATION_PROMPT
from app.models.finding import FindingCreate
from app.pipeline.embedder import NormEmbedder

logger = logging.getLogger(__name__)


class DuplicationDetector:
    """Детектор дублирования норм внутри кластеров."""

    def __init__(self) -> None:
        self._client = OllamaClient()
        self._embedder = NormEmbedder()
        self._collection = get_chroma_collection("norms")

    async def detect_duplications(self) -> list[FindingCreate]:
        """Выявить дублирующиеся нормы.

        Алгоритм:
            1. Для каждого кластера получить попарное сходство норм.
            2. Отфильтровать пары с cosine similarity > SIMILARITY_THRESHOLD.
            3. Подтвердить через LLM с использованием DUPLICATION_PROMPT.
            4. Создать Finding для подтверждённых дублирований.

        Returns:
            Список FindingCreate для сохранения в БД.
        """
        threshold = settings.SIMILARITY_THRESHOLD
        findings: list[FindingCreate] = []

        # Загружаем кластеры из БД
        clusters = await self._load_clusters()
        if not clusters:
            logger.warning("Нет кластеров для анализа дублирования")
            return findings

        logger.info(
            "Анализ дублирования: %d кластеров, порог сходства %.2f",
            len(clusters),
            threshold,
        )

        # Загружаем тексты норм
        norm_texts = await self._load_norm_texts()

        for cluster_id, norm_ids in clusters.items():
            if len(norm_ids) < 2:
                continue

            # Получаем попарные сходства
            pairs = self._embedder.get_pairwise_similarity(norm_ids)

            # Фильтруем по порогу
            high_sim_pairs = [
                (a_id, b_id, score)
                for a_id, b_id, score in pairs
                if score >= threshold
            ]

            if not high_sim_pairs:
                continue

            # Ограничиваем количество пар на кластер (топ-10 по сходству)
            high_sim_pairs.sort(key=lambda x: x[2], reverse=True)
            high_sim_pairs = high_sim_pairs[:10]

            logger.info(
                "Кластер %d: %d пар для проверки LLM",
                cluster_id,
                len(high_sim_pairs),
            )

            for norm_a_id, norm_b_id, score in high_sim_pairs:
                text_a = norm_texts.get(norm_a_id, "")
                text_b = norm_texts.get(norm_b_id, "")

                if not text_a or not text_b:
                    continue

                # Подтверждаем через LLM
                finding = await self._confirm_duplication(
                    norm_a_id, norm_b_id, text_a, text_b, score, cluster_id
                )
                if finding:
                    findings.append(finding)

        logger.info("Обнаружено %d дублирований", len(findings))
        return findings

    async def _confirm_duplication(
        self,
        norm_a_id: str,
        norm_b_id: str,
        text_a: str,
        text_b: str,
        score: float,
        cluster_id: int,
    ) -> FindingCreate | None:
        """Подтвердить дублирование через LLM.

        Returns:
            FindingCreate если дублирование подтверждено, иначе None.
        """
        prompt = DUPLICATION_PROMPT.format(
            norm_a_text=text_a,
            norm_b_text=text_b,
        )

        try:
            result = await self._client.generate_json(
                prompt=prompt,
                temperature=settings.LLM_TEMPERATURE_ANALYSIS,
            )
        except Exception:
            logger.exception(
                "Ошибка LLM при проверке дублирования %s - %s", norm_a_id, norm_b_id
            )
            return None

        is_dup = result.get("is_duplication", False)
        if not is_dup:
            return None

        confidence = float(result.get("confidence", score))
        severity = result.get("severity", "medium")
        explanation = result.get("explanation", "Дублирование подтверждено LLM")

        logger.info(
            "Дублирование подтверждено: %s <-> %s (confidence=%.2f, severity=%s)",
            norm_a_id,
            norm_b_id,
            confidence,
            severity,
        )

        return FindingCreate(
            type="duplication",
            severity=severity,
            confidence=confidence,
            norm_a_id=norm_a_id,
            norm_b_id=norm_b_id,
            explanation=explanation,
            cluster_id=cluster_id,
        )

    async def _load_clusters(self) -> dict[int, list[str]]:
        """Загрузить кластеры из БД."""
        async with get_db() as db:
            cursor = await db.execute(
                "SELECT id, cluster_id FROM norms WHERE cluster_id IS NOT NULL ORDER BY cluster_id"
            )
            rows = await cursor.fetchall()

        clusters: dict[int, list[str]] = {}
        for row in rows:
            cid = row["cluster_id"]
            clusters.setdefault(cid, []).append(row["id"])
        return clusters

    async def _load_norm_texts(self) -> dict[str, str]:
        """Загрузить тексты всех норм из БД."""
        async with get_db() as db:
            cursor = await db.execute("SELECT id, text FROM norms")
            rows = await cursor.fetchall()
        return {row["id"]: row["text"] for row in rows}
