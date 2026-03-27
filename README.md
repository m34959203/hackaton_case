# ZanAlytics

**AI-система анализа и оптимизации законодательства Республики Казахстан**

> Decentrathon 5.0 | Трек: AI inDrive Gov | Кейс 1: Законодательная энтропия

[![Python](https://img.shields.io/badge/Python-3.12-blue)](https://python.org)
[![Next.js](https://img.shields.io/badge/Next.js-16-black)](https://nextjs.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

---

## Проблема

Количество законов и нормативных актов РК растёт экспоненциально. Новые поправки накладываются на старые, устаревшие нормы формально продолжают действовать, возникают **противоречия** и **дублирование**. Юристы тратят тысячи часов на проверку актуальности норм, а бизнес несёт издержки из-за регуляторной неопределённости.

## Решение

ZanAlytics — AI-система, которая:

- **Парсит** нормативные документы с [adilet.zan.kz](https://adilet.zan.kz) (официальная база НПА РК)
- **Выявляет** противоречия, дублирование и устаревшие нормы с помощью NLP и LLM
- **Визуализирует** связи между законами в интерактивном 3D-графе
- **Объясняет**, почему норма помечена как проблемная (Explainable AI)

## Текущие результаты

| Метрика | Значение |
|---------|----------|
| Документов проанализировано | 59 (кодексы + законы РК) |
| Норм извлечено | 54 526 |
| Перекрёстных ссылок | 870 514 |
| Тематических кластеров | 672 |
| Обнаружено дублирований | 200 |
| Обнаружено устаревших норм | 100 |
| Узлов в графе | 118 639 |
| Рёбер в графе | 196 453 |

## Архитектура

```
┌─────────────────────────────────┐
│     Frontend (Next.js :3300)    │
│  3D-граф • Дашборд • Сравнение  │
└──────────────┬──────────────────┘
               │ REST API + SSE
┌──────────────▼──────────────────┐
│     Backend (FastAPI :8001)     │
│  Scraper • NLP Pipeline • API   │
├──────┬────────┬─────────────────┤
│Ollama│ChromaDB│     SQLite      │
│:11434│embedded│   (metadata)    │
└──────┴────────┴─────────────────┘
```

### Стек технологий

| Компонент | Технология |
|-----------|-----------|
| Backend | Python 3.12, FastAPI, aiohttp, BeautifulSoup4, pydantic-settings |
| Frontend | Next.js 16, React 19, TypeScript 5, Tailwind CSS 4, shadcn/ui |
| 3D-визуализация | react-force-graph-3d, Three.js |
| Графики | Recharts |
| Data fetching | TanStack React Query |
| LLM | Ollama + qwen2.5:14b (анализ) |
| Embeddings | Ollama + nomic-embed-text (768-dim) |
| Vector DB | ChromaDB (embedded, persistent, cosine distance) |
| Graph | NetworkX → JSON → react-force-graph-3d |
| Clustering | UMAP (n_components=50) + HDBSCAN (min_cluster_size=5) |
| Database | SQLite (aiosqlite, 4 таблицы + 6 индексов) |

## Пайплайн анализа

```
Документы (adilet.zan.kz) — 59 документов
    │
    ▼
1. Парсинг HTML → извлечение статей и параграфов (54 526 норм)
    │
    ▼
2. Эмбеддинги (nomic-embed-text, 768-dim) → ChromaDB (~8 мин)
    │
    ▼
3. Кластеризация (UMAP + HDBSCAN) → 672 тематических кластера (~39 мин)
    │
    ▼
4. Анализ внутри кластеров:
    ├── Cosine similarity ≥ 0.92 → ДУБЛИРОВАНИЕ (200 находок)
    ├── LLM-as-Judge → ПРОТИВОРЕЧИЕ (в разработке)
    └── Статус документа → УСТАРЕВШИЕ НОРМЫ (100 находок)
    │
    ▼
5. Граф связей (NetworkX) → 3D визуализация
    │
    ▼
6. LLM-объяснения для каждого обнаружения
```

## Быстрый старт

### Требования

- Docker & Docker Compose
- NVIDIA GPU с CUDA (для Ollama)
- 16+ GB VRAM (рекомендуется)
- Ollama с моделями `qwen2.5:14b` и `nomic-embed-text`

### Запуск через Docker

```bash
# 1. Клонировать репозиторий
git clone https://github.com/m34959203/hackaton_case.git
cd hackaton_case

# 2. Настроить окружение
cp .env.example .env

# 3. Запустить сервисы
docker compose up -d

# 4. Открыть в браузере
open http://localhost:3300
```

### Запуск для разработки

```bash
# Backend (требуется conda или venv с Python 3.12)
cd backend
conda activate zan  # или: python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Инициализация и парсинг
python -m scripts.scrape
python -m scripts.quick_analyze

# Запуск API
uvicorn app.main:app --host 0.0.0.0 --port 8001

# Frontend (в отдельном терминале)
cd frontend
npm install
npm run dev  # порт 3300
```

## Страницы

| Страница | URL | Описание |
|----------|-----|----------|
| Дашборд | `/` | Метрики, графики по типам/серьёзности/доменам, последние находки |
| 3D-граф | `/graph` | Интерактивный граф связей, фильтры, клик по узлу/ребру |
| Обнаружения | `/findings` | Таблица с фильтрами по типу и серьёзности, пагинация |
| Детали | `/findings/:id` | Сравнение норм бок-о-бок + объяснение ИИ |
| Документы | `/documents` | Список документов с фильтрами |
| Документ | `/documents/:id` | Дерево статей/норм + связанные находки |
| Анализ | `/analyze` | Ввод текста → SSE-анализ в реалтайме |
| О системе | `/about` | Методология, стек, disclaimer |

### Цветовая схема графа

**Узлы** (по типу документа):
- 🟦 Индиго `#4f46e5` — Кодексы
- 🟩 Зелёный `#16a34a` — Законы
- 🟪 Фиолетовый `#9333ea` — Указы
- ⬜ Серый `#6b7280` — Постановления

**Рёбра** (по типу связи):
- 🔴 Красный `#ef4444` — Противоречия (+ анимированные частицы)
- 🟠 Оранжевый `#f97316` — Дублирования
- ⚪ Серый `#d1d5db` — Перекрёстные ссылки

## API-документация

Swagger UI: `http://localhost:8001/docs`

| Метод | Путь | Описание |
|-------|------|----------|
| GET | `/api/health` | Проверка здоровья (SQLite, ChromaDB, Ollama) |
| GET | `/api/stats` | Статистика дашборда |
| GET | `/api/documents` | Список документов (пагинация, фильтры) |
| GET | `/api/documents/:id` | Документ + список норм |
| GET | `/api/findings` | Список обнаружений (пагинация, фильтры) |
| GET | `/api/findings/:id` | Детали обнаружения + нормы |
| GET | `/api/graph` | Данные графа (nodes + links) |
| GET | `/api/search?q=текст` | Семантический поиск по нормам |
| GET | `/api/compare/:a/:b` | Сравнение двух норм |
| POST | `/api/analyze` | Анализ текста (SSE stream) |

## Демо-набор данных

59 документов из 12 правовых областей:

| Область | Документов | Ключевые |
|---------|-----------|----------|
| Конституция | 1 | Конституция РК |
| Труд | 8 | Трудовой кодекс, Социальный кодекс, Занятость |
| Земля | 4 | Земельный кодекс, Жилищные отношения |
| Налоги | 6 | Налоговый кодекс, Бюджетный кодекс, Госзакупки |
| Образование | 4 | Об образовании, О науке |
| Здравоохранение | 4 | Кодекс о здоровье, ОСМС |
| Экология | 5 | Экологический кодекс, Водный, Лесной |
| Предпринимательство | 8 | Предпринимательский кодекс, ГК, Конкуренция |
| Административное | 9 | УК, УПК, КоАП, Госслужба |
| Процессуальное | 3 | ГПК, Арбитраж |
| Транспорт | 3 | Дорожное движение, ОСАГО |
| Госуправление | 3 | Местное управление, Госуслуги |

## Структура проекта

```
hackaton_case/
├── backend/                    # FastAPI backend (35+ файлов)
│   ├── app/
│   │   ├── api/                # 9 REST endpoints
│   │   │   ├── documents.py    # /api/documents
│   │   │   ├── findings.py     # /api/findings
│   │   │   ├── graph.py        # /api/graph
│   │   │   ├── search.py       # /api/search
│   │   │   ├── compare.py      # /api/compare
│   │   │   ├── analyze.py      # /api/analyze (SSE)
│   │   │   └── stats.py        # /api/stats + /api/health
│   │   ├── scraper/            # Парсер adilet.zan.kz
│   │   │   ├── fetcher.py      # aiohttp + rate limit + retry + cache
│   │   │   ├── parser.py       # BeautifulSoup4 → метаданные + текст
│   │   │   ├── structural.py   # Regex state machine → статьи/пункты
│   │   │   └── seed_docs.py    # 59 верифицированных DOC_ID
│   │   ├── pipeline/           # NLP-анализ
│   │   │   ├── embedder.py     # Ollama nomic-embed-text → ChromaDB
│   │   │   ├── clusterer.py    # UMAP + HDBSCAN + LLM naming
│   │   │   ├── dedup.py        # Cosine similarity + LLM confirmation
│   │   │   ├── contradiction.py# LLM-as-Judge
│   │   │   ├── outdated.py     # Status + dates + LLM
│   │   │   └── graph_builder.py# NetworkX → JSON
│   │   ├── llm/                # Ollama integration
│   │   │   ├── client.py       # Async httpx client
│   │   │   └── prompts.py      # 5 промптов на русском
│   │   ├── models/             # Pydantic models
│   │   ├── config.py           # pydantic-settings
│   │   ├── database.py         # SQLite + ChromaDB
│   │   └── main.py             # FastAPI app
│   ├── scripts/
│   │   ├── scrape.py           # Парсинг документов
│   │   ├── analyze.py          # Полный pipeline
│   │   └── quick_analyze.py    # Быстрый анализ (embedding-based)
│   ├── data/                   # SQLite, ChromaDB, raw HTML, graph.json
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/                   # Next.js 16 frontend (40+ файлов)
│   └── src/
│       ├── app/                # 9 страниц (App Router)
│       ├── components/         # 16 React-компонентов
│       │   ├── dashboard/      # StatsCards, Charts (5)
│       │   ├── graph/          # ForceGraph3D, Controls, NodeInfo (3)
│       │   ├── findings/       # Table, Filters, Comparison, AI (5)
│       │   ├── analyze/        # Form, Progress, Results (3)
│       │   └── layout/         # Sidebar, Header
│       └── lib/                # API client, types, utils
├── docs/                       # 10 документов
├── docker-compose.yml
├── Makefile
└── CLAUDE.md                   # Правила разработки
```

## Ограничения

- Система является **инструментом поддержки**, а не заменой юридического эксперта
- Обнаружения требуют **верификации человеком** (human-in-the-loop)
- Качество анализа зависит от полноты данных в демо-наборе
- LLM может генерировать ложноположительные результаты — для каждого обнаружения указан уровень уверенности
- Поддерживается только русская версия документов (казахская — в планах)

## Методология

Подробное описание методологии анализа: [docs/METHODOLOGY.md](docs/METHODOLOGY.md)

## Команда

**Центр ИИ при ЖезУ** (Жезказган, Казахстан)

## Лицензия

MIT License — см. [LICENSE](LICENSE)
