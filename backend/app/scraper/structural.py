"""Разбиение текста НПА на отдельные нормы (статьи и пункты).

Использует regex-автомат для выделения структурных элементов:
статей (Статья N.) и пунктов внутри них (нумерованных абзацев).
"""

import logging
import re

from app.models.document import NormCreate

logger = logging.getLogger(__name__)

# Паттерн заголовка статьи: "Статья 15.", "Статья 15-1.", "Статья 15. Название"
_ARTICLE_PATTERN = re.compile(
    r"^\s*Статья\s+(\d+(?:-\d+)?)\s*\.(.*)$",
    re.MULTILINE,
)

# Паттерн нумерованного пункта: "1.", "1)", "1-1.", "1-1)"
_PARAGRAPH_PATTERN = re.compile(
    r"^\s*(\d+(?:-\d+)?)\s*[.)]\s+",
    re.MULTILINE,
)

# Паттерн подпункта: "1)", "а)", "1-1)"
_SUBPARAGRAPH_PATTERN = re.compile(
    r"^\s*(?:\d+\)|[а-яё]\))\s+",
    re.MULTILINE,
)

# Минимальная длина текста нормы (символов) — фильтр мусора
_MIN_NORM_LENGTH = 20

# Максимальная длина текста нормы (символов) — разбить слишком длинные
_MAX_NORM_LENGTH = 3000


def _clean_norm_text(text: str) -> str:
    """Очистить текст нормы от сносок и лишних пробелов."""
    # Убрать сноски вида [1], [*]
    text = re.sub(r"\[\d+\]", "", text)
    text = re.sub(r"\[\*\]", "", text)
    # Убрать ссылки на редакции: "(в ред. от ...)"
    text = re.sub(r"\(в\s+ред(?:акции)?\.?\s+[^)]*\)", "", text)
    # Нормализовать пробелы
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _split_article_into_paragraphs(
    doc_id: str, article_num: str, article_text: str
) -> list[NormCreate]:
    """Разбить текст статьи на отдельные пункты."""
    norms: list[NormCreate] = []
    art_int = int(article_num.split("-")[0])

    # Найти все позиции нумерованных пунктов
    matches = list(_PARAGRAPH_PATTERN.finditer(article_text))

    if not matches:
        # Статья без нумерованных пунктов — целиком как одна норма
        cleaned = _clean_norm_text(article_text)
        if len(cleaned) >= _MIN_NORM_LENGTH:
            norms.append(
                NormCreate(
                    id=f"{doc_id}_art{article_num}_p0",
                    doc_id=doc_id,
                    article=art_int,
                    paragraph=0,
                    text=cleaned[:_MAX_NORM_LENGTH],
                )
            )
        return norms

    # Текст до первого пункта (преамбула статьи)
    preamble = article_text[: matches[0].start()].strip()
    if preamble and len(_clean_norm_text(preamble)) >= _MIN_NORM_LENGTH:
        norms.append(
            NormCreate(
                id=f"{doc_id}_art{article_num}_p0",
                doc_id=doc_id,
                article=art_int,
                paragraph=0,
                text=_clean_norm_text(preamble)[:_MAX_NORM_LENGTH],
            )
        )

    # Каждый нумерованный пункт
    for i, match in enumerate(matches):
        para_num_str = match.group(1)
        para_num = int(para_num_str.split("-")[0])
        start = match.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(article_text)
        para_text = article_text[start:end]
        cleaned = _clean_norm_text(para_text)

        if len(cleaned) < _MIN_NORM_LENGTH:
            continue

        # Если текст слишком длинный, ищем подпункты
        if len(cleaned) > _MAX_NORM_LENGTH:
            sub_matches = list(_SUBPARAGRAPH_PATTERN.finditer(para_text))
            if len(sub_matches) > 1:
                # Разбить по подпунктам — каждый как отдельная норма
                for j, sub in enumerate(sub_matches):
                    sub_start = sub.start()
                    sub_end = (
                        sub_matches[j + 1].start()
                        if j + 1 < len(sub_matches)
                        else len(para_text)
                    )
                    sub_text = _clean_norm_text(para_text[sub_start:sub_end])
                    if len(sub_text) >= _MIN_NORM_LENGTH:
                        norms.append(
                            NormCreate(
                                id=f"{doc_id}_art{article_num}_p{para_num_str}_{j}",
                                doc_id=doc_id,
                                article=art_int,
                                paragraph=para_num,
                                text=sub_text[:_MAX_NORM_LENGTH],
                            )
                        )
                continue

        norms.append(
            NormCreate(
                id=f"{doc_id}_art{article_num}_p{para_num_str}",
                doc_id=doc_id,
                article=art_int,
                paragraph=para_num,
                text=cleaned[:_MAX_NORM_LENGTH],
            )
        )

    return norms


def split_into_norms(doc_id: str, body: str) -> list[NormCreate]:
    """Разбить полный текст документа на нормы (пункты статей).

    Алгоритм: regex-автомат находит границы статей (Статья N.),
    затем каждая статья разбивается на нумерованные пункты.
    Генерирует ID вида {doc_id}_art{N}_p{M}.
    """
    if not body or len(body.strip()) < _MIN_NORM_LENGTH:
        logger.warning("Пустой или слишком короткий текст документа: %s", doc_id)
        return []

    norms: list[NormCreate] = []

    # Найти все статьи
    article_matches = list(_ARTICLE_PATTERN.finditer(body))

    if not article_matches:
        # Документ без статей — разбить по абзацам
        logger.warning("Статьи не найдены в документе %s, разбиваю по абзацам", doc_id)
        paragraphs = [p.strip() for p in body.split("\n\n") if p.strip()]
        for i, para in enumerate(paragraphs):
            cleaned = _clean_norm_text(para)
            if len(cleaned) >= _MIN_NORM_LENGTH:
                norms.append(
                    NormCreate(
                        id=f"{doc_id}_p{i}",
                        doc_id=doc_id,
                        article=0,
                        paragraph=i,
                        text=cleaned[:_MAX_NORM_LENGTH],
                    )
                )
        logger.info("Документ %s: %d норм (по абзацам)", doc_id, len(norms))
        return norms

    # Обработать каждую статью
    for i, match in enumerate(article_matches):
        article_num = match.group(1)
        start = match.end()
        end = (
            article_matches[i + 1].start()
            if i + 1 < len(article_matches)
            else len(body)
        )
        article_text = body[start:end]
        article_norms = _split_article_into_paragraphs(doc_id, article_num, article_text)
        norms.extend(article_norms)

    logger.info(
        "Документ %s: %d статей, %d норм",
        doc_id,
        len(article_matches),
        len(norms),
    )
    return norms
