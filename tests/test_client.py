"""Transport behaviour: retries, caching and error reporting."""

from __future__ import annotations

import pytest
import requests
import responses

import alepe
from alepe import _cache, _client

URL = "https://dadosabertos.alepe.pe.gov.br/api/v1/parlamentares/"


@responses.activate
def test_transient_status_is_retried_then_succeeds(monkeypatch):
    monkeypatch.setattr(_client.time, "sleep", lambda _s: None)
    responses.add(responses.GET, URL, status=503)
    responses.add(responses.GET, URL, json=[{"nomeParlamentar": "A", "partido": "P"}])

    frame = alepe.representatives(refresh=True)
    assert len(responses.calls) == 2
    assert frame["nome_parlamentar"].iloc[0] == "A"


@responses.activate
def test_client_error_is_not_retried(monkeypatch):
    monkeypatch.setattr(_client.time, "sleep", lambda _s: None)
    responses.add(responses.GET, URL, status=404)

    with pytest.raises(alepe.AlepeHTTPError) as excinfo:
        alepe.representatives(refresh=True)

    assert len(responses.calls) == 1
    assert excinfo.value.status == 404


@responses.activate
def test_connection_failure_raises_with_no_status(monkeypatch):
    monkeypatch.setattr(_client.time, "sleep", lambda _s: None)
    responses.add(responses.GET, URL, body=requests.ConnectionError("boom"))

    with pytest.raises(alepe.AlepeHTTPError) as excinfo:
        alepe.representatives(refresh=True)

    assert excinfo.value.status is None
    assert excinfo.value.url == URL


@responses.activate
def test_unparseable_body_raises_parse_error():
    responses.add(responses.GET, URL, body="not json at all")
    with pytest.raises(alepe.AlepeParseError):
        alepe.representatives(refresh=True)


@responses.activate
def test_second_call_is_served_from_cache():
    responses.add(responses.GET, URL, json=[{"nomeParlamentar": "A", "partido": "P"}])

    alepe.representatives()
    alepe.representatives()

    assert len(responses.calls) == 1


@responses.activate
def test_refresh_bypasses_the_cache():
    responses.add(responses.GET, URL, json=[{"nomeParlamentar": "A", "partido": "P"}])

    alepe.representatives()
    alepe.representatives(refresh=True)

    assert len(responses.calls) == 2


@responses.activate
def test_stale_entries_are_refetched(monkeypatch):
    responses.add(responses.GET, URL, json=[{"nomeParlamentar": "A", "partido": "P"}])

    alepe.representatives()
    monkeypatch.setitem(_cache._state, "ttl", 0.0)
    alepe.representatives()

    assert len(responses.calls) == 2


def test_configure_rejects_unknown_options():
    with pytest.raises(ValueError):
        alepe.configure(nonsense=1)


def test_default_timeout_clears_the_slow_endpoint():
    # /licitacoes needs 25-30 s; a 30 s timeout failed on margin alone.
    assert _client.configure()["timeout"] >= 60
