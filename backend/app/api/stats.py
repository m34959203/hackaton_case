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


class ModelProvider(BaseModel):
    """Информация о провайдере LLM."""

    id: str
    name: str
    models: list[str]
    configured: bool


class ModelsInfoResponse(BaseModel):
    """Информация о текущем провайдере и доступных моделях."""

    current_provider: str
    current_model: str
    providers: list[ModelProvider]


class SetModelRequest(BaseModel):
    """Запрос на смену провайдера/модели."""

    provider: str
    model: str | None = None


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

    # Текущий провайдер и модель
    provider = settings.LLM_PROVIDER
    if provider == "openai":
        current_model = settings.OPENAI_MODEL
    elif provider == "anthropic":
        current_model = settings.ANTHROPIC_MODEL
    elif provider == "gemini":
        current_model = settings.GEMINI_MODEL
    else:
        current_model = settings.OLLAMA_MODEL

    # --- Ollama ---
    ollama_models: list[str] = []
    ollama_configured = True
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{settings.OLLAMA_URL}/api/tags")
            data = resp.json()
            ollama_models = [
                m["name"]
                for m in data.get("models", [])
                if "embed" not in m["name"]
            ]
    except Exception:
        ollama_configured = False
        ollama_models = [settings.OLLAMA_MODEL]

    # --- OpenAI-совместимый API ---
    openai_configured = bool(settings.OPENAI_API_KEY)
    openai_models = [settings.OPENAI_MODEL]

    # --- Anthropic ---
    anthropic_configured = bool(settings.ANTHROPIC_API_KEY)
    anthropic_models = [settings.ANTHROPIC_MODEL]

    # --- Google Gemini ---
    gemini_configured = bool(settings.GEMINI_API_KEY)
    gemini_models = [settings.GEMINI_MODEL, "gemini-2.5-flash-preview-05-20", "gemini-2.5-pro-preview-06-05"]

    providers = [
        ModelProvider(
            id="ollama",
            name="Ollama (локальный)",
            models=ollama_models,
            configured=ollama_configured,
        ),
        ModelProvider(
            id="openai",
            name="OpenAI API (Together.ai / Groq / OpenRouter)",
            models=openai_models,
            configured=openai_configured,
        ),
        ModelProvider(
            id="anthropic",
            name="Anthropic (Claude)",
            models=anthropic_models,
            configured=anthropic_configured,
        ),
        ModelProvider(
            id="gemini",
            name="Google Gemini",
            models=gemini_models,
            configured=gemini_configured,
        ),
    ]

    return ModelsInfoResponse(
        current_provider=provider,
        current_model=current_model,
        providers=providers,
    )


@router.post("/models")
async def set_model(body: SetModelRequest) -> dict:
    """Сменить LLM-провайдер и/или модель для анализа."""
    provider = body.provider
    model = body.model

    if provider not in ("ollama", "openai", "anthropic", "gemini"):
        raise HTTPException(
            status_code=400,
            detail=f"Неизвестный провайдер: {provider}. Допустимые: ollama, openai, anthropic, gemini",
        )

    # Проверка наличия API-ключа для облачных провайдеров
    if provider == "openai" and not settings.OPENAI_API_KEY:
        raise HTTPException(
            status_code=400,
            detail="API-ключ для OpenAI не настроен (ZAN_OPENAI_API_KEY)",
        )
    if provider == "anthropic" and not settings.ANTHROPIC_API_KEY:
        raise HTTPException(
            status_code=400,
            detail="API-ключ для Anthropic не настроен (ZAN_ANTHROPIC_API_KEY)",
        )
    if provider == "gemini" and not settings.GEMINI_API_KEY:
        raise HTTPException(
            status_code=400,
            detail="API-ключ для Gemini не настроен (ZAN_GEMINI_API_KEY)",
        )

    # Переключаем провайдер
    settings.LLM_PROVIDER = provider

    # Обновляем модель если указана
    if model:
        if provider == "ollama":
            settings.OLLAMA_MODEL = model
        elif provider == "openai":
            settings.OPENAI_MODEL = model
        elif provider == "anthropic":
            settings.ANTHROPIC_MODEL = model
        elif provider == "gemini":
            settings.GEMINI_MODEL = model

    # Определяем текущую модель для ответа
    if provider == "openai":
        current_model = settings.OPENAI_MODEL
    elif provider == "anthropic":
        current_model = settings.ANTHROPIC_MODEL
    elif provider == "gemini":
        current_model = settings.GEMINI_MODEL
    else:
        current_model = settings.OLLAMA_MODEL

    logger.info("LLM переключён: provider=%s, model=%s", provider, current_model)

    return {"status": "ok", "provider": provider, "model": current_model}


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
