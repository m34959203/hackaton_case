"""Асинхронный клиент для Ollama REST API."""

import json
import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class OllamaClient:
    """HTTP-клиент для взаимодействия с Ollama (generate + embed)."""

    def __init__(self, base_url: str | None = None) -> None:
        self._base_url = (base_url or settings.OLLAMA_URL).rstrip("/")
        self._generate_timeout = 120.0
        self._embed_timeout = 60.0

    # ------------------------------------------------------------------
    # Текстовая генерация
    # ------------------------------------------------------------------

    async def generate(
        self,
        prompt: str,
        model: str | None = None,
        temperature: float = 0.1,
        max_tokens: int = 500,
    ) -> str:
        """Генерация текстового ответа через POST /api/generate.

        Args:
            prompt: Текст промпта.
            model: Название модели (по умолчанию из конфига).
            temperature: Температура сэмплирования.
            max_tokens: Максимальное число токенов в ответе.

        Returns:
            Сгенерированный текст.
        """
        model = model or settings.OLLAMA_MODEL
        payload: dict = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        logger.debug(
            "Ollama generate: model=%s, temperature=%s, max_tokens=%s",
            model,
            temperature,
            max_tokens,
        )

        async with httpx.AsyncClient(timeout=self._generate_timeout) as client:
            response = await client.post(
                f"{self._base_url}/api/generate",
                json=payload,
            )
            response.raise_for_status()

        data = response.json()
        text: str = data.get("response", "")
        logger.debug("Ollama generate: получено %d символов", len(text))
        return text

    # ------------------------------------------------------------------
    # Генерация с JSON-выходом
    # ------------------------------------------------------------------

    async def generate_json(
        self,
        prompt: str,
        model: str | None = None,
        temperature: float = 0.1,
    ) -> dict:
        """Генерация структурированного JSON через POST /api/generate.

        Устанавливает ``format: "json"`` для получения валидного JSON.

        Args:
            prompt: Текст промпта (должен явно просить JSON).
            model: Название модели.
            temperature: Температура сэмплирования.

        Returns:
            Распарсенный JSON-ответ в виде словаря.

        Raises:
            ValueError: Если ответ модели не является валидным JSON.
        """
        model = model or settings.OLLAMA_MODEL
        payload: dict = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "format": "json",
            "options": {
                "temperature": temperature,
                "num_predict": settings.LLM_MAX_TOKENS_CLASSIFY,
            },
        }

        logger.debug("Ollama generate_json: model=%s", model)

        async with httpx.AsyncClient(timeout=self._generate_timeout) as client:
            response = await client.post(
                f"{self._base_url}/api/generate",
                json=payload,
            )
            response.raise_for_status()

        raw_text: str = response.json().get("response", "")

        try:
            result: dict = json.loads(raw_text)
        except json.JSONDecodeError as exc:
            logger.error("Невалидный JSON от Ollama: %s", raw_text[:500])
            raise ValueError(f"Ollama вернул невалидный JSON: {raw_text[:200]}") from exc

        logger.debug("Ollama generate_json: получен объект с %d ключами", len(result))
        return result

    # ------------------------------------------------------------------
    # Эмбеддинги
    # ------------------------------------------------------------------

    async def embed(
        self,
        texts: list[str],
        model: str | None = None,
    ) -> list[list[float]]:
        """Батчевое создание эмбеддингов через POST /api/embed.

        Args:
            texts: Список текстов для векторизации.
            model: Модель эмбеддингов (по умолчанию из конфига).

        Returns:
            Список векторов (по одному на каждый текст).
        """
        model = model or settings.OLLAMA_EMBED_MODEL
        payload: dict = {
            "model": model,
            "input": texts,
        }

        logger.debug("Ollama embed: model=%s, кол-во текстов=%d", model, len(texts))

        async with httpx.AsyncClient(timeout=self._embed_timeout) as client:
            response = await client.post(
                f"{self._base_url}/api/embed",
                json=payload,
            )
            response.raise_for_status()

        data = response.json()
        embeddings: list[list[float]] = data.get("embeddings", [])
        logger.debug("Ollama embed: получено %d векторов", len(embeddings))
        return embeddings
