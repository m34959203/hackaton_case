"""Подключение к SQLite и ChromaDB."""

import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

import aiosqlite
import chromadb

from app.config import settings

logger = logging.getLogger(__name__)

# SQL-схема базы данных
_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS documents (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    doc_type TEXT NOT NULL,
    date_adopted TEXT,
    date_amended TEXT,
    status TEXT DEFAULT 'active',
    domain TEXT,
    adopting_body TEXT,
    legal_force TEXT,
    body TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS norms (
    id TEXT PRIMARY KEY,
    doc_id TEXT NOT NULL REFERENCES documents(id),
    article INTEGER NOT NULL,
    paragraph INTEGER,
    text TEXT NOT NULL,
    cluster_id INTEGER,
    cluster_topic TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS cross_refs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    from_doc TEXT NOT NULL REFERENCES documents(id),
    to_doc TEXT NOT NULL REFERENCES documents(id),
    context_text TEXT
);

CREATE TABLE IF NOT EXISTS findings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type TEXT NOT NULL,
    severity TEXT NOT NULL,
    confidence REAL NOT NULL,
    norm_a_id TEXT NOT NULL REFERENCES norms(id),
    norm_b_id TEXT REFERENCES norms(id),
    explanation TEXT NOT NULL,
    cluster_id INTEGER,
    recommendation TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_norms_doc ON norms(doc_id);
CREATE INDEX IF NOT EXISTS idx_norms_cluster ON norms(cluster_id);
CREATE INDEX IF NOT EXISTS idx_findings_type ON findings(type);
CREATE INDEX IF NOT EXISTS idx_findings_severity ON findings(severity);
CREATE INDEX IF NOT EXISTS idx_cross_refs_from ON cross_refs(from_doc);
CREATE INDEX IF NOT EXISTS idx_cross_refs_to ON cross_refs(to_doc);
"""


async def init_db() -> None:
    """Инициализация БД: создание директорий и таблиц."""
    db_path = Path(settings.DB_PATH)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    async with aiosqlite.connect(settings.DB_PATH) as db:
        await db.executescript(_SCHEMA_SQL)
        await db.commit()
    logger.info("БД инициализирована: %s", settings.DB_PATH)


@asynccontextmanager
async def get_db() -> AsyncGenerator[aiosqlite.Connection, None]:
    """Контекстный менеджер для получения соединения с SQLite."""
    db = await aiosqlite.connect(settings.DB_PATH)
    db.row_factory = aiosqlite.Row
    try:
        yield db
    finally:
        await db.close()


def get_chroma_client() -> chromadb.ClientAPI:
    """Получить клиент ChromaDB с персистентным хранилищем."""
    chroma_path = Path(settings.CHROMA_PATH)
    chroma_path.mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(path=str(chroma_path))


def get_chroma_collection(
    name: str = "norms",
) -> chromadb.Collection:
    """Получить коллекцию норм в ChromaDB."""
    client = get_chroma_client()
    return client.get_or_create_collection(
        name=name,
        metadata={"hnsw:space": "cosine"},
    )
