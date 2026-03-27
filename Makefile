.PHONY: setup dev scrape embed analyze demo test lint format clean

# First-time setup: pull models, scrape, embed, analyze
setup:
	docker exec ollama ollama pull qwen2.5:14b
	docker exec ollama ollama pull nomic-embed-text
	docker exec backend python -m scripts.scrape --all
	docker exec backend python -m scripts.process --embed --cluster
	docker exec backend python -m scripts.analyze --all

# Start all services for development
dev:
	docker compose up -d

# Scrape documents from adilet.zan.kz
scrape:
	cd backend && python -m scripts.scrape --all

# Generate embeddings and clusters
embed:
	cd backend && python -m scripts.process --embed --cluster

# Run analysis pipeline
analyze:
	cd backend && python -m scripts.analyze --all

# Load demo data and start
demo:
	docker compose up -d
	docker exec backend python -m scripts.load_demo

# Run tests
test:
	cd backend && pytest tests/ -v
	cd frontend && npm run test

# Lint code
lint:
	cd backend && ruff check .
	cd frontend && npm run lint

# Format code
format:
	cd backend && ruff format .
	cd frontend && npx prettier --write "src/**/*.{ts,tsx}"

# Clean generated data
clean:
	rm -rf backend/data/
	rm -rf frontend/.next/
	rm -rf frontend/node_modules/
