"""Shared sync helpers used by every content sync task.

The design rules (see docs/BUILD_PLAN.md section 4):
- a sync never raises out of a task (one bad item must not crash the worker);
- every run records a ``SyncLog`` row describing what happened;
- upserts are idempotent, keyed by ``external_id``.
"""

import logging
from datetime import date, datetime

from django.db import transaction
from django.db.models import Case, IntegerField, Value, When
from django.utils import timezone
from django.utils.dateparse import parse_date as _django_parse_date

from core.models import SyncLog

logger = logging.getLogger(__name__)

ERROR_MESSAGE_MAX_LENGTH = 1000  # keep SyncLog.error_message bounded


class SyncRun:
    """Context manager that records a ``SyncLog`` and never lets a task crash.

    Usage::

        with SyncRun(SyncLog.Source.TMDB) as run:
            for item in fetch():
                try:
                    store_item(Movie, item["id"], {...})
                    run.processed(1)
                except Exception as exc:
                    run.error(f"item {item['id']}: {exc}")

    On exit the run is marked:
    - ``success`` when nothing went wrong;
    - ``partial`` when some items errored but some were processed;
    - ``failed`` when an exception escaped the block, or every item errored and
      nothing was processed (a total failure).

    Any exception raised inside the block is swallowed and logged.
    """

    def __init__(self, source):
        self.source = source
        self.log = None
        self._errors = []
        self._processed = 0

    def __enter__(self):
        self.log = SyncLog.objects.create(source=self.source, status=SyncLog.Status.RUNNING)
        return self

    def processed(self, count):
        """Record that ``count`` items were successfully stored."""
        self._processed += count

    def error(self, message):
        """Record a per-item error without aborting the run."""
        self._errors.append(str(message))
        logger.warning("Sync %s: item error: %s", self.source, message)

    def __exit__(self, exc_type, exc, tb):
        self.log.finished_at = timezone.now()
        self.log.items_processed = self._processed

        if exc_type is not None:
            self.log.status = SyncLog.Status.FAILED
            self.log.error_message = self._truncate(f"{exc_type.__name__}: {exc}")
            logger.exception("Sync %s failed with an exception", self.source, exc_info=(exc_type, exc, tb))
        elif self._errors and self._processed == 0:
            self.log.status = SyncLog.Status.FAILED  # total failure: everything errored
            self.log.error_message = self._truncate("; ".join(self._errors))
        elif self._errors:
            self.log.status = SyncLog.Status.PARTIAL
            self.log.error_message = self._truncate("; ".join(self._errors))
        else:
            self.log.status = SyncLog.Status.SUCCESS

        self.log.save()
        return True  # swallow any exception from the block

    @staticmethod
    def _truncate(message):
        return message[:ERROR_MESSAGE_MAX_LENGTH]


def store_item(model, external_id, defaults):
    """Idempotently upsert one row keyed by ``external_id``, stamping sync time.

    Returns ``(obj, created)`` like ``update_or_create``. Running a sync twice
    produces the same row, never a duplicate.
    """
    merged = {**defaults, "last_synced_at": timezone.now()}
    return model.objects.update_or_create(external_id=str(external_id), defaults=merged)


@transaction.atomic
def replace_trending_ranks(model, ordered_external_ids):
    """Assign ``trending_rank`` 1..N to the given ids and clear it on all others.

    Done in two queries inside one transaction so the ranking is always
    consistent (no window where two rows share a rank or an old rank lingers).
    """
    ids = [str(external_id) for external_id in ordered_external_ids]

    # Clear ranks that are set on rows not in the new list.
    model.objects.filter(trending_rank__isnull=False).exclude(external_id__in=ids).update(trending_rank=None)

    if not ids:
        return
    whens = [When(external_id=external_id, then=Value(rank)) for rank, external_id in enumerate(ids, start=1)]
    model.objects.filter(external_id__in=ids).update(trending_rank=Case(*whens, output_field=IntegerField()))


def parse_date(value):
    """Best-effort parse to a ``date``; return ``None`` for empty or invalid input.

    External APIs hand back dates as strings, sometimes empty (``""``) or malformed
    (``"2021-00-00"``). Those must become ``None`` rather than blow up a sync.
    """
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    try:
        return _django_parse_date(str(value).strip())
    except (ValueError, TypeError):
        return None
