.PHONY: install test run migrate-init migrate-upgrade docker-up docker-down

install:
	python -m pip install --upgrade pip
	cd backend && pip install -r requirements.txt

test:
	cd backend && pytest

lint:
	python -m pip install --upgrade pip
	pip install black isort ruff mypy

	# format checkers
	cd backend && black --check .
	cd backend && isort --check-only .
	cd backend && ruff check .
	cd backend && mypy app tests || true

run:
	cd backend && python manage.py

migrate-init:
	cd backend && flask db init
	cd backend && flask db migrate -m "initial schema"
	cd backend && flask db upgrade

migrate-upgrade:
	cd backend && flask db upgrade

docker-up:
	docker compose -f deploy/compose.yaml up --build -d

docker-down:
	docker compose -f deploy/compose.yaml down
