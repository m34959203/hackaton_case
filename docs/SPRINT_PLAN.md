# Спринт-план: 10 дней (27 марта — 5 апреля 2026)

## Фаза 1: Фундамент (Дни 1-3, 27-29 марта) ✅ ЗАВЕРШЕНА

### День 1 (27 марта) — Полный scaffold ✅
- [x] 17 файлов документации
- [x] Backend: 35+ Python файлов (config, database, models, scraper, pipeline, llm, api)
- [x] Frontend: 40+ TS/TSX файлов (9 страниц, 16 компонентов, shadcn/ui)
- [x] Парсинг 59 документов → 54 526 норм, 870 514 ссылок
- [x] Эмбеддинг → ChromaDB (54 526 векторов, 768-dim)
- [x] Кластеризация UMAP+HDBSCAN → 672 кластера с LLM-именованием
- [x] Quick analyze: 200 дублирований + 100 устаревших
- [x] Docker: Dockerfile backend + frontend
- [x] 6 коммитов на GitHub

### День 2 (28 марта) — Анализ + Интеграция ✅
- [x] Улучшен промпт противоречий → 6 реальных коллизий через Ollama
- [x] Граф оптимизирован: 118K узлов → 59 (только документы)
- [x] CORS для портов 3300 + Tailscale
- [x] Frontend: все типы → snake_case, подключение к API
- [x] Loading/error/empty states на всех 8 страницах
- [x] Docker compose: full e2e тест пройден
- [x] 50 дублирований обогащены LLM-объяснениями

### День 3 (29 марта) — Сдача этапа #1 + Gemini + Редизайн ✅
- [x] Trailing slash fix (redirect_slashes=False) — все 9 endpoints 200 OK
- [x] Multi-provider LLM: Ollama, OpenAI API, Anthropic, **Google Gemini**
- [x] Gemini 2.0 Flash подключён — **19 новых противоречий за 3 мин** (итого 25)
- [x] auto_pipeline.sh — автономный скрипт (scrape→embed→analyze→graph→export)
- [x] Demo data: seed_data.json (447KB) + highlights.json (38KB)
- [x] Frontend: fix compare/analyze, SVG favicon, OG metadata
- [x] **Полный UI/UX редизайн** по UI Pro Max: Trust & Authority дизайн-система
  - Navy #1E3A8A + Gold #B45309 палитра
  - Тёмный sidebar с Lucide иконками
  - Gradient hero dashboard, цветные stats cards
  - Glass-панели на графе, professional findings table
  - Smooth transitions, hover effects, consistent rounding
- [x] Production deploy: http://100.118.110.5:3300
- [x] **Сдача этапа #1**: GitHub + работающий MVP
- [x] 16 коммитов на GitHub

---

## Фаза 2: Ядро анализа (Дни 4-7, 30 марта — 2 апреля)

**Цель**: Качественные findings + интерактивный frontend. Сдача этапа #2.

### День 4 (30 марта) — Расширение анализа
- [ ] Запустить поиск противоречий через Gemini на 500+ пар (auto_pipeline.sh)
- [ ] Добавить retry + rate limit handling в Gemini клиент
- [ ] LLM-обогащение оставшихся 150 дублирований
- [ ] Добавить recommendations для каждого finding
- [ ] Проверить frontend с 325+ findings

### День 5 (31 марта) — Интерактивность
- [ ] Семантический поиск: тестирование /api/search с реальными запросами
- [ ] SSE-анализ нового текста: end-to-end тест /analyze
- [ ] Клик по узлу графа → навигация к документу
- [ ] Клик по ребру графа → навигация к finding
- [ ] Фильтры графа: по типу документа и типу связи

### День 6 (1 апреля) — Polish + Mobile
- [ ] Responsive layout для мобильных
- [ ] Анимации графа (частицы на contradiction рёбрах)
- [ ] Word-level diff в NormComparison
- [ ] Улучшить About страницу (методология для жюри)
- [ ] Темная/светлая тема переключатель

### День 7 (2 апреля) — Сдача этапа #2
- [ ] Записать демо-видео (3-5 мин)
- [ ] Обновить README со скриншотами
- [ ] Docker compose финальная проверка
- [ ] **Сдача этапа #2**: GitHub + демо-видео + README

---

## Фаза 3: Финал (Дни 8-10, 3-5 апреля)

### День 8-9 (3-4 апреля)
- [ ] Bug fix по результатам тестирования
- [ ] Презентация (13 слайдов)
- [ ] Запись и монтаж демо-видео
- [ ] Финальный Docker деплой

### День 10 (5 апреля) — Финальная сдача (дедлайн 23:59)
- [ ] Последние правки
- [ ] Push на GitHub
- [ ] **СДАЧА** до 23:59

---

## Текущие метрики (обновлено 29 марта, День 3)

| Метрика | Значение |
|---------|----------|
| Документов | 59 |
| Норм | 54 526 |
| Перекрёстных ссылок | 870 514 |
| Эмбеддингов (ChromaDB) | 54 526 (768-dim) |
| Кластеров | 672 |
| **Findings: противоречия** | **25** (7 high, 8 medium, 10 low) |
| Findings: дублирования | 200 (50 с LLM-объяснениями) |
| Findings: устаревшие | 100 |
| **Findings: всего** | **325** |
| Граф: узлы | 59 (документы) |
| Граф: рёбра | 177 |
| LLM провайдеры | Ollama, OpenAI, Anthropic, **Gemini** |
| Backend файлов | 35+ Python |
| Frontend файлов | 40+ TS/TSX |
| Коммитов | 16 |
| Дизайн-система | Trust & Authority (Navy + Gold) |

## Архитектура

```
┌─────────────────────────────────────┐
│     Frontend (Next.js 16)           │
│  :3300 (dev) / :3100 (Docker)       │
│  Trust & Authority дизайн-система   │
│  3D-граф • Дашборд • Сравнение      │
└──────────────┬──────────────────────┘
               │ REST API + SSE
┌──────────────▼──────────────────────┐
│     Backend (FastAPI)               │
│  :8001 (dev) / :8000 (Docker)       │
│  Scraper • NLP Pipeline • API       │
├──────┬────────┬─────────────────────┤
│LLM   │ChromaDB│     SQLite          │
│Multi │embedded│   (metadata)        │
│Prov. │        │                     │
└──────┴────────┴─────────────────────┘
  ↕ Ollama (local)
  ↕ Gemini API (cloud) ← active
  ↕ OpenAI/Anthropic (cloud, optional)
```

## Порты

| Сервис | Dev | Docker | Tailscale |
|--------|-----|--------|-----------|
| Backend | 8001 | 8000 | 100.118.110.5:8001 |
| Frontend | 3300 | 3100 | 100.118.110.5:3300 |
| Ollama | 11434 | — | — |
| Swagger | 8001/docs | 8000/docs | 100.118.110.5:8001/docs |

## Ключевые скрипты

```bash
# Автономный полный пайплайн
cd backend && nohup bash scripts/auto_pipeline.sh &
tail -f logs/pipeline.log       # мониторинг
kill $(cat logs/pipeline.pid)   # стоп

# Отдельные этапы
python -m scripts.scrape           # парсинг 59 документов
python -m scripts.quick_analyze    # быстрый анализ (embedding-based)
python -m scripts.enrich_findings  # LLM-обогащение
python -m scripts.export_demo      # экспорт demo JSON
```
