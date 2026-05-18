.PHONY: dev worker beat api

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
