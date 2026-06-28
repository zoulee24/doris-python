.PHONY: format lint

format:
	ruff format .

lint:
	ruff check src/

