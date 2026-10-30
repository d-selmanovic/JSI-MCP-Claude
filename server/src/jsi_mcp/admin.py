"""Read-only admin status page (/admin, /admin/status.json).

Off unless JSI_ADMIN_PASSWORD is set (≥ 16 characters). Login via HTTP Basic (user "admin"). Shows server and
configuration state (never values of secrets), a DB reachability check, tool-call counters and the last calls of
this instance (no arguments, no results) and the last MCP write actions from mcp_aenderung (metadata only, no
before/after values). Nothing can be changed here – settings and secrets stay in Manufact.
"""
from __future__ import annotations

import base64
import collections
import hmac
import html
import json
import threading
import time
from datetime import datetime, timezone
from typing import Any

from . import db
from .config import Config

ADMIN_USER = "admin"
RECENT_MAX = 100
_lock = threading.Lock()
_started = time.time()
_counts: dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
_recent: collections.deque = collections.deque(maxlen=RECENT_MAX)


def record(sub: str, tool: str, status: str, duration_ms: int, rows: int | None) -> None:
    """Called by tool_wrapper for every call (in-memory, per instance, reset on restart)."""
    with _lock:
        _counts[tool][status.split(":")[0]] += 1
        _recent.append({"zeit": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"), "sub": sub, "tool": tool,
                        "status": status, "ms": duration_ms, "redova": rows})


def authorized(cfg: Config, header: str | None) -> bool:
    if not cfg.admin_password or not header or not header.startswith("Basic "):
        return False
    try:
        user, _, pw = base64.b64decode(header[6:]).decode("utf-8").partition(":")
    except (ValueError, UnicodeDecodeError):
        return False
    return hmac.compare_digest(user.encode(), ADMIN_USER.encode()) & hmac.compare_digest(
        pw.encode(), cfg.admin_password.encode())


def _db_check(cfg: Config) -> dict:
    if not cfg.db_ready():
        return {"ok": False, "fehler": "Datenbank nicht konfiguriert"}
    t0 = time.monotonic()
    try:
        db.query(cfg, "SELECT 1 AS ok", ())
        return {"ok": True, "ms": round((time.monotonic() - t0) * 1000)}
    except Exception as e:  # report the type only; messages may contain host names
        return {"ok": False, "fehler": type(e).__name__, "detail": str(e)[:200] if isinstance(e, db.DbError) else None}


def _writes(cfg: Config) -> dict:
    if not cfg.db_ready():
        return {"verfuegbar": False}
    try:
        rows = db.query(cfg, "SELECT a_id, a_zeit, a_werkzeug, a_aktion, a_tabelle, a_datensatz_id, a_zustand "
                             "FROM mcp_aenderung ORDER BY a_id DESC LIMIT 20", ())
        return {"verfuegbar": True, "letzte": rows}
    except Exception as e:
        return {"verfuegbar": False, "fehler": type(e).__name__}


def status(cfg: Config, version: str, tools: list[str]) -> dict:
    with _lock:
        counts = {t: dict(c) for t, c in sorted(_counts.items())}
        recent = list(reversed(_recent))
    return {
        "server": {"version": version, "laeuft_seit_utc": datetime.fromtimestamp(_started, timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
                   "uptime_min": round((time.time() - _started) / 60, 1),
                   "hinweis": "Zähler und letzte Aufrufe gelten nur für diese Instanz seit dem letzten Start."},
        "konfiguration": {"db_ziel": cfg.db_target, "db_konfiguriert": cfg.db_ready(), "schreiben_aktiv": cfg.writes_allowed,
                          "schreiben_schalter": cfg.writes_enabled, "auth": "disabled(local)" if cfg.auth_disabled else "workos",
                          "authkit_domain": cfg.authkit_domain, "public_url": cfg.public_url,
                          "ca_zertifikat": bool(cfg.db.ca_pem), "fehler": cfg.errors},
        "datenbank": _db_check(cfg),
        "tools": tools,
        "aufrufe_zaehler": counts,
        "letzte_aufrufe": recent,
        "letzte_schreibaktionen": _writes(cfg),
    }


def _table(rows: list[dict]) -> str:
    if not rows:
        return "<p class=muted>–</p>"
    cols = list(rows[0])
    head = "".join(f"<th>{html.escape(str(c))}</th>" for c in cols)
    body = "".join("<tr>" + "".join(f"<td>{html.escape('' if r.get(c) is None else str(r.get(c)))}</td>" for c in cols)
                   + "</tr>" for r in rows)
    return f"<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"


def page(st: dict) -> str:
    k, d = st["konfiguration"], st["datenbank"]
    ok = lambda b: "<span class=ok>✔</span>" if b else "<span class=bad>✘</span>"  # noqa: E731
    counts = [{"tool": t, **c} for t, c in st["aufrufe_zaehler"].items()]
    errs = "".join(f"<li>{html.escape(e)}</li>" for e in k["fehler"]) or "<li class=muted>keine</li>"
    w = st["letzte_schreibaktionen"]
    return f"""<!doctype html><html lang=de><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1"><meta http-equiv=refresh content=30>
<title>JSI MCP – Status</title><style>
body{{font-family:system-ui,sans-serif;margin:16px;color:#1d1d1f;background:#fafafa}}h1{{font-size:20px}}h2{{font-size:16px;margin-top:24px}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:8px}}.card{{background:#fff;border:1px solid #ddd;border-radius:6px;padding:10px}}
table{{border-collapse:collapse;width:100%;font-size:13px;background:#fff}}td,th{{border:1px solid #ddd;padding:4px 6px;text-align:left}}
.ok{{color:#0a7d32}}.bad{{color:#c0262d}}.muted{{color:#777}}.wrap{{overflow-x:auto}}
@media (prefers-color-scheme:dark){{body{{background:#161618;color:#eee}}.card,table{{background:#222;border-color:#444}}td,th{{border-color:#444}}}}
</style></head><body>
<h1>JSI MCP – Status <span class=muted>v{html.escape(st['server']['version'])}</span></h1>
<p class=muted>Nur lesen · aktualisiert alle 30 s · Einstellungen und Secrets ändern: Manufact → Server → Environment variables · {html.escape(st['server']['hinweis'])}</p>
<div class=grid>
<div class=card>Datenbank erreichbar {ok(d.get('ok'))}<br><span class=muted>{html.escape(str(d.get('ms', d.get('fehler', ''))))}{' ms' if d.get('ok') else ''}</span></div>
<div class=card>DB-Ziel: <b>{html.escape(k['db_ziel'])}</b><br>konfiguriert {ok(k['db_konfiguriert'])} · CA-Zertifikat {ok(k['ca_zertifikat'])}</div>
<div class=card>Schreiben aktiv {ok(k['schreiben_aktiv'])}<br><span class=muted>Schalter JSI_WRITES_ENABLED = {k['schreiben_schalter']}</span></div>
<div class=card>Anmeldung: <b>{html.escape(k['auth'])}</b><br><span class=muted>{html.escape(str(k['authkit_domain']))}</span></div>
<div class=card>Läuft seit {html.escape(st['server']['laeuft_seit_utc'])} UTC<br><span class=muted>{st['server']['uptime_min']} min · {len(st['tools'])} Tools</span></div>
</div>
<h2>Konfigurationsfehler</h2><ul>{errs}</ul>
{'' if d.get('ok') or not d.get('detail') else '<p class=bad>' + html.escape(d['detail']) + '</p>'}
<h2>Aufrufe je Tool (diese Instanz)</h2><div class=wrap>{_table(counts)}</div>
<h2>Letzte Aufrufe (ohne Inhalte)</h2><div class=wrap>{_table(st['letzte_aufrufe'][:50])}</div>
<h2>Letzte Schreibaktionen (mcp_aenderung, ohne Werte)</h2><div class=wrap>{_table(w.get('letzte', [])) if w.get('verfuegbar') else '<p class=muted>nicht verfügbar ' + html.escape(str(w.get('fehler', ''))) + '</p>'}</div>
</body></html>"""


def json_body(st: dict) -> str:
    return json.dumps(st, ensure_ascii=False, default=str)


SECURITY_HEADERS = {"Cache-Control": "no-store", "X-Frame-Options": "DENY", "X-Content-Type-Options": "nosniff",
                    "Referrer-Policy": "no-referrer", "Content-Security-Policy": "default-src 'none'; style-src 'unsafe-inline'"}
