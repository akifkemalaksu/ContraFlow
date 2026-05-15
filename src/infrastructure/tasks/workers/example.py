from src.infrastructure.tasks.celery_app import celery_app


@celery_app.task(name="send_welcome_email", bind=True, max_retries=3)
def send_welcome_email(self, user_id: str, email: str) -> dict:
    try:
        # Gerçek implementasyonda SMTP / SES entegrasyonu buraya gelir
        return {"status": "sent", "user_id": user_id, "email": email}
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)
