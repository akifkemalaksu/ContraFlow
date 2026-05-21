.PHONY: dev worker beat api docker docker-down docker-rebuild

docker:
	docker compose -f docker/docker-compose.yml up --build -d

docker-rebuild:
	docker compose -f docker/docker-compose.yml build --no-cache app && docker compose -f docker/docker-compose.yml up -d app

docker-down:
	docker compose -f docker/docker-compose.yml down

dev:
	@trap 'kill 0' INT; \
	uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000 & \
	uv run celery -A src.infrastructure.tasks.celery_app worker --loglevel=info & \
	uv run celery -A src.infrastructure.tasks.celery_app beat --loglevel=info & \
	wait

api:
	uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

worker:
	uv run celery -A src.infrastructure.tasks.celery_app worker --loglevel=info

beat:
	uv run celery -A src.infrastructure.tasks.celery_app beat --loglevel=info
