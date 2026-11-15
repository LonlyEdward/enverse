"""Celery tasks: detect/generate notifications, then dispatch email digests."""

import logging

from celery import shared_task

from .services import dispatch_notifications, generate_notifications

logger = logging.getLogger(__name__)


@shared_task(name="notifications.tasks.generate_notifications")
def generate_notifications_task():
    created = generate_notifications()
    logger.info("Notification generation built %s rows", created)
    return created


@shared_task(name="notifications.tasks.dispatch_notifications")
def dispatch_notifications_task():
    sent = dispatch_notifications()
    logger.info("Notification dispatch sent %s email rows", sent)
    return sent
