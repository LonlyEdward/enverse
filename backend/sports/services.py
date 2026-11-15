"""Pure football helpers: the season for a date, and the status mapping.

These live apart from the mappers because they are the two pieces of business
logic worth unit-testing on their own (no I/O, no database).
"""

from .models import FootballFixture

# API-Football ``status.short`` -> our coarse FootballFixture.Status. Codes not
# listed fall back to SCHEDULED (the safe default: treat an unknown state as "not
# yet played" rather than silently dropping the fixture).
#
#   NS, TBD                              -> scheduled (not started / time undefined)
#   1H, HT, 2H, ET, BT, P, LIVE,         -> live (in progress, incl. suspended and
#   SUSP, INT                                   interrupted, which may still resume)
#   FT, AET, PEN                         -> finished
#   PST                                  -> postponed
#   CANC, ABD, AWD, WO                   -> cancelled (incl. abandoned, awarded, walkover)
STATUS_MAP = {
    "NS": FootballFixture.Status.SCHEDULED,
    "TBD": FootballFixture.Status.SCHEDULED,
    "1H": FootballFixture.Status.LIVE,
    "HT": FootballFixture.Status.LIVE,
    "2H": FootballFixture.Status.LIVE,
    "ET": FootballFixture.Status.LIVE,
    "BT": FootballFixture.Status.LIVE,
    "P": FootballFixture.Status.LIVE,
    "LIVE": FootballFixture.Status.LIVE,
    "SUSP": FootballFixture.Status.LIVE,
    "INT": FootballFixture.Status.LIVE,
    "FT": FootballFixture.Status.FINISHED,
    "AET": FootballFixture.Status.FINISHED,
    "PEN": FootballFixture.Status.FINISHED,
    "PST": FootballFixture.Status.POSTPONED,
    "CANC": FootballFixture.Status.CANCELLED,
    "ABD": FootballFixture.Status.CANCELLED,
    "AWD": FootballFixture.Status.CANCELLED,
    "WO": FootballFixture.Status.CANCELLED,
}


def map_status(short):
    return STATUS_MAP.get((short or "").upper(), FootballFixture.Status.SCHEDULED)


def current_season(today):
    """Return the API-Football season year for ``today``.

    European seasons span two calendar years and are labelled by the year they
    start in. A season kicks off in summer, so from July onward we are in the
    season labelled with the current year; before July we are still in last
    year's season. ``today`` is passed in (never read from the clock here) so the
    boundary is testable.
    """
    return today.year if today.month >= 7 else today.year - 1
