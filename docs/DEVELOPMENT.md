# Руководство по разработке

## Требования

- Python 3.12+
- Node.js 20+
- Docker & Docker Compose
- NVIDIA GPU с CUDA 12+ (для Ollama и эмбеддингов)
- 16+ GB VRAM (рекомендуется 24+)

## Структура проекта

```
hackaton_case/
├── backend/                 # Python FastAPI backend
│   ├── app/
│   │   ├── main.py          # FastAPI app entry point
│   │   ├── config.py        # Настройки (pydantic-settings)
│   │   ├── database.py      # SQLite + ChromaDB connections
│   │   ├── api/             # REST API endpoints
│   │   ├── scraper/         # Парсер adilet.zan.kz
│   │   ├── pipeline/        # NLP анализ
│   │   ├── llm/             # Ollama клиент
│   │   ├── models/          # Pydantic модели
│   │   └── utils/           # Утилиты
│   ├── scripts/             # CLI скрипты
│   ├── data/                # Runtime данные (gitignored)
│   └── pyproject.toml       # Зависимости
├── frontend/                # Next.js frontend
│   ├── src/
│   │   ├── app/             # Pages (App Router)
│   │   ├── components/      # React компоненты
│   │   ├── lib/             # API клиент, типы
│   │   └── hooks/           # React хуки
│   └── package.json
├── docs/                    # Документация
├── demo/                    # Демо-данные
└── docker-compose.yml
```

## Локальная разработка

### 1. Backend

```bash
cd backend

# Активировать conda-окружение (Python 3.12)
conda activate zan
# Python: /home/ubuntu/miniconda3/envs/zan/bin/python

# Установить зависимости
pip install -r requirements.txt

# Запустить API (порт 8001, т.к. 8000 занят на сервере)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

> **Важно**: на dev-сервере порт 8000 занят другим сервисом. Backend запускается на **8001**.

### 2. Frontend

```bash
cd frontend

# Установить зависимости
npm install

# Запустить dev server (порт 3300, т.к. 3100 занят)
npm run dev
# Откроется на http://localhost:3300
```

> **Важно**: порт 3100 занят. Frontend настроен на **3300** (см. `package.json` → `dev` скрипт).
> `NEXT_PUBLIC_API_URL` должен указывать на `http://localhost:8001` при локальной разработке.

### 3. Ollama

```bash
# Ollama должен быть запущен отдельно или через docker compose
ollama serve

# Загрузить модели
ollama pull qwen2.5:14b
ollama pull nomic-embed-text
```

## Docker

### Полный запуск

```bash
docker compose up -d
```

### Только backend

```bash
docker compose up -d ollama backend
```

### Пересборка после изменений

```bash
docker compose build backend
docker compose up -d backend
```

## Makefile

```bash
make setup      # Первый запуск: scrape + analyze
make dev        # Запуск backend (8001) + frontend (3300) для разработки
make docker     # Сборка Docker-образов и запуск контейнеров
make scrape     # Парсинг документов с adilet.zan.kz
make analyze    # Полный анализ (эмбеддинги + кластеризация + findings)
make embed      # Генерация эмбеддингов (алиас для analyze)
make stop       # Остановка Docker контейнеров
make logs       # Логи Docker контейнеров
make test       # Запуск тестов (pytest)
make lint       # Проверка кода (ruff + eslint)
make format     # Форматирование (ruff format + prettier)
make clean      # Очистка данных (SQLite, ChromaDB, raw HTML, .next)
```

## Скрипты CLI

### Парсинг документов

```bash
cd backend
conda activate zan

# Парсинг всех 59 документов из seed-списка (кэш в data/raw_html/)
python -m scripts.scrape

# Быстрый анализ (эмбеддинги + дублирование + устаревшие)
python -m scripts.quick_analyze
```

### Перезапуск сервисов

```bash
# Backend: перезапуск (Ctrl+C и заново)
cd backend && conda activate zan
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001

# Frontend: перезапуск
cd frontend
npm run dev

# Docker: перезапуск
docker compose down && docker compose up -d

# Проверка здоровья
curl http://localhost:8001/api/health
```

## Переменные окружения

| Переменная | Описание | Default |
|-----------|----------|---------|
| `OLLAMA_URL` | URL Ollama API | `http://localhost:11434` |
| `OLLAMA_MODEL` | Модель для анализа | `qwen2.5:14b` |
| `EMBED_MODEL` | Модель эмбеддингов | `nomic-embed-text` |
| `DATABASE_URL` | Путь к SQLite | `sqlite:///data/zandb.sqlite` |
| `CHROMA_PERSIST_DIR` | Директория ChromaDB | `./data/chroma` |
| `SCRAPE_RATE_LIMIT` | Запросов в секунду | `2` |
| `SIMILARITY_THRESHOLD` | Порог дублирования | `0.85` |
| `CONTRADICTION_CONFIDENCE` | Мин. уверенность | `0.7` |
| `NEXT_PUBLIC_API_URL` | URL API для frontend | `http://localhost:8001` (dev) / `http://localhost:8000` (Docker) |

## Тестирование

### Backend

```bash
cd backend
pytest tests/ -v
pytest tests/ -v --cov=app  # с покрытием
```

### Frontend

```bash
cd frontend
npm run test
```

## Code Style

### Python (Backend)
- **Formatter**: `ruff format`
- **Linter**: `ruff check`
- **Type checking**: `mypy` (strict)
- **Import sorting**: ruff (isort compatible)

### TypeScript (Frontend)
- **Formatter**: `prettier`
- **Linter**: `eslint` (next config)
- **Strict mode**: enabled

## Git Workflow

```bash
# Ветки
main        # Стабильный код
dev         # Текущая разработка
feat/*      # Фичи
fix/*       # Баг-фиксы

# Коммиты (conventional commits)
feat: add contradiction detection pipeline
fix: handle empty articles in parser
docs: update API documentation
refactor: extract embedding logic
```

## Troubleshooting

### Ollama не отвечает
```bash
# Проверить статус
curl http://localhost:11434/api/tags
# Перезапустить
docker compose restart ollama
```

### ChromaDB ошибки
```bash
# Очистить и пересоздать
rm -rf backend/data/chroma
python -m scripts.process --embed
```

### GPU out of memory
```bash
# Проверить VRAM
nvidia-smi
# Использовать меньшую модель
export OLLAMA_MODEL=qwen2.5:7b
```
