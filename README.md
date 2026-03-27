# ZanAlytics

**AI-система анализа и оптимизации законодательства Республики Казахстан**

> Decentrathon 5.0 | Трек: AI inDrive Gov | Кейс 1: Законодательная энтропия

[![Python](https://img.shields.io/badge/Python-3.12-blue)](https://python.org)
[![Next.js](https://img.shields.io/badge/Next.js-15-black)](https://nextjs.org)
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

## Скриншоты

> _Будут добавлены после завершения разработки UI_

## Архитектура

```
┌─────────────────────────────────┐
│     Frontend (Next.js :3100)    │
│  3D-граф • Дашборд • Сравнение  │
└──────────────┬──────────────────┘
               │ REST API + SSE
┌──────────────▼──────────────────┐
│     Backend (FastAPI :8000)     │
│  Scraper • NLP Pipeline • API   │
├──────┬────────┬─────────────────┤
│Ollama│ChromaDB│     SQLite      │
│:11434│embedded│   (metadata)    │
└──────┴────────┴─────────────────┘
```

### Стек технологий

| Компонент | Технология |
|-----------|-----------|
| Backend | Python 3.12, FastAPI, aiohttp, BeautifulSoup4 |
| Frontend | Next.js 15, React 19, TypeScript, Tailwind CSS, shadcn/ui |
| LLM | Ollama + Qwen2.5:14B (анализ) |
| Embeddings | BAAI/bge-m3 (1024-dim, мультиязычные) |
| Vector DB | ChromaDB (embedded, persistent) |
| Graph | NetworkX → react-force-graph-3d |
| Clustering | UMAP + HDBSCAN |
| NLP | natasha, razdel (русский язык) |

## Пайплайн анализа

```
Документы (adilet.zan.kz)
    │
    ▼
1. Парсинг HTML → извлечение статей и параграфов
    │
    ▼
2. Эмбеддинги (bge-m3) → ChromaDB
    │
    ▼
3. Кластеризация (UMAP + HDBSCAN) → тематические группы
    │
    ▼
4. Анализ внутри кластеров:
    ├── Cosine similarity > 0.85 → ДУБЛИРОВАНИЕ
    ├── LLM-as-Judge → ПРОТИВОРЕЧИЕ
    └── Статус + даты → УСТАРЕВШИЕ НОРМЫ
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
- NVIDIA GPU с CUDA (для Ollama и эмбеддингов)
- 16+ GB VRAM (рекомендуется)

### Запуск

```bash
# 1. Клонировать репозиторий
git clone https://github.com/m34959203/hackaton_case.git
cd hackaton_case

# 2. Настроить окружение
cp .env.example .env

# 3. Запустить все сервисы
docker compose up -d

# 4. Загрузить модели Ollama (первый запуск)
docker exec ollama ollama pull qwen2.5:14b
docker exec ollama ollama pull nomic-embed-text

# 5. Запустить начальный парсинг и анализ
make setup

# 6. Открыть в браузере
open http://localhost:3100
```

### Запуск для разработки

```bash
# Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8000

# Frontend (в отдельном терминале)
cd frontend
npm install
npm run dev -- -p 3100
```

## Использование

### Дашборд (`/`)
Обзорная страница с ключевыми метриками: количество проанализированных документов, найденных противоречий, дублирований и устаревших норм.

### 3D-граф (`/graph`)
Интерактивная визуализация связей между законами:
- **Синие узлы** — кодексы
- **Зелёные узлы** — законы
- **Красные рёбра** — противоречия
- **Оранжевые рёбра** — дублирования
- **Серые рёбра** — перекрёстные ссылки

### Обнаружения (`/findings`)
Список всех найденных проблем с фильтрацией по типу, серьёзности и правовой области.

### Сравнение (`/findings/:id`)
Две нормы бок-о-бок с подсветкой различий и объяснением ИИ.

### Анализ (`/analyze`)
Загрузка текста нового документа для анализа в реальном времени.

## Источники данных

- **Әділет** ([adilet.zan.kz](https://adilet.zan.kz)) — информационно-правовая система НПА РК, Институт законодательства и правовой информации при Министерстве юстиции
- **Открытые данные** ([data.egov.kz](https://data.egov.kz)) — портал открытых данных

### Демо-набор данных

Для демонстрации проанализированы ~50 ключевых документов в области трудового права:
- Конституция РК
- Трудовой кодекс
- Предпринимательский кодекс
- Гражданский кодекс (общая и особенная части)
- Налоговый кодекс
- Закон о занятости населения
- ~40 связанных законов и подзаконных актов

## API-документация

Swagger UI доступен по адресу: `http://localhost:8000/docs`

Ключевые эндпоинты:

| Метод | Путь | Описание |
|-------|------|----------|
| GET | `/api/stats` | Статистика дашборда |
| GET | `/api/documents` | Список документов |
| GET | `/api/findings` | Список обнаружений |
| GET | `/api/graph` | Данные графа (JSON) |
| POST | `/api/search` | Семантический поиск |
| POST | `/api/analyze` | Анализ нового текста (SSE) |
| GET | `/api/compare/{a}/{b}` | Сравнение двух норм |

## Ограничения

- Система является **инструментом поддержки**, а не заменой юридического эксперта
- Обнаружения требуют **верификации человеком** (human-in-the-loop)
- Качество анализа зависит от полноты данных в демо-наборе
- LLM может генерировать ложноположительные результаты — для каждого обнаружения указан уровень уверенности
- Поддерживается только русская версия документов (казахская — в планах)

## Методология

Подробное описание методологии анализа: [docs/METHODOLOGY.md](docs/METHODOLOGY.md)

## Структура проекта

```
hackaton_case/
├── backend/              # FastAPI backend
│   ├── app/
│   │   ├── api/          # REST endpoints
│   │   ├── scraper/      # adilet.zan.kz parser
│   │   ├── pipeline/     # NLP analysis pipeline
│   │   ├── llm/          # Ollama client + prompts
│   │   └── models/       # Data models
│   └── scripts/          # CLI scripts
├── frontend/             # Next.js frontend
│   └── src/
│       ├── app/          # Pages (App Router)
│       ├── components/   # React components
│       └── lib/          # API client, types
├── docs/                 # Documentation
├── demo/                 # Pre-analyzed demo data
└── docker-compose.yml    # Orchestration
```

## Команда

**Центр ИИ при ЖезУ** (Жезказган, Казахстан)

## Лицензия

MIT License — см. [LICENSE](LICENSE)
