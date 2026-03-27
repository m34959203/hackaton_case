.PHONY: setup dev docker scrape analyze embed clean lint format test stop logs

# ============================================================
# ZanAlytics — Makefile
# ============================================================

# --- Первый запуск: парсинг + анализ ---
setup: scrape analyze
	@echo "=== Setup complete ==="

# --- Локальная разработка (без Docker) ---
dev:
	@echo "=== Starting backend (port 8000) and frontend (port 3300) ==="
	cd backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload &
	cd frontend && npm run dev &
	@echo "Backend: http://localhost:8001  |  Frontend: http://localhost:3300"
	@wait

# --- Docker: сборка и запуск ---
docker:
	docker compose build
	docker compose up -d
	@echo "=== Docker containers started ==="
	@echo "Backend:  http://localhost:8000"
	@echo "Frontend: http://localhost:3100"

# --- Парсинг документов с adilet.zan.kz ---
scrape:
	cd backend && python -m scripts.scrape

# --- Полный анализ (эмбеддинги + кластеризация + выявление проблем) ---
analyze:
	cd backend && python -m scripts.analyze

# --- Только эмбеддинги и кластеризация ---
embed:
	cd backend && python -m scripts.analyze

# --- Остановка Docker контейнеров ---
stop:
	docker compose down

# --- Логи Docker ---
logs:
	docker compose logs -f

# --- Линтинг ---
lint:
	cd backend && ruff check .
	cd frontend && npm run lint

# --- Форматирование ---
format:
	cd backend && ruff format .
	cd frontend && npx prettier --write "src/**/*.{ts,tsx}"

# --- Тесты ---
test:
	cd backend && pytest tests/ -v

# --- Очистка данных ---
clean:
	rm -rf backend/data/chroma
	rm -rf backend/data/raw_html
	rm -f backend/data/zandb.sqlite
	rm -f backend/data/graph.json
	rm -rf frontend/.next/
	@echo "=== Data cleaned ==="
