"""Универсальный LLM-клиент с поддержкой Ollama, OpenAI API, Anthropic."""

import json
import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class LLMClient:
    """Универсальный LLM-клиент с поддержкой Ollama, OpenAI-совместимых API и Anthropic."""

    def __init__(self, base_url: str | None = None) -> None:
        self._ollama_base_url = (base_url or settings.OLLAMA_URL).rstrip("/")
        self._generate_timeout = 120.0
        self._embed_timeout = 60.0

    # ------------------------------------------------------------------
    # Определение текущей модели по провайдеру
    # ------------------------------------------------------------------

    @staticmethod
    def _current_model() -> str:
        """Возвращает имя текущей модели в зависимости от провайдера."""
        provider = settings.LLM_PROVIDER
        if provider == "openai":
            return settings.OPENAI_MODEL
        elif provider == "anthropic":
            return settings.ANTHROPIC_MODEL
        elif provider == "gemini":
            return settings.GEMINI_MODEL
        return settings.OLLAMA_MODEL

    # ------------------------------------------------------------------
    # Текстовая генерация (роутинг по провайдеру)
    # ------------------------------------------------------------------

    async def generate(
        self,
        prompt: str,
        model: str | None = None,
        temperature: float = 0.1,
        max_tokens: int = 500,
    ) -> str:
        """Генерация текстового ответа через текущий LLM-провайдер.

        Args:
            prompt: Текст промпта.
            model: Название модели (по умолчанию из конфига текущего провайдера).
            temperature: Температура сэмплирования.
            max_tokens: Максимальное число токенов в ответе.

        Returns:
            Сгенерированный текст.
        """
        provider = settings.LLM_PROVIDER

        if provider == "openai":
            return await self._openai_generate(prompt, model, temperature, max_tokens)
        elif provider == "anthropic":
            return await self._anthropic_generate(prompt, model, temperature, max_tokens)
        elif provider == "gemini":
            return await self._gemini_generate(prompt, model, temperature, max_tokens)
        else:
            return await self._ollama_generate(prompt, model, temperature, max_tokens)

    # ------------------------------------------------------------------
    # Генерация с JSON-выходом (роутинг по провайдеру)
    # ------------------------------------------------------------------

    async def generate_json(
        self,
        prompt: str,
        model: str | None = None,
        temperature: float = 0.1,
    ) -> dict:
        """Генерация структурированного JSON через текущий LLM-провайдер.

        Args:
            prompt: Текст промпта (должен явно просить JSON).
            model: Название модели.
            temperature: Температура сэмплирования.

        Returns:
            Распарсенный JSON-ответ в виде словаря.

        Raises:
            ValueError: Если ответ модели не является валидным JSON.
        """
        provider = settings.LLM_PROVIDER

        if provider == "openai":
            return await self._openai_generate_json(prompt, model, temperature)
        elif provider == "anthropic":
            return await self._anthropic_generate_json(prompt, model, temperature)
        elif provider == "gemini":
            return await self._gemini_generate_json(prompt, model, temperature)
        else:
            return await self._ollama_generate_json(prompt, model, temperature)

    # ------------------------------------------------------------------
    # Эмбеддинги (всегда через Ollama — локальный nomic-embed-text)
    # ------------------------------------------------------------------

    async def embed(
        self,
        texts: list[str],
        model: str | None = None,
    ) -> list[list[float]]:
        """Батчевое создание эмбеддингов через Ollama POST /api/embed.

        Эмбеддинги всегда создаются локально через Ollama (nomic-embed-text),
        независимо от выбранного LLM-провайдера.

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
                f"{self._ollama_base_url}/api/embed",
                json=payload,
            )
            response.raise_for_status()

        data = response.json()
        embeddings: list[list[float]] = data.get("embeddings", [])
        logger.debug("Ollama embed: получено %d векторов", len(embeddings))
        return embeddings

    # ==================================================================
    # Ollama
    # ==================================================================

    async def _ollama_generate(
        self,
        prompt: str,
        model: str | None = None,
        temperature: float = 0.1,
        max_tokens: int = 500,
    ) -> str:
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
            model, temperature, max_tokens,
        )

        async with httpx.AsyncClient(timeout=self._generate_timeout) as client:
            response = await client.post(
                f"{self._ollama_base_url}/api/generate",
                json=payload,
            )
            response.raise_for_status()

        data = response.json()
        text: str = data.get("response", "")
        logger.debug("Ollama generate: получено %d символов", len(text))
        return text

    async def _ollama_generate_json(
        self,
        prompt: str,
        model: str | None = None,
        temperature: float = 0.1,
    ) -> dict:
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
                f"{self._ollama_base_url}/api/generate",
                json=payload,
            )
            response.raise_for_status()

        raw_text: str = response.json().get("response", "")
        return self._parse_json(raw_text, "Ollama")

    # ==================================================================
    # OpenAI-совместимый API (Together.ai, Groq, OpenRouter и др.)
    # ==================================================================

    async def _openai_generate(
        self,
        prompt: str,
        model: str | None = None,
        temperature: float = 0.1,
        max_tokens: int = 500,
    ) -> str:
        model = model or settings.OPENAI_MODEL
        logger.debug(
            "OpenAI generate: model=%s, temperature=%s, max_tokens=%s",
            model, temperature, max_tokens,
        )

        async with httpx.AsyncClient(timeout=self._generate_timeout) as client:
            response = await client.post(
                f"{settings.OPENAI_BASE_URL}/chat/completions",
                headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY}"},
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                },
            )
            response.raise_for_status()

        text: str = response.json()["choices"][0]["message"]["content"]
        logger.debug("OpenAI generate: получено %d символов", len(text))
        return text

    async def _openai_generate_json(
        self,
        prompt: str,
        model: str | None = None,
        temperature: float = 0.1,
    ) -> dict:
        model = model or settings.OPENAI_MODEL
        logger.debug("OpenAI generate_json: model=%s", model)

        request_json: dict = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": settings.LLM_MAX_TOKENS_CLASSIFY,
        }
        # response_format поддерживается большинством OpenAI-совместимых API
        request_json["response_format"] = {"type": "json_object"}

        async with httpx.AsyncClient(timeout=self._generate_timeout) as client:
            response = await client.post(
                f"{settings.OPENAI_BASE_URL}/chat/completions",
                headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY}"},
                json=request_json,
            )
            response.raise_for_status()

        raw_text: str = response.json()["choices"][0]["message"]["content"]
        return self._parse_json(raw_text, "OpenAI")

    # ==================================================================
    # Anthropic API (Claude)
    # ==================================================================

    async def _anthropic_generate(
        self,
        prompt: str,
        model: str | None = None,
        temperature: float = 0.1,
        max_tokens: int = 500,
    ) -> str:
        model = model or settings.ANTHROPIC_MODEL
        logger.debug(
            "Anthropic generate: model=%s, temperature=%s, max_tokens=%s",
            model, temperature, max_tokens,
        )

        async with httpx.AsyncClient(timeout=self._generate_timeout) as client:
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": settings.ANTHROPIC_API_KEY,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": model,
                    "max_tokens": max_tokens,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": temperature,
                },
            )
            response.raise_for_status()

        data = response.json()
        # Anthropic возвращает список content blocks
        text: str = data["content"][0]["text"]
        logger.debug("Anthropic generate: получено %d символов", len(text))
        return text

    async def _anthropic_generate_json(
        self,
        prompt: str,
        model: str | None = None,
        temperature: float = 0.1,
    ) -> dict:
        model = model or settings.ANTHROPIC_MODEL
        logger.debug("Anthropic generate_json: model=%s", model)

        async with httpx.AsyncClient(timeout=self._generate_timeout) as client:
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": settings.ANTHROPIC_API_KEY,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": model,
                    "max_tokens": settings.LLM_MAX_TOKENS_CLASSIFY,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": temperature,
                },
            )
            response.raise_for_status()

        data = response.json()
        raw_text: str = data["content"][0]["text"]
        return self._parse_json(raw_text, "Anthropic")

    # ==================================================================
    # Google Gemini API
    # ==================================================================

    async def _gemini_generate(
        self,
        prompt: str,
        model: str | None = None,
        temperature: float = 0.1,
        max_tokens: int = 500,
    ) -> str:
        """Генерация через Google Gemini API (OpenAI-совместимый endpoint)."""
        model = model or settings.GEMINI_MODEL
        logger.debug(
            "Gemini generate: model=%s, temperature=%s, max_tokens=%s",
            model, temperature, max_tokens,
        )

        async with httpx.AsyncClient(timeout=self._generate_timeout) as client:
            response = await client.post(
                "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
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

    async def _gemini_generate_json(
        self,
        prompt: str,
        model: str | None = None,
        temperature: float = 0.1,
    ) -> dict:
        """Генерация JSON через Google Gemini API."""
        model = model or settings.GEMINI_MODEL
        logger.debug("Gemini generate_json: model=%s", model)

        async with httpx.AsyncClient(timeout=self._generate_timeout) as client:
            response = await client.post(
                "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
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
        return self._parse_json(raw_text, "Gemini")

    # ==================================================================
    # Утилиты
    # ==================================================================

    @staticmethod
    def _parse_json(raw_text: str, provider_name: str) -> dict:
        """Парсинг JSON из ответа LLM. Пробует извлечь JSON из markdown-блоков."""
        text = raw_text.strip()

        # Попытка извлечь JSON из markdown code block
        if text.startswith("```"):
            lines = text.split("\n")
            # Убираем первую и последнюю строку (```)
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
            logger.error("Невалидный JSON от %s: %s", provider_name, raw_text[:500])
            raise ValueError(
                f"{provider_name} вернул невалидный JSON: {raw_text[:200]}"
            ) from exc

        logger.debug(
            "%s generate_json: получен объект с %d ключами",
            provider_name, len(result),
        )
        return result


# Обратная совместимость — OllamaClient это алиас для LLMClient
OllamaClient = LLMClient
