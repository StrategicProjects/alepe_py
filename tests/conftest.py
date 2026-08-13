"""Test fixtures.

The payloads under ``fixtures/`` are verbatim samples of real API responses,
captured on 2026-08-13 and shared with the R sibling so that both packages are
tested against exactly the same bytes. Nothing here touches the network.
"""

from __future__ import annotations

import json
import pathlib

import pytest

FIXTURES = pathlib.Path(__file__).parent / "fixtures"


@pytest.fixture
def fixture_json():
    def _load(name: str) -> list:
        return json.loads((FIXTURES / name).read_text(encoding="utf-8"))

    return _load


@pytest.fixture
def fixture_text():
    def _load(name: str) -> str:
        return (FIXTURES / name).read_text(encoding="utf-8")

    return _load


@pytest.fixture(autouse=True)
def no_cache(tmp_path, monkeypatch):
    """Point the cache at a throwaway directory for every test."""
    from alepe import _cache

    monkeypatch.setitem(_cache._state, "dir", tmp_path / "cache")
    yield
