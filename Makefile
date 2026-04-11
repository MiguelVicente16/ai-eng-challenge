.PHONY: install lint format test check run docker-build docker-up

install:
	uv sync --all-extras

lint:
	uv run ruff check src/ tests/

format:
	uv run ruff format src/ tests/

format-check:
	uv run ruff format --check src/ tests/

test:
	uv run pytest -v

check: lint format-check test

run:
	uv run uvicorn src.main:app --reload --port 8000

docker-build:
	docker build -t ai-eng-challenge .

docker-up:
	docker compose up --build
