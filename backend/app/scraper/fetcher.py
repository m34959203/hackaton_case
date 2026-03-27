"""Асинхронный HTTP-клиент для скачивания документов с adilet.zan.kz."""

import asyncio
import logging
from pathlib import Path

import aiohttp

from app.config import settings

logger = logging.getLogger(__name__)


class AdiletFetcher:
    """Загрузчик HTML-страниц с adilet.zan.kz.

    Поддерживает rate limiting, кэширование и retry с экспоненциальной задержкой.
    """

    MAX_RETRIES = 3
    BACKOFF_BASE = 2.0

    def __init__(self) -> None:
        self._semaphore = asyncio.Semaphore(settings.SCRAPER_RATE_LIMIT)
        self._session: aiohttp.ClientSession | None = None
        self._cache_dir = Path(settings.RAW_HTML_PATH)
        self._cache_dir.mkdir(parents=True, exist_ok=True)

    async def _get_session(self) -> aiohttp.ClientSession:
        """Получить или создать aiohttp-сессию."""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=60)
            self._session = aiohttp.ClientSession(
                timeout=timeout,
                headers={
                    "User-Agent": "ZanAlytics/1.0 (hackathon research bot)",
                    "Accept-Language": "ru",
                },
            )
        return self._session

    async def close(self) -> None:
        """Закрыть HTTP-сессию."""
        if self._session and not self._session.closed:
            await self._session.close()

    def _cache_path(self, doc_id: str, suffix: str = "") -> Path:
        """Путь к кэш-файлу для данного документа."""
        filename = f"{doc_id}{suffix}.html"
        return self._cache_dir / filename

    def _is_cached(self, doc_id: str, suffix: str = "") -> bool:
        """Проверить наличие документа в кэше."""
        path = self._cache_path(doc_id, suffix)
        return path.exists() and path.stat().st_size > 0

    def _read_cache(self, doc_id: str, suffix: str = "") -> str:
        """Прочитать HTML из кэша."""
        return self._cache_path(doc_id, suffix).read_text(encoding="utf-8")

    def _write_cache(self, doc_id: str, html: str, suffix: str = "") -> None:
        """Сохранить HTML в кэш."""
        self._cache_path(doc_id, suffix).write_text(html, encoding="utf-8")

    async def _fetch_url(self, url: str) -> str:
        """Выполнить HTTP-запрос с retry и rate limiting.

        Повторяет запрос до MAX_RETRIES раз с экспоненциальной задержкой.
        """
        session = await self._get_session()
        last_error: Exception | None = None

        for attempt in range(self.MAX_RETRIES):
            async with self._semaphore:
                try:
                    async with session.get(
                        url, ssl=settings.SCRAPER_SSL_VERIFY
                    ) as resp:
                        resp.raise_for_status()
                        return await resp.text(encoding="utf-8")
                except (aiohttp.ClientError, asyncio.TimeoutError) as exc:
                    last_error = exc
                    delay = self.BACKOFF_BASE ** attempt
                    logger.warning(
                        "Попытка %d/%d для %s: %s. Повтор через %.1f сек.",
                        attempt + 1,
                        self.MAX_RETRIES,
                        url,
                        exc,
                        delay,
                    )
                    await asyncio.sleep(delay)

        msg = f"Не удалось загрузить {url} после {self.MAX_RETRIES} попыток"
        raise aiohttp.ClientError(msg) from last_error

    async def fetch_document(self, doc_id: str) -> str:
        """Загрузить основную страницу документа.

        Возвращает HTML-текст. Использует кэш при повторных запросах.
        """
        if self._is_cached(doc_id):
            logger.debug("Кэш-попадание: %s", doc_id)
            return self._read_cache(doc_id)

        url = f"{settings.ADILET_BASE_URL}/rus/docs/{doc_id}"
        html = await self._fetch_url(url)
        self._write_cache(doc_id, html)
        logger.info("Загружен документ: %s", doc_id)
        return html

    async def fetch_info(self, doc_id: str) -> str:
        """Загрузить страницу метаданных документа (/info).

        Содержит таблицу с параметрами: дата принятия, орган, юридическая сила и т.д.
        """
        suffix = "_info"
        if self._is_cached(doc_id, suffix):
            logger.debug("Кэш-попадание: %s (info)", doc_id)
            return self._read_cache(doc_id, suffix)

        url = f"{settings.ADILET_BASE_URL}/rus/docs/{doc_id}/info"
        html = await self._fetch_url(url)
        self._write_cache(doc_id, html, suffix)
        logger.info("Загружена информация: %s", doc_id)
        return html

    async def fetch_links(self, doc_id: str) -> str:
        """Загрузить страницу перекрёстных ссылок документа (/links).

        Содержит блоки div#from (ссылается на) и div#to (ссылаются на этот).
        """
        suffix = "_links"
        if self._is_cached(doc_id, suffix):
            logger.debug("Кэш-попадание: %s (links)", doc_id)
            return self._read_cache(doc_id, suffix)

        url = f"{settings.ADILET_BASE_URL}/rus/docs/{doc_id}/links"
        html = await self._fetch_url(url)
        self._write_cache(doc_id, html, suffix)
        logger.info("Загружены ссылки: %s", doc_id)
        return html
