"""Эндпоинт семантического поиска по нормам через ChromaDB."""

import logging

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.database import get_chroma_collection, get_db
from app.llm.client import OllamaClient
from app.models.document import NormBrief

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/search", tags=["Поиск"])

_ollama = OllamaClient()


# --- Pydantic-модели ответов ---


class SearchResult(BaseModel):
    """Результат семантического поиска — норма с оценкой похожести."""

    norm: NormBrief
    doc_title: str | None = None
    similarity: float


class SearchResponse(BaseModel):
    """Ответ семантического поиска."""

    query: str
    results: list[SearchResult]
    total: int


# --- Эндпоинт ---


@router.get("", response_model=SearchResponse)
async def semantic_search(
    q: str = Query(..., min_length=2, description="Текст запроса для поиска"),
    limit: int = Query(20, ge=1, le=100, description="Максимум результатов"),
) -> SearchResponse:
    """Семантический поиск по нормам.

    Создаёт эмбеддинг запроса через Ollama, ищет ближайшие нормы в ChromaDB,
    возвращает результаты с оценкой похожести.
    """
    # Создаём эмбеддинг запроса
    try:
        embeddings = await _ollama.embed([q])
    except Exception as exc:
        logger.error("Ошибка получения эмбеддинга: %s", exc)
        raise HTTPException(
            status_code=503, detail="Сервис эмбеддингов недоступен"
        ) from exc

    if not embeddings:
        raise HTTPException(status_code=500, detail="Пустой ответ от модели эмбеддингов")

    query_embedding = embeddings[0]

    # Поиск в ChromaDB
    try:
        collection = get_chroma_collection()
        chroma_results = collection.query(
            query_embeddings=[query_embedding],
            n_results=limit,
            include=["distances", "metadatas"],
        )
    except Exception as exc:
        logger.error("Ошибка поиска в ChromaDB: %s", exc)
        raise HTTPException(
            status_code=503, detail="ChromaDB недоступна"
        ) from exc

    if not chroma_results["ids"] or not chroma_results["ids"][0]:
        return SearchResponse(query=q, results=[], total=0)

    norm_ids = chroma_results["ids"][0]
    distances = chroma_results["distances"][0] if chroma_results["distances"] else []

    # Загружаем полные данные норм из SQLite
    placeholders = ",".join("?" for _ in norm_ids)
    async with get_db() as db:
        rows = await db.execute_fetchall(
            f"""
            SELECT n.id, n.doc_id, n.article, n.paragraph, n.text, d.title
            FROM norms n
            LEFT JOIN documents d ON d.id = n.doc_id
            WHERE n.id IN ({placeholders})
            """,
            norm_ids,
        )

    # Индексируем строки по ID нормы
    norm_map: dict[str, tuple] = {}
    for r in rows:
        norm_map[r[0]] = r

    # Собираем результаты в порядке релевантности
    results: list[SearchResult] = []
    for i, norm_id in enumerate(norm_ids):
        r = norm_map.get(norm_id)
        if not r:
            continue

        # ChromaDB возвращает косинусное расстояние, конвертируем в похожесть
        distance = distances[i] if i < len(distances) else 1.0
        similarity = max(0.0, 1.0 - distance)

        results.append(
            SearchResult(
                norm=NormBrief(
                    id=r[0], doc_id=r[1], article=r[2], paragraph=r[3], text=r[4]
                ),
                doc_title=r[5],
                similarity=round(similarity, 4),
            )
        )

    return SearchResponse(query=q, results=results, total=len(results))
