"""Эндпоинты для работы с обнаружениями (findings)."""

import logging

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.database import get_db
from app.models.document import NormBrief
from app.models.finding import FindingDetail, FindingResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/findings", tags=["Обнаружения"])


# --- Pydantic-модели ответов ---


class FindingListResponse(BaseModel):
    """Список обнаружений с пагинацией."""

    items: list[FindingResponse]
    total: int
    page: int
    limit: int


# --- Эндпоинты ---


@router.get("/", response_model=FindingListResponse)
async def list_findings(
    page: int = Query(1, ge=1, description="Номер страницы"),
    limit: int = Query(20, ge=1, le=100, description="Размер страницы"),
    type: str | None = Query(None, description="Фильтр по типу: contradiction, duplication, outdated"),
    severity: str | None = Query(None, description="Фильтр по серьёзности: high, medium, low"),
    domain: str | None = Query(None, description="Фильтр по домену (через документ нормы A)"),
) -> FindingListResponse:
    """Получить список обнаружений с пагинацией и фильтрами."""
    offset = (page - 1) * limit

    where_clauses: list[str] = []
    params: list[str | int] = []

    if type:
        where_clauses.append("f.type = ?")
        params.append(type)
    if severity:
        where_clauses.append("f.severity = ?")
        params.append(severity)
    if domain:
        where_clauses.append("d_a.domain = ?")
        params.append(domain)

    where_sql = ""
    if where_clauses:
        where_sql = "WHERE " + " AND ".join(where_clauses)

    async with get_db() as db:
        # Общее количество
        count_query = f"""
            SELECT COUNT(*) FROM findings f
            LEFT JOIN norms n_a ON n_a.id = f.norm_a_id
            LEFT JOIN documents d_a ON d_a.id = n_a.doc_id
            {where_sql}
        """
        row = await db.execute_fetchall(count_query, params)
        total = row[0][0] if row else 0

        # Обнаружения с нормами
        query = f"""
            SELECT f.id, f.type, f.severity, f.confidence,
                   f.explanation, f.created_at,
                   n_a.id, n_a.doc_id, n_a.article, n_a.paragraph, n_a.text,
                   n_b.id, n_b.doc_id, n_b.article, n_b.paragraph, n_b.text,
                   n_a.cluster_topic
            FROM findings f
            LEFT JOIN norms n_a ON n_a.id = f.norm_a_id
            LEFT JOIN norms n_b ON n_b.id = f.norm_b_id
            LEFT JOIN documents d_a ON d_a.id = n_a.doc_id
            {where_sql}
            ORDER BY
                CASE f.severity WHEN 'high' THEN 1 WHEN 'medium' THEN 2 ELSE 3 END,
                f.confidence DESC
            LIMIT ? OFFSET ?
        """
        rows = await db.execute_fetchall(query, params + [limit, offset])

    items: list[FindingResponse] = []
    for r in rows:
        norm_a = NormBrief(
            id=r[6], doc_id=r[7], article=r[8], paragraph=r[9], text=r[10]
        )
        norm_b = None
        if r[11]:
            norm_b = NormBrief(
                id=r[11], doc_id=r[12], article=r[13], paragraph=r[14], text=r[15]
            )
        items.append(
            FindingResponse(
                id=r[0],
                type=r[1],
                severity=r[2],
                confidence=r[3],
                explanation=r[4],
                created_at=r[5],
                norm_a=norm_a,
                norm_b=norm_b,
                cluster_topic=r[16],
            )
        )

    return FindingListResponse(items=items, total=total, page=page, limit=limit)


@router.get("/{finding_id}", response_model=FindingDetail)
async def get_finding(finding_id: int) -> FindingDetail:
    """Получить детальную информацию об обнаружении с полным текстом норм."""
    async with get_db() as db:
        rows = await db.execute_fetchall(
            """
            SELECT f.id, f.type, f.severity, f.confidence,
                   f.explanation, f.recommendation, f.cluster_id, f.created_at,
                   n_a.id, n_a.doc_id, n_a.article, n_a.paragraph, n_a.text,
                   n_b.id, n_b.doc_id, n_b.article, n_b.paragraph, n_b.text,
                   n_a.cluster_topic
            FROM findings f
            LEFT JOIN norms n_a ON n_a.id = f.norm_a_id
            LEFT JOIN norms n_b ON n_b.id = f.norm_b_id
            WHERE f.id = ?
            """,
            [finding_id],
        )

    if not rows:
        raise HTTPException(status_code=404, detail="Обнаружение не найдено")

    r = rows[0]
    norm_a = NormBrief(
        id=r[8], doc_id=r[9], article=r[10], paragraph=r[11], text=r[12]
    )
    norm_b = None
    if r[13]:
        norm_b = NormBrief(
            id=r[13], doc_id=r[14], article=r[15], paragraph=r[16], text=r[17]
        )

    return FindingDetail(
        id=r[0],
        type=r[1],
        severity=r[2],
        confidence=r[3],
        explanation=r[4],
        recommendation=r[5],
        cluster_id=r[6],
        created_at=r[7],
        norm_a=norm_a,
        norm_b=norm_b,
        cluster_topic=r[18],
    )
