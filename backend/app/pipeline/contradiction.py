"""Выявление противоречий между нормами."""

import logging

from app.config import settings
from app.database import get_db
from app.llm.client import OllamaClient
from app.llm.prompts import CONTRADICTION_PROMPT
from app.models.finding import FindingCreate

logger = logging.getLogger(__name__)


class ContradictionDetector:
    """Детектор противоречий между нормами из разных документов."""

    def __init__(self) -> None:
        self._client = OllamaClient()

    async def detect_contradictions(self) -> list[FindingCreate]:
        """Выявить противоречия между нормами в кластерах.

        Алгоритм:
            1. Для каждого кластера найти пары норм из РАЗНЫХ документов.
            2. Отправить каждую пару на анализ LLM через CONTRADICTION_PROMPT.
            3. Отфильтровать по confidence >= CONTRADICTION_CONFIDENCE_MIN.
            4. Создать Finding для подтверждённых противоречий.

        Returns:
            Список FindingCreate для сохранения в БД.
        """
        findings: list[FindingCreate] = []
        min_confidence = settings.CONTRADICTION_CONFIDENCE_MIN

        # Загружаем кластеры с информацией о документах
        clusters = await self._load_clusters_with_docs()
        if not clusters:
            logger.warning("Нет кластеров для анализа противоречий")
            return findings

        logger.info(
            "Анализ противоречий: %d кластеров, мин. confidence=%.2f",
            len(clusters),
            min_confidence,
        )

        # Загружаем заголовки документов
        doc_titles = await self._load_doc_titles()

        for cluster_id, norms in clusters.items():
            # Формируем пары из разных документов
            cross_doc_pairs = self._get_cross_doc_pairs(norms)

            if not cross_doc_pairs:
                continue

            logger.info(
                "Кластер %d: %d межд.-документных пар для анализа",
                cluster_id,
                len(cross_doc_pairs),
            )

            for norm_a, norm_b in cross_doc_pairs:
                finding = await self._check_contradiction(
                    norm_a=norm_a,
                    norm_b=norm_b,
                    doc_titles=doc_titles,
                    min_confidence=min_confidence,
                    cluster_id=cluster_id,
                )
                if finding:
                    findings.append(finding)

        logger.info("Обнаружено %d противоречий", len(findings))
        return findings

    async def _check_contradiction(
        self,
        norm_a: dict,
        norm_b: dict,
        doc_titles: dict[str, str],
        min_confidence: float,
        cluster_id: int,
    ) -> FindingCreate | None:
        """Проверить пару норм на противоречие через LLM.

        Returns:
            FindingCreate если противоречие подтверждено, иначе None.
        """
        doc_a_title = doc_titles.get(norm_a["doc_id"], norm_a["doc_id"])
        doc_b_title = doc_titles.get(norm_b["doc_id"], norm_b["doc_id"])

        prompt = CONTRADICTION_PROMPT.format(
            doc_a_title=doc_a_title,
            norm_a_text=norm_a["text"],
            doc_b_title=doc_b_title,
            norm_b_text=norm_b["text"],
        )

        try:
            result = await self._client.generate_json(
                prompt=prompt,
                temperature=settings.LLM_TEMPERATURE_ANALYSIS,
            )
        except Exception:
            logger.exception(
                "Ошибка LLM при проверке противоречия %s - %s",
                norm_a["id"],
                norm_b["id"],
            )
            return None

        is_contradiction = result.get("is_contradiction", False)
        confidence = float(result.get("confidence", 0.0))

        if not is_contradiction or confidence < min_confidence:
            return None

        severity = result.get("severity", "medium")
        explanation = result.get("explanation", "Противоречие подтверждено LLM")
        legal_principle = result.get("legal_principle", "")

        if legal_principle:
            explanation = f"{explanation}\n\nПрименимый принцип: {legal_principle}"

        logger.info(
            "Противоречие подтверждено: %s <-> %s (confidence=%.2f, severity=%s)",
            norm_a["id"],
            norm_b["id"],
            confidence,
            severity,
        )

        return FindingCreate(
            type="contradiction",
            severity=severity,
            confidence=confidence,
            norm_a_id=norm_a["id"],
            norm_b_id=norm_b["id"],
            explanation=explanation,
            cluster_id=cluster_id,
        )

    def _get_cross_doc_pairs(
        self, norms: list[dict]
    ) -> list[tuple[dict, dict]]:
        """Сформировать пары норм из разных документов.

        Ограничивает количество пар для больших кластеров.
        """
        pairs: list[tuple[dict, dict]] = []
        max_pairs = 5  # ограничение для контроля нагрузки на LLM (хакатон)

        for i in range(len(norms)):
            for j in range(i + 1, len(norms)):
                if norms[i]["doc_id"] != norms[j]["doc_id"]:
                    pairs.append((norms[i], norms[j]))
                    if len(pairs) >= max_pairs:
                        return pairs
        return pairs

    async def _load_clusters_with_docs(self) -> dict[int, list[dict]]:
        """Загрузить кластеры с текстами и doc_id."""
        async with get_db() as db:
            cursor = await db.execute(
                "SELECT id, doc_id, text, cluster_id FROM norms "
                "WHERE cluster_id IS NOT NULL ORDER BY cluster_id"
            )
            rows = await cursor.fetchall()

        clusters: dict[int, list[dict]] = {}
        for row in rows:
            cid = row["cluster_id"]
            clusters.setdefault(cid, []).append(
                {
                    "id": row["id"],
                    "doc_id": row["doc_id"],
                    "text": row["text"],
                }
            )
        return clusters

    async def _load_doc_titles(self) -> dict[str, str]:
        """Загрузить заголовки документов."""
        async with get_db() as db:
            cursor = await db.execute("SELECT id, title FROM documents")
            rows = await cursor.fetchall()
        return {row["id"]: row["title"] for row in rows}
