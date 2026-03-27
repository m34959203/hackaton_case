"""Эндпоинт сравнения двух норм."""

import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.database import get_db
from app.models.document import NormBrief
from app.models.finding import FindingResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/compare", tags=["Сравнение"])


# --- Pydantic-модели ответов ---


class NormWithDoc(BaseModel):
    """Норма с информацией о документе."""

    id: str
    doc_id: str
    article: int
    paragraph: int | None = None
    text: str
    doc_title: str | None = None
    doc_type: str | None = None
    domain: str | None = None


class CompareResponse(BaseModel):
    """Результат сравнения двух норм."""

    norm_a: NormWithDoc
    norm_b: NormWithDoc
    findings: list[FindingResponse]


# --- Эндпоинт ---


@router.get("/{norm_a_id}/{norm_b_id}", response_model=CompareResponse)
async def compare_norms(norm_a_id: str, norm_b_id: str) -> CompareResponse:
    """Сравнить две нормы: показать тексты, информацию о документах и существующие обнаружения."""
    async with get_db() as db:
        # Загружаем обе нормы с данными документов
        norm_a_rows = await db.execute_fetchall(
            """
            SELECT n.id, n.doc_id, n.article, n.paragraph, n.text,
                   d.title, d.doc_type, d.domain
            FROM norms n
            LEFT JOIN documents d ON d.id = n.doc_id
            WHERE n.id = ?
            """,
            [norm_a_id],
        )

        if not norm_a_rows:
            raise HTTPException(status_code=404, detail=f"Норма {norm_a_id} не найдена")

        norm_b_rows = await db.execute_fetchall(
            """
            SELECT n.id, n.doc_id, n.article, n.paragraph, n.text,
                   d.title, d.doc_type, d.domain
            FROM norms n
            LEFT JOIN documents d ON d.id = n.doc_id
            WHERE n.id = ?
            """,
            [norm_b_id],
        )

        if not norm_b_rows:
            raise HTTPException(status_code=404, detail=f"Норма {norm_b_id} не найдена")

        # Ищем существующие обнаружения между этими нормами
        finding_rows = await db.execute_fetchall(
            """
            SELECT f.id, f.type, f.severity, f.confidence,
                   f.explanation, f.created_at,
                   n_a.id, n_a.doc_id, n_a.article, n_a.paragraph, n_a.text,
                   n_b.id, n_b.doc_id, n_b.article, n_b.paragraph, n_b.text,
                   n_a.cluster_topic
            FROM findings f
            LEFT JOIN norms n_a ON n_a.id = f.norm_a_id
            LEFT JOIN norms n_b ON n_b.id = f.norm_b_id
            WHERE (f.norm_a_id = ? AND f.norm_b_id = ?)
               OR (f.norm_a_id = ? AND f.norm_b_id = ?)
            """,
            [norm_a_id, norm_b_id, norm_b_id, norm_a_id],
        )

    # Формируем нормы
    a = norm_a_rows[0]
    norm_a = NormWithDoc(
        id=a[0], doc_id=a[1], article=a[2], paragraph=a[3], text=a[4],
        doc_title=a[5], doc_type=a[6], domain=a[7],
    )

    b = norm_b_rows[0]
    norm_b = NormWithDoc(
        id=b[0], doc_id=b[1], article=b[2], paragraph=b[3], text=b[4],
        doc_title=b[5], doc_type=b[6], domain=b[7],
    )

    # Формируем обнаружения
    findings: list[FindingResponse] = []
    for r in finding_rows:
        f_norm_a = NormBrief(
            id=r[6], doc_id=r[7], article=r[8], paragraph=r[9], text=r[10]
        )
        f_norm_b = None
        if r[11]:
            f_norm_b = NormBrief(
                id=r[11], doc_id=r[12], article=r[13], paragraph=r[14], text=r[15]
            )
        findings.append(
            FindingResponse(
                id=r[0], type=r[1], severity=r[2], confidence=r[3],
                explanation=r[4], created_at=r[5],
                norm_a=f_norm_a, norm_b=f_norm_b, cluster_topic=r[16],
            )
        )

    return CompareResponse(norm_a=norm_a, norm_b=norm_b, findings=findings)
