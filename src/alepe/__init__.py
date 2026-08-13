"""Access the open data API of the Legislative Assembly of Pernambuco.

ALEPE publishes its representatives, staff, payroll, contracts, procurement and
legislative propositions at https://dadosabertos.alepe.pe.gov.br. This package
wraps every documented endpoint, one function each, returning a pandas
``DataFrame`` with snake_case column names and parsed types::

    import alepe

    alepe.representatives()
    alepe.staff(status="permanent")
    alepe.contracts()
    alepe.bills(year=2024)

Column names keep the official Portuguese field names, normalised to
snake_case, so a result stays traceable to its source. Filter *values* accept
both vocabularies: ``staff(status="permanent")`` and ``staff(status="efetivo")``
are the same query. Every function also has a Portuguese alias named after the
endpoint it wraps — ``servidores()``, ``licitacoes()``, ``projetos()`` — for
keeping a pipeline in one language.

Responses are cached for six hours, and failed requests are retried with
exponential backoff. Unlike the R sibling, which CRAN policy requires to warn
and return an empty result, this package raises
:class:`~alepe.AlepeHTTPError` when the API cannot be reached.
"""

from __future__ import annotations

__version__ = "0.1.0"

from ._cache import cache_clear, cache_dir
from ._cache import enabled as cache_enabled
from ._cache import set_enabled as set_cache
from ._cache import set_ttl as set_cache_ttl
from ._cache import ttl as cache_ttl
from ._client import configure
from ._errors import AlepeError, AlepeHTTPError, AlepeInputError, AlepeParseError
from ._parse import empty_frame as _empty_frame
from .money import CONTRACTS_SCHEMA, PROCUREMENTS_SCHEMA, contracts, procurements
from .people import (
    DEPARTMENTS_SCHEMA,
    POSITIONS_SCHEMA,
    REMUNERATION_SCHEMA,
    REPRESENTATIVES_SCHEMA,
    STAFF_SCHEMA,
    departments,
    positions,
    remuneration,
    representatives,
    staff,
)
from .propositions import DETAIL_SCHEMA, LISTING_SCHEMA, bills, indications, requests

_SCHEMAS = {
    "representatives": REPRESENTATIVES_SCHEMA,
    "staff": STAFF_SCHEMA,
    "positions": POSITIONS_SCHEMA,
    "departments": DEPARTMENTS_SCHEMA,
    "remuneration": REMUNERATION_SCHEMA,
    "contracts": CONTRACTS_SCHEMA,
    "procurements": PROCUREMENTS_SCHEMA,
    "bills": LISTING_SCHEMA,
    "indications": LISTING_SCHEMA,
    "requests": LISTING_SCHEMA,
    "proposition_detail": DETAIL_SCHEMA,
}


def empty(endpoint: str):
    """A correctly typed empty frame for an endpoint.

    Useful as a fallback when :class:`AlepeHTTPError` is caught and the code
    downstream still expects the columns to be there — which is what the R
    sibling returns of its own accord, CRAN policy requiring it.
    """
    try:
        schema = _SCHEMAS[endpoint]
    except KeyError:
        raise ValueError(
            f"Unknown endpoint {endpoint!r}. Use one of: {', '.join(sorted(_SCHEMAS))}."
        ) from None
    return _empty_frame(schema)


# --- Portuguese aliases ---------------------------------------------------
#
# Named after the API endpoint each one wraps, so a pipeline can stay in
# Portuguese end to end. The propositions aliases translate the argument names
# too, which is why they are written out rather than assigned.

parlamentares = representatives
servidores = staff
cargos = positions
lotacoes = departments
remuneracao = remuneration
contratos = contracts
licitacoes = procurements
limpar_cache = cache_clear


def projetos(numero=None, ano=None, legislatura=None, refresh=False):
    """Alias de :func:`bills`, com argumentos em português."""
    return bills(number=numero, year=ano, legislature=legislatura, refresh=refresh)


def indicacoes(numero=None, ano=None, legislatura=None, refresh=False):
    """Alias de :func:`indications`, com argumentos em português."""
    return indications(number=numero, year=ano, legislature=legislatura, refresh=refresh)


def requerimentos(numero=None, ano=None, legislatura=None, refresh=False):
    """Alias de :func:`requests`, com argumentos em português."""
    return requests(number=numero, year=ano, legislature=legislatura, refresh=refresh)


__all__ = [
    "__version__",
    # endpoints
    "representatives",
    "staff",
    "positions",
    "departments",
    "remuneration",
    "contracts",
    "procurements",
    "bills",
    "indications",
    "requests",
    # Portuguese aliases
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
    # helpers
    "empty",
    # configuration
    "configure",
    "cache_dir",
    "cache_clear",
    "cache_enabled",
    "cache_ttl",
    "set_cache",
    "set_cache_ttl",
    # errors
    "AlepeError",
    "AlepeHTTPError",
    "AlepeInputError",
    "AlepeParseError",
]
