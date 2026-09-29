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

# Only /servidores honours efetivo-cedido; /cargos ignores it and returns every
# status, as it does for any unknown value, so positions() must refuse it.
_STAFF_STATUS = {**_STATUS, "lent": "efetivo-cedido", "efetivo-cedido": "efetivo-cedido"}


def map_status(status: str | None, lent: bool = False) -> str | None:
    """Translate an employment-status filter to the API's ``vinculo`` value.

    Accepts the English vocabulary and the original API terms alike, so
    ``"permanent"`` and ``"efetivo"`` are the same query. ``lent`` also allows
    ``"lent"`` / ``"efetivo-cedido"``, which only the staff endpoint supports.
    """
    if status is None:
        return None
    table = _STAFF_STATUS if lent else _STATUS
    try:
        return table[status]
    except KeyError:
        raise ValueError(
            f"Unknown status {status!r}. Use one of: {', '.join(sorted(table))}."
        ) from None


def representatives(refresh: bool = False) -> pd.DataFrame:
    """Members of the current legislature, with name and party."""
    records = _client.fetch_json("parlamentares", refresh=refresh)
    return to_frame(records, REPRESENTATIVES_SCHEMA)


def staff(status: str | None = None, refresh: bool = False) -> pd.DataFrame:
    """The Assembly's staff roster, optionally filtered by employment status.

    ``status`` is ``"permanent"``, ``"commissioned"``, ``"seconded"`` (staff from
    other bodies placed at the Assembly's disposal) or ``"lent"`` (the Assembly's
    own permanent staff lent to other bodies, a subset of ``"permanent"``); the
    API terms ``"efetivo"``, ``"comissionado"``, ``"a-disposicao"`` and
    ``"efetivo-cedido"`` work too. Lent staff are published with ``vinculo``
    ``"Efetivo"``, so this filter is the only way to tell them apart.
    """
    records = _client.fetch_json(
        "servidores", {"vinculo": map_status(status, lent=True)}, refresh=refresh
    )
    return to_frame(records, STAFF_SCHEMA)


def positions(status: str | None = None, refresh: bool = False) -> pd.DataFrame:
    """Staff counts per position and level.

    ``status`` takes the same values as :func:`staff` except ``"lent"``, which
    the API ignores for this endpoint.
    """
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
