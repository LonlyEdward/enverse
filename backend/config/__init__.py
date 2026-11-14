"""Expose the Celery app so Django picks it up on startup and @shared_task works."""

from config.celery import celery_app

__all__ = ("celery_app",)
