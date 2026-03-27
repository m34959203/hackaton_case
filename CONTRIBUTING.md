# Contributing

## Git Workflow

1. Создайте ветку от `main`:
   ```bash
   git checkout -b feat/your-feature
   ```

2. Коммитьте с [Conventional Commits](https://www.conventionalcommits.org/):
   ```
   feat: add contradiction detection
   fix: handle empty articles in parser
   docs: update API documentation
   refactor: extract embedding logic
   test: add parser unit tests
   chore: update dependencies
   ```

3. Перед push:
   ```bash
   make lint
   make test
   ```

4. Создайте Pull Request в `main`.

## Code Style

### Python
- Ruff для линтинга и форматирования
- Type hints обязательны для публичных функций
- Docstrings на русском для бизнес-логики, на английском для утилит

### TypeScript
- ESLint + Prettier
- Strict mode
- Интерфейсы вместо type aliases для объектов

## Архитектурные принципы

1. **Модульность** — каждый модуль pipeline/ отвечает за одну задачу
2. **Explainability first** — любой результат анализа должен быть объяснимым
3. **Human-in-the-loop** — система помогает, а не заменяет эксперта
4. **Cache everything** — сырые HTML, эмбеддинги, результаты LLM
5. **Graceful degradation** — если Ollama недоступен, показываем кэшированные данные
