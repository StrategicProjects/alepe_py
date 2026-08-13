# The API's quirks

The ALEPE open data API is generated from an internal system and shows it. Each
of the quirks below produced a wrong result before it was understood, and each
is handled for you — but knowing they exist explains some of the shapes you
will see in the data.

## Two naming conventions at once

`/servidores` answers with `NOME_LOTACAO`; `/parlamentares` answers with
`nomeParlamentar`; `/contratos` mixes `modalidade` with `vigenciaInicio`. The
package normalises all of them to snake_case without translating the word, so
`nome_lotacao` and `nome_parlamentar` stay traceable to the field they came
from.

## Two number encodings at once

Some fields arrive as Brazilian money strings, `"1.234,56"`. Others arrive as
plain float-formatted strings: `"119267.04"` for a contract value, `"2026.00"`
for a year.

Reading either with a fixed locale corrupts the other. A Brazilian locale reads
`"119267.04"` as 11 926 704 — a contract inflated a hundredfold, silently and
plausibly. The parser decides per value instead: a comma always marks the
decimal, and a dot is a grouping mark only when it separates pure three-digit
groups.

## Dates in three shapes

`dd/mm/yyyy` in the propositions, ISO in some fields, and serialised PHP
`DateTime` objects in others:

```json
{"date": "2026-05-05 00:00:00.000000", "timezone_type": 3, "timezone": "America/Recife"}
```

All three come back as `datetime.date`.

## Propositions are XML inside CSV

`/proposicoes/{projetos,indicacoes,requerimentos}` do not serve JSON. They serve
a CSV with a single column, and that column carries XML: one self-contained
fragment per proposition when listing, one full document when fetching a single
one. The package parses both into ordinary columns.

Free-text fields are HTML, and in `/indicacoes` they are double-encoded
(`&amp;agrave;` for `à`). Markup and entities are stripped, so `ementa` is
plain readable text.

## One very slow endpoint

`/licitacoes` takes 25–30 seconds to answer, and the service cuts its own query
off at 30 seconds. It therefore alternates between a 200 with the full payload
and a bare 500 at exactly the 30-second mark, depending on load. This is why
the default timeout is 60 seconds rather than the usual 30, and why the cache
matters more here than it looks.

## Fields the service publishes empty

At the time of writing, `/licitacoes` returns `valorEstimado`, `vencedor` and
`valorAdjudicado` as null for every process, and `/contratos` fills
`numeroContrato` with the contractor's tax id rather than the contract number.
The package passes both through as published rather than guessing — a wrong
value invented by a client is worse than an honest gap.

## The API blocks datacenter IPs

Requests from GitHub-hosted runners never complete: DNS resolves, but the TCP
handshake to port 443 gets no answer at all. The test suite is therefore fully
offline, running against fixtures that are verbatim samples of real responses.
If you are automating on cloud infrastructure and seeing timeouts, this is
probably why, and it is not something the package can work around.
