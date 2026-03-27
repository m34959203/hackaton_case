"""Конфигурация приложения через pydantic-settings."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Настройки приложения. Значения можно переопределить через переменные окружения."""

    # LLM-провайдер: "ollama" | "openai" | "anthropic" | "gemini"
    LLM_PROVIDER: str = "ollama"

    # Ollama (локальный)
    OLLAMA_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen2.5:14b"
    OLLAMA_EMBED_MODEL: str = "nomic-embed-text"

    # OpenAI-совместимый API (Together.ai, Groq, OpenRouter и др.)
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = "https://api.together.xyz/v1"
    OPENAI_MODEL: str = "meta-llama/Llama-3.1-70B-Instruct-Turbo"

    # Anthropic API (Claude)
    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_MODEL: str = "claude-sonnet-4-20250514"

    # Google Gemini API
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.0-flash"

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
