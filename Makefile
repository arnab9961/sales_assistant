.PHONY: up down test logs load-data clean

up:
	docker compose up --build -d

down:
	docker compose down

test:
	python -m pytest tests/ -v

logs:
	docker compose logs -f

load-data:
	python -c "from app.database import SessionLocal; from app.etl.loader import run_etl; db = SessionLocal(); run_etl(db, 'data'); db.close(); print('ETL Reload Complete.')"

clean:
	docker compose down -v
	rm -rf .pytest_cache htmlcov .coverage sales_ops.db
