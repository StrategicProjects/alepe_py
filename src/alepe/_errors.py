"""Exceptions raised by alepe.

Every error the package raises inherits from :class:`AlepeError`, so a caller
can catch the whole family with one ``except``. The subclasses exist so that a
caller can tell a bad query from a bad connection without parsing messages.

Note the difference from the R sibling: CRAN's policy on internet resources
requires R packages to warn and return an empty result rather than stop, so
``alepe`` for R returns a zero-row tibble when the API is unreachable. Python
has no such constraint and swallowing a failure would be surprising here, so
this package raises. :func:`~alepe.request` callers who want the R behaviour
can catch :class:`AlepeHTTPError` and fall back to an empty frame.
"""

from __future__ import annotations


class AlepeError(Exception):
    """Base class for every error this package raises."""


class AlepeHTTPError(AlepeError):
    """A non-success HTTP status, or a request that never got a response.

    Attributes
    ----------
    status:
        The HTTP status code, or ``None`` when the request failed before a
        response arrived (timeout, DNS failure, refused connection).
    url:
        The URL that was requested.
    """

    def __init__(self, message: str, status: int | None = None, url: str | None = None) -> None:
        super().__init__(message)
        self.status = status
        self.url = url


class AlepeParseError(AlepeError):
    """A response the package cannot make sense of."""


class AlepeInputError(AlepeError):
    """An argument combination the API cannot express."""
