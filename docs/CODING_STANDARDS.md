# Стандарты кодирования

## Python (Backend)

### Форматирование
- **Инструмент**: `ruff format` (совместим с black)
- Максимальная длина строки: **100 символов**
- Отступы: **4 пробела**
- Кавычки: **двойные** (`"string"`)
- Trailing commas: **да** (в многострочных конструкциях)

### Линтинг
- **Инструмент**: `ruff check`
- Правила: `E`, `F`, `W`, `I` (isort), `UP` (pyupgrade), `B` (bugbear)
- Игнорировать: `E501` (длина строки — контролируется formatter)

### Типизация
- Type hints обязательны для:
  - Аргументов функций
  - Возвращаемых значений
  - Переменных класса
- Использовать встроенные типы Python 3.12: `list[str]`, `dict[str, int]`, `str | None`
- НЕ использовать `typing.List`, `typing.Dict`, `typing.Optional`

### Именование
```python
# Модули и файлы
graph_builder.py          # snake_case

# Классы
class DocumentParser:     # PascalCase

# Функции и методы
async def fetch_document(): # snake_case, async где возможно

# Переменные
norm_text: str            # snake_case
SIMILARITY_THRESHOLD = 0.85  # UPPER_SNAKE для констант

# Приватные
_parse_article()          # одно подчёркивание
```

### Структура файла
```python
"""Модуль для [описание]."""

# stdlib imports
import asyncio
import logging
from pathlib import Path

# third-party imports
import httpx
from pydantic import BaseModel

# local imports
from app.config import settings
from app.models.document import Document

logger = logging.getLogger(__name__)


# Constants
MAX_RETRIES = 3


# Models / Data classes
class ParseResult(BaseModel):
    """Результат парсинга документа."""
    title: str
    articles: list[Article]


# Functions
async def parse_document(doc_id: str) -> ParseResult:
    """Распарсить документ с adilet.zan.kz."""
    ...
```

### Async
```python
# ДА — async для I/O
async def fetch_page(url: str) -> str:
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        return response.text

# НЕТ — sync для CPU-bound
def compute_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    return cosine_similarity(vec_a, vec_b)
```

### Логирование
```python
import logging

logger = logging.getLogger(__name__)

# ДА
logger.info("Parsed %d norms from %s", count, doc_id)
logger.error("Failed to fetch %s: %s", url, exc)

# НЕТ
print(f"Parsed {count} norms")
```

### Pydantic-модели
```python
from pydantic import BaseModel, Field


class NormResponse(BaseModel):
    """Норма (пункт статьи) для API-ответа."""

    id: str
    doc_id: str
    article: int
    paragraph: int
    text: str
    cluster_id: int | None = None
    cluster_topic: str | None = None
    findings_count: int = 0


class FindingCreate(BaseModel):
    """Создание нового обнаружения."""

    type: str = Field(pattern=r"^(contradiction|duplication|outdated)$")
    severity: str = Field(pattern=r"^(high|medium|low)$")
    confidence: float = Field(ge=0.0, le=1.0)
    norm_a_id: str
    norm_b_id: str | None = None
    explanation: str
```

### FastAPI endpoints
```python
from fastapi import APIRouter, Query, HTTPException

router = APIRouter(prefix="/api/findings", tags=["findings"])


@router.get("")
async def list_findings(
    type: str | None = Query(None, pattern=r"^(contradiction|duplication|outdated)$"),
    severity: str | None = Query(None, pattern=r"^(high|medium|low)$"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
) -> dict:
    """Список обнаруженных проблем с фильтрацией."""
    ...


@router.get("/{finding_id}")
async def get_finding(finding_id: int) -> dict:
    """Детали обнаружения с полным объяснением."""
    finding = await db.get_finding(finding_id)
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")
    return finding
```

### Обработка ошибок
```python
# На границах системы (API, внешние вызовы)
@router.get("/{doc_id}")
async def get_document(doc_id: str):
    try:
        doc = await fetch_document(doc_id)
    except httpx.HTTPError as e:
        logger.error("Failed to fetch %s: %s", doc_id, e)
        raise HTTPException(status_code=502, detail="Source unavailable")
    return doc

# Внутри pipeline — НЕ ловить, пусть всплывает
async def embed_norms(norms: list[Norm]) -> list[list[float]]:
    vectors = await ollama_embed(texts=[n.text for n in norms])
    return vectors  # если упадёт — ошибка видна на уровне API
```

---

## TypeScript (Frontend)

### Форматирование
- **Инструмент**: Prettier
- Максимальная длина строки: **100 символов**
- Отступы: **2 пробела**
- Кавычки: **двойные** в JSX, **одинарные** в TS
- Точки с запятой: **нет** (Prettier default)
- Trailing commas: **all**

### Именование
```typescript
// Файлы компонентов
ForceGraph3D.tsx          // PascalCase
NormComparison.tsx

// Файлы утилит
api.ts                    // camelCase
types.ts

// Компоненты
function DashboardPage()  // PascalCase

// Хуки
function useGraph()       // camelCase с use-

// Интерфейсы
interface FindingResponse  // PascalCase, НЕ IFindingResponse

// Переменные, функции
const totalFindings       // camelCase
function fetchStats()     // camelCase

// Константы
const API_BASE_URL        // UPPER_SNAKE
```

### Компоненты
```tsx
// Серверный компонент (по умолчанию в App Router)
// НЕ добавлять "use client" если не нужно

export default async function FindingsPage() {
  const findings = await fetchFindings()
  return <FindingsList findings={findings} />
}
```

```tsx
// Клиентский компонент (интерактивность, состояние, эффекты)
'use client'

import { useState } from 'react'

interface Props {
  findingId: number
}

export function AiExplanation({ findingId }: Props) {
  const [expanded, setExpanded] = useState(false)
  // ...
}
```

### Типы
```typescript
// lib/types.ts

export interface Document {
  id: string
  title: string
  docType: 'code' | 'law' | 'decree' | 'resolution'
  dateAdopted: string
  dateAmended: string
  status: 'active' | 'expired'
  domain: string
  normsCount: number
  findingsCount: number
}

export interface Finding {
  id: number
  type: 'contradiction' | 'duplication' | 'outdated'
  severity: 'high' | 'medium' | 'low'
  confidence: number
  normA: NormBrief
  normB: NormBrief | null
  explanation: string
  clusterTopic: string
}

// НЕ использовать any
// ДА: unknown + type guard
// ДА: generic types
```

### API-клиент
```typescript
// lib/api.ts
const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...init?.headers,
    },
  })
  if (!res.ok) {
    throw new Error(`API error: ${res.status}`)
  }
  return res.json()
}

// Типизированные функции
export const getStats = () => apiFetch<StatsResponse>('/api/stats')
export const getFindings = (params?: FindingsParams) =>
  apiFetch<PaginatedResponse<Finding>>(`/api/findings?${new URLSearchParams(params)}`)
```

### Dynamic imports (для Three.js)
```tsx
// graph/page.tsx
'use client'

import dynamic from 'next/dynamic'

const ForceGraph3D = dynamic(
  () => import('@/components/graph/ForceGraph3D'),
  { ssr: false, loading: () => <GraphSkeleton /> },
)
```

---

## SQL (SQLite)

### Таблицы
```sql
-- snake_case для таблиц и колонок
CREATE TABLE documents (
    id TEXT PRIMARY KEY,            -- DOC_ID с adilet.zan.kz
    title TEXT NOT NULL,
    doc_type TEXT NOT NULL,          -- code, law, decree, resolution, order
    date_adopted TEXT,               -- ISO 8601 (YYYY-MM-DD)
    date_amended TEXT,
    status TEXT DEFAULT 'active',    -- active, expired
    domain TEXT,
    adopting_body TEXT,
    legal_force TEXT,
    body TEXT,                       -- полный текст
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE norms (
    id TEXT PRIMARY KEY,             -- {doc_id}_art{N}_p{M}
    doc_id TEXT NOT NULL REFERENCES documents(id),
    article INTEGER NOT NULL,
    paragraph INTEGER,
    text TEXT NOT NULL,
    cluster_id INTEGER,
    cluster_topic TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE cross_refs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    from_doc TEXT NOT NULL REFERENCES documents(id),
    to_doc TEXT NOT NULL REFERENCES documents(id),
    context_text TEXT
);

CREATE TABLE findings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type TEXT NOT NULL,               -- contradiction, duplication, outdated
    severity TEXT NOT NULL,            -- high, medium, low
    confidence REAL NOT NULL,
    norm_a_id TEXT NOT NULL REFERENCES norms(id),
    norm_b_id TEXT REFERENCES norms(id),
    explanation TEXT NOT NULL,
    cluster_id INTEGER,
    recommendation TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

-- Индексы
CREATE INDEX idx_norms_doc ON norms(doc_id);
CREATE INDEX idx_norms_cluster ON norms(cluster_id);
CREATE INDEX idx_findings_type ON findings(type);
CREATE INDEX idx_findings_severity ON findings(severity);
CREATE INDEX idx_cross_refs_from ON cross_refs(from_doc);
CREATE INDEX idx_cross_refs_to ON cross_refs(to_doc);
```

---

## Git Commits

### Формат (Conventional Commits)
```
<type>: <description>

[optional body]
```

### Типы
| Тип | Когда |
|-----|-------|
| `feat` | Новая функциональность |
| `fix` | Исправление бага |
| `docs` | Только документация |
| `refactor` | Рефакторинг без изменения поведения |
| `style` | Форматирование, без изменения логики |
| `test` | Добавление/исправление тестов |
| `chore` | Сборка, зависимости, конфиг |

### Примеры
```
feat: add contradiction detection pipeline
feat: implement 3D graph visualization
fix: handle empty articles in structural parser
fix: correct cosine similarity threshold
docs: add API reference documentation
refactor: extract Ollama client to separate module
chore: add docker-compose with healthchecks
```

### Правила
- Описание на **английском**, в imperative mood
- Первая буква строчная
- Без точки в конце
- Максимум 72 символа в заголовке
