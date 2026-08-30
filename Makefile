.PHONY: help install proto test lint format docker-build up down seed-analyst executive-demo clean

help:
	@echo "VeriPay monorepo"
	@echo "  make install    - install Python + JS deps"
	@echo "  make proto      - generate gRPC/TS code from proto/"
	@echo "  make test       - run pytest + vitest"
	@echo "  make lint       - ruff + mypy + eslint"
	@echo "  make up         - docker-compose up (local stack)"
	@echo "  make down       - docker-compose down"
	@echo "  make seed-analyst - re-seed the analyst console alert queue"
	@echo "  make executive-demo - run the offline executive board demo"

install:
	pip install -e ".[dev]" -e libs/veripay_common
	@for s in services/*; do [ -f $$s/pyproject.toml ] && pip install -e $$s || true; done
	cd web && npm install

proto:
	buf generate proto

test:
	pytest
	cd web && npm test -- --run

lint:
	ruff check .
	mypy libs services
	cd web && npm run lint

format:
	ruff format .
	ruff check --fix .

docker-build:
	docker compose build

up:
	docker compose up -d

down:
	docker compose down -v

seed-analyst:
	docker compose run --rm seed_analyst

executive-demo:
	python scripts/executive-demo.py --offline

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .ruff_cache -exec rm -rf {} + 2>/dev/null || true
