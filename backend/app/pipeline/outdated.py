"""Выявление устаревших норм."""

import logging
import re

from app.config import settings
from app.database import get_db
from app.llm.client import OllamaClient
from app.llm.prompts import OUTDATED_PROMPT
from app.models.finding import FindingCreate

logger = logging.getLogger(__name__)

# Паттерны временных маркеров (даты в прошлом, устаревшие сроки)
_TEMPORAL_PATTERNS = [
    re.compile(r"до\s+20[01]\d\s+года", re.IGNORECASE),
    re.compile(r"до\s+1\s+января\s+20[01]\d", re.IGNORECASE),
    re.compile(r"в\s+(?:19|200)\d\s+году", re.IGNORECASE),
    re.compile(r"утратив(?:ший|шая|шее|шие)\s+силу", re.IGNORECASE),
    re.compile(r"прекрат(?:ить|ившей|ившего)\s+действие", re.IGNORECASE),
]


class OutdatedDetector:
    """Детектор устаревших норм."""

    def __init__(self) -> None:
        self._client = OllamaClient()

    async def detect_outdated(self) -> list[FindingCreate]:
        """Выявить устаревшие нормы.

        Проверки:
            1. Статус документа = 'expired' или класс status_yts.
            2. Ссылки на документы со статусом 'expired'.
            3. Временные маркеры (даты в прошлом, устаревшие формулировки).
            4. Подтверждение через LLM с использованием OUTDATED_PROMPT.

        Returns:
            Список FindingCreate для сохранения в БД.
        """
        findings: list[FindingCreate] = []

        # 1. Проверка по статусу документа
        expired_findings = await self._check_expired_status()
        findings.extend(expired_findings)

        # 2. Проверка ссылок на отменённые документы
        ref_findings = await self._check_expired_references()
        findings.extend(ref_findings)

        # 3. Проверка временных маркеров в тексте
        temporal_findings = await self._check_temporal_markers()
        findings.extend(temporal_findings)

        logger.info("Обнаружено %d устаревших норм", len(findings))
        return findings

    async def _check_expired_status(self) -> list[FindingCreate]:
        """Найти нормы из документов со статусом expired/status_yts."""
        findings: list[FindingCreate] = []

        async with get_db() as db:
            cursor = await db.execute(
                """
                SELECT n.id AS norm_id, n.text, n.cluster_id,
                       d.id AS doc_id, d.title, d.status, d.date_adopted
                FROM norms n
                JOIN documents d ON n.doc_id = d.id
                WHERE d.status = 'expired'
                """
            )
            rows = await cursor.fetchall()

        if not rows:
            logger.info("Нет документов со статусом expired")
            return findings

        logger.info("Найдено %d норм из документов со статусом expired", len(rows))

        for row in rows:
            finding = await self._confirm_outdated(
                norm_id=row["norm_id"],
                norm_text=row["text"],
                doc_title=row["title"],
                date_adopted=row["date_adopted"] or "неизвестна",
                current_status="утратил силу",
                referenced_docs_status="н/д",
                cluster_id=row["cluster_id"],
                reason="status",
                base_severity="high",
                base_confidence=0.95,
            )
            if finding:
                findings.append(finding)

        return findings

    async def _check_expired_references(self) -> list[FindingCreate]:
        """Найти нормы, ссылающиеся на отменённые документы."""
        findings: list[FindingCreate] = []

        async with get_db() as db:
            # Нормы из документов, которые ссылаются на expired-документы
            cursor = await db.execute(
                """
                SELECT DISTINCT n.id AS norm_id, n.text, n.cluster_id,
                       d_from.title AS doc_title, d_from.date_adopted,
                       d_from.status AS from_status,
                       d_to.title AS ref_doc_title, d_to.status AS ref_status
                FROM cross_refs cr
                JOIN documents d_from ON cr.from_doc = d_from.id
                JOIN documents d_to ON cr.to_doc = d_to.id
                JOIN norms n ON n.doc_id = d_from.id
                WHERE d_to.status = 'expired'
                AND d_from.status != 'expired'
                """
            )
            rows = await cursor.fetchall()

        if not rows:
            logger.info("Нет ссылок на отменённые документы")
            return findings

        logger.info("Найдено %d норм со ссылками на отменённые документы", len(rows))

        # Дедупликация по norm_id (одна норма может ссылаться на несколько expired)
        seen: set[str] = set()
        for row in rows:
            norm_id = row["norm_id"]
            if norm_id in seen:
                continue
            seen.add(norm_id)

            ref_info = f"{row['ref_doc_title']} (статус: {row['ref_status']})"

            finding = await self._confirm_outdated(
                norm_id=norm_id,
                norm_text=row["text"],
                doc_title=row["doc_title"],
                date_adopted=row["date_adopted"] or "неизвестна",
                current_status=row["from_status"],
                referenced_docs_status=ref_info,
                cluster_id=row["cluster_id"],
                reason="references",
                base_severity="high",
                base_confidence=0.85,
            )
            if finding:
                findings.append(finding)

        return findings

    async def _check_temporal_markers(self) -> list[FindingCreate]:
        """Найти нормы с временными маркерами (даты в прошлом)."""
        findings: list[FindingCreate] = []

        async with get_db() as db:
            cursor = await db.execute(
                """
                SELECT n.id AS norm_id, n.text, n.cluster_id,
                       d.title, d.date_adopted, d.status
                FROM norms n
                JOIN documents d ON n.doc_id = d.id
                WHERE d.status != 'expired'
                """
            )
            rows = await cursor.fetchall()

        matched_norms: list[dict] = []
        for row in rows:
            text = row["text"]
            for pattern in _TEMPORAL_PATTERNS:
                if pattern.search(text):
                    matched_norms.append(dict(row))
                    break

        if not matched_norms:
            logger.info("Нет норм с временными маркерами")
            return findings

        logger.info("Найдено %d норм с временными маркерами", len(matched_norms))

        for norm_data in matched_norms:
            finding = await self._confirm_outdated(
                norm_id=norm_data["norm_id"],
                norm_text=norm_data["text"],
                doc_title=norm_data["title"],
                date_adopted=norm_data["date_adopted"] or "неизвестна",
                current_status=norm_data["status"],
                referenced_docs_status="н/д",
                cluster_id=norm_data["cluster_id"],
                reason="content",
                base_severity="medium",
                base_confidence=0.7,
            )
            if finding:
                findings.append(finding)

        return findings

    async def _confirm_outdated(
        self,
        norm_id: str,
        norm_text: str,
        doc_title: str,
        date_adopted: str,
        current_status: str,
        referenced_docs_status: str,
        cluster_id: int | None,
        reason: str,
        base_severity: str,
        base_confidence: float,
    ) -> FindingCreate | None:
        """Подтвердить устаревшую норму через LLM.

        Returns:
            FindingCreate если устаревание подтверждено, иначе None.
        """
        prompt = OUTDATED_PROMPT.format(
            norm_text=norm_text,
            doc_title=doc_title,
            date_adopted=date_adopted,
            current_status=current_status,
            referenced_docs_status=referenced_docs_status,
        )

        try:
            result = await self._client.generate_json(
                prompt=prompt,
                temperature=settings.LLM_TEMPERATURE_ANALYSIS,
            )
        except Exception:
            logger.exception("Ошибка LLM при проверке устаревания нормы %s", norm_id)
            # Для expired-документов создаём finding даже без LLM
            if reason == "status":
                return FindingCreate(
                    type="outdated",
                    severity=base_severity,
                    confidence=base_confidence,
                    norm_a_id=norm_id,
                    explanation=f"Документ '{doc_title}' утратил силу.",
                    cluster_id=cluster_id,
                    recommendation="Необходимо проверить актуальность нормы.",
                )
            return None

        is_outdated = result.get("is_outdated", False)
        if not is_outdated:
            return None

        confidence = float(result.get("confidence", base_confidence))
        severity = result.get("severity", base_severity)
        explanation = result.get("explanation", f"Норма устарела (причина: {reason})")

        logger.info(
            "Устаревание подтверждено: %s (причина=%s, confidence=%.2f)",
            norm_id,
            reason,
            confidence,
        )

        return FindingCreate(
            type="outdated",
            severity=severity,
            confidence=confidence,
            norm_a_id=norm_id,
            explanation=explanation,
            cluster_id=cluster_id,
            recommendation=result.get("recommendation"),
        )
