"""sql_query: read-only SQL for admins/developers (jsi:sql:read), executed only after the human confirms it.

Confirmation is enforced by the server, not by the agent: before anything runs, the server asks the client for a
form elicitation that shows the exact statement. On this stateless deployment that works only for clients on
protocol 2026-07-28+ that declare form elicitation (the answer comes back as an InputRequiredResult round); every
other client is refused (no back-channel, no confirmation, no SQL). The SDK pins the answer to the rendered
question, so a changed statement is asked again.

Guards on top of that: one SELECT/WITH/EXPLAIN statement, no `*` select list, no INTO/locking/file functions,
[TAJNO] columns refused (sensitive.assert_clean_sql + column GRANTs of the read-only user), personal-data column
names (sql_pii_kolone.json, all tables) only with pii=true + jsi:kandidati:pii, MAX_EXECUTION_TIME and a READ ONLY
transaction (db.query), row limit. The log line holds a SHA-256 of the statement, never its text.
"""

import functools
import hashlib
import json
import logging
import os
import re
import time
from typing import Annotated, Any

from mcp.server.mcpserver import AcceptedElicitation, Context, Elicit, ElicitationResult, Resolve
from mcp.server.mcpserver.exceptions import ToolError
from mcp_types.version import is_version_at_least
from pydantic import BaseModel, Field

from . import db
from .auth import current_principal
from .config import QUERY_TIMEOUT_S, Config
from .permissions import KANDIDATI_PII, SQL_READ, PermissionDenied, Principal, require
from .sensitive import SensitiveColumnError, assert_clean_sql
from .tools_read import DATA_NOTE, InputError

LIMIT_DEFAULT = 200
LIMIT_MAX = 1000
SQL_MAX_LEN = 10_000
MIN_PROTOCOL = "2026-07-28"
log = logging.getLogger("jsi_mcp.calls")

_STRING = re.compile(r"'(?:[^'\\]|\\.|'')*'|\"(?:[^\"\\]|\\.|\"\")*\"")
_COMMENT = re.compile(r"/\*.*?\*/|--[ \t][^\n]*|#[^\n]*", re.S)
_IDENT = re.compile(r"`([^`]+)`|\b([A-Za-z_][A-Za-z0-9_$]*)\b")
_FORBIDDEN = re.compile(
    r"\b(insert|update|delete|replace|drop|alter|create|truncate|rename|grant|revoke|set|call|do|handler|load|"
    r"lock|unlock|into|outfile|dumpfile|load_file|sleep|benchmark|get_lock|analyze|optimize|flush|kill|"
    r"shutdown|prepare|execute|deallocate)\b", re.I)
_STAR = re.compile(r"\bselect\s+(?:all\s+|distinct\s+|distinctrow\s+)?\*|[\w`]\s*\.\s*\*", re.I)


class Bestaetigung(BaseModel):
    ausfuehren: bool = Field(description="Ja – diese SQL-Abfrage jetzt gegen die JSI-Datenbank ausführen")


@functools.lru_cache(maxsize=1)
def pii_columns() -> frozenset[str]:
    with open(os.path.join(os.path.dirname(__file__), "sql_pii_kolone.json"), encoding="utf-8") as f:
        return frozenset(json.load(f)["kolone"])


def _code(sql: str) -> str:
    """The statement without string literals and comments (for structural checks)."""
    if "/*!" in sql:
        raise InputError("MySQL-Sonderkommentare /*! … */ sind nicht erlaubt")
    return _COMMENT.sub(" ", _STRING.sub("''", sql))


def check(sql: str, pii: bool) -> str:
    """Validate the statement; return it without a trailing semicolon. Raises InputError/SensitiveColumnError."""
    if not isinstance(sql, str) or not sql.strip():
        raise InputError("sql: Abfrage fehlt")
    if len(sql) > SQL_MAX_LEN:
        raise InputError(f"sql: höchstens {SQL_MAX_LEN} Zeichen")
    stmt = sql.strip().rstrip(";").strip()
    code = _code(stmt)
    if ";" in code:
        raise InputError("sql: genau eine Anweisung (kein ';' in der Mitte)")
    first = (code.lstrip("( \n\t").split(None, 1) or [""])[0].lower()
    if first not in ("select", "with", "explain"):
        raise InputError("sql: nur SELECT, WITH … SELECT oder EXPLAIN SELECT")
    bad = sorted({m.group(1).upper() for m in _FORBIDDEN.finditer(code)})
    if bad:
        raise InputError(f"sql: nicht erlaubt in sql_query: {', '.join(bad)} (nur lesen)")
    if _STAR.search(code):
        raise InputError("sql: kein SELECT * / tabela.* – Spalten ausdrücklich nennen (COUNT(*) ist erlaubt)")
    assert_clean_sql(stmt)
    if not pii:
        idents = {(a or b).lower() for a, b in _IDENT.findall(code)}
        hit = sorted(idents & pii_columns())
        if hit:
            raise InputError(f"sql: Spalten mit Personendaten {hit} – nur mit pii=true und jsi:kandidati:pii")
    return stmt


def preflight(cfg: Config, p: Principal, ctx: Context, sql: str, pii: bool) -> str:
    """Everything that must hold before the user is even asked."""
    require(p, [SQL_READ] + ([KANDIDATI_PII] if pii else []))
    stmt = check(sql, pii)
    version = ctx.protocol_version or "unbekannt"
    caps = ctx.client_capabilities
    form = bool(caps and caps.elicitation is not None and (caps.elicitation.form is not None or caps.elicitation.url is None))
    if version == "unbekannt" or not is_version_at_least(version, MIN_PROTOCOL) or not form:
        raise PermissionError(
            "sql_query braucht eine Bestätigung durch den Menschen; dieser Client kann sie nicht anzeigen "
            f"(Protokoll {version}, Bestätigungsdialog/elicitation: {'ja' if form else 'nein'}; nötig: "
            f"Protokoll ≥ {MIN_PROTOCOL} mit elicitation). Abfrage nicht ausgeführt. / Potrebna je potvrda korisnika.")
    return stmt


def make_tool(cfg: Config):
    """Build the sql_query tool function (closure over cfg so the resolver can check the principal first)."""

    def confirm(ctx: Context, sql: str, limit: int | None = None, pii: bool = False):
        p = current_principal(cfg)
        try:
            stmt = preflight(cfg, p, ctx, sql, pii)
        except (PermissionDenied, PermissionError, InputError, SensitiveColumnError) as e:
            _log(p, "refused:" + type(e).__name__, sql, None, 0)
            raise ToolError(str(e)) from None
        lim = LIMIT_DEFAULT if limit is None else limit
        return Elicit(f"SQL-Abfrage gegen die JSI-Datenbank ({cfg.db_target}) ausführen? Nur lesen, höchstens "
                      f"{lim} Zeilen{', mit Personendaten' if pii else ''}.\n\n{stmt}\n\n"
                      "/ Izvršiti ovaj SQL upit (samo čitanje)?", Bestaetigung)

    async def sql_query(
        sql: Annotated[str, Field(max_length=SQL_MAX_LEN, description="Eine lesende MySQL-Abfrage (SELECT / WITH / "
                                  "EXPLAIN) gegen jsicrm; Spalten ausdrücklich nennen")],
        ok: Annotated[ElicitationResult[Bestaetigung], Resolve(confirm)],
        limit: Annotated[int | None, Field(ge=1, le=LIMIT_MAX, description=f"Höchstens so viele Zeilen (Standard "
                                           f"{LIMIT_DEFAULT}, max {LIMIT_MAX})")] = None,
        pii: Annotated[bool, Field(description="Spalten mit Personendaten erlauben – nur auf ausdrücklichen Wunsch, "
                                               "Permission jsi:kandidati:pii")] = False,
    ) -> dict:
        import anyio

        p, t0 = current_principal(cfg), time.monotonic()
        if not (isinstance(ok, AcceptedElicitation) and ok.data.ausfuehren):
            _log(p, "declined", sql, None, 0)
            return {"izvrseno": False, "napomena": "Nicht ausgeführt – der Nutzer hat nicht bestätigt. / Nije izvršeno."}
        try:
            require(p, [SQL_READ] + ([KANDIDATI_PII] if pii else []))  # again: the answer may come rounds later
            stmt = check(sql, pii)
            lim = LIMIT_DEFAULT if limit is None else limit
            rows = await anyio.to_thread.run_sync(functools.partial(db.query, cfg, stmt, None, lim + 1))
        except (PermissionDenied, InputError, SensitiveColumnError, db.DbNotConfigured, db.DbError) as e:
            _log(p, "error:" + type(e).__name__, sql, None, 0)
            raise ToolError(str(e)) from None
        except Exception as e:  # like tool_wrapper: never pass driver messages (host names …) to the client
            logging.getLogger("jsi_mcp").exception("tool sql_query failed")
            _log(p, "error:" + type(e).__name__, sql, None, 0)
            raise ToolError(f"Interner Fehler / Interna greška ({type(e).__name__}).") from None
        more = len(rows) > lim
        rows = rows[:lim]
        _log(p, "ok", sql, len(rows), 1, round((time.monotonic() - t0) * 1000))
        return {"izvrseno": True, "rezultat": rows, "broj_redova": len(rows),
                "stranica": {"ima_jos": more, "pregled": f"Prikazano {len(rows)} redova"
                             + (f" (ograničeno na {lim}; ima još – suzi upit ili povećaj limit)" if more else ".")},
                "napomene": [f"Timeout {QUERY_TIMEOUT_S} s, samo čitanje."], "stanje_podataka": DATA_NOTE}

    return sql_query


def _log(p: Principal, status: str, sql: str, rows: int | None, executed: int, ms: int = 0) -> None:
    from . import admin
    digest = hashlib.sha256(sql.encode("utf-8", "replace")).hexdigest()[:16] if isinstance(sql, str) else None
    log.info(json.dumps({"event": "tool_call", "sub": p.sub, "tool": "sql_query", "status": status, "rows": rows,
                         "sql_sha256": digest, "executed": executed, "duration_ms": ms}))
    admin.record(p.sub, "sql_query", status, ms, rows)
