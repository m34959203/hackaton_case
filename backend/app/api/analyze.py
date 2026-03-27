"""Эндпоинт анализа текста с потоковой передачей прогресса через SSE."""

import json
import logging

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.database import get_chroma_collection, get_db
from app.llm.client import OllamaClient
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/analyze", tags=["Анализ"])

_ollama = OllamaClient()


# --- Pydantic-модели ---


class AnalyzeRequest(BaseModel):
    """Запрос на анализ текста нормы."""

    text: str = Field(min_length=10, description="Текст нормы для анализа")


# --- Вспомогательные функции ---


def _sse_event(event: str, data: dict) -> str:
    """Формирование SSE-события."""
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


async def _analysis_stream(text: str):
    """Генератор SSE-событий для анализа текста.

    Этапы:
    1. embedding — создание эмбеддинга входного текста
    2. searching — поиск похожих норм в ChromaDB
    3. analyzing — анализ через LLM
    4. result — итоговый результат
    """
    # Этап 1: Эмбеддинг
    yield _sse_event("embedding", {"status": "Создание эмбеддинга текста..."})

    try:
        embeddings = await _ollama.embed([text])
        query_embedding = embeddings[0]
    except Exception as exc:
        logger.error("Ошибка эмбеддинга: %s", exc)
        yield _sse_event("error", {"message": "Ошибка создания эмбеддинга"})
        return

    yield _sse_event("embedding", {"status": "Эмбеддинг создан", "done": True})

    # Этап 2: Поиск похожих норм
    yield _sse_event("searching", {"status": "Поиск похожих норм в базе..."})

    try:
        collection = get_chroma_collection()
        chroma_results = collection.query(
            query_embeddings=[query_embedding],
            n_results=10,
            include=["distances", "metadatas", "documents"],
        )
    except Exception as exc:
        logger.error("Ошибка поиска в ChromaDB: %s", exc)
        yield _sse_event("error", {"message": "Ошибка поиска в ChromaDB"})
        return

    similar_norms: list[dict] = []
    if chroma_results["ids"] and chroma_results["ids"][0]:
        norm_ids = chroma_results["ids"][0]
        distances = chroma_results["distances"][0] if chroma_results["distances"] else []

        # Загружаем данные из SQLite
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

        norm_map = {r[0]: r for r in rows}
        for i, nid in enumerate(norm_ids):
            r = norm_map.get(nid)
            if not r:
                continue
            distance = distances[i] if i < len(distances) else 1.0
            similarity = max(0.0, 1.0 - distance)
            if similarity >= settings.SIMILARITY_THRESHOLD * 0.7:
                similar_norms.append({
                    "id": r[0],
                    "doc_id": r[1],
                    "article": r[2],
                    "paragraph": r[3],
                    "text": r[4],
                    "doc_title": r[5],
                    "similarity": round(similarity, 4),
                })

    yield _sse_event("searching", {
        "status": f"Найдено {len(similar_norms)} похожих норм",
        "count": len(similar_norms),
        "done": True,
    })

    # Этап 3: Анализ через LLM
    yield _sse_event("analyzing", {"status": "Анализ текста через ИИ..."})

    context_norms = "\n\n".join(
        f"[{n['doc_title']}] Ст.{n['article']} п.{n['paragraph']}: {n['text']}"
        for n in similar_norms[:5]
    )

    prompt = f"""Ты — юридический эксперт по законодательству Республики Казахстан.
Проанализируй следующий текст нормы и определи потенциальные проблемы.

ВХОДНОЙ ТЕКСТ:
{text}

ПОХОЖИЕ СУЩЕСТВУЮЩИЕ НОРМЫ:
{context_norms if context_norms else "Похожих норм не найдено."}

Определи:
1. Есть ли противоречия с существующими нормами?
2. Есть ли дублирование?
3. Есть ли признаки устаревшей нормы?

Ответь в формате JSON:
{{
    "findings": [
        {{
            "type": "contradiction|duplication|outdated",
            "severity": "high|medium|low",
            "confidence": 0.0-1.0,
            "related_norm_id": "id нормы или null",
            "explanation": "объяснение на русском"
        }}
    ],
    "summary": "общий вывод на русском"
}}"""

    try:
        result = await _ollama.generate_json(
            prompt=prompt,
            temperature=settings.LLM_TEMPERATURE_ANALYSIS,
        )
    except Exception as exc:
        logger.error("Ошибка LLM анализа: %s", exc)
        yield _sse_event("error", {"message": "Ошибка анализа через ИИ"})
        return

    yield _sse_event("analyzing", {"status": "Анализ завершён", "done": True})

    # Этап 4: Результат
    yield _sse_event("result", {
        "findings": result.get("findings", []),
        "summary": result.get("summary", "Анализ завершён"),
        "similar_norms": similar_norms,
    })


# --- Эндпоинт ---


@router.post("")
async def analyze_text(request: AnalyzeRequest) -> StreamingResponse:
    """Анализ текста нормы с потоковой передачей прогресса через SSE.

    Возвращает поток SSE-событий:
    - embedding — создание эмбеддинга
    - searching — поиск похожих норм
    - analyzing — анализ через LLM
    - result — итоговый результат
    - error — при ошибке
    """
    return StreamingResponse(
        _analysis_stream(request.text),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
