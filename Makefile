.PHONY: format lint

format:
	ruff format src/

lint:
	ruff check src/

