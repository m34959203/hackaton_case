"""Конфигурация приложения через pydantic-settings."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Настройки приложения. Значения можно переопределить через переменные окружения."""

    # Ollama
    OLLAMA_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen2.5:14b"
    OLLAMA_EMBED_MODEL: str = "nomic-embed-text"

    # Хранилища (относительно backend/)
    DB_PATH: str = "data/zandb.sqlite"
    CHROMA_PATH: str = "data/chroma"
    RAW_HTML_PATH: str = "data/raw_html"

    # Парсер adilet.zan.kz
    ADILET_BASE_URL: str = "https://adilet.zan.kz"
    SCRAPER_RATE_LIMIT: int = 2
    SCRAPER_SSL_VERIFY: bool = False

    # Пороги анализа
    SIMILARITY_THRESHOLD: float = 0.85
    CONTRADICTION_CONFIDENCE_MIN: float = 0.6

    # Параметры LLM
    LLM_TEMPERATURE_ANALYSIS: float = 0.1
    LLM_TEMPERATURE_EXPLAIN: float = 0.3
    LLM_MAX_TOKENS_EXPLAIN: int = 1000
    LLM_MAX_TOKENS_CLASSIFY: int = 500

    # API
    API_PAGE_SIZE: int = 20
    CORS_ORIGINS: list[str] = [
        "http://localhost:3100",
        "http://localhost:3300",
        "http://100.118.110.5:3300",
    ]

    model_config = {"env_prefix": "ZAN_"}


settings = Settings()
