# Changelog

## 0.1.1

* `set_cache_ttl(0)` now always re-fetches. Stale entries were detected by
  comparing file ages, and on Windows the clock and NTFS timestamps are coarse
  enough that a response written a moment earlier had an age of zero, so it was
  still served.
* Corrected Marcos Wasiliew's e-mail address in the package metadata.

## 0.1.0

Initial release.

* One function per endpoint of the ALEPE open data API — `representatives`,
  `staff`, `positions`, `departments`, `remuneration`, `contracts`,
  `procurements`, `bills`, `indications`, `requests` — each returning a pandas
  frame with snake_case column names and parsed types.
* A Portuguese alias for every one of them, named after the endpoint it wraps
  (`servidores`, `licitacoes`, `projetos`, ...), with Portuguese argument names
  on the propositions aliases.
* Response cache with a six-hour lifetime, `refresh=True` per call, and
  `ALEPE_CACHE_DIR` for keeping responses between sessions.
* Retries on 429 and 5xx with exponential backoff, and a 60-second timeout —
  measured against `/licitacoes`, which takes 25–30 s to answer.
* `AlepeHTTPError` carries the status and URL; `alepe.empty(endpoint)` gives a
  typed empty frame for code that wants the R sibling's behaviour.
