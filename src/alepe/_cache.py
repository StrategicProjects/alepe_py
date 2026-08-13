"""Response cache.

The API sends no ``ETag``, ``Cache-Control`` or ``Last-Modified`` header, so
anything keyed off those would store nothing. This is a small cache of its own,
keyed on the request URL.

It writes to the session's temporary directory by default, so nothing is left
on the user's filesystem without being asked for. Call :func:`cache_dir` with a
path, or set ``ALEPE_CACHE_DIR``, to keep responses between sessions.

The default lifetime is six hours: the published datasets change at most daily,
and ``/licitacoes`` takes half a minute to answer, so re-fetching it inside one
analysis session is pure waiting.
"""

from __future__ import annotations

import hashlib
import os
import pathlib
import tempfile
import time

_DEFAULT_TTL = 6 * 3600.0

_state: dict = {"dir": None, "enabled": True, "ttl": _DEFAULT_TTL}


def default_dir() -> pathlib.Path:
    env = os.environ.get("ALEPE_CACHE_DIR")
    if env:
        return pathlib.Path(env)
    return pathlib.Path(tempfile.gettempdir()) / "alepe-cache"


def cache_dir(path: str | os.PathLike | None = None) -> pathlib.Path:
    """Where cached responses are stored.

    Called with no argument, reports the directory in use. Called with a path,
    switches to it for the rest of the session and creates it.
    """
    if path is not None:
        _state["dir"] = pathlib.Path(path)
    if _state["dir"] is None:
        _state["dir"] = default_dir()
    _state["dir"].mkdir(parents=True, exist_ok=True)
    return _state["dir"]


def enabled() -> bool:
    """Whether responses are being cached."""
    return bool(_state["enabled"])


def set_enabled(value: bool) -> bool:
    """Turn the cache on or off for the rest of the session."""
    _state["enabled"] = bool(value)
    return _state["enabled"]


def ttl() -> float:
    """How long a cached response is considered fresh, in seconds."""
    return float(_state["ttl"])


def set_ttl(seconds: float) -> float:
    """Set how long a cached response is considered fresh."""
    if seconds < 0:
        raise ValueError("ttl must not be negative.")
    _state["ttl"] = float(seconds)
    return _state["ttl"]


def cache_clear() -> int:
    """Delete every cached response. Returns how many files were removed."""
    directory = cache_dir()
    removed = 0
    for entry in directory.glob("*.cache"):
        try:
            entry.unlink()
            removed += 1
        except OSError:
            pass
    return removed


def _key(url: str) -> pathlib.Path:
    digest = hashlib.sha256(url.encode("utf-8")).hexdigest()[:32]
    return cache_dir() / f"{digest}.cache"


def read(url: str) -> bytes | None:
    """The cached body for ``url``, or ``None`` if absent, stale or disabled."""
    if not enabled():
        return None
    path = _key(url)
    try:
        age = time.time() - path.stat().st_mtime
    except OSError:
        return None
    if age > ttl():
        return None
    try:
        return path.read_bytes()
    except OSError:
        return None


def write(url: str, body: bytes) -> None:
    """Store ``body`` as the cached response for ``url``."""
    if not enabled():
        return
    path = _key(url)
    try:
        # Write to a sibling and rename, so a crash mid-write cannot leave a
        # truncated body that a later read would trust.
        tmp = path.with_suffix(".part")
        tmp.write_bytes(body)
        tmp.replace(path)
    except OSError:
        pass
