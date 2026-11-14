"""Celery application for EnVerse.

Configuration lives in Django settings under the ``CELERY_`` namespace, and task
modules are discovered automatically from each installed app's ``tasks.py``.
"""

import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

celery_app = Celery("config")
celery_app.config_from_object("django.conf:settings", namespace="CELERY")
celery_app.autodiscover_tasks()
