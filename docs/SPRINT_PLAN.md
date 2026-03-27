# Спринт-план: 10 дней (27 марта — 5 апреля 2026)

## Фаза 1: Фундамент (Дни 1-3, 27-29 марта)

**Цель**: MVP — парсер + эмбеддинги + базовый граф. Сдача этапа #1.

### День 1 (27 марта) — Инициализация + Парсер + Backend + Frontend ✅ ЗАВЕРШЁН
- [x] Инициализация репозитория, структура проекта
- [x] Документация (README, CLAUDE.md, docs/ — 17 файлов)
- [x] `backend/app/config.py` — настройки через pydantic-settings
- [x] `backend/app/database.py` — подключение SQLite + ChromaDB
- [x] `backend/app/models/document.py` — модели Document, Norm, CrossRef
- [x] `backend/app/models/finding.py` — модель Finding
- [x] `backend/app/scraper/seed_docs.py` — 59 верифицированных DOC_ID
- [x] `backend/app/scraper/fetcher.py` — async HTTP-клиент (aiohttp, rate limit, retry, cache)
- [x] `backend/app/scraper/parser.py` — извлечение текста, метаданных, ссылок
- [x] `backend/app/scraper/structural.py` — разбиение на статьи/пункты (regex state machine)
- [x] `backend/scripts/scrape.py` — CLI для запуска парсинга
- [x] Парсинг 59 документов → **54 526 норм, 870 514 ссылок**
- [x] `backend/app/llm/client.py` — async Ollama клиент (httpx)
- [x] `backend/app/llm/prompts.py` — 5 промптов на русском (contradiction, duplication, outdated, explanation, cluster_topic)
- [x] `backend/app/pipeline/embedder.py` — эмбеддинги Ollama nomic-embed-text → ChromaDB
- [x] `backend/app/pipeline/clusterer.py` — UMAP + HDBSCAN → 672 кластера
- [x] `backend/app/pipeline/dedup.py` — cosine similarity + LLM подтверждение
- [x] `backend/app/pipeline/contradiction.py` — LLM-as-Judge
- [x] `backend/app/pipeline/outdated.py` — статус + даты + LLM
- [x] `backend/app/pipeline/graph_builder.py` — NetworkX → JSON
- [x] `backend/app/main.py` — FastAPI app с lifespan, CORS, all routers
- [x] `backend/app/api/` — все 9 endpoints (documents, findings, graph, search, compare, analyze SSE, stats, health)
- [x] `backend/scripts/quick_analyze.py` — быстрый анализ (embedding-based dedup + LLM contradictions)
- [x] Frontend: Next.js 16 scaffold, shadcn/ui, TanStack React Query
- [x] Frontend: layout (Sidebar, Header), Providers
- [x] Frontend: Dashboard — StatsCards, FindingsByTypeChart, DomainChart, SeverityChart, RecentFindings
- [x] Frontend: 3D-граф — ForceGraph3D (dynamic import), GraphControls, GraphNodeInfo
- [x] Frontend: Findings — FindingsTable, FindingsFilters, NormComparison, AiExplanation
- [x] Frontend: Analyze — AnalysisForm, AnalysisProgress, AnalysisResults (SSE)
- [x] Frontend: Documents — список + детали с деревом норм
- [x] Frontend: About — методология
- [x] Эмбеддинг 54 526 норм → ChromaDB (768 dim, ~8 мин)
- [x] Кластеризация UMAP+HDBSCAN → 672 кластера с LLM-именованием (~39 мин)
- [x] Quick analyze: 200 дублирований + 100 устаревших = **300 findings**
- [x] Граф: 118 639 узлов, 196 453 рёбер → `data/graph.json`
- [x] Docker: `backend/Dockerfile`, `frontend/Dockerfile`, `docker-compose.yml`
- [x] 6 коммитов, всё на GitHub
- [x] Backend API работает на порту 8001
- [x] Frontend работает на порту 3300
- [x] `npm run build` — 0 ошибок TypeScript

### День 2 (28 марта) — Противоречия + Граф оптимизация
- [ ] Улучшить промпт противоречий (текущий слишком строгий: 0/50 проверок)
- [ ] Перезапустить LLM-анализ с улучшенным промптом → найти реальные противоречия
- [ ] Оптимизировать граф: оставить ~60 узлов (документы), убрать 118K (перекрёстные ссылки)
- [ ] Добавить LLM-объяснения для дублирований (сейчас только cosine score)
- [ ] Проверить frontend подключение к API (dashboard, graph, findings)
- [ ] Fix: frontend CORS для порта 3300
- [ ] Тестирование всех страниц с реальными данными

### День 3 (29 марта) — MVP Delivery + Сдача этапа #1
- [ ] Fix все баги, найденные при тестировании
- [ ] Docker compose up — проверить полный деплой
- [ ] Обновить README с актуальными данными и портами
- [ ] **Сдача этапа #1**: GitHub + архитектура + работающий MVP

---

## Фаза 2: Ядро анализа (Дни 4-7, 30 марта — 2 апреля)

**Цель**: Качественные findings + интерактивный frontend. Сдача этапа #2.

### День 4 (30 марта) — Улучшение качества анализа
- [ ] Расширить LLM-анализ: проверить больше пар на противоречия
- [ ] Добавить duplication confirmation через LLM для топ-50 embedding-дублирований
- [ ] Запуск полного анализа с улучшенными промптами
- [ ] Генерация LLM-объяснений для каждого finding

### День 5 (31 марта) — Frontend интеграция
- [ ] Подключить Dashboard к реальным данным /api/stats
- [ ] Подключить 3D-граф к /api/graph (оптимизированный)
- [ ] Подключить Findings к /api/findings с реальной пагинацией
- [ ] Подключить Finding detail к /api/findings/:id
- [ ] Тестирование SSE анализа (/analyze)

### День 6 (1 апреля) — UI polish
- [ ] Loading states, error states, empty states
- [ ] Анимации перехода между страницами
- [ ] Responsive layout для мобильных
- [ ] Оптимизация 3D-графа (только документы, не все нормы)

### День 7 (2 апреля) — Сдача этапа #2
- [ ] Финальное тестирование
- [ ] Записать короткое демо-видео (3-5 мин)
- [ ] Обновить README
- [ ] **Сдача этапа #2**: GitHub + демо-видео + README

---

## Фаза 3: Финал (Дни 8-10, 3-5 апреля)

**Цель**: Полировка, демо-видео, презентация, финальная сдача.

### День 8 (3 апреля) — Техническая экспертиза + Bug fix
- [ ] Исправление багов
- [ ] Frontend: `/about` — методология (Explainability)
- [ ] Docker: финальная проверка `docker compose up`
- [ ] Предгенерация демо-данных (`demo/seed_data.json`)

### День 9 (4 апреля) — Документация + Демо-видео
- [ ] Обновить README: скриншоты, актуальные данные
- [ ] Записать демо-видео (3-5 минут)
- [ ] Создать презентацию (13 слайдов по docs/PRESENTATION.md)
- [ ] UI polish: финальные правки

### День 10 (5 апреля) — Финальная сдача (дедлайн 23:59)
- [ ] Финальное тестирование Docker-деплоя
- [ ] Редактирование демо-видео
- [ ] Финализация презентации
- [ ] Push всего на GitHub
- [ ] **СДАЧА** до 23:59

---

## Текущие метрики (обновлено 27 марта)

| Метрика | Значение |
|---------|----------|
| Документов | 59 |
| Норм | 54 526 |
| Перекрёстных ссылок | 870 514 |
| Эмбеддингов (ChromaDB) | 54 526 (768-dim) |
| Кластеров | 672 |
| Findings: дублирования | 200 |
| Findings: устаревшие | 100 |
| Findings: противоречия | 0 (требует доработки промпта) |
| Граф: узлы | 118 639 |
| Граф: рёбра | 196 453 |
| Backend файлов | 35+ Python |
| Frontend файлов | 40+ TS/TSX |
| Коммитов | 6 |

## Критический путь

```
Парсинг → Эмбеддинги → Кластеризация → Анализ → Frontend → Polish
(✅ 6 сек)  (✅ 8 мин)   (✅ 39 мин)    (✅ 12 мин) (✅ scaffold) (День 2+)
```

**Блокер**: Противоречия = 0. Нужно улучшить промпт и стратегию выбора пар для LLM.

## Fallback-стратегия

| Риск | Fallback |
|------|----------|
| adilet.zan.kz недоступен | ✅ HTML закэширован в data/raw_html/ |
| LLM даёт плохие результаты | ✅ Embedding-based дублирование работает без LLM |
| Противоречия не находятся | Ослабить порог confidence, расширить промпт |
| Не хватает времени на frontend | ✅ Все 9 страниц уже scaffold'ены |
| Docker не работает у жюри | Демо-видео как backup |
