# Архитектура системы

## Обзор

ZanAlytics построена по модульной архитектуре с разделением на три основных слоя: Frontend (визуализация), Backend (API + анализ), Storage (данные).

## Диаграмма компонентов

```
┌────────────────────────────────────────────────────────────┐
│                      USER BROWSER                          │
└────────────────────────────┬───────────────────────────────┘
                             │
                       :3100 (HTTPS)
                             │
┌────────────────────────────▼───────────────────────────────┐
│                    FRONTEND (Next.js 15)                    │
│                                                             │
│  ┌─────────────┐ ┌──────────────┐ ┌─────────────────────┐  │
│  │  Dashboard   │ │  3D Graph    │ │  Findings Browser   │  │
│  │  (recharts)  │ │  (force-     │ │  (table + filters)  │  │
│  │              │ │   graph-3d)  │ │                     │  │
│  └─────────────┘ └──────────────┘ └─────────────────────┘  │
│  ┌─────────────┐ ┌──────────────┐ ┌─────────────────────┐  │
│  │  Norm        │ │  Upload &    │ │  About /            │  │
│  │  Comparison  │ │  Analyze     │ │  Methodology        │  │
│  │  (diff view) │ │  (SSE)       │ │                     │  │
│  └─────────────┘ └──────────────┘ └─────────────────────┘  │
└────────────────────────────┬───────────────────────────────┘
                             │
                    REST API + SSE
                             │
┌────────────────────────────▼───────────────────────────────┐
│                   BACKEND (FastAPI)                         │
│                       :8000                                 │
│                                                             │
│  ┌──────────────────────┐  ┌─────────────────────────────┐ │
│  │      API Layer        │  │      Scraper Module         │ │
│  │  /api/documents       │  │  fetcher.py (aiohttp)      │ │
│  │  /api/findings        │  │  parser.py (BS4)           │ │
│  │  /api/graph           │  │  structural.py (regex)     │ │
│  │  /api/search          │  │  seed_docs.py              │ │
│  │  /api/analyze (SSE)   │  │                            │ │
│  │  /api/stats           │  └─────────────────────────────┘ │
│  │  /api/compare         │                                  │
│  └──────────┬───────────┘                                  │
│             │                                               │
│  ┌──────────▼───────────┐  ┌─────────────────────────────┐ │
│  │   Analysis Pipeline  │  │       LLM Client            │ │
│  │  embedder.py         │  │  client.py (httpx→Ollama)   │ │
│  │  clusterer.py        │  │  prompts.py (templates)     │ │
│  │  dedup.py            │◄─┤                             │ │
│  │  contradiction.py    │  └──────────────┬──────────────┘ │
│  │  outdated.py         │                 │                 │
│  │  graph_builder.py    │                 │                 │
│  └──────────┬───────────┘                 │                 │
└─────────────┼─────────────────────────────┼─────────────────┘
              │                             │
     ┌────────┼────────┐                    │
     │        │        │                    │
     ▼        ▼        ▼                    ▼
┌────────┐┌───────┐┌────────┐        ┌──────────┐
│ChromaDB││SQLite ││NetworkX│        │  Ollama  │
│embedded││zandb  ││in-mem  │        │  :11434  │
│        ││.sqlite││        │        │qwen2.5:14b│
│vectors ││meta-  ││graph   │        │nomic-    │
│norms   ││data   ││export  │        │embed-text│
└────────┘└───────┘└────────┘        └──────────┘
```

## Компоненты

### Frontend

| Компонент | Технология | Назначение |
|-----------|-----------|------------|
| App Shell | Next.js 15 (App Router) | SSR, маршрутизация, layout |
| UI Kit | shadcn/ui + Tailwind CSS 4 | Компоненты, стили |
| 3D Graph | react-force-graph-3d + Three.js | Визуализация графа НПА |
| Charts | Recharts | Статистика дашборда |
| Data Fetching | TanStack React Query | Кэширование, рефетч |

### Backend

| Модуль | Файлы | Назначение |
|--------|-------|------------|
| API | `api/*.py` | REST endpoints, CORS, validation |
| Scraper | `scraper/*.py` | Парсинг adilet.zan.kz |
| Pipeline | `pipeline/*.py` | NLP анализ, кластеризация |
| LLM | `llm/*.py` | Клиент Ollama, промпты |
| Models | `models/*.py` | Pydantic/dataclass модели |

### Storage

| Хранилище | Назначение | Объём |
|-----------|-----------|-------|
| SQLite | Метаданные документов, нормы, обнаружения | ~50 MB |
| ChromaDB | Векторные эмбеддинги норм | ~100 MB |
| NetworkX | Граф связей (в памяти, экспорт в JSON) | ~5 MB |
| Raw HTML | Кэш скачанных страниц | ~200 MB |

## Потоки данных

### 1. Парсинг (offline, batch)

```
adilet.zan.kz → fetcher.py → raw HTML files
                                    │
                              parser.py → metadata + text
                                    │
                           structural.py → articles, paragraphs
                                    │
                              SQLite (documents, norms, cross_refs)
```

### 2. Индексация (offline, batch)

```
SQLite (norms) → embedder.py → bge-m3/nomic-embed → ChromaDB
                                                         │
                 clusterer.py ← UMAP + HDBSCAN ──────────┘
                      │
                 SQLite (norms.cluster_id, norms.topic)
```

### 3. Анализ (offline, batch)

```
ChromaDB + SQLite → dedup.py ──────────┐
                  → contradiction.py ───┤→ SQLite (findings)
                  → outdated.py ────────┘
                         │
                  graph_builder.py → NetworkX → JSON cache
```

### 4. Запросы (online, real-time)

```
User request → FastAPI → SQLite/ChromaDB → JSON response → Frontend
```

### 5. Анализ нового текста (online, SSE)

```
User text → /api/analyze → embedder → ChromaDB search → LLM analysis
                              │              │                │
                              └──── SSE events ───────────────┘
                                         │
                                    Frontend (AnalysisProgress)
```

## Порты

| Сервис | Порт | Протокол |
|--------|------|----------|
| Frontend (Next.js) | 3100 | HTTP |
| Backend (FastAPI) | 8000 | HTTP |
| Ollama | 11434 | HTTP |
| ChromaDB | — | Embedded (in-process) |
| SQLite | — | File-based |

## Масштабирование

Текущая архитектура рассчитана на демо (50-80 документов, ~5000 норм). Для продакшена:

| Компонент | Текущий | Продакшн |
|-----------|---------|----------|
| Vector DB | ChromaDB (embedded) | Qdrant / Milvus (distributed) |
| Metadata DB | SQLite | PostgreSQL |
| Graph DB | NetworkX (in-memory) | Neo4j / ArangoDB |
| LLM | Ollama (single GPU) | vLLM (multi-GPU) / API |
| Frontend | Next.js dev | Next.js + CDN |
| Deployment | Docker Compose | Kubernetes |

## Безопасность

- Все данные публичные (открытая база НПА)
- Нет аутентификации (демо-режим)
- Rate limiting на API (50 req/min)
- CORS ограничен localhost
- В продакшне: JWT auth, HTTPS, WAF
