# Changelog

## День 1 (27 марта 2026)

- Инициализация проекта: структура, документация (17 файлов), CLAUDE.md
- Backend: FastAPI, config, database (SQLite + ChromaDB), модели данных
- Парсер adilet.zan.kz: fetcher, parser, structural, seed_docs (59 документов)
- Парсинг: 54 526 норм, 870 514 перекрёстных ссылок
- NLP-пайплайн: embedder, clusterer (672 кластера), dedup, contradiction, outdated, graph_builder
- LLM-интеграция: async Ollama-клиент, 5 промптов на русском
- API: 9 эндпоинтов (documents, findings, graph, search, compare, analyze SSE, stats, health)
- Quick analyze: 200 дублирований + 100 устаревших = 300 findings
- Frontend: Next.js 16, shadcn/ui, все 9 страниц (dashboard, 3D-граф, findings, documents, analyze, about)
- Docker: Dockerfile для backend и frontend, docker-compose.yml
- 6 коммитов

## День 2 (28 марта 2026)

- Оптимизация графа: 118 639 узлов -> 59 узлов (только документы), 171 ребро
- Улучшение промпта противоречий: найдено 6 реальных противоречий
- Enrichment: LLM-объяснения для 50 дублирований
- Fix: CORS для порта 3300
- Fix: типы TypeScript обновлены под реальный API
- Docker build: 0 ошибок
- Frontend: loading states для всех страниц
- Итого findings: 306 (6 противоречий + 200 дублирований + 100 устаревших)

## День 3 (29 марта 2026)

- Fix: trailing slash в API-роутах
- Обновление документации: README, SPRINT_PLAN, DEVELOPMENT, CHANGELOG
- Docker compose: e2e тестирование
- Сдача этапа #1
