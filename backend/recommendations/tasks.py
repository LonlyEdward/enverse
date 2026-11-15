"""Daily recompute of every active user's recommendations, per-user isolated."""

import logging

from celery import shared_task
from django.contrib.auth import get_user_model

from .services import recompute_for_user

logger = logging.getLogger(__name__)


@shared_task(name="recommendations.tasks.recompute_recommendations")
def recompute_recommendations():
    User = get_user_model()
    done = 0
    for user in User.objects.filter(is_active=True).iterator():
        try:
            recompute_for_user(user)
            done += 1
        except Exception:
            # One user's bad data must not stop the batch.
            logger.exception("Failed to recompute recommendations for user %s", user.id)
    logger.info("Recomputed recommendations for %s users", done)
    return done
