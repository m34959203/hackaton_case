# ZanAlytics — Правила разработки

## Проект
AI-система анализа законодательства РК для хакатона Decentrathon 5.0 (Кейс 1: Законодательная энтропия).
Дедлайн: **5 апреля 2026, 23:59**.

## Язык
- Интерфейс, комментарии к бизнес-логике, документация — **русский**
- Код, имена переменных, имена файлов, git-коммиты — **английский**
- LLM-промпты для анализа законов — **русский** (лучше качество на русских текстах)

## Архитектура

### Backend (Python 3.12, FastAPI)
- Директория: `backend/`
- Entry point: `backend/app/main.py`
- Порт: **8000**
- База: SQLite (`backend/data/zandb.sqlite`)
- Векторы: ChromaDB embedded (`backend/data/chroma/`)
- Кэш HTML: `backend/data/raw_html/`

### Frontend (Next.js 15, TypeScript, React 19)
- Директория: `frontend/`
- Порт: **3100**
- App Router (не Pages Router)
- UI Kit: shadcn/ui + Tailwind CSS 4

### LLM
- Ollama на порту **11434** (уже запущен в ~/ai-server/)
- Модель анализа: `qwen2.5:14b`
- Модель эмбеддингов: `nomic-embed-text`
- Обращение к Ollama через `httpx` (async), URL: `http://localhost:11434`
- НЕ использовать langchain/llamaindex — прямые HTTP-вызовы к Ollama API

## Структура Backend

```
backend/app/
├── main.py              # FastAPI app, CORS, lifespan
├── config.py            # Settings (pydantic-settings)
├── database.py          # SQLite + ChromaDB connections
├── models/              # Pydantic-модели данных
│   ├── document.py      # Document, Norm
│   └── finding.py       # Finding (contradiction/duplication/outdated)
├── scraper/             # Парсер adilet.zan.kz
│   ├── fetcher.py       # aiohttp + rate limiter + retry
│   ├── parser.py        # BeautifulSoup → извлечение текста/метаданных
│   ├── structural.py    # Разбиение на статьи/пункты (regex)
│   └── seed_docs.py     # Список DOC_ID для парсинга
├── pipeline/            # Аналитический пайплайн
│   ├── embedder.py      # Нормы → эмбеддинги → ChromaDB
│   ├── clusterer.py     # UMAP + HDBSCAN
│   ├── dedup.py         # Выявление дублирования (cosine > 0.85)
│   ├── contradiction.py # LLM-as-Judge — противоречия
│   ├── outdated.py      # Устаревшие нормы (статус + даты + LLM)
│   └── graph_builder.py # NetworkX → JSON для фронта
├── llm/
│   ├── client.py        # Ollama HTTP-клиент (httpx async)
│   └── prompts.py       # Все промпт-шаблоны (на русском)
├── api/                 # REST endpoints
│   ├── documents.py     # /api/documents
│   ├── findings.py      # /api/findings
│   ├── graph.py         # /api/graph
│   ├── search.py        # /api/search
│   ├── compare.py       # /api/compare
│   ├── analyze.py       # /api/analyze (SSE)
│   └── stats.py         # /api/stats
└── utils/
    └── text.py          # Нормализация текста, NLP-утилиты
```

## Структура Frontend

```
frontend/src/
├── app/
│   ├── layout.tsx           # Root layout + sidebar
│   ├── page.tsx             # Dashboard (главная)
│   ├── graph/page.tsx       # 3D-граф (react-force-graph-3d)
│   ├── documents/
│   │   ├── page.tsx         # Список документов
│   │   └── [id]/page.tsx    # Документ + дерево статей
│   ├── findings/
│   │   ├── page.tsx         # Список обнаружений
│   │   └── [id]/page.tsx    # Детали + сравнение норм + объяснение ИИ
│   ├── analyze/page.tsx     # Загрузка + анализ в реальном времени
│   └── about/page.tsx       # Методология
├── components/
│   ├── ui/                  # shadcn/ui (НЕ модифицировать)
│   ├── graph/               # ForceGraph3D, GraphControls
│   ├── dashboard/           # StatsCards, Charts
│   ├── findings/            # FindingCard, NormComparison, AiExplanation
│   └── layout/              # Sidebar, Header
├── lib/
│   ├── api.ts               # Fetch-обёртка для backend API
│   └── types.ts             # TypeScript интерфейсы
└── hooks/                   # React хуки (useGraph, useAnalysis)
```

## Правила кода

### Python
- Async everywhere: все I/O-операции через `async/await`
- Type hints обязательны для аргументов и возвращаемых значений
- Pydantic для валидации входных/выходных данных API
- Никаких `print()` — только `logging`
- `ruff` для линтинга и форматирования
- Импорты: stdlib → third-party → local (ruff сортирует автоматически)

### TypeScript
- Strict mode
- Интерфейсы для объектов (не type aliases)
- `"use client"` только для компонентов с состоянием/эффектами
- react-force-graph-3d: dynamic import с `ssr: false` (Three.js не работает в SSR)
- TanStack React Query для запросов к API
- Никаких `any` — описывать типы

### Общее
- Один файл — одна ответственность
- Максимум 300 строк на файл; если больше — разбить
- Никаких хардкод-значений — всё через config.py / .env
- Все пороги анализа (similarity_threshold, confidence) — в конфиге
- Error handling: на границах системы (API, внешние вызовы), не внутри pipeline

## Правила парсера (scraper/)

- Rate limit: **2 запроса/секунду** к adilet.zan.kz (asyncio.Semaphore)
- Кэшировать сырой HTML в `data/raw_html/{doc_id}.html`
- Пропускать уже скачанные документы (проверка по файлу в кэше)
- `ssl=False` в aiohttp (у сайта проблемы с сертификатом)
- Парсить только русскую версию (`/rus/docs/`)
- HTML-селекторы:
  - Заголовок: `h1` в `div.container_alpha.slogan`
  - Статус: `span.status` (классы: `status_new`, `status_upd`, `status_yts`)
  - Текст: `div.container_gamma.text > article`
  - Метаданные: `table.params` на странице `/info`
  - Перекрёстные ссылки: `div#from`, `div#to` на странице `/links`

## Правила анализа (pipeline/)

- Единица анализа — **норма** (пункт статьи), НЕ целый документ
- Эмбеддинги через Ollama API (`nomic-embed-text`), endpoint: `/api/embed`
- Кластеризация: UMAP (n_components=50) → HDBSCAN (min_cluster_size=5)
- Дублирование: cosine similarity > 0.85, подтверждение через LLM
- Противоречие: LLM-as-Judge с structured output (JSON)
- Устаревшие: статус `status_yts` ИЛИ ссылка на отменённый документ ИЛИ временной маркер
- Все промпты — в `llm/prompts.py`, НЕ хардкодить в pipeline
- Каждое обнаружение (Finding) содержит:
  - type: contradiction | duplication | outdated
  - severity: high | medium | low
  - confidence: float 0-1
  - explanation: str (от LLM, на русском)

## Правила LLM-промптов (llm/prompts.py)

- Все промпты на **русском** (qwen2.5:14b лучше работает с русскими юридическими текстами на русских промптах)
- Требовать JSON-ответ (для парсинга)
- Включать юридический контекст: lex posterior, lex specialis, иерархия НПА
- Включать примеры (few-shot) для каждого типа анализа
- Температура: 0.1 для анализа, 0.3 для объяснений
- max_tokens: 1000 для объяснений, 500 для классификации

## Правила API (api/)

- Все эндпоинты под префиксом `/api/`
- Пагинация: `?page=1&limit=20` для списков
- Фильтрация через query params: `?type=contradiction&severity=high&domain=Труд`
- SSE (Server-Sent Events) для `/api/analyze` — реалтайм прогресс
- CORS: разрешить `localhost:3100`
- Swagger UI автоматически на `/docs`
- Health check: `GET /api/health` — проверка Ollama, ChromaDB, SQLite

## Правила Frontend

- Приоритет страниц для демо (в порядке важности):
  1. Dashboard (`/`) — метрики, графики
  2. 3D-граф (`/graph`) — wow-фактор
  3. Детали обнаружения (`/findings/[id]`) — NormComparison + AiExplanation
  4. Список обнаружений (`/findings`) — таблица с фильтрами
  5. Анализ (`/analyze`) — загрузка + SSE прогресс
  6. Документы, About — если останется время
- Цветовая схема графа:
  - Узлы: синий=кодекс, зелёный=закон, фиолетовый=указ, серый=постановление
  - Рёбра: красный=противоречие, оранжевый=дублирование, серый=ссылка
- Все тексты интерфейса на **русском**
- Обязательно: disclaimer "Анализ выполнен ИИ и требует верификации юристом"
- Обязательно: кнопка "Неверное обнаружение" (human-in-the-loop)

## Docker

- НЕ создавать отдельный контейнер Ollama — использовать уже запущенный на сервере (localhost:11434)
- Backend: Python 3.12 slim + CUDA runtime (для sentence-transformers)
- Frontend: multi-stage build (Node → nginx)
- `docker compose up` должен запускать всё с нуля
- Healthchecks на каждый сервис

## Git

- Ветка: `main` (хакатон — не до веток)
- Conventional commits: `feat:`, `fix:`, `docs:`, `refactor:`
- Коммитить рабочее состояние каждые 2-3 часа
- НЕ коммитить: `backend/data/`, `node_modules/`, `.env`, `.next/`

## Приоритеты (что важнее)

1. **Рабочий прототип** > красивый код
2. **Реальные данные** > синтетические
3. **Explainability** > количество обнаружений
4. **3D-граф** > все остальные страницы
5. **Docker compose up** > инструкция по ручной установке
6. **README** > прочая документация

## Чего НЕ делать

- НЕ использовать langchain, llamaindex — прямые вызовы к Ollama
- НЕ использовать Neo4j, PostgreSQL — SQLite + ChromaDB + NetworkX
- НЕ парсить казахскую версию документов (на MVP только русская)
- НЕ пытаться проанализировать все 230 000 документов — только демо-набор (~50)
- НЕ делать аутентификацию — демо-режим, open access
- НЕ тратить время на тесты — хакатон, не продакшн
- НЕ overengineering — минимум абстракций, максимум результата
