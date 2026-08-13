"""Representatives, staff, positions, departments and remuneration."""

from __future__ import annotations

import pandas as pd

from . import _client
from ._parse import to_frame

REPRESENTATIVES_SCHEMA = {"nome_parlamentar": "str", "partido": "str"}

STAFF_SCHEMA = {
    "nome": "str",
    "codigo_lotacao": "str",
    "nome_lotacao": "str",
    "cargo_efetivo": "str",
    "cargo_nivel": "str",
    "vinculo": "str",
    "data_admissao": "date",
}

POSITIONS_SCHEMA = {"total": "int", "cargo_nivel": "str"}

DEPARTMENTS_SCHEMA = {"total": "int", "nome_lotacao": "str", "vinculo": "str"}

REMUNERATION_SCHEMA = {
    "cargo": "str",
    "remuneracao": "float",
    "tipo_cargo": "str",
    "mes_competencia": "int",
    "ano_competencia": "int",
}

_STATUS = {
    "permanent": "efetivo",
    "commissioned": "comissionado",
    "seconded": "a-disposicao",
    "efetivo": "efetivo",
    "comissionado": "comissionado",
    "a-disposicao": "a-disposicao",
}


def map_status(status: str | None) -> str | None:
    """Translate an employment-status filter to the API's ``vinculo`` value.

    Accepts the English vocabulary and the original API terms alike, so
    ``"permanent"`` and ``"efetivo"`` are the same query.
    """
    if status is None:
        return None
    try:
        return _STATUS[status]
    except KeyError:
        raise ValueError(
            f"Unknown status {status!r}. Use one of: {', '.join(sorted(_STATUS))}."
        ) from None


def representatives(refresh: bool = False) -> pd.DataFrame:
    """Members of the current legislature, with name and party."""
    records = _client.fetch_json("parlamentares", refresh=refresh)
    return to_frame(records, REPRESENTATIVES_SCHEMA)


def staff(status: str | None = None, refresh: bool = False) -> pd.DataFrame:
    """The Assembly's staff roster, optionally filtered by employment status."""
    records = _client.fetch_json("servidores", {"vinculo": map_status(status)}, refresh=refresh)
    return to_frame(records, STAFF_SCHEMA)


def positions(status: str | None = None, refresh: bool = False) -> pd.DataFrame:
    """Staff counts per position and level."""
    records = _client.fetch_json("cargos", {"vinculo": map_status(status)}, refresh=refresh)
    return to_frame(records, POSITIONS_SCHEMA)


def departments(refresh: bool = False) -> pd.DataFrame:
    """Active staff counts per department and employment status.

    The reference period is fixed by the API, and retired staff are excluded.
    """
    records = _client.fetch_json("lotacoes", refresh=refresh)
    return to_frame(records, DEPARTMENTS_SCHEMA)


def remuneration(refresh: bool = False) -> pd.DataFrame:
    """Published remuneration per position, for the current reference month."""
    records = _client.fetch_json("remuneracao", refresh=refresh)
    return to_frame(records, REMUNERATION_SCHEMA)
