"""Shared HTTP session for talking to external APIs.

A session built here retries transient failures with exponential backoff and
applies a default timeout to every request, so individual client code never has
to remember either. Used by the sync clients in Phases 3-7.
"""

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# (connect timeout, read timeout) in seconds. External APIs can be slow to
# respond but should connect quickly; a hung request must not wedge a worker.
DEFAULT_TIMEOUT = (5, 20)

# Generic, non-identifying client name on purpose: never leak project/user info.
USER_AGENT = "EnVerse/1.0 (+https://enverse.app)"


class _TimeoutHTTPAdapter(HTTPAdapter):
    """HTTPAdapter that applies a default timeout when the caller gives none."""

    def __init__(self, *args, timeout=DEFAULT_TIMEOUT, **kwargs):
        self._timeout = timeout
        super().__init__(*args, **kwargs)

    def send(self, request, **kwargs):
        if kwargs.get("timeout") is None:
            kwargs["timeout"] = self._timeout
        return super().send(request, **kwargs)


def build_session(user_agent=USER_AGENT, timeout=DEFAULT_TIMEOUT):
    """Return a ``requests.Session`` with retries and a default timeout.

    ``allowed_methods=None`` means *every* method is retried, including POST.
    This matters because AniList (Phase 5) is GraphQL over POST; urllib3's default
    retry policy skips POST, which would leave those syncs with no retries.
    """
    retry = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=None,  # retry all methods, POST included
        respect_retry_after_header=True,
        raise_on_status=False,
    )
    adapter = _TimeoutHTTPAdapter(max_retries=retry, timeout=timeout)
    session = requests.Session()
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    session.headers["User-Agent"] = user_agent
    return session
