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