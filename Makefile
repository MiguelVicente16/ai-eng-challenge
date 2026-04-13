.PHONY: install lint format format-check test check run simulate simulate-all simulate-interactive draw-graph docker-build docker-up

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

simulate:
	uv run python scripts/simulate_call.py

simulate-all:
	uv run python scripts/simulate_call.py --scenario all

simulate-interactive:
	uv run python scripts/simulate_call.py --interactive

draw-graph:
	PYTHONPATH=. uv run python scripts/draw_graph.py

docker-build:
	docker build -t ai-eng-challenge .

docker-up:
	docker compose up --build
