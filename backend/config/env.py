"""Small environment-variable helpers.

These exist because the obvious approaches are wrong:
``bool(os.environ.get("DEBUG"))`` is truthy for the *string* ``"False"``,
and ``int(os.environ["X"])`` explodes when the variable is unset or empty.
Keep this module dependency-free so it can be imported anywhere, including
from settings before Django is configured.
"""

import os
from urllib.parse import urlsplit, urlunsplit

TRUE_VALUES = {"1", "true", "yes", "on"}


def env_bool(name, default=False):
    """Parse a boolean env var; ``"False"``/``"0"``/``"no"`` are all falsey."""
    value = os.environ.get(name)
    return default if value is None else value.strip().lower() in TRUE_VALUES


def env_int(name, default):
    """Parse an int env var, falling back to ``default`` when unset or empty."""
    value = os.environ.get(name, "").strip()
    return int(value) if value else default


def env_list(name, default=""):
    """Parse a comma-separated env var into a list of non-empty, trimmed items."""
    return [item.strip() for item in os.environ.get(name, default).split(",") if item.strip()]


def with_redis_db(url, db):
    """Return ``url`` with its path (the Redis database number) replaced by ``/db``.

    Works whether the URL already names a database or not::

        redis://:pw@host:6379/0  -> redis://:pw@host:6379/1
        redis://host:6379        -> redis://host:6379/1
    """
    return urlunsplit(urlsplit(url)._replace(path=f"/{db}"))
