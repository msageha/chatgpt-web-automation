.PHONY: install run lint format clean help

setup:
	uv venv --python=python3.12
	. .venv/bin/activate && uv pip sync requirements/requirements.txt

run:
	python -m src.main

lint:
	@echo "Running mypy"
	uvx mypy src/ --explicit-package-bases
	@echo "Running ruff"
	uvx ruff check src/

format:
	@echo "Running black"
	uvx black src/
	@echo "Running isort"
	uvx isort src/

clean:
	rm -rf __pycache__ .pytest_cache
	rm -f logs/*.png logs/*.html logs/*.log

docker-build:
	docker build -t chatgpt-web-automation .

docker-run:
	docker run --rm -v $(PWD):/app chatgpt-web-automation
