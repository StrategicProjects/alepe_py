"""The parsing rules, which is where this API's quirks live."""

from __future__ import annotations

import math

import pandas as pd
import pytest

from alepe._parse import clean_name, parse_date, parse_number, strip_html, to_frame


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("NOME_LOTACAO", "nome_lotacao"),
        ("CARGO NÍVEL", "cargo_nivel"),
        ("CPF/CNPJ ", "cpf_cnpj"),
        ("nomeParlamentar", "nome_parlamentar"),
        ("cpfCnpj", "cpf_cnpj"),
        ("vigenciaInicio", "vigencia_inicio"),
        ("dataPublicacao", "data_publicacao"),
    ],
)
def test_clean_name_handles_both_naming_conventions(raw, expected):
    assert clean_name(raw) == expected


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("1.234,56", 1234.56),  # Brazilian money string
        ("119267.04", 119267.04),  # plain float string
        ("2026.00", 2026.0),  # float-formatted integer
        ("R$ 10,50", 10.5),  # currency prefix
        ("12.345.678", 12345678.0),  # pure 3-digit groups: grouping dots
        ("256", 256.0),
        (11685.70, 11685.70),
    ],
)
def test_parse_number_handles_both_encodings(raw, expected):
    assert parse_number(raw) == pytest.approx(expected)


def test_parse_number_returns_nan_for_empty_and_junk():
    assert math.isnan(parse_number(""))
    assert math.isnan(parse_number(None))
    assert math.isnan(parse_number("n/a"))


def test_parse_date_accepts_every_shape_the_api_sends():
    assert parse_date("14/06/2024") == pd.Timestamp("2024-06-14")
    assert parse_date("2026-05-05 00:00:00.000000") == pd.Timestamp("2026-05-05")
    nested = {"date": "2026-05-05 00:00:00.000000", "timezone": "America/Recife"}
    assert parse_date(nested) == pd.Timestamp("2026-05-05")
    assert pd.isna(parse_date(None))


def test_strip_html_decodes_double_encoded_entities():
    # This is how an indicacao ementa actually arrives.
    raw = "&lt;p&gt;Indicamos &amp;agrave; Mesa&lt;/p&gt;"
    assert strip_html(raw) == "Indicamos à Mesa"


def test_to_frame_types_columns_and_fills_missing_fields():
    schema = {"nome": "str", "total": "int", "valor": "float", "inicio": "date"}
    records = [
        {"NOME": "ANA", "TOTAL": "12", "VALOR": "1.234,56", "INICIO": "01/02/2024"},
        {"NOME": "BIA", "TOTAL": "3", "VALOR": "10,00"},  # no INICIO
    ]
    frame = to_frame(records, schema)

    assert list(frame.columns) == ["nome", "total", "valor", "inicio"]
    assert frame["total"].tolist() == [12, 3]
    assert frame["valor"].tolist() == pytest.approx([1234.56, 10.0])
    assert frame["inicio"].iloc[0].isoformat() == "2024-02-01"
    assert pd.isna(frame["inicio"].iloc[1])


def test_to_frame_of_no_records_keeps_the_schema():
    schema = {"nome": "str", "total": "int"}
    frame = to_frame([], schema)
    assert list(frame.columns) == ["nome", "total"]
    assert len(frame) == 0
