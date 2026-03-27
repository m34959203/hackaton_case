"""Эндпоинт для получения данных графа связей между нормами."""

import json
import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/graph", tags=["Граф"])

# Путь к кэш-файлу графа
_GRAPH_CACHE = Path(settings.DB_PATH).parent / "graph.json"


# --- Pydantic-модели ответов ---


class GraphNode(BaseModel):
    """Узел графа (документ)."""

    id: str
    name: str
    group: str | None = None
    val: float = 1.0
    color: str | None = None
    findingsCount: int = 0
    domain: str | None = None
    status: str | None = None


class GraphLink(BaseModel):
    """Ребро графа (связь между узлами)."""

    source: str
    target: str
    type: str | None = None
    color: str | None = None
    value: float = 1.0
    label: str | None = None


class GraphResponse(BaseModel):
    """Полный граф для react-force-graph-3d."""

    nodes: list[GraphNode]
    links: list[GraphLink]


# --- Эндпоинт ---


@router.get("", response_model=GraphResponse)
async def get_graph() -> GraphResponse:
    """Получить полный граф связей из кэш-файла graph.json.

    Файл генерируется пайплайном graph_builder.py.
    Формат совместим с react-force-graph-3d.
    """
    if not _GRAPH_CACHE.exists():
        logger.warning("Файл графа не найден: %s", _GRAPH_CACHE)
        # Возвращаем пустой граф вместо ошибки
        return GraphResponse(nodes=[], links=[])

    try:
        raw = _GRAPH_CACHE.read_text(encoding="utf-8")
        data = json.loads(raw)
    except (json.JSONDecodeError, OSError) as exc:
        logger.error("Ошибка чтения графа: %s", exc)
        raise HTTPException(status_code=500, detail="Ошибка чтения файла графа") from exc

    nodes = [GraphNode(**n) for n in data.get("nodes", [])]
    links = [GraphLink(**link) for link in data.get("links", [])]

    logger.info("Граф загружен: %d узлов, %d рёбер", len(nodes), len(links))
    return GraphResponse(nodes=nodes, links=links)
