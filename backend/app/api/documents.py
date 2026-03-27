"""Эндпоинты для работы с документами НПА."""

import logging

from fastapi import APIRouter, HTTPException, Query

from app.database import get_db
from app.models.document import DocumentResponse, NormBrief, NormResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/documents", tags=["Документы"])


# --- Pydantic-модели ответов ---


from pydantic import BaseModel


class DocumentListResponse(BaseModel):
    """Список документов с пагинацией."""

    items: list[DocumentResponse]
    total: int
    page: int
    limit: int


class DocumentDetailResponse(DocumentResponse):
    """Документ с вложенным списком норм."""

    norms: list[NormBrief] = []


class NormListResponse(BaseModel):
    """Список норм документа."""

    items: list[NormResponse]
    total: int


# --- Эндпоинты ---


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    page: int = Query(1, ge=1, description="Номер страницы"),
    limit: int = Query(20, ge=1, le=100, description="Размер страницы"),
    domain: str | None = Query(None, description="Фильтр по домену"),
    doc_type: str | None = Query(None, description="Фильтр по типу документа"),
    status: str | None = Query(None, description="Фильтр по статусу"),
) -> DocumentListResponse:
    """Получить список документов с пагинацией и фильтрами."""
    offset = (page - 1) * limit

    where_clauses: list[str] = []
    params: list[str] = []

    if domain:
        where_clauses.append("d.domain = ?")
        params.append(domain)
    if doc_type:
        where_clauses.append("d.doc_type = ?")
        params.append(doc_type)
    if status:
        where_clauses.append("d.status = ?")
        params.append(status)

    where_sql = ""
    if where_clauses:
        where_sql = "WHERE " + " AND ".join(where_clauses)

    async with get_db() as db:
        # Общее количество
        row = await db.execute_fetchall(
            f"SELECT COUNT(*) as cnt FROM documents d {where_sql}",
            params,
        )
        total = row[0][0] if row else 0

        # Документы с агрегатами
        query = f"""
            SELECT d.*,
                   COUNT(DISTINCT n.id) as norms_count,
                   COUNT(DISTINCT f.id) as findings_count
            FROM documents d
            LEFT JOIN norms n ON n.doc_id = d.id
            LEFT JOIN findings f ON f.norm_a_id = n.id OR f.norm_b_id = n.id
            {where_sql}
            GROUP BY d.id
            ORDER BY d.date_adopted DESC
            LIMIT ? OFFSET ?
        """
        rows = await db.execute_fetchall(query, params + [limit, offset])

    items = [
        DocumentResponse(
            id=r[0],
            title=r[1],
            doc_type=r[2],
            date_adopted=r[3],
            date_amended=r[4],
            status=r[5],
            domain=r[6],
            adopting_body=r[7],
            legal_force=r[8],
            norms_count=r[11],
            findings_count=r[12],
        )
        for r in rows
    ]

    return DocumentListResponse(items=items, total=total, page=page, limit=limit)


@router.get("/{doc_id}", response_model=DocumentDetailResponse)
async def get_document(doc_id: str) -> DocumentDetailResponse:
    """Получить документ по ID с вложенным списком норм."""
    async with get_db() as db:
        # Документ
        rows = await db.execute_fetchall(
            """
            SELECT d.*,
                   COUNT(DISTINCT n.id) as norms_count,
                   COUNT(DISTINCT f.id) as findings_count
            FROM documents d
            LEFT JOIN norms n ON n.doc_id = d.id
            LEFT JOIN findings f ON f.norm_a_id = n.id OR f.norm_b_id = n.id
            WHERE d.id = ?
            GROUP BY d.id
            """,
            [doc_id],
        )

        if not rows:
            raise HTTPException(status_code=404, detail="Документ не найден")

        r = rows[0]

        # Нормы документа
        norm_rows = await db.execute_fetchall(
            "SELECT id, doc_id, article, paragraph, text FROM norms WHERE doc_id = ? ORDER BY article, paragraph",
            [doc_id],
        )

    norms = [
        NormBrief(
            id=nr[0],
            doc_id=nr[1],
            article=nr[2],
            paragraph=nr[3],
            text=nr[4],
        )
        for nr in norm_rows
    ]

    return DocumentDetailResponse(
        id=r[0],
        title=r[1],
        doc_type=r[2],
        date_adopted=r[3],
        date_amended=r[4],
        status=r[5],
        domain=r[6],
        adopting_body=r[7],
        legal_force=r[8],
        norms_count=r[11],
        findings_count=r[12],
        norms=norms,
    )


@router.get("/{doc_id}/norms", response_model=NormListResponse)
async def get_document_norms(doc_id: str) -> NormListResponse:
    """Получить список норм документа."""
    async with get_db() as db:
        # Проверяем существование документа
        doc_rows = await db.execute_fetchall(
            "SELECT id FROM documents WHERE id = ?", [doc_id]
        )
        if not doc_rows:
            raise HTTPException(status_code=404, detail="Документ не найден")

        rows = await db.execute_fetchall(
            """
            SELECT n.id, n.doc_id, n.article, n.paragraph, n.text,
                   n.cluster_id, n.cluster_topic,
                   COUNT(DISTINCT f.id) as findings_count
            FROM norms n
            LEFT JOIN findings f ON f.norm_a_id = n.id OR f.norm_b_id = n.id
            WHERE n.doc_id = ?
            GROUP BY n.id
            ORDER BY n.article, n.paragraph
            """,
            [doc_id],
        )

    items = [
        NormResponse(
            id=r[0],
            doc_id=r[1],
            article=r[2],
            paragraph=r[3],
            text=r[4],
            cluster_id=r[5],
            cluster_topic=r[6],
            findings_count=r[7],
        )
        for r in rows
    ]

    return NormListResponse(items=items, total=len(items))
