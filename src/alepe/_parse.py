"""Turning API payloads into typed frames.

The ALEPE API is generated from an internal system and shows it. Three quirks
drive everything in this module, and each one cost a wrong result before it was
understood:

* Field names come in two conventions at once — ``NOME_LOTACAO`` from
  ``/servidores``, ``nomeParlamentar`` from ``/parlamentares``.
* Numbers come in two encodings at once — ``"1.234,56"`` in free text and
  float-formatted strings such as ``"119267.04"`` or ``"2026.00"`` in the money
  endpoints. Reading either with a fixed locale corrupts the other: a Brazilian
  locale turns ``"119267.04"`` into 11 926 704.
* Dates arrive either as ``dd/mm/yyyy`` strings or as serialised PHP DateTime
  objects, ``{"date": "2026-05-05 00:00:00.000000", "timezone": ...}``.
"""

from __future__ import annotations

import html
import re
import unicodedata

import pandas as pd

_CAMEL = re.compile(r"([a-z0-9])([A-Z])")
_NON_ALNUM = re.compile(r"[^a-z0-9]+")
_GROUPED = re.compile(r"^-?\d{1,3}(\.\d{3})+$")
_TAG = re.compile(r"<[^>]+>")
_WS = re.compile(r"\s+")


def clean_name(name: str) -> str:
    """Normalise one API field name to snake_case, keeping the Portuguese word.

    Accents are stripped by decomposition rather than by a locale-dependent
    transliteration, so the result does not depend on the machine's locale.
    """
    text = _CAMEL.sub(r"\1_\2", str(name))
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = _NON_ALNUM.sub("_", text.lower())
    return text.strip("_")


def clean_names(names) -> list[str]:
    """Normalise a sequence of field names."""
    return [clean_name(n) for n in names]


def parse_number(value) -> float:
    """Parse the two numeric encodings the API mixes.

    A comma always marks the decimal. Without a comma, a dot is a grouping mark
    only when it separates pure three-digit groups (``"12.345.678"``);
    otherwise it is the decimal point (``"119267.04"``).
    """
    if value is None or isinstance(value, bool):
        return float("nan")
    if isinstance(value, (int, float)):
        return float(value)

    text = re.sub(r"[^0-9.,-]", "", str(value))
    if not text:
        return float("nan")

    if "," in text:
        text = text.replace(".", "").replace(",", ".", 1)
    elif _GROUPED.match(text):
        text = text.replace(".", "")

    try:
        return float(text)
    except ValueError:
        return float("nan")


def parse_date(value):
    """Parse ``dd/mm/yyyy``, ISO, or a serialised DateTime object."""
    if isinstance(value, dict):
        value = value.get("date")
    if value is None:
        return pd.NaT

    text = str(value).strip()
    if re.match(r"^\d{4}-\d{2}-\d{2}", text):
        return pd.Timestamp(text[:10])
    if re.match(r"^\d{2}/\d{2}/\d{4}", text):
        day, month, year = text[:10].split("/")
        return pd.Timestamp(f"{year}-{month}-{day}")
    return pd.NaT


def strip_html(text) -> str:
    """Remove markup and decode entities from a free-text field.

    Proposition summaries arrive as HTML, and those of ``/indicacoes`` arrive
    double-encoded (``&amp;agrave;``), so entities are decoded twice before the
    tags come out.
    """
    if text is None:
        return ""
    out = html.unescape(html.unescape(str(text)))
    out = _TAG.sub(" ", out)
    out = html.unescape(out)
    return _WS.sub(" ", out).strip()


def _scalar(record: dict, field: str):
    """Look a cleaned field name up in a record with raw API names."""
    for key, value in record.items():
        if clean_name(key) == field:
            return value
    return None


def to_frame(records: list, schema: dict) -> pd.DataFrame:
    """Build a typed frame from a list of API records.

    ``schema`` maps cleaned column names to ``"str"``, ``"int"``, ``"float"``
    or ``"date"``. Columns absent from the payload come back as missing values
    rather than disappearing, so the shape of the frame does not depend on what
    the API happened to send.
    """
    columns: dict[str, list] = {name: [] for name in schema}

    for record in records:
        if not isinstance(record, dict):
            raise TypeError(f"Expected a record mapping, got {type(record).__name__}.")
        for name in schema:
            columns[name].append(_scalar(record, name))

    frame = pd.DataFrame(columns)
    return _cast(frame, schema)


def _cast(frame: pd.DataFrame, schema: dict) -> pd.DataFrame:
    for name, kind in schema.items():
        column = frame[name]
        if kind == "int":
            # Round first: years and process numbers arrive float-formatted
            # ("2026.00"), and truncating them would be off by one on any value
            # the service renders as "n.99".
            frame[name] = column.map(parse_number).round().astype("Int64")
        elif kind == "float":
            frame[name] = column.map(parse_number).astype("Float64")
        elif kind == "date":
            frame[name] = pd.to_datetime(column.map(parse_date)).dt.date
        else:
            frame[name] = column.map(lambda v: None if v is None else str(v)).astype("string")
    return frame


def empty_frame(schema: dict) -> pd.DataFrame:
    """An empty frame with the schema's columns and types."""
    return to_frame([], schema)


# --- propositions: XML inside a CSV column -------------------------------
#
# The propositions endpoints answer CSV whose single column carries XML: one
# self-contained fragment per row in listing mode, one document in detail mode.
# The fragments are machine-generated, flat and attribute-quoted, so regular
# expressions are enough and lxml stays out of the dependency list.

_ATTR = re.compile(r'([A-Za-z][\w.-]*)="([^"]*)"')
_AUTHOR = re.compile(r'<autor\s[^>]*nome="([^"]*)"')


def root_attributes(fragment: str) -> dict:
    """The attributes of the first tag of an XML fragment."""
    head = fragment.split(">", 1)[0]
    return {key: html.unescape(value) for key, value in _ATTR.findall(head)}


def authors(fragment: str) -> str | None:
    """The ``nome`` of every ``<autor>``, joined with ``"; "``."""
    names = [html.unescape(name) for name in _AUTHOR.findall(fragment)]
    return "; ".join(names) if names else None


def element_text(document: str, tag: str) -> str | None:
    """The text of a leaf element, or ``None`` when it is absent."""
    match = re.search(rf"<{tag}(?:\s[^>]*)?>(.*?)</{tag}>", document, re.DOTALL)
    if match is None:
        return None
    return html.unescape(match.group(1))
