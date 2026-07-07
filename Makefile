.PHONY: install dev test clean run docker-build docker-up lint format

install:
	pip install -r requirements.txt

dev:
	pip install -r requirements-dev.txt

test:
	pytest tests/ -v --cov=. --cov-report=html

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	rm -rf .pytest_cache .coverage htmlcov/ dist/ build/

run:
	streamlit run app/main.py

api:
	uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

docker-build:
	docker-compose -f deployment/docker/docker-compose.yml build

docker-up:
	docker-compose -f deployment/docker/docker-compose.yml up -d

docker-down:
	docker-compose -f deployment/docker/docker-compose.yml down

lint:
	flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
	pylint app/ core/ api/

format:
	black .
	isort .

setup-db:
	python scripts/setup_db.py

migrate:
	python scripts/migrate_data.py

benchmark:
	python scripts/benchmark.py