"""FastAPI-приложение ZanAlytics — анализ законодательства РК."""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from app.config import settings
from app.database import init_db

from app.api.documents import router as documents_router
from app.api.findings import router as findings_router
from app.api.graph import router as graph_router
from app.api.search import router as search_router
from app.api.compare import router as compare_router
from app.api.analyze import router as analyze_router
from app.api.stats import router as stats_router

logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Жизненный цикл приложения: инициализация БД при старте."""
    logger.info("Инициализация базы данных...")
    await init_db()
    logger.info("Приложение запущено")
    yield
    logger.info("Приложение остановлено")


app = FastAPI(
    title="ZanAlytics API",
    description="AI-система анализа законодательства Республики Казахстан",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Роутеры
app.include_router(documents_router)
app.include_router(findings_router)
app.include_router(graph_router)
app.include_router(search_router)
app.include_router(compare_router)
app.include_router(analyze_router)
app.include_router(stats_router)


@app.get("/", include_in_schema=False)
async def root() -> RedirectResponse:
    """Перенаправление на документацию Swagger UI."""
    return RedirectResponse(url="/docs")
