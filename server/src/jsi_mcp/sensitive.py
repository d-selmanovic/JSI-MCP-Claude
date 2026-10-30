"""[TAJNO] columns (osjetljive_kolone.md) – never selected, written, logged or returned.

Every SQL statement the server executes passes `assert_clean_sql`; a statement that names one of
these columns is refused before it reaches the database (defence in depth on top of DB GRANTs).
"""
from __future__ import annotations

import os
import re

from .config import PACKAGE_DIR

_MD = os.path.join(PACKAGE_DIR, "osjetljive_kolone.md")


def _load() -> dict[str, frozenset[str]]:
    out: dict[str, set[str]] = {}
    with open(_MD, encoding="utf-8") as f:
        for line in f:
            m = re.match(r"^\|\s*`([a-z0-9_]+)`\s*\|\s*`([a-z0-9_]+)`\s*\|", line)
            if m:
                out.setdefault(m.group(1), set()).add(m.group(2))
    return {t: frozenset(c) for t, c in out.items()}


SENSITIVE: dict[str, frozenset[str]] = _load()
# Column names that are unique enough to be refused wherever they appear in SQL.
# `users.password` / `users.token` are generic names; they are refused as qualified names and
# whenever the table `users` is referenced.
_GENERIC = {"password", "token"}
SENSITIVE_COLUMN_NAMES = frozenset(c for cols in SENSITIVE.values() for c in cols if c not in _GENERIC)


class SensitiveColumnError(PermissionError):
    pass


_IDENT = re.compile(r"[A-Za-z0-9_]+")


def is_sensitive(table: str, column: str) -> bool:
    return column in SENSITIVE.get(table, frozenset())


def assert_clean_sql(sql: str) -> None:
    tokens = {t.lower() for t in _IDENT.findall(sql)}
    hit = tokens & SENSITIVE_COLUMN_NAMES
    if hit:
        raise SensitiveColumnError(f"SQL referenziert gesperrte [TAJNO]-Spalte(n): {sorted(hit)}")
    if re.search(r"\busers\b", sql, re.IGNORECASE) and tokens & _GENERIC:
        raise SensitiveColumnError("SQL referenziert gesperrte Spalte der Tabelle users.")


def strip_sensitive(table: str, row: dict) -> dict:
    bad = SENSITIVE.get(table, frozenset())
    return {k: v for k, v in row.items() if k not in bad}
