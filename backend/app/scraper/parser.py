"""Парсер HTML-страниц adilet.zan.kz в структурированные данные."""

import logging
import re

from bs4 import BeautifulSoup

from app.models.document import CrossRefCreate, DocumentCreate

logger = logging.getLogger(__name__)

# Маппинг CSS-классов статуса на внутренние значения
_STATUS_MAP = {
    "status_new": "active",
    "status_upd": "active",
    "status_yts": "expired",
}

# Маппинг ключевых слов заголовка на тип документа
_DOCTYPE_KEYWORDS = {
    "кодекс": "code",
    "закон": "law",
    "указ": "decree",
    "постановление": "resolution",
    "приказ": "order",
}


def _detect_doc_type(title: str) -> str:
    """Определить тип документа по заголовку."""
    title_lower = title.lower()
    for keyword, dtype in _DOCTYPE_KEYWORDS.items():
        if keyword in title_lower:
            return dtype
    return "law"


def _extract_status(soup: BeautifulSoup) -> str:
    """Извлечь статус документа из span.status."""
    status_span = soup.select_one("span.status")
    if not status_span:
        return "active"
    for css_class, status_val in _STATUS_MAP.items():
        if css_class in status_span.get("class", []):
            return status_val
    return "active"


def _clean_text(text: str) -> str:
    """Очистить текст от лишних пробелов и спецсимволов."""
    text = re.sub(r"\xa0", " ", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def parse_document(html: str, doc_id: str) -> DocumentCreate:
    """Извлечь основные данные документа из HTML.

    Парсит заголовок (h1 в div.container_alpha.slogan), статус (span.status)
    и текст (div.container_gamma.text > article).
    """
    soup = BeautifulSoup(html, "lxml")

    # Заголовок
    title_el = soup.select_one("div.container_alpha.slogan h1")
    title = _clean_text(title_el.get_text()) if title_el else f"Документ {doc_id}"

    # Статус
    status = _extract_status(soup)

    # Текст документа
    body_el = soup.select_one("div.container_gamma.text > article")
    body = _clean_text(body_el.get_text(separator="\n")) if body_el else ""

    # Тип документа
    doc_type = _detect_doc_type(title)

    logger.info(
        "Распарсен документ %s: %s [%s, %s]",
        doc_id,
        title[:60],
        doc_type,
        status,
    )

    return DocumentCreate(
        id=doc_id,
        title=title,
        doc_type=doc_type,
        status=status,
        body=body,
    )


def parse_info(html: str) -> dict:
    """Извлечь метаданные из таблицы параметров на странице /info.

    Возвращает словарь с ключами: date_adopted, date_amended, adopting_body,
    legal_force, domain.
    """
    soup = BeautifulSoup(html, "lxml")
    result: dict = {}

    params_table = soup.select_one("table.params")
    if not params_table:
        logger.warning("Таблица параметров не найдена")
        return result

    # Маппинг заголовков таблицы на поля модели
    field_map = {
        "дата принятия": "date_adopted",
        "дата ввода в действие": "date_adopted",
        "последнее изменение": "date_amended",
        "дата последнего изменения": "date_amended",
        "принявший орган": "adopting_body",
        "вид документа": "legal_force",
        "сфера правоотношений": "domain",
    }

    rows = params_table.select("tr")
    for row in rows:
        cells = row.select("td")
        if len(cells) < 2:
            continue
        key = _clean_text(cells[0].get_text()).lower().rstrip(":")
        value = _clean_text(cells[1].get_text())
        if not value:
            continue
        for pattern, field in field_map.items():
            if pattern in key:
                result[field] = value
                break

    logger.debug("Метаданные: %s", result)
    return result


def parse_links(html: str, doc_id: str) -> list[CrossRefCreate]:
    """Извлечь перекрёстные ссылки из страницы /links.

    Парсит блоки div#from (документ ссылается на) и div#to (ссылаются на документ).
    """
    soup = BeautifulSoup(html, "lxml")
    refs: list[CrossRefCreate] = []

    doc_id_pattern = re.compile(r"/rus/docs/([A-Za-z0-9]+)")

    # Документы, на которые ссылается данный
    from_block = soup.select_one("div#from")
    if from_block:
        for link in from_block.select("a[href]"):
            href = link.get("href", "")
            match = doc_id_pattern.search(str(href))
            if match:
                target_id = match.group(1)
                context = _clean_text(link.get_text())[:200]
                refs.append(
                    CrossRefCreate(
                        from_doc=doc_id,
                        to_doc=target_id,
                        context_text=context if context else None,
                    )
                )

    # Документы, которые ссылаются на данный
    to_block = soup.select_one("div#to")
    if to_block:
        for link in to_block.select("a[href]"):
            href = link.get("href", "")
            match = doc_id_pattern.search(str(href))
            if match:
                source_id = match.group(1)
                context = _clean_text(link.get_text())[:200]
                refs.append(
                    CrossRefCreate(
                        from_doc=source_id,
                        to_doc=doc_id,
                        context_text=context if context else None,
                    )
                )

    logger.info("Найдено %d перекрёстных ссылок для %s", len(refs), doc_id)
    return refs
