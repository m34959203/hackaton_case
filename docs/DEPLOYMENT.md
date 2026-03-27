# Руководство по развёртыванию

## Быстрый старт (Docker Compose)

### Требования

- Docker 24+
- Docker Compose v2
- NVIDIA Container Toolkit (для GPU)
- 32 GB RAM (минимум 16 GB)
- NVIDIA GPU с 16+ GB VRAM

### Шаги

```bash
# 1. Клонировать
git clone https://github.com/m34959203/hackaton_case.git
cd hackaton_case

# 2. Настроить
cp .env.example .env
# Отредактировать .env при необходимости

# 3. Запустить
docker compose up -d

# 4. Первичная настройка (модели + данные)
make setup
# Или вручную:
docker exec ollama ollama pull qwen2.5:14b
docker exec ollama ollama pull nomic-embed-text
docker exec backend python -m scripts.scrape --all
docker exec backend python -m scripts.process --embed --cluster
docker exec backend python -m scripts.analyze --all

# 5. Открыть
# Frontend: http://localhost:3100
# API docs: http://localhost:8000/docs
```

### Демо-режим (без парсинга)

```bash
# Загрузить предварительно проанализированные данные
make demo
# Эквивалент:
docker exec backend python -m scripts.load_demo
docker compose up -d
```

## Docker Compose

```yaml
services:
  ollama:
    image: ollama/ollama:latest
    ports: ["11434:11434"]
    volumes: [ollama_data:/root/.ollama]
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    restart: unless-stopped

  backend:
    build: ./backend
    ports: ["8000:8000"]
    volumes: [./backend/data:/app/data]
    environment:
      OLLAMA_URL: http://ollama:11434
    depends_on: [ollama]
    restart: unless-stopped

  frontend:
    build: ./frontend
    ports: ["3100:3000"]
    environment:
      NEXT_PUBLIC_API_URL: http://localhost:8000
    depends_on: [backend]
    restart: unless-stopped

volumes:
  ollama_data:
```

## Проверка работоспособности

```bash
# Статус контейнеров
docker compose ps

# Health check
curl http://localhost:8000/api/health

# Логи
docker compose logs -f backend
docker compose logs -f frontend

# GPU usage
nvidia-smi
```

## Остановка

```bash
# Остановить все сервисы
docker compose down

# Остановить с удалением данных
docker compose down -v
```

## Обновление

```bash
git pull
docker compose build
docker compose up -d
```

## Ресурсы сервера

### Минимальные
| Ресурс | Значение |
|--------|---------|
| CPU | 4 cores |
| RAM | 16 GB |
| VRAM | 12 GB |
| Disk | 10 GB |

### Рекомендуемые
| Ресурс | Значение |
|--------|---------|
| CPU | 8+ cores |
| RAM | 32 GB |
| VRAM | 24+ GB |
| Disk | 50 GB |
| GPU | NVIDIA RTX 3090/4090/5090 |
