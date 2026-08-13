# Reference

## Endpoints

Every function returns a pandas `DataFrame`. Pass `refresh=True` to any of them
to bypass the response cache for that call.

::: alepe.representatives
::: alepe.staff
::: alepe.positions
::: alepe.departments
::: alepe.remuneration
::: alepe.contracts
::: alepe.procurements
::: alepe.bills
::: alepe.indications
::: alepe.requests

## Portuguese aliases

Each endpoint has an alias named after the endpoint it wraps, so a pipeline can
stay in Portuguese end to end. `parlamentares`, `servidores`, `cargos`,
`lotacoes`, `remuneracao`, `contratos` and `licitacoes` are the same objects as
their English counterparts; the propositions aliases translate the argument
names as well.

::: alepe.projetos
::: alepe.indicacoes
::: alepe.requerimentos

## Configuration

::: alepe.configure
::: alepe.cache_dir
::: alepe.cache_clear
::: alepe.empty

## Errors

::: alepe.AlepeError
::: alepe.AlepeHTTPError
::: alepe.AlepeParseError
::: alepe.AlepeInputError
