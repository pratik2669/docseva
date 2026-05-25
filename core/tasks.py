from __future__ import annotations

from celery import shared_task
from django.core.mail import mail_admins


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 3})
def send_admin_notification(self, subject: str, message: str) -> int:
    """Small production-safe async task example for operational alerts."""
    mail_admins(subject=subject, message=message, fail_silently=False)
    return 1
