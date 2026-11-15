"""Pure-ish event detection: one function per case, each returning ``Event``s.

Detectors only *read* content models and return events; they never write. The one
state change — marking an anime episode ``notified`` — is carried on the event
(``flip_episode_id``) and applied by the generator inside the same transaction as
the notification insert, so the flag and the row commit together.

Each detector is isolated by :func:`collect_events`: if one raises, it is logged
and the others still run, so a single bad row never blocks every notification.
"""

import logging
from dataclasses import dataclass
from datetime import timedelta

from django.db.models import F

from anime.models import AnimeEpisode
from games.models import Game
from movies.models import Movie
from notifications.models import Notification
from sports.models import FootballFixture
from tv.models import TVSeason, TVShow

logger = logging.getLogger(__name__)

# Windows. Kept as module constants so tests can reason about the boundaries.
RELEASE_RECENT = timedelta(days=3)      # a movie/game/episode counts as "just out"
MATCH_REMINDER = timedelta(hours=24)    # remind this long before kickoff
MATCH_RESULT = timedelta(days=2)        # surface a result this long after it finished


@dataclass(frozen=True)
class Event:
    """One thing worth telling a user about, before audience/preference filtering.

    ``audience`` is a tuple of ``(content_type, object_id)`` follow-targets: whoever
    follows any of them is a candidate recipient (football has two — both teams).
    ``genres`` lets the generator drop users who muted a genre without re-querying
    the item. ``flip_episode_id`` is set only for anime episodes.
    """

    kind: str
    content_type: str
    object_id: int
    title: str
    body: str
    event_key: str
    audience: tuple
    genres: tuple = ()
    flip_episode_id: int | None = None


def _follow_target(content_type, object_id):
    return ((content_type, object_id),)


def detect_released(now):
    """Movies and games whose release date is within the recent window."""
    today = now.date()
    start = today - RELEASE_RECENT
    events = []
    for model, content_type in ((Movie, "movie"), (Game, "game")):
        for item in model.objects.filter(release_date__gte=start, release_date__lte=today):
            events.append(
                Event(
                    kind=Notification.Kind.RELEASE,
                    content_type=content_type,
                    object_id=item.id,
                    title=f"{item.title} is out",
                    body=f"{item.title} was released on {item.release_date:%b %d, %Y}.",
                    event_key=f"released:{content_type}:{item.id}",
                    audience=_follow_target(content_type, item.id),
                    genres=tuple(item.genres or ()),
                )
            )
    return events


def detect_release_changed(now):
    """Movies and games whose release date shifted (previous != current)."""
    events = []
    for model, content_type in ((Movie, "movie"), (Game, "game")):
        # Both dates present and genuinely different (excluded at the DB level).
        qs = (
            model.objects.filter(previous_release_date__isnull=False, release_date__isnull=False)
            .exclude(previous_release_date=F("release_date"))
        )
        for item in qs:
            new_date = item.release_date.isoformat()
            events.append(
                Event(
                    kind=Notification.Kind.UPDATE,
                    content_type=content_type,
                    object_id=item.id,
                    title=f"{item.title} has a new release date",
                    body=f"{item.title} is now releasing on {item.release_date:%b %d, %Y}.",
                    # The new date is in the key, so a *further* shift notifies again
                    # but the same shift never does.
                    event_key=f"release_changed:{content_type}:{item.id}:{new_date}",
                    audience=_follow_target(content_type, item.id),
                    genres=tuple(item.genres or ()),
                )
            )
    return events


def detect_anime_episodes(now):
    """Anime episodes that have aired but not yet been notified."""
    episodes = AnimeEpisode.objects.filter(
        notified=False, aired_at__isnull=False, aired_at__lte=now
    ).select_related("anime")
    events = []
    for episode in episodes:
        anime = episode.anime
        events.append(
            Event(
                kind=Notification.Kind.RELEASE,
                content_type="anime",
                object_id=anime.id,
                title=f"{anime.title} — episode {episode.episode_number}",
                body=f"Episode {episode.episode_number} of {anime.title} is now available.",
                event_key=f"episode:anime:{anime.id}:{episode.episode_number}",
                audience=_follow_target("anime", anime.id),
                genres=tuple(anime.genres or ()),
                flip_episode_id=episode.id,
            )
        )
    return events


def detect_football(now):
    """Upcoming-match reminders and recent results for both teams of a fixture."""
    events = []
    reminders = FootballFixture.objects.select_related("home_team", "away_team").filter(
        status=FootballFixture.Status.SCHEDULED, kickoff_at__gt=now, kickoff_at__lte=now + MATCH_REMINDER
    )
    for fixture in reminders:
        events.append(_fixture_event(fixture, kind=Notification.Kind.SCHEDULE, prefix="match_reminder",
                                     title=f"{_match(fixture)} kicks off soon",
                                     body=f"{_match(fixture)} starts {fixture.kickoff_at:%b %d, %H:%M} UTC."))

    results = FootballFixture.objects.select_related("home_team", "away_team").filter(
        status=FootballFixture.Status.FINISHED, kickoff_at__gte=now - MATCH_RESULT, kickoff_at__lte=now
    )
    for fixture in results:
        score = f"{fixture.home_score}–{fixture.away_score}"
        events.append(_fixture_event(fixture, kind=Notification.Kind.UPDATE, prefix="match_result",
                                     title=f"Result: {_match(fixture)}",
                                     body=f"Full time: {fixture.home_team.name} {score} {fixture.away_team.name}."))
    return events


def _match(fixture):
    return f"{fixture.home_team.name} vs {fixture.away_team.name}"


def _fixture_event(fixture, *, kind, prefix, title, body):
    return Event(
        kind=kind,
        content_type="football",
        object_id=fixture.id,
        title=title,
        body=body,
        event_key=f"{prefix}:{fixture.id}",
        # Followers of either team should hear about the match.
        audience=(("football", fixture.home_team_id), ("football", fixture.away_team_id)),
    )


def detect_tv(now):
    """TV next episodes that have aired and seasons that have started, in the window."""
    today = now.date()
    start = today - RELEASE_RECENT
    events = []

    for show in TVShow.objects.filter(next_episode_air_date__gte=start, next_episode_air_date__lte=today):
        season = show.next_episode_season
        number = show.next_episode_number
        events.append(
            Event(
                kind=Notification.Kind.RELEASE,
                content_type="tv",
                object_id=show.id,
                title=f"{show.title} — new episode",
                body=f"A new episode of {show.title} has aired.",
                event_key=f"tv_episode:{show.id}:{season}:{number}",
                audience=_follow_target("tv", show.id),
                genres=tuple(show.genres or ()),
            )
        )

    for season in TVSeason.objects.select_related("show").filter(air_date__gte=start, air_date__lte=today):
        show = season.show
        events.append(
            Event(
                kind=Notification.Kind.UPDATE,
                content_type="tv",
                object_id=show.id,
                title=f"{show.title} — season {season.season_number}",
                body=f"Season {season.season_number} of {show.title} has started.",
                event_key=f"tv_season:{show.id}:{season.season_number}",
                audience=_follow_target("tv", show.id),
                genres=tuple(show.genres or ()),
            )
        )
    return events


DETECTORS = (detect_released, detect_release_changed, detect_anime_episodes, detect_football, detect_tv)


def collect_events(now):
    """Run every detector, isolating failures, and return the combined events."""
    events = []
    for detector in DETECTORS:
        try:
            events.extend(detector(now))
        except Exception:
            name = getattr(detector, "__name__", repr(detector))
            logger.exception("Notification detector %s failed", name)
    return events
