"""Administrative contracts and procurement processes."""

from __future__ import annotations

import pandas as pd

from . import _client
from ._parse import to_frame

CONTRACTS_SCHEMA = {
    "modalidade": "str",
    "numero_contrato": "str",
    "ano": "int",
    "contratada": "str",
    "cpf_cnpj": "str",
    "objeto": "str",
    "valor": "float",
    "numero_licitacao": "int",
    "ano_licitacao": "int",
    "vigencia_inicio": "date",
    "vigencia_fim": "date",
}

PROCUREMENTS_SCHEMA = {
    "numero_processo": "int",
    "ano": "int",
    "numero_modalidade": "int",
    "modalidade": "str",
    "objeto": "str",
    "valor_estimado": "float",
    "status": "str",
    "vencedor": "str",
    "valor_adjudicado": "float",
}


def contracts(refresh: bool = False) -> pd.DataFrame:
    """The Assembly's administrative contracts.

    Identifier fields are kept exactly as published, float-formatting artefacts
    included: at the time of writing the service fills ``numeroContrato`` with
    the contractor's tax id rather than the contract number.
    """
    records = _client.fetch_json("contratos", refresh=refresh)
    return to_frame(records, CONTRACTS_SCHEMA)


def procurements(refresh: bool = False) -> pd.DataFrame:
    """The Assembly's procurement processes.

    This is the slowest endpoint of the API: it takes 25-30 s to answer and the
    service cuts its own query off at 30 s, so an occasional failure is the
    service timing out on itself rather than anything local. ``valor_estimado``,
    ``vencedor`` and ``valor_adjudicado`` are published empty for every process
    at the time of writing.
    """
    records = _client.fetch_json("licitacoes", refresh=refresh)
    return to_frame(records, PROCUREMENTS_SCHEMA)
