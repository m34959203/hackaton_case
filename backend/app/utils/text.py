"""Утилиты для обработки текста."""

import re
import unicodedata


def normalize_text(text: str) -> str:
    """Нормализация текста: пробелы, кавычки, юникод.

    Удаляет лишние пробелы, нормализует различные типы кавычек
    к единому формату, приводит юникод к NFC-форме.
    """
    # Нормализация юникода
    text = unicodedata.normalize("NFC", text)

    # Замена различных типов кавычек на стандартные
    text = re.sub(r"[«»„""\u201c\u201d\u201e]", '"', text)
    text = re.sub(r"[''`\u2018\u2019]", "'", text)

    # Замена неразрывных пробелов и табуляций на обычные пробелы
    text = re.sub(r"[\xa0\t\u200b\u200c\u200d\ufeff]", " ", text)

    # Удаление множественных пробелов
    text = re.sub(r" {2,}", " ", text)

    # Удаление пробелов в начале/конце строк
    text = re.sub(r"^ +| +$", "", text, flags=re.MULTILINE)

    # Удаление множественных пустых строк (оставляем максимум одну)
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def truncate(text: str, max_len: int = 500) -> str:
    """Обрезать текст до указанной длины с многоточием.

    Обрезает по границе слова, чтобы не разрывать слова.
    """
    if len(text) <= max_len:
        return text

    # Обрезаем по границе слова
    truncated = text[:max_len]
    last_space = truncated.rfind(" ")
    if last_space > max_len * 0.7:
        truncated = truncated[:last_space]

    return truncated.rstrip() + "..."
