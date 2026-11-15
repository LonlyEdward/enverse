"""Turning events into stored notifications, and sending the email digests.

``generate_notifications`` runs the detectors, works out who should receive each
event (followers minus people who muted the kind, channel or a genre) and writes
in-app rows and pending email rows. ``dispatch_notifications`` sends the pending
email rows as one digest per user.
"""

import logging
from collections import defaultdict
from datetime import timedelta

from django.core.mail import send_mail
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from anime.models import AnimeEpisode
from library.models import Following

from .events import collect_events
from .models import Notification, NotificationPreference

logger = logging.getLogger(__name__)

EMAIL_BATCH = 200
EMAIL_MAX_AGE = timedelta(days=2)

# event kind -> the preference flag that turns it off.
_KIND_PREF = {
    Notification.Kind.RELEASE: "notify_releases",
    Notification.Kind.SCHEDULE: "notify_schedules",
    Notification.Kind.UPDATE: "notify_updates",
}

# An unsaved default used for users who have never touched their preferences:
# everything on, nothing muted.
_DEFAULT_PREF = NotificationPreference()


def _follower_ids(audience):
    """User ids following any of an event's targets, with notifications enabled."""
    predicate = Q()
    for content_type, object_id in audience:
        predicate |= Q(content_type=content_type, object_id=object_id)
    if not predicate:
        return set()
    return set(
        Following.objects.filter(predicate, notifications_enabled=True).values_list("user_id", flat=True)
    )


def _wants(pref, event):
    """Whether this user's preferences admit this event at all (kind + genres)."""
    if not getattr(pref, _KIND_PREF[event.kind]):
        return False
    if pref.muted_genres and set(pref.muted_genres) & set(event.genres):
        return False
    return True


def generate_notifications(now=None):
    """Detect events and write the resulting notification rows. Idempotent.

    Returns the number of rows created (best effort: ``ignore_conflicts`` means a
    re-run inserts zero). The anime ``notified`` flips and the row inserts share one
    transaction, so a flag never flips without its rows.
    """
    now = now or timezone.now()
    events = collect_events(now)
    if not events:
        return 0

    # One preferences lookup for every candidate recipient across all events.
    audiences = {event.event_key: _follower_ids(event.audience) for event in events}
    all_user_ids = set().union(*audiences.values()) if audiences else set()
    prefs = {p.user_id: p for p in NotificationPreference.objects.filter(user_id__in=all_user_ids)}

    rows = []
    flip_episode_ids = set()
    for event in events:
        if event.flip_episode_id is not None:
            flip_episode_ids.add(event.flip_episode_id)
        for user_id in audiences[event.event_key]:
            pref = prefs.get(user_id, _DEFAULT_PREF)
            if not _wants(pref, event):
                continue
            for channel, enabled in (
                (Notification.Channel.IN_APP, pref.in_app_enabled),
                (Notification.Channel.EMAIL, pref.email_enabled),
            ):
                if enabled:
                    rows.append(_build_row(user_id, event, channel))

    with transaction.atomic():
        created = Notification.objects.bulk_create(rows, ignore_conflicts=True)
        if flip_episode_ids:
            AnimeEpisode.objects.filter(id__in=flip_episode_ids).update(notified=True)
    # ignore_conflicts makes the returned list unreliable for a count on re-runs,
    # so report how many rows we built to insert.
    return len(rows)


def _build_row(user_id, event, channel):
    return Notification(
        user_id=user_id,
        kind=event.kind,
        content_type=event.content_type,
        object_id=event.object_id,
        title=event.title,
        body=event.body,
        channel=channel,
        event_key=event.event_key,
    )


def dispatch_notifications(now=None):
    """Send pending email rows as one digest per user. At-least-once.

    We mark ``sent_at`` only *after* the send succeeds, so a crash between sending
    and marking can repeat a digest — duplicates are acceptable, lost mail is not.
    Rows older than ``EMAIL_MAX_AGE`` are left unsent (too stale to be useful), and
    at most ``EMAIL_BATCH`` rows are handled per run.
    """
    now = now or timezone.now()
    cutoff = now - EMAIL_MAX_AGE
    pending = list(
        Notification.objects.filter(
            channel=Notification.Channel.EMAIL, sent_at__isnull=True, created_at__gte=cutoff
        )
        .select_related("user")
        .order_by("user_id", "created_at")[:EMAIL_BATCH]
    )
    if not pending:
        return 0

    by_user = defaultdict(list)
    for row in pending:
        by_user[row.user].append(row)

    sent_ids = []
    for user, rows in by_user.items():
        if not user.email:
            continue
        try:
            _send_digest(user, rows)
        except Exception:
            # Leave sent_at null so the next run retries this user's digest.
            logger.exception("Failed to send notification digest to user %s", user.id)
            continue
        sent_ids.extend(row.id for row in rows)

    if sent_ids:
        Notification.objects.filter(id__in=sent_ids).update(sent_at=now)
    return len(sent_ids)


def _send_digest(user, rows):
    lines = [f"- {row.title}: {row.body}" if row.body else f"- {row.title}" for row in rows]
    subject = f"You have {len(rows)} update{'s' if len(rows) != 1 else ''} on EnVerse"
    body = "Here's what's new for the things you follow:\n\n" + "\n".join(lines)
    send_mail(subject, body, None, [user.email])  # from = DEFAULT_FROM_EMAIL
