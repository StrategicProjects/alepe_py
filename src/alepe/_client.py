"""HTTP transport: timeouts, retries, caching and error reporting.

The ALEPE open data API is a plain REST service: one path per dataset, no
authentication, no pagination. What it does have is one very slow endpoint, so
the defaults here are set by measurement rather than habit — see ``timeout``
below.
"""

from __future__ import annotations

import threading
import time
from urllib.parse import urlencode

import requests

from . import _cache
from ._errors import AlepeHTTPError, AlepeParseError

BASE_URL = "https://dadosabertos.alepe.pe.gov.br/api/v1"

# Only these are worth retrying. A 4xx other than 429 is the service rejecting
# the request itself and will fail identically every time.
TRANSIENT = frozenset({429, 500, 502, 503, 504})

_config = {
    # 60 s, not the usual 30: /licitacoes regularly takes 25-30 s to answer and
    # the service cuts it off at 30 s of its own accord, so a 30 s client
    # timeout fails on margin alone rather than on any real fault.
    "timeout": 60.0,
    "max_tries": 3,
    "base_url": BASE_URL,
}

_session_lock = threading.Lock()
_session: requests.Session | None = None


def configure(**options) -> dict:
    """Set connection options for the session, or read them back.

    Parameters
    ----------
    timeout:
        Seconds to wait for a response. Default 60.
    max_tries:
        How many attempts a request gets before giving up. Default 3.
    base_url:
        The API root, for pointing the package at a mirror or a test double.

    Returns
    -------
    dict
        The configuration after applying the changes.
    """
    unknown = set(options) - set(_config)
    if unknown:
        raise ValueError(f"Unknown option(s): {', '.join(sorted(unknown))}.")
    _config.update({k: v for k, v in options.items() if v is not None})
    return dict(_config)


def _user_agent() -> str:
    from . import __version__

    return f"alepe/{__version__} (https://github.com/StrategicProjects/alepe_py)"


def session() -> requests.Session:
    global _session
    with _session_lock:
        if _session is None:
            _session = requests.Session()
            _session.headers.update({"User-Agent": _user_agent()})
        return _session


def build_url(endpoint: str, params: dict | None = None) -> str:
    """The full URL for an endpoint, with ``None`` parameters dropped."""
    query = {k: v for k, v in (params or {}).items() if v is not None}
    url = f"{_config['base_url']}/{endpoint.strip('/')}/"
    if query:
        url = f"{url}?{urlencode(query)}"
    return url


def fetch(endpoint: str, params: dict | None = None, refresh: bool = False) -> bytes:
    """Fetch an endpoint and return the raw body.

    Retries 429 and 5xx with exponential backoff, serves from the cache when a
    fresh copy is there, and raises :class:`~alepe._errors.AlepeHTTPError` when
    the service cannot be reached or answers with an error.
    """
    url = build_url(endpoint, params)

    if not refresh:
        cached = _cache.read(url)
        if cached is not None:
            return cached

    tries = max(1, int(_config["max_tries"]))
    last_error: str = ""
    last_status: int | None = None

    for attempt in range(1, tries + 1):
        try:
            response = session().get(url, timeout=_config["timeout"])
        except requests.RequestException as exc:
            last_error, last_status = str(exc), None
        else:
            if response.status_code < 400:
                _cache.write(url, response.content)
                return response.content
            last_status = response.status_code
            last_error = f"HTTP {response.status_code} {response.reason}"
            if response.status_code not in TRANSIENT:
                break

        if attempt < tries:
            time.sleep(2**attempt)

    raise AlepeHTTPError(
        f"Could not fetch {url}: {last_error}. "
        "The service may be temporarily unavailable; try again later.",
        status=last_status,
        url=url,
    )


def fetch_json(endpoint: str, params: dict | None = None, refresh: bool = False) -> list:
    """Fetch an endpoint and parse it as a JSON list of records."""
    import json

    body = fetch(endpoint, params, refresh=refresh)
    try:
        data = json.loads(body)
    except ValueError as exc:
        raise AlepeParseError(f"Could not parse the response of {endpoint} as JSON: {exc}") from exc
    if isinstance(data, dict):
        data = [data]
    if not isinstance(data, list):
        raise AlepeParseError(
            f"Expected a list of records from {endpoint}, got {type(data).__name__}."
        )
    return data


def fetch_text(endpoint: str, params: dict | None = None, refresh: bool = False) -> str:
    """Fetch an endpoint and decode it as UTF-8 text."""
    body = fetch(endpoint, params, refresh=refresh)
    return body.decode("utf-8", errors="replace")
