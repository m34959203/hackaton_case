"""Pydantic-модели для документов и норм."""

from pydantic import BaseModel, Field


# --- Модели строк БД ---


class Document(BaseModel):
    """Документ НПА (строка из таблицы documents)."""

    id: str
    title: str
    doc_type: str
    date_adopted: str | None = None
    date_amended: str | None = None
    status: str = "active"
    domain: str | None = None
    adopting_body: str | None = None
    legal_force: str | None = None
    body: str | None = None
    created_at: str | None = None


class NormCreate(BaseModel):
    """Входные данные от парсера для создания нормы."""

    id: str
    doc_id: str
    article: int
    paragraph: int | None = None
    text: str


class CrossRefCreate(BaseModel):
    """Входные данные от парсера для перекрёстной ссылки."""

    from_doc: str
    to_doc: str
    context_text: str | None = None


class Norm(BaseModel):
    """Норма — пункт статьи (строка из таблицы norms)."""

    id: str
    doc_id: str
    article: int
    paragraph: int | None = None
    text: str
    cluster_id: int | None = None
    cluster_topic: str | None = None
    created_at: str | None = None


class CrossRef(BaseModel):
    """Перекрёстная ссылка между документами (строка из таблицы cross_refs)."""

    id: int
    from_doc: str
    to_doc: str
    context_text: str | None = None


# --- Модели для API-ответов ---


class NormBrief(BaseModel):
    """Краткая информация о норме для вложенных ответов."""

    id: str
    doc_id: str
    article: int
    paragraph: int | None = None
    text: str = Field(description="Текст нормы")


class NormResponse(BaseModel):
    """Норма для API-ответа с дополнительными полями."""

    id: str
    doc_id: str
    article: int
    paragraph: int | None = None
    text: str
    cluster_id: int | None = None
    cluster_topic: str | None = None
    findings_count: int = 0


class DocumentResponse(BaseModel):
    """Документ для API-ответа с агрегированными данными."""

    id: str
    title: str
    doc_type: str
    date_adopted: str | None = None
    date_amended: str | None = None
    status: str
    domain: str | None = None
    adopting_body: str | None = None
    legal_force: str | None = None
    norms_count: int = 0
    findings_count: int = 0


# --- Модели для входных данных ---


class DocumentCreate(BaseModel):
    """Входные данные от парсера для создания документа."""

    id: str
    title: str
    doc_type: str = Field(pattern=r"^(code|law|decree|resolution|order)$")
    date_adopted: str | None = None
    date_amended: str | None = None
    status: str = Field(default="active", pattern=r"^(active|expired)$")
    domain: str | None = None
    adopting_body: str | None = None
    legal_force: str | None = None
    body: str | None = None
