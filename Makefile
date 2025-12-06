
IMAGE_NAME = lyftr-api
CONTAINER_NAME = lyftr-backend

.PHONY: help up down logs test clean

help:
	@echo "Available commands:"
	@echo "  make up      - Start the application (Docker Compose)"
	@echo "  make down    - Stop the application"
	@echo "  make logs    - View application logs"
	@echo "  make test    - Run unit tests"
	@echo "  make clean   - Remove temporary files and volumes"

up:
	docker compose up -d --build

down:
	docker compose down -v

logs:
	docker compose logs -f api

test:
	docker compose run --rm api pytest -v tests/

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	rm -rf .pytest_cache
	rm -rf data/*.db