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

# Создать виртуальное окружение
python -m venv .venv
source .venv/bin/activate

# Установить зависимости
pip install -e ".[dev]"

# Настроить переменные
cp ../.env.example .env
# Отредактировать .env

# Запустить
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Frontend

```bash
cd frontend

# Установить зависимости
npm install

# Запустить dev server
npm run dev -- -p 3100
```

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
make setup      # Первоначальная настройка (модели + парсинг + анализ)
make dev        # Запуск всех сервисов для разработки
make scrape     # Парсинг документов с adilet.zan.kz
make embed      # Генерация эмбеддингов
make analyze    # Запуск анализа (дублирование + противоречия + устаревшие)
make demo       # Загрузка демо-данных + запуск
make test       # Запуск тестов
make lint       # Проверка кода (ruff + eslint)
make format     # Форматирование (ruff format + prettier)
```

## Скрипты CLI

### Парсинг документов

```bash
cd backend

# Парсинг всех документов из seed-списка
python -m scripts.scrape --all

# Парсинг конкретного документа
python -m scripts.scrape --doc K1500000414

# Парсинг с расширением по ссылкам
python -m scripts.scrape --doc K1500000414 --follow-links --depth 1
```

### Генерация эмбеддингов

```bash
# Все нормы
python -m scripts.process --embed

# С кластеризацией
python -m scripts.process --embed --cluster
```

### Анализ

```bash
# Полный анализ
python -m scripts.analyze --all

# Только дублирование
python -m scripts.analyze --dedup

# Только противоречия
python -m scripts.analyze --contradictions

# Только устаревшие
python -m scripts.analyze --outdated
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
| `NEXT_PUBLIC_API_URL` | URL API для frontend | `http://localhost:8000` |

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
