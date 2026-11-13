"""Filters and sorting on any column of a report table, applied to the rows the
report already built, so the table and its CSV export always show the same rows.

Query parameters (one or more, combined with AND):
  q.<column>=text        text contains (case-insensitive)
  in.<column>=a,b        exactly one of the values (dropdowns); "-" matches an empty cell
  min.<column>=n         number at least n          max.<column>=n   number at most n
  from.<column>=date     date on or after (YYYY-MM-DD)  to.<column>=date  on or before
  sort=<column>&order=asc|desc   empty cells always last
A column name that is not in the rows is rejected (ValueError), so a typo never
silently returns everything.
"""
from typing import Iterable, Mapping

PREFIXES = ("q", "in", "min", "max", "from", "to")


def _num(v):
    if isinstance(v, bool) or v is None or v == "":
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _text(v) -> str:
    if v is None:
        return ""
    if isinstance(v, bool):
        return "true" if v else "false"
    return str(v)


def parse(params: Iterable[tuple[str, str]]) -> tuple[list[tuple[str, str, str]], str | None, bool]:
    """(filters [(kind, column, value)], sort column, descending) from query items."""
    filters, sort, desc = [], None, False
    for key, value in params:
        if key == "sort":
            sort = value or None
        elif key == "order":
            desc = value.lower() == "desc"
        elif "." in key:
            kind, column = key.split(".", 1)
            if kind in PREFIXES and value != "":
                filters.append((kind, column, value))
    return filters, sort, desc


def apply(rows: list[dict], params: Iterable[tuple[str, str]]) -> list[dict]:
    filters, sort, desc = parse(params)
    columns = set(rows[0]) if rows else set()
    for _kind, column, _value in filters:
        if rows and column not in columns:
            raise ValueError(f"Unknown column: {column}")
    if sort and rows and sort not in columns:
        raise ValueError(f"Unknown column: {sort}")

    def keep(row: Mapping) -> bool:
        for kind, column, value in filters:
            cell = row.get(column)
            if kind == "q" and value.lower() not in _text(cell).lower():
                return False
            if kind == "in":
                wanted = {v.strip() for v in value.split(",")}
                if (_text(cell) or "-") not in wanted:
                    return False
            if kind in ("min", "max"):
                n, limit = _num(cell), _num(value)
                if limit is None:
                    raise ValueError(f"{kind}.{column} must be a number")
                if n is None or (kind == "min" and n < limit) or (kind == "max" and n > limit):
                    return False
            if kind in ("from", "to"):
                day = _text(cell)[:10]
                if not day or (kind == "from" and day < value[:10]) or (kind == "to" and day > value[:10]):
                    return False
        return True

    out = [r for r in rows if keep(r)]
    if sort:
        def key(r):
            cell = r.get(sort)
            n = _num(cell)
            return (n,) if n is not None and not isinstance(cell, str) else (_text(cell).lower(),)
        filled = [r for r in out if r.get(sort) not in (None, "")]
        empty = [r for r in out if r.get(sort) in (None, "")]
        out = sorted(filled, key=key, reverse=desc) + empty
    return out
