"""Эндпоинты статистики, моделей и проверки здоровья системы."""

import logging

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.config import settings
from app.database import get_chroma_collection, get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["Статистика"])


# --- Pydantic-модели ответов ---


class DomainStat(BaseModel):
    """Статистика по домену."""

    domain: str
    docs_count: int
    norms_count: int
    findings_count: int


class FindingTypeStat(BaseModel):
    """Статистика по типу обнаружения."""

    type: str
    count: int


class FindingSeverityStat(BaseModel):
    """Статистика по серьёзности обнаружения."""

    severity: str
    count: int


class StatsResponse(BaseModel):
    """Общая статистика для дашборда."""

    total_documents: int
    total_norms: int
    total_findings: int
    findings_by_type: list[FindingTypeStat]
    findings_by_severity: list[FindingSeverityStat]
    top_domains: list[DomainStat]


class ServiceStatus(BaseModel):
    """Статус отдельного сервиса."""

    name: str
    status: str
    detail: str | None = None


class HealthResponse(BaseModel):
    """Проверка здоровья всех сервисов."""

    status: str
    services: list[ServiceStatus]


class ModelsInfoResponse(BaseModel):
    """Информация о текущей модели."""

    current_model: str
    available: list[str]
    provider: str = "gemini"


class SetModelRequest(BaseModel):
    """Запрос на смену модели."""

    model: str


# --- Эндпоинты ---


@router.get("/stats", response_model=StatsResponse)
async def get_stats() -> StatsResponse:
    """Получить сводную статистику для дашборда."""
    async with get_db() as db:
        # Общие счётчики
        docs_row = await db.execute_fetchall("SELECT COUNT(*) FROM documents")
        total_documents = docs_row[0][0] if docs_row else 0

        norms_row = await db.execute_fetchall("SELECT COUNT(*) FROM norms")
        total_norms = norms_row[0][0] if norms_row else 0

        findings_row = await db.execute_fetchall("SELECT COUNT(*) FROM findings")
        total_findings = findings_row[0][0] if findings_row else 0

        # По типу обнаружений
        type_rows = await db.execute_fetchall(
            "SELECT type, COUNT(*) as cnt FROM findings GROUP BY type ORDER BY cnt DESC"
        )
        findings_by_type = [
            FindingTypeStat(type=r[0], count=r[1]) for r in type_rows
        ]

        # По серьёзности
        severity_rows = await db.execute_fetchall(
            """SELECT severity, COUNT(*) as cnt FROM findings
               GROUP BY severity
               ORDER BY CASE severity WHEN 'high' THEN 1 WHEN 'medium' THEN 2 ELSE 3 END"""
        )
        findings_by_severity = [
            FindingSeverityStat(severity=r[0], count=r[1]) for r in severity_rows
        ]

        # Топ доменов
        domain_rows = await db.execute_fetchall(
            """
            SELECT d.domain,
                   COUNT(DISTINCT d.id) as docs_count,
                   COUNT(DISTINCT n.id) as norms_count,
                   COUNT(DISTINCT f.id) as findings_count
            FROM documents d
            LEFT JOIN norms n ON n.doc_id = d.id
            LEFT JOIN findings f ON f.norm_a_id = n.id OR f.norm_b_id = n.id
            WHERE d.domain IS NOT NULL
            GROUP BY d.domain
            ORDER BY findings_count DESC
            LIMIT 10
            """
        )
        top_domains = [
            DomainStat(
                domain=r[0], docs_count=r[1], norms_count=r[2], findings_count=r[3]
            )
            for r in domain_rows
        ]

    return StatsResponse(
        total_documents=total_documents,
        total_norms=total_norms,
        total_findings=total_findings,
        findings_by_type=findings_by_type,
        findings_by_severity=findings_by_severity,
        top_domains=top_domains,
    )


@router.get("/models", response_model=ModelsInfoResponse)
async def list_models() -> ModelsInfoResponse:
    """Список доступных LLM-провайдеров и моделей."""

    available = [
        "gemini-2.0-flash",
        "gemini-2.5-flash-preview-05-20",
        "gemini-2.5-pro-preview-06-05",
    ]

    return ModelsInfoResponse(
        current_model=settings.GEMINI_MODEL,
        available=available,
    )


@router.post("/models")
async def set_model(body: SetModelRequest) -> dict:
    """Сменить модель Gemini для анализа."""
    settings.GEMINI_MODEL = body.model
    logger.info("Модель переключена: %s", body.model)
    return {"status": "ok", "model": body.model}


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Проверка здоровья всех сервисов: Ollama, ChromaDB, SQLite."""
    services: list[ServiceStatus] = []
    all_ok = True

    # SQLite
    try:
        async with get_db() as db:
            await db.execute_fetchall("SELECT 1")
        services.append(ServiceStatus(name="sqlite", status="ok"))
    except Exception as exc:
        all_ok = False
        services.append(
            ServiceStatus(name="sqlite", status="error", detail=str(exc))
        )

    # ChromaDB
    try:
        collection = get_chroma_collection()
        count = collection.count()
        services.append(
            ServiceStatus(name="chromadb", status="ok", detail=f"{count} векторов")
        )
    except Exception as exc:
        all_ok = False
        services.append(
            ServiceStatus(name="chromadb", status="error", detail=str(exc))
        )

    # Ollama
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{settings.OLLAMA_URL}/api/tags")
            resp.raise_for_status()
            models = resp.json().get("models", [])
            model_names = [m["name"] for m in models[:5]]
            services.append(
                ServiceStatus(
                    name="ollama",
                    status="ok",
                    detail=f"Модели: {', '.join(model_names)}",
                )
            )
    except Exception as exc:
        all_ok = False
        services.append(
            ServiceStatus(name="ollama", status="error", detail=str(exc))
        )

    return HealthResponse(
        status="ok" if all_ok else "degraded",
        services=services,
    )
