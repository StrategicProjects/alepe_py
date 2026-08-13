"""Endpoint functions against verbatim samples of real API responses."""

from __future__ import annotations

import pandas as pd
import pytest

import alepe
from alepe import _client


@pytest.fixture
def serve_json(monkeypatch, fixture_json):
    def _serve(name):
        records = fixture_json(name)
        monkeypatch.setattr(_client, "fetch_json", lambda *a, **k: records)
        return records

    return _serve


@pytest.fixture
def serve_text(monkeypatch, fixture_text):
    def _serve(name):
        text = fixture_text(name)
        monkeypatch.setattr(_client, "fetch_text", lambda *a, **k: text)
        return text

    return _serve


def test_representatives(serve_json):
    serve_json("parlamentares.json")
    frame = alepe.representatives()
    assert list(frame.columns) == ["nome_parlamentar", "partido"]
    assert frame["nome_parlamentar"].iloc[0] == "Abimael Santos"


def test_staff_parses_the_nested_admission_date(serve_json):
    serve_json("servidores.json")
    frame = alepe.staff()
    assert list(frame.columns) == [
        "nome",
        "codigo_lotacao",
        "nome_lotacao",
        "cargo_efetivo",
        "cargo_nivel",
        "vinculo",
        "data_admissao",
    ]
    assert frame["data_admissao"].notna().all()


def test_positions_and_departments(serve_json):
    serve_json("cargos.json")
    positions = alepe.positions()
    assert positions["total"].dtype == "Int64"
    assert (positions["total"] > 0).all()

    serve_json("lotacoes.json")
    departments = alepe.departments()
    assert list(departments.columns) == ["total", "nome_lotacao", "vinculo"]


def test_remuneration_reads_dot_decimals(serve_json):
    serve_json("remuneracao.json")
    frame = alepe.remuneration()
    # "11685.70" must not become 1168570
    assert frame["remuneracao"].iloc[0] == pytest.approx(11685.70)
    assert frame["ano_competencia"].dtype == "Int64"


def test_contracts_read_values_years_and_dates(serve_json):
    serve_json("contratos.json")
    frame = alepe.contracts()
    assert frame["valor"].iloc[0] == pytest.approx(119267.04)
    assert frame["ano"].iloc[0] == 2026
    assert frame["vigencia_inicio"].notna().all()
    assert (frame["vigencia_fim"] >= frame["vigencia_inicio"]).all()


def test_procurements(serve_json):
    serve_json("licitacoes.json")
    frame = alepe.procurements()
    assert list(frame.columns) == [
        "numero_processo",
        "ano",
        "numero_modalidade",
        "modalidade",
        "objeto",
        "valor_estimado",
        "status",
        "vencedor",
        "valor_adjudicado",
    ]
    assert frame["numero_processo"].dtype == "Int64"


def test_bills_listing(serve_text):
    serve_text("projetos.csv")
    frame = alepe.bills(year=2024)
    assert list(frame.columns) == [
        "docid",
        "numero",
        "ano",
        "legislatura",
        "tipo",
        "subtipo",
        "ementa",
        "data_publicacao",
        "autores",
    ]
    assert frame["ano"].iloc[0] == 2024
    assert frame["legislatura"].iloc[0] == "VIGÉSIMA"
    assert not frame["ementa"].str.contains("<").any()


def test_indications_listing_strips_double_encoded_html(serve_text):
    serve_text("indicacoes.csv")
    frame = alepe.indications(year=2024)
    assert len(frame) > 0
    assert not frame["ementa"].str.contains("&lt;|&amp;|<p").any()
    assert frame["autores"].notna().all()


def test_bills_detail(serve_text):
    serve_text("projeto_detalhe.csv")
    frame = alepe.bills(number=3, year=2024)
    assert len(frame) == 1
    row = frame.iloc[0]
    assert row["numero"] == 3
    assert row["autores"] == "Coronel Alberto Feitosa"
    assert row["regime_tramitacao"] == "Ordinária"
    assert row["data_publicacao"] == pd.Timestamp("2024-06-14").date()
    assert row["materia"].startswith("Art. 1")


def test_detail_mode_needs_year_with_number():
    with pytest.raises(alepe.AlepeInputError):
        alepe.bills(number=10)


def test_status_filter_accepts_both_vocabularies(serve_json):
    serve_json("servidores.json")
    assert alepe.staff(status="permanent").equals(alepe.staff(status="efetivo"))
    with pytest.raises(ValueError):
        alepe.staff(status="nope")


def test_portuguese_aliases_reach_the_same_functions(serve_json, serve_text):
    serve_json("servidores.json")
    assert alepe.servidores().equals(alepe.staff())

    serve_text("projetos.csv")
    assert alepe.projetos(ano=2024).equals(alepe.bills(year=2024))

    for alias in (
        "parlamentares",
        "servidores",
        "cargos",
        "lotacoes",
        "remuneracao",
        "contratos",
        "licitacoes",
        "projetos",
        "indicacoes",
        "requerimentos",
        "limpar_cache",
    ):
        assert callable(getattr(alepe, alias))


def test_empty_returns_a_typed_frame_for_each_endpoint():
    frame = alepe.empty("procurements")
    assert len(frame) == 0
    assert list(frame.columns) == list(alepe.PROCUREMENTS_SCHEMA)
    assert frame["valor_estimado"].dtype == "Float64"

    with pytest.raises(ValueError):
        alepe.empty("nope")
