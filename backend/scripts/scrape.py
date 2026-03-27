"""CLI-скрипт для полного цикла скрапинга adilet.zan.kz.

Использование: python -m scripts.scrape

Загружает документы из seed-списка, парсит HTML, разбивает на нормы
и сохраняет результаты в SQLite.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Добавить корень backend в sys.path для импортов app.*
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import settings
from app.database import get_db, init_db
from app.scraper.fetcher import AdiletFetcher
from app.scraper.parser import parse_document, parse_info, parse_links
from app.scraper.seed_docs import get_all_docs
from app.scraper.structural import split_into_norms

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("scrape")


async def _save_document(db, doc_data, info: dict, domain: str) -> None:
    """Сохранить документ в БД."""
    await db.execute(
        """INSERT OR REPLACE INTO documents
           (id, title, doc_type, date_adopted, date_amended,
            status, domain, adopting_body, legal_force, body)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            doc_data.id,
            doc_data.title,
            doc_data.doc_type,
            info.get("date_adopted", doc_data.date_adopted),
            info.get("date_amended", doc_data.date_amended),
            doc_data.status,
            info.get("domain", domain),
            info.get("adopting_body"),
            info.get("legal_force"),
            doc_data.body,
        ),
    )


async def _save_norms(db, norms) -> int:
    """Сохранить нормы в БД. Возвращает количество сохранённых."""
    count = 0
    for norm in norms:
        await db.execute(
            """INSERT OR REPLACE INTO norms
               (id, doc_id, article, paragraph, text)
               VALUES (?, ?, ?, ?, ?)""",
            (norm.id, norm.doc_id, norm.article, norm.paragraph, norm.text),
        )
        count += 1
    return count


async def _save_cross_refs(db, refs) -> int:
    """Сохранить перекрёстные ссылки в БД. Возвращает количество сохранённых."""
    count = 0
    for ref in refs:
        await db.execute(
            """INSERT INTO cross_refs (from_doc, to_doc, context_text)
               VALUES (?, ?, ?)""",
            (ref.from_doc, ref.to_doc, ref.context_text),
        )
        count += 1
    return count


async def main() -> None:
    """Главная функция скрапинга: загрузка, парсинг, сохранение."""
    logger.info("=== Запуск скрапинга adilet.zan.kz ===")

    # Инициализация БД
    await init_db()

    docs = get_all_docs()
    logger.info("Документов в seed-списке: %d", len(docs))

    fetcher = AdiletFetcher()
    total_norms = 0
    total_refs = 0
    errors = 0

    try:
        async with get_db() as db:
            for i, seed in enumerate(docs, 1):
                doc_id = seed["doc_id"]
                domain = seed["domain"]
                logger.info(
                    "[%d/%d] Обработка: %s (%s)",
                    i,
                    len(docs),
                    seed["title"][:50],
                    doc_id,
                )

                try:
                    # Загрузить страницы
                    html = await fetcher.fetch_document(doc_id)
                    info_html = await fetcher.fetch_info(doc_id)
                    links_html = await fetcher.fetch_links(doc_id)

                    # Парсинг
                    doc_data = parse_document(html, doc_id)
                    info = parse_info(info_html)
                    refs = parse_links(links_html, doc_id)

                    # Разбиение на нормы
                    norms = split_into_norms(doc_id, doc_data.body or "")

                    # Сохранение
                    await _save_document(db, doc_data, info, domain)
                    norm_count = await _save_norms(db, norms)
                    ref_count = await _save_cross_refs(db, refs)
                    await db.commit()

                    total_norms += norm_count
                    total_refs += ref_count
                    logger.info(
                        "  -> %d норм, %d ссылок сохранено",
                        norm_count,
                        ref_count,
                    )

                except Exception:
                    errors += 1
                    logger.exception("Ошибка обработки %s", doc_id)
                    continue

        logger.info("=== Скрапинг завершён ===")
        logger.info(
            "Документов: %d, Норм: %d, Ссылок: %d, Ошибок: %d",
            len(docs) - errors,
            total_norms,
            total_refs,
            errors,
        )

    finally:
        await fetcher.close()


if __name__ == "__main__":
    asyncio.run(main())
