# API Reference

Base URL: `http://localhost:8000`

Swagger UI: `http://localhost:8000/docs`

---

## Health Check

### `GET /api/health`

Проверка состояния всех компонентов.

**Response** `200 OK`:
```json
{
  "status": "healthy",
  "ollama": true,
  "chroma": true,
  "database": true,
  "documents_count": 52,
  "norms_count": 4830
}
```

---

## Statistics

### `GET /api/stats`

Статистика дашборда.

**Response** `200 OK`:
```json
{
  "total_documents": 52,
  "total_norms": 4830,
  "total_findings": 147,
  "contradictions": 23,
  "duplications": 89,
  "outdated": 35,
  "by_domain": {
    "Труд": {"docs": 15, "findings": 52},
    "Гражданское право": {"docs": 12, "findings": 38},
    "Налоги": {"docs": 8, "findings": 27}
  },
  "by_severity": {
    "high": 12,
    "medium": 67,
    "low": 68
  }
}
```

---

## Documents

### `GET /api/documents`

Список документов.

**Query Parameters**:
| Параметр | Тип | Описание |
|----------|-----|----------|
| `domain` | string | Фильтр по правовой области |
| `status` | string | `active` / `expired` |
| `page` | int | Страница (default: 1) |
| `limit` | int | Элементов на страницу (default: 20, max: 100) |
| `search` | string | Поиск по названию |

**Response** `200 OK`:
```json
{
  "items": [
    {
      "id": "K1500000414",
      "title": "Трудовой кодекс Республики Казахстан",
      "doc_type": "code",
      "date_adopted": "2015-11-23",
      "date_amended": "2026-01-15",
      "status": "active",
      "domain": "Труд",
      "norms_count": 1250,
      "findings_count": 18
    }
  ],
  "total": 52,
  "page": 1,
  "pages": 3
}
```

### `GET /api/documents/{doc_id}`

Детали документа.

**Response** `200 OK`:
```json
{
  "id": "K1500000414",
  "title": "Трудовой кодекс Республики Казахстан",
  "doc_type": "code",
  "date_adopted": "2015-11-23",
  "date_amended": "2026-01-15",
  "status": "active",
  "domain": "Труд",
  "adopting_body": "Парламент Республики Казахстан",
  "legal_force": "Кодекс",
  "norms_count": 1250,
  "findings_count": 18,
  "cross_refs_from": 45,
  "cross_refs_to": 128
}
```

### `GET /api/documents/{doc_id}/norms`

Нормы документа (статьи, пункты).

**Response** `200 OK`:
```json
{
  "items": [
    {
      "id": "K1500000414_art15_p3",
      "article": 15,
      "paragraph": 3,
      "text": "Срок рассмотрения трудовых споров составляет тридцать календарных дней.",
      "cluster_id": 7,
      "cluster_topic": "Сроки рассмотрения",
      "findings_count": 2
    }
  ],
  "total": 1250
}
```

---

## Findings

### `GET /api/findings`

Список обнаруженных проблем.

**Query Parameters**:
| Параметр | Тип | Описание |
|----------|-----|----------|
| `type` | string | `contradiction` / `duplication` / `outdated` |
| `severity` | string | `high` / `medium` / `low` |
| `domain` | string | Правовая область |
| `doc_id` | string | Фильтр по документу |
| `page` | int | Страница |
| `limit` | int | Элементов на страницу |

**Response** `200 OK`:
```json
{
  "items": [
    {
      "id": 42,
      "type": "contradiction",
      "severity": "high",
      "confidence": 0.87,
      "norm_a": {
        "id": "K1500000414_art15_p3",
        "doc_title": "Трудовой кодекс",
        "article": 15,
        "paragraph": 3,
        "text_preview": "Срок рассмотрения составляет 30 дней..."
      },
      "norm_b": {
        "id": "Z2100000003_art22_p1",
        "doc_title": "Закон о занятости",
        "article": 22,
        "paragraph": 1,
        "text_preview": "Рассматривается в течение 15 рабочих дней..."
      },
      "explanation_preview": "Нормы устанавливают разные сроки...",
      "cluster_topic": "Сроки рассмотрения"
    }
  ],
  "total": 147,
  "page": 1,
  "pages": 8
}
```

### `GET /api/findings/{id}`

Детали обнаружения с полным объяснением.

**Response** `200 OK`:
```json
{
  "id": 42,
  "type": "contradiction",
  "severity": "high",
  "confidence": 0.87,
  "norm_a": {
    "id": "K1500000414_art15_p3",
    "doc_id": "K1500000414",
    "doc_title": "Трудовой кодекс Республики Казахстан",
    "article": 15,
    "paragraph": 3,
    "text": "Срок рассмотрения трудовых споров составляет тридцать календарных дней.",
    "date_adopted": "2015-11-23"
  },
  "norm_b": {
    "id": "Z2100000003_art22_p1",
    "doc_id": "Z2100000003",
    "doc_title": "Закон Республики Казахстан «О занятости населения»",
    "article": 22,
    "paragraph": 1,
    "text": "Заявление рассматривается в течение пятнадцати рабочих дней со дня подачи.",
    "date_adopted": "2021-09-01"
  },
  "similarity": 0.73,
  "explanation": "Нормы устанавливают разные сроки для рассмотрения заявлений в сфере трудовых отношений. Статья 15 п.3 Трудового кодекса указывает 30 календарных дней, тогда как статья 22 п.1 Закона о занятости — 15 рабочих дней. Это создаёт правовую неопределённость для заявителей.\n\nС точки зрения lex posterior, Закон о занятости (2021) принят позже Трудового кодекса (2015) и может рассматриваться как специальная норма.",
  "recommendation": "Привести ст.15 Трудового кодекса в соответствие с Законом о занятости или уточнить область применения каждой нормы.",
  "cluster_topic": "Сроки рассмотрения"
}
```

---

## Graph

### `GET /api/graph`

Данные графа связей для визуализации.

**Query Parameters**:
| Параметр | Тип | Описание |
|----------|-----|----------|
| `level` | string | `document` (default) / `article` |
| `domain` | string | Фильтр по области |
| `finding_type` | string | Фильтр по типу обнаружения |

**Response** `200 OK`:
```json
{
  "nodes": [
    {
      "id": "K1500000414",
      "label": "Трудовой кодекс",
      "type": "code",
      "domain": "Труд",
      "size": 45,
      "findings_count": 18,
      "status": "active"
    }
  ],
  "links": [
    {
      "source": "K1500000414",
      "target": "K950001000_",
      "type": "reference",
      "weight": 12
    },
    {
      "source": "K1500000414",
      "target": "Z2100000003",
      "type": "contradiction",
      "finding_id": 42,
      "weight": 3
    }
  ],
  "stats": {
    "nodes": 52,
    "edges": 340,
    "contradictions": 23,
    "duplications": 89
  }
}
```

### `GET /api/graph/subgraph/{doc_id}`

Подграф (ego network) вокруг документа.

**Query Parameters**:
| Параметр | Тип | Описание |
|----------|-----|----------|
| `depth` | int | Глубина обхода (1 или 2) |

---

## Search

### `POST /api/search`

Семантический поиск по нормам.

**Request Body**:
```json
{
  "query": "ответственность работодателя за задержку заработной платы",
  "top_k": 10,
  "domain_filter": "Труд"
}
```

**Response** `200 OK`:
```json
{
  "results": [
    {
      "norm_id": "K1500000414_art134_p1",
      "doc_title": "Трудовой кодекс",
      "article": 134,
      "paragraph": 1,
      "text": "При задержке выплаты заработной платы работодатель обязан...",
      "score": 0.91,
      "domain": "Труд"
    }
  ]
}
```

---

## Compare

### `GET /api/compare/{norm_a_id}/{norm_b_id}`

Сравнение двух норм.

**Response** `200 OK`:
```json
{
  "norm_a": { "...": "..." },
  "norm_b": { "...": "..." },
  "similarity": 0.73,
  "analysis": {
    "relation": "contradiction",
    "confidence": 0.87,
    "explanation": "...",
    "conflicting_fragments": {
      "norm_a": "тридцать календарных дней",
      "norm_b": "пятнадцати рабочих дней"
    }
  }
}
```

### `POST /api/compare`

Сравнение произвольных текстов.

**Request Body**:
```json
{
  "text_a": "Срок рассмотрения составляет 30 дней",
  "text_b": "Рассматривается в течение 15 рабочих дней"
}
```

---

## Analyze

### `POST /api/analyze`

Анализ нового текста в реальном времени (Server-Sent Events).

**Request Body**:
```json
{
  "text": "Статья 15. Срок рассмотрения обращений...",
  "title": "Проект закона об обращениях"
}
```

**Response** `200 OK` (text/event-stream):
```
data: {"step": "parsing", "progress": 0.1, "message": "Разбор текста на нормы..."}

data: {"step": "embedding", "progress": 0.3, "message": "Генерация эмбеддингов..."}

data: {"step": "searching", "progress": 0.5, "message": "Поиск похожих норм в базе..."}

data: {"step": "analyzing", "progress": 0.7, "message": "Анализ на противоречия..."}

data: {"step": "finding", "progress": 0.8, "finding": {"type": "duplication", "...": "..."}}

data: {"step": "complete", "progress": 1.0, "total_findings": 3}
```

---

## Clusters

### `GET /api/clusters`

Тематические кластеры норм.

**Response** `200 OK`:
```json
{
  "clusters": [
    {
      "id": 7,
      "topic": "Сроки рассмотрения обращений",
      "norms_count": 45,
      "findings_count": 8,
      "top_documents": ["Трудовой кодекс", "Закон о занятости"]
    }
  ]
}
```

---

## Error Responses

Все ошибки возвращаются в формате:

```json
{
  "detail": "Document not found",
  "status_code": 404
}
```

| Код | Описание |
|-----|----------|
| 400 | Некорректный запрос |
| 404 | Ресурс не найден |
| 422 | Ошибка валидации |
| 500 | Внутренняя ошибка сервера |
| 503 | Ollama или ChromaDB недоступен |
