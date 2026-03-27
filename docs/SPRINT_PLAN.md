# Спринт-план: 10 дней (27 марта — 5 апреля 2026)

## Фаза 1: Фундамент (Дни 1-3, 27-29 марта)

**Цель**: MVP — парсер + эмбеддинги + базовый граф. Сдача этапа #1.

### День 1 (27 марта) — Инициализация + Парсер
- [x] Инициализация репозитория, структура проекта
- [x] Документация (README, CLAUDE.md, docs/)
- [ ] `backend/app/config.py` — настройки через pydantic-settings
- [ ] `backend/app/database.py` — подключение SQLite + ChromaDB
- [ ] `backend/app/models/document.py` — модели Document, Norm, CrossRef
- [ ] `backend/app/models/finding.py` — модель Finding
- [ ] `backend/app/scraper/seed_docs.py` — список ~50 DOC_ID для демо
- [ ] `backend/app/scraper/fetcher.py` — async HTTP-клиент (aiohttp, rate limit)
- [ ] `backend/app/scraper/parser.py` — извлечение текста, метаданных, ссылок
- [ ] `backend/app/scraper/structural.py` — разбиение на статьи/пункты
- [ ] `backend/scripts/scrape.py` — CLI для запуска парсинга
- [ ] **Запустить парсинг на ночь** (50+ документов)
- [ ] Первый push на GitHub

### День 2 (28 марта) — База данных + Эмбеддинги
- [ ] Создание таблиц SQLite (documents, norms, cross_refs, findings)
- [ ] Загрузка распарсенных данных в SQLite
- [ ] `backend/app/pipeline/embedder.py` — эмбеддинги через Ollama nomic-embed-text
- [ ] Индексация всех норм в ChromaDB
- [ ] `backend/app/main.py` — FastAPI skeleton
- [ ] `backend/app/api/stats.py` — `/api/stats`, `/api/health`
- [ ] `backend/app/api/documents.py` — `/api/documents`
- [ ] Frontend: `npx create-next-app`, shadcn/ui init
- [ ] Frontend: layout (Sidebar, Header), Dashboard page с placeholder

### День 3 (29 марта) — Кластеризация + Граф + MVP Delivery
- [ ] `backend/app/pipeline/clusterer.py` — UMAP + HDBSCAN
- [ ] `backend/app/pipeline/graph_builder.py` — NetworkX из cross_refs
- [ ] `backend/app/api/graph.py` — `/api/graph` endpoint
- [ ] Frontend: `ForceGraph3D.tsx` — 3D-граф с реальными данными
- [ ] Frontend: подключить Dashboard к `/api/stats`
- [ ] Docker: `backend/Dockerfile`
- [ ] **Сдача этапа #1**: GitHub + архитектура + работающий MVP

---

## Фаза 2: Ядро анализа (Дни 4-7, 30 марта — 2 апреля)

**Цель**: Полный pipeline анализа + интерактивный frontend. Сдача этапа #2.

### День 4 (30 марта) — Дублирование + Противоречия
- [ ] `backend/app/llm/client.py` — async Ollama клиент
- [ ] `backend/app/llm/prompts.py` — промпты (противоречие, дублирование, устаревшие)
- [ ] `backend/app/pipeline/dedup.py` — pairwise similarity > 0.85, LLM подтверждение
- [ ] `backend/app/pipeline/contradiction.py` — LLM-as-Judge, structured JSON output
- [ ] Запуск дублирования на всех кластерах
- [ ] `backend/app/api/findings.py` — `/api/findings`

### День 5 (31 марта) — Устаревшие + Поиск + Сравнение
- [ ] `backend/app/pipeline/outdated.py` — status + date + LLM check
- [ ] Запуск полного анализа (dedup + contradiction + outdated)
- [ ] `backend/app/api/search.py` — `/api/search` (семантический)
- [ ] `backend/app/api/compare.py` — `/api/compare/{a}/{b}`
- [ ] Frontend: `/findings` — список обнаружений с фильтрами
- [ ] Frontend: `/findings/[id]` — NormComparison + AiExplanation

### День 6 (1 апреля) — Frontend: Dashboard + Graph + Polish
- [ ] Dashboard: подключить recharts (donut, bar, timeline)
- [ ] Graph: цвета по типу, фильтры, клик по узлу → sidebar info
- [ ] Graph: анимированные красные частицы на рёбрах-противоречиях
- [ ] FindingCard: badges (тип, серьёзность, уверенность)
- [ ] NormComparison: подсветка различий (word-level diff)
- [ ] AiExplanation: карточка с объяснением + disclaimer

### День 7 (2 апреля) — Анализ в реалтайме + 2-й кластер
- [ ] `backend/app/api/analyze.py` — `/api/analyze` (SSE)
- [ ] Frontend: `/analyze` — загрузка текста + прогресс-бар + findings
- [ ] (Опционально) Добавить 2-й кластер: Земельный кодекс + связанные
- [ ] `backend/app/api/clusters.py` — `/api/clusters`
- [ ] **Сдача этапа #2**: GitHub + демо-видео + README

---

## Фаза 3: Финал (Дни 8-10, 3-5 апреля)

**Цель**: Полировка, демо-видео, презентация, финальная сдача.

### День 8 (3 апреля) — Техническая экспертиза + Bug fix
- [ ] Исправление багов, найденных при тестировании
- [ ] Loading states, error states, empty states на всех страницах
- [ ] Frontend: `/about` — методология (для критерия Explainability)
- [ ] Frontend: `/documents` — браузер документов с деревом статей
- [ ] Docker: `frontend/Dockerfile`, проверка `docker compose up`
- [ ] Предгенерация демо-данных (`demo/seed_data.json`)

### День 9 (4 апреля) — Документация + Демо-видео
- [ ] Обновить README: скриншоты, актуальные данные
- [ ] Записать демо-видео (3-5 минут):
  1. Dashboard с метриками
  2. 3D-граф (вращение, клик по узлу)
  3. Обнаружение противоречия (сравнение + объяснение)
  4. Загрузка нового текста → анализ в реалтайме
- [ ] Создать презентацию (13 слайдов по docs/PRESENTATION.md)
- [ ] UI polish: анимации, transitions, responsive

### День 10 (5 апреля) — Финальная сдача (дедлайн 23:59)
- [ ] Финальное тестирование Docker-деплоя
- [ ] Редактирование демо-видео
- [ ] Финализация презентации
- [ ] Push всего на GitHub
- [ ] **СДАЧА** до 23:59

---

## Критический путь

```
Парсинг (День 1) → Эмбеддинги (День 2) → Кластеризация (День 3)
                                               │
                              Анализ (Дни 4-5) → Frontend (Дни 6-7) → Polish (Дни 8-10)
```

**Блокер #1**: Парсер ДОЛЖЕН работать к концу Дня 1. Всё остальное зависит от данных.

**Блокер #2**: Эмбеддинги ДОЛЖНЫ быть готовы к Дню 3. Без них нет кластеризации и анализа.

## Fallback-стратегия

| Риск | Fallback |
|------|----------|
| adilet.zan.kz недоступен | Предзагруженный `demo/seed_data.json` |
| LLM даёт плохие результаты | Только embedding-based дублирование (без LLM) |
| Не хватает времени на frontend | Dashboard + Graph = достаточно для демо |
| Docker не работает у жюри | Демо-видео как backup |
