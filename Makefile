format:
	ruff format .

lint:
	ruff check .

lint-fix:
	ruff check . --fix

typecheck:
	mypy .

check:
	lint typecheck

up:
	docker compose up --build -d

down:
	docker compose down

migrate:
	docker compose exec app alembic upgrade head

logs:
	docker compose logs -f app

up-prod:
	docker compose --env-file .env.prod up --build -d