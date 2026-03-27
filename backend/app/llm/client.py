"""LLM-клиент для Google Gemini API."""

import json
import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"


class LLMClient:
    """LLM-клиент через Google Gemini API (OpenAI-совместимый endpoint)."""

    def __init__(self) -> None:
        self._ollama_base_url = settings.OLLAMA_URL.rstrip("/")
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
        """Генерация текстового ответа через Gemini."""
        model = model or settings.GEMINI_MODEL

        logger.debug("Gemini generate: model=%s, temp=%s", model, temperature)

        async with httpx.AsyncClient(timeout=self._generate_timeout) as client:
            response = await client.post(
                GEMINI_API_URL,
                headers={
                    "Authorization": f"Bearer {settings.GEMINI_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                },
            )
            response.raise_for_status()

        text: str = response.json()["choices"][0]["message"]["content"]
        logger.debug("Gemini generate: получено %d символов", len(text))
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
        """Генерация структурированного JSON через Gemini."""
        model = model or settings.GEMINI_MODEL

        logger.debug("Gemini generate_json: model=%s", model)

        async with httpx.AsyncClient(timeout=self._generate_timeout) as client:
            response = await client.post(
                GEMINI_API_URL,
                headers={
                    "Authorization": f"Bearer {settings.GEMINI_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": temperature,
                    "max_tokens": settings.LLM_MAX_TOKENS_CLASSIFY,
                    "response_format": {"type": "json_object"},
                },
            )
            response.raise_for_status()

        raw_text: str = response.json()["choices"][0]["message"]["content"]
        return self._parse_json(raw_text)

    # ------------------------------------------------------------------
    # Эмбеддинги (через Ollama — локальный nomic-embed-text)
    # ------------------------------------------------------------------

    async def embed(
        self,
        texts: list[str],
        model: str | None = None,
    ) -> list[list[float]]:
        """Батчевое создание эмбеддингов через Ollama (nomic-embed-text)."""
        model = model or settings.OLLAMA_EMBED_MODEL
        payload: dict = {"model": model, "input": texts}

        logger.debug("Ollama embed: model=%s, текстов=%d", model, len(texts))

        async with httpx.AsyncClient(timeout=self._embed_timeout) as client:
            response = await client.post(
                f"{self._ollama_base_url}/api/embed",
                json=payload,
            )
            response.raise_for_status()

        data = response.json()
        embeddings: list[list[float]] = data.get("embeddings", [])
        logger.debug("Ollama embed: получено %d векторов", len(embeddings))
        return embeddings

    # ------------------------------------------------------------------
    # Утилиты
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_json(raw_text: str) -> dict:
        """Парсинг JSON из ответа LLM."""
        text = raw_text.strip()

        # Извлечь JSON из markdown code block
        if text.startswith("```"):
            lines = text.split("\n")
            json_lines = []
            inside = False
            for line in lines:
                if line.strip().startswith("```") and not inside:
                    inside = True
                    continue
                elif line.strip() == "```" and inside:
                    break
                elif inside:
                    json_lines.append(line)
            if json_lines:
                text = "\n".join(json_lines)

        try:
            result: dict = json.loads(text)
        except json.JSONDecodeError as exc:
            logger.error("Невалидный JSON от Gemini: %s", raw_text[:500])
            raise ValueError(f"Gemini вернул невалидный JSON: {raw_text[:200]}") from exc

        return result


# Обратная совместимость
OllamaClient = LLMClient
