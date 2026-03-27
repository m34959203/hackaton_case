FROM python:3.12-slim

WORKDIR /app

# Системные зависимости для lxml и scipy
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libxml2-dev \
    libxslt1-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код приложения (data/ исключен через .dockerignore)
COPY app/ ./app/
COPY scripts/ ./scripts/

# Создаем директории для данных (будут перекрыты volume mount)
RUN mkdir -p data/raw_html data/chroma

# Переменные окружения по умолчанию
ENV ZAN_OLLAMA_URL=http://host.docker.internal:11434 \
    ZAN_OLLAMA_MODEL=qwen2.5:14b \
    ZAN_OLLAMA_EMBED_MODEL=nomic-embed-text \
    ZAN_DB_PATH=data/zandb.sqlite \
    ZAN_CHROMA_PATH=data/chroma \
    ZAN_RAW_HTML_PATH=data/raw_html

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --retries=5 --start-period=15s \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/api/health').raise_for_status()"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
