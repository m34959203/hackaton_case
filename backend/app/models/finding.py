"""Pydantic-модели для обнаружений (findings)."""

from pydantic import BaseModel, Field

from app.models.document import NormBrief


# --- Модель строки БД ---


class Finding(BaseModel):
    """Обнаружение — проблема в законодательстве (строка из таблицы findings)."""

    id: int
    type: str
    severity: str
    confidence: float
    norm_a_id: str
    norm_b_id: str | None = None
    explanation: str
    cluster_id: int | None = None
    recommendation: str | None = None
    created_at: str | None = None


# --- Модели для API-ответов ---


class FindingResponse(BaseModel):
    """Обнаружение для списка в API-ответе."""

    id: int
    type: str = Field(description="Тип: contradiction, duplication, outdated")
    severity: str = Field(description="Серьёзность: high, medium, low")
    confidence: float = Field(ge=0.0, le=1.0)
    norm_a: NormBrief
    norm_b: NormBrief | None = None
    explanation: str
    cluster_topic: str | None = None
    created_at: str | None = None


class FindingDetail(BaseModel):
    """Детальное обнаружение с полной информацией для страницы деталей."""

    id: int
    type: str
    severity: str
    confidence: float
    norm_a: NormBrief
    norm_b: NormBrief | None = None
    explanation: str
    recommendation: str | None = None
    cluster_id: int | None = None
    cluster_topic: str | None = None
    created_at: str | None = None


# --- Модель для входных данных пайплайна ---


class FindingCreate(BaseModel):
    """Создание нового обнаружения из аналитического пайплайна."""

    type: str = Field(pattern=r"^(contradiction|duplication|outdated)$")
    severity: str = Field(pattern=r"^(high|medium|low)$")
    confidence: float = Field(ge=0.0, le=1.0)
    norm_a_id: str
    norm_b_id: str | None = None
    explanation: str
    cluster_id: int | None = None
    recommendation: str | None = None
