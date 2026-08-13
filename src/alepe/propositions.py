"""Bills, indications and requests.

These three endpoints do not serve JSON. They serve CSV whose single column
carries XML: one self-contained fragment per proposition in listing mode, one
full document in detail mode. Both shapes are parsed here into ordinary frames,
with markup and entities stripped from the free-text fields.
"""

from __future__ import annotations

import csv
import io

import pandas as pd

from . import _client
from ._errors import AlepeInputError
from ._parse import authors, element_text, empty_frame, root_attributes, strip_html, to_frame

LISTING_SCHEMA = {
    "docid": "int",
    "numero": "int",
    "ano": "int",
    "legislatura": "str",
    "tipo": "str",
    "subtipo": "str",
    "ementa": "str",
    "data_publicacao": "date",
    "autores": "str",
}

DETAIL_SCHEMA = {
    "numero": "int",
    "ano": "int",
    "legislatura": "str",
    "tipo": "str",
    "autores": "str",
    "ementa": "str",
    "materia": "str",
    "justificativa": "str",
    "regime_tramitacao": "str",
    "impacto_orcamentario": "str",
    "resultado_final": "str",
    "data_publicacao": "date",
    "numero_dpl": "int",
    "lotacao_atual": "str",
}

_DETAIL_TAGS = {
    "ementa": "ementa",
    "materia": "materia",
    "justificativa": "justificativa",
    "regime_tramitacao": "regimeTramitacao",
    "impacto_orcamentario": "impactoOrcamentario",
    "resultado_final": "resultadoFinal",
    "data_publicacao": "dataPublicacao",
    "numero_dpl": "numeroDpl",
    "lotacao_atual": "lotacaoAtual",
}


def _cells(text: str) -> list[str]:
    reader = csv.reader(io.StringIO(text))
    rows = list(reader)
    if not rows:
        return []
    return [row[0] for row in rows[1:] if row]


def parse_listing(text: str) -> pd.DataFrame:
    """Parse listing-mode CSV into one row per proposition."""
    # The last row of these files is blank; keying on docid drops it without
    # having to care how many trailing rows the service adds.
    cells = [cell for cell in _cells(text) if 'docid="' in cell]
    if not cells:
        return empty_frame(LISTING_SCHEMA)

    records = []
    for cell in cells:
        record = root_attributes(cell)
        record["autores"] = authors(cell)
        records.append(record)

    frame = to_frame(records, LISTING_SCHEMA)
    frame["legislatura"] = frame["legislatura"].str.strip()
    frame["ementa"] = frame["ementa"].map(strip_html).astype("string")
    return frame


def parse_detail(text: str) -> pd.DataFrame:
    """Parse detail-mode CSV into a single row."""
    document = "\n".join(_cells(text))
    if not document.strip():
        return empty_frame(DETAIL_SCHEMA)

    body = document.split("?>", 1)[-1].lstrip()
    record = root_attributes(body)
    record["autores"] = authors(body)
    for column, tag in _DETAIL_TAGS.items():
        record[column] = element_text(body, tag)

    frame = to_frame([record], DETAIL_SCHEMA)
    frame["legislatura"] = frame["legislatura"].str.strip()
    for column in ("ementa", "materia", "justificativa"):
        frame[column] = frame[column].map(strip_html).astype("string")
    return frame


def _propositions(
    kind: str,
    number: int | None,
    year: int | None,
    legislature: int | None,
    refresh: bool,
) -> pd.DataFrame:
    if number is not None and year is None:
        raise AlepeInputError(
            "number requires year: the detail mode of the propositions API "
            "selects a single proposition by number and year together."
        )

    text = _client.fetch_text(
        f"proposicoes/{kind}",
        {"numero": number, "ano": year, "legislatura": legislature, "formato": "csv"},
        refresh=refresh,
    )
    return parse_detail(text) if number is not None else parse_listing(text)


def bills(
    number: int | None = None,
    year: int | None = None,
    legislature: int | None = None,
    refresh: bool = False,
) -> pd.DataFrame:
    """Bills (``projetos de lei``).

    Pass ``number`` together with ``year`` for the full record of a single
    proposition; pass ``year`` and/or ``legislature`` to list summaries. With no
    filter at all the API defaults to the current year.
    """
    return _propositions("projetos", number, year, legislature, refresh)


def indications(
    number: int | None = None,
    year: int | None = None,
    legislature: int | None = None,
    refresh: bool = False,
) -> pd.DataFrame:
    """Indications (``indicações``). Same two query modes as :func:`bills`."""
    return _propositions("indicacoes", number, year, legislature, refresh)


def requests(
    number: int | None = None,
    year: int | None = None,
    legislature: int | None = None,
    refresh: bool = False,
) -> pd.DataFrame:
    """Requests (``requerimentos``). Same two query modes as :func:`bills`."""
    return _propositions("requerimentos", number, year, legislature, refresh)
