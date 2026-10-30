"""Audited write tools: record_preview, record_write, set_application_status.

Flow: validate -> plan (before/after, diff, preview_hash) -> [dry_run stops here]
      -> transaction: re-plan with SELECT ... FOR UPDATE, compare preview_hash, write, audit row in
         mcp_aenderung, COMMIT. Any error -> ROLLBACK + row in mcp_fehler (best effort).
No hard deletes: `archive` sets the registry's archive columns.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import logging
import re
from typing import Any

from . import db
from .config import Config
from .permissions import KANDIDATI_PII, Principal, require, write_permission
from .registry import REGISTRY, Column, Entity
from .tools_read import InputError

log = logging.getLogger("jsi_mcp.writes")

NOW = "@now"
EMPLOYEE = "@employee_id"
LICENCE_TOKENS = {"AM", "A1", "A2", "A", "B1", "B", "BE", "C1", "C1E", "C", "CE", "D1", "D1E", "D", "DE", "E", "F", "G", "M"}


class WriteError(RuntimeError):
    pass


class WritesDisabled(WriteError):
    pass


class ConflictError(WriteError):
    pass


# ---------------------------------------------------------------- validation
def _check_value(e: Entity, c: Column, v: Any) -> Any:
    where = f"{e.name}.{c.name}"
    if v is None:
        if not c.nullable:
            raise InputError(f"{where}: darf nicht leer (null) sein")
        return None
    t = c.type
    if t == "int":
        if isinstance(v, bool) or not isinstance(v, int):
            raise InputError(f"{where}: Ganzzahl erwartet")
        if not -2_147_483_648 <= v <= 2_147_483_647:
            raise InputError(f"{where}: Zahl außerhalb des int-Bereichs")
        return v
    if t == "enum":
        if v not in c.values or isinstance(v, bool):
            raise InputError(f"{where}: Wert {v!r} nicht erlaubt; erlaubt: {c.values}")
        return v
    if t in ("str", "text"):
        if not isinstance(v, str):
            raise InputError(f"{where}: Text erwartet")
        v = v.strip()
        lim = c.max_len or 65535
        if len(v) > lim:
            raise InputError(f"{where}: max. {lim} Zeichen")
        if "\x00" in v:
            raise InputError(f"{where}: ungültige Zeichen")
        return v
    if t == "date":
        if not isinstance(v, str) or not re.match(r"^\d{4}-\d{2}-\d{2}$", v):
            raise InputError(f"{where}: Datum YYYY-MM-DD erwartet")
        try:
            d = dt.date.fromisoformat(v)
        except ValueError:
            raise InputError(f"{where}: ungültiges Datum") from None
        if d.year < 1900 or d.year > 2100:
            raise InputError(f"{where}: Datum außerhalb 1900–2100")
        return v
    if t == "datetime":
        if not isinstance(v, str):
            raise InputError(f"{where}: Zeitstempel erwartet")
        try:
            return dt.datetime.fromisoformat(v).strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            raise InputError(f"{where}: ungültiger Zeitstempel") from None
    if t == "licence_list":
        if isinstance(v, list):
            toks = v
        elif isinstance(v, str):
            toks = [x for x in re.split(r"[,; ]+", v) if x]
        else:
            raise InputError(f"{where}: Liste von Kategorien erwartet, z. B. ['B','C','CE']")
        toks = [str(x).upper().strip() for x in toks]
        bad = [x for x in toks if x not in LICENCE_TOKENS]
        if bad:
            raise InputError(f"{where}: unbekannte Kategorien {bad}")
        seen: list[str] = []
        for x in toks:
            if x not in seen:
                seen.append(x)
        s = ",".join(seen)
        if len(s) > (c.max_len or 25):
            raise InputError(f"{where}: zu lang")
        return s or None
    raise InputError(f"{where}: Typ {t} nicht unterstützt")


def validate(e: Entity, action: str, values: dict[str, Any], p: Principal) -> dict[str, Any]:
    if action not in e.actions:
        raise InputError(f"Aktion {action!r} für {e.name} nicht erlaubt; erlaubt: {e.actions}")
    if action == "archive":
        if values:
            raise InputError("archive nimmt keine values")
        return {}
    if not isinstance(values, dict) or not values:
        raise InputError("values (Objekt mit Spalten) fehlt")
    unknown = set(values) - set(e.columns)
    if unknown:
        raise InputError(f"Spalten nicht beschreibbar für {e.name}: {sorted(unknown)}; erlaubt: {sorted(e.columns)}")
    out = {}
    for k, v in values.items():
        c = e.columns[k]
        if action == "update" and c.create_only:
            raise InputError(f"{e.name}.{k}: nach Anlage nicht änderbar")
        if c.pii:
            require(p, [KANDIDATI_PII])
        out[k] = _check_value(e, c, v)
    if action == "create":
        missing = [c.name for c in e.columns.values() if c.required_on_create and out.get(c.name) in (None, "")]
        if missing:
            raise InputError(f"Pflichtfelder fehlen für {e.name}: {missing}")
    return out


# ---------------------------------------------------------------- planning
def _select_cols(e: Entity) -> list[str]:
    cols = [e.pk] + list(e.columns) + [c for c in e.archive if c not in e.columns]
    if e.candidate_ref and e.candidate_ref not in cols:
        cols.append(e.candidate_ref)
    return list(dict.fromkeys(cols))


def _fetch_before(cur, e: Entity, record_id: int, lock: bool) -> dict | None:
    sql = (f"SELECT {', '.join(_select_cols(e))} FROM {e.table} WHERE {e.pk} = %s" + (" FOR UPDATE" if lock else ""))
    db.execute(cur, sql, (record_id,))
    row = cur.fetchone()
    return {k: db.jsonable(v) for k, v in row.items()} if row else None


def _check_refs_and_unique(cur, e: Entity, action: str, values: dict, before: dict | None, record_id: int | None) -> list[str]:
    problems = []
    for k, v in values.items():
        col = e.columns.get(k)
        ref = col.references if col else None
        if not ref or v is None:
            continue
        if v == 0 and ref.get("allow_zero"):
            continue
        db.execute(cur, f"SELECT 1 FROM {ref['table']} WHERE {ref['column']} = %s LIMIT 1", (v,))
        if cur.fetchone() is None:
            problems.append(f"{k}={v}: kein Datensatz in {ref['table']}.{ref['column']}")
    if e.unique_together and action == "create":
        conds = " AND ".join(f"{c} = %s" for c in e.unique_together)
        db.execute(cur, f"SELECT {e.pk} FROM {e.table} WHERE {conds} LIMIT 1", tuple(values.get(c) for c in e.unique_together))
        hit = cur.fetchone()
        if hit:
            problems.append(f"existiert bereits ({', '.join(e.unique_together)}) als {e.pk}={hit[e.pk]}")
    for c in e.unique_nonzero:
        v = values.get(c)
        if v:
            db.execute(cur, f"SELECT {e.pk} FROM {e.table} WHERE {c} = %s AND {e.pk} <> %s LIMIT 1", (v, record_id or 0))
            hit = cur.fetchone()
            if hit:
                problems.append(f"{c}={v} ist bereits mit {e.pk}={hit[e.pk]} verknüpft")
    return problems


def _hash(*parts: Any) -> str:
    return hashlib.sha256(json.dumps(parts, sort_keys=True, default=str, ensure_ascii=False).encode()).hexdigest()[:32]


def _redact(e: Entity, row: dict | None, p: Principal) -> dict | None:
    if row is None or p.has(KANDIDATI_PII):
        return row
    return {k: ("***" if k in e.columns and e.columns[k].pii and v not in (None, "") else v) for k, v in row.items()}


def precheck(p: Principal, entity: str, action: str, values: dict[str, Any] | None) -> tuple[Entity, dict]:
    """Entity, permission and value validation – no DB access, so it runs before connecting."""
    e = REGISTRY.get(entity)
    if e is None:
        raise InputError(f"Entität unbekannt: {entity}; erlaubt: {sorted(REGISTRY)}")
    if e.process_tool:
        raise InputError(f"{entity} nur über das Prozess-Tool {e.process_tool}")
    require(p, [write_permission(entity, action)])
    return e, validate(e, action, values or {}, p)


def plan(cur, cfg: Config, p: Principal, entity: str, action: str, record_id: int | None,
         values: dict[str, Any] | None, lock: bool = False) -> dict:
    e, vals = precheck(p, entity, action, values)
    before = None
    if action in ("update", "archive"):
        if isinstance(record_id, bool) or not isinstance(record_id, int) or record_id <= 0:
            raise InputError("record_id (positive Ganzzahl) fehlt für update/archive")
        before = _fetch_before(cur, e, record_id, lock)
        if before is None:
            raise InputError(f"{e.table}.{e.pk}={record_id} nicht gefunden")
    elif record_id is not None:
        raise InputError("record_id nur bei update/archive")
    if action == "archive":
        vals = dict(e.archive)
    problems = _check_refs_and_unique(cur, e, action, vals, before, record_id)
    if action == "create":
        sets = {**{k: v for k, v in e.create_defaults.items()}, **vals, **e.fixed}
        after = {k: _placeholder(cfg, v, display=True) for k, v in sets.items()}
        diff = {k: {"vorher": None, "nachher": after[k]} for k in after}
    else:
        sets = vals
        after = {**before, **vals}
        diff = {k: {"vorher": before.get(k), "nachher": v} for k, v in vals.items() if before.get(k) != v}
    cand = None
    if e.candidate_ref:
        cand = (after if action == "create" else before).get(e.candidate_ref)
    preview_hash = _hash(entity, action, record_id, vals, before)
    return {
        "entity": e, "action": action, "record_id": record_id, "sets": sets, "before": before, "after": after,
        "diff": diff, "problems": problems, "kandidat_id": cand if isinstance(cand, int) else None,
        "preview_hash": preview_hash,
    }


def _placeholder(cfg: Config, v: Any, display: bool = False) -> Any:
    if v == NOW:
        return "NOW()" if display else NOW
    if v == EMPLOYEE:
        return cfg.write_employee_id
    return v


def _public(plan_: dict, p: Principal, dry_run: bool) -> dict:
    e: Entity = plan_["entity"]
    diff = plan_["diff"]
    if not p.has(KANDIDATI_PII):
        diff = {k: ({"vorher": "***", "nachher": "***"} if e.columns.get(k) and e.columns[k].pii else d) for k, d in diff.items()}
    return {
        "dry_run": dry_run, "entity": e.name, "table": e.table, "action": plan_["action"], "record_id": plan_["record_id"],
        "kandidat_id": plan_["kandidat_id"], "vorher": _redact(e, plan_["before"], p), "promjene": diff,
        "bez_promjene": not diff, "problemi": plan_["problems"], "preview_hash": plan_["preview_hash"],
        "permission": write_permission(e.name, plan_["action"]),
    }


def _gate(cfg: Config) -> None:
    if not cfg.writes_allowed:
        raise WritesDisabled(
            "Schreiben deaktiviert / Pisanje isključeno: braucht JSI_WRITES_ENABLED=true und JSI_DB_TARGET=mirror "
            f"(aktuell writes_enabled={cfg.writes_enabled}, target={cfg.db_target})."
        )


# ---------------------------------------------------------------- tools
def record_preview(cfg: Config, p: Principal, entity: str, action: str, record_id: int | None = None,
                   values: dict[str, Any] | None = None) -> dict:
    precheck(p, entity, action, values)
    with db.read_cursor(cfg) as cur:
        pl = plan(cur, cfg, p, entity, action, record_id, values, lock=False)
    out = _public(pl, p, dry_run=True)
    out["schreiben_aktiv"] = cfg.writes_allowed
    return out


def record_write(cfg: Config, p: Principal, entity: str, action: str, record_id: int | None = None,
                 values: dict[str, Any] | None = None, dry_run: bool = True, preview_hash: str | None = None,
                 grund: str | None = None) -> dict:
    if dry_run:
        return record_preview(cfg, p, entity, action, record_id, values)
    precheck(p, entity, action, values)
    _gate(cfg)
    try:
        with db.write_conn(cfg) as conn:
            with conn.cursor() as cur:
                pl = plan(cur, cfg, p, entity, action, record_id, values, lock=True)
                if preview_hash and preview_hash != pl["preview_hash"]:
                    raise ConflictError("Datensatz hat sich seit der Vorschau geändert / Zapis je promijenjen – neu prüfen (record_preview).")
                if pl["problems"]:
                    raise InputError("Prüfung fehlgeschlagen: " + "; ".join(pl["problems"]))
                if not pl["diff"]:
                    conn.rollback()
                    out = _public(pl, p, dry_run=False)
                    out["ausgefuehrt"] = False
                    out["hinweis"] = "Keine Änderung nötig / Nema promjene."
                    return out
                new_id = _apply(cur, cfg, pl)
                audit_id = _audit(cur, "record_write", pl, new_id, p, grund)
            conn.commit()
    except Exception as ex:
        _log_error(cfg, "record_write", ex, {"entity": entity, "action": action, "record_id": record_id, "sub": p.sub})
        raise
    out = _public(pl, p, dry_run=False)
    out.update(ausgefuehrt=True, record_id=new_id, audit_id=audit_id)
    return out


def _apply(cur, cfg: Config, pl: dict) -> int:
    e: Entity = pl["entity"]
    sets = pl["sets"]
    if pl["action"] == "create":
        cols, ph, params = [], [], []
        for k, v in sets.items():
            cols.append(k)
            v = _placeholder(cfg, v)
            if v == NOW:
                ph.append("NOW()")
            else:
                ph.append("%s")
                params.append(v)
        db.execute(cur, f"INSERT INTO {e.table} ({', '.join(cols)}) VALUES ({', '.join(ph)})", tuple(params))
        return int(cur.lastrowid)
    assign = ", ".join(f"{k} = %s" for k in sets)
    n = db.execute(cur, f"UPDATE {e.table} SET {assign} WHERE {e.pk} = %s", tuple(sets.values()) + (pl["record_id"],))
    if n != 1:
        raise WriteError(f"UPDATE betraf {n} Zeilen statt 1 – abgebrochen")
    return int(pl["record_id"])


def _audit(cur, tool: str, pl: dict, record_id: int, p: Principal, grund: str | None) -> int:
    e: Entity = pl["entity"]
    vorher = {k: d["vorher"] for k, d in pl["diff"].items()}
    nachher = {k: d["nachher"] for k, d in pl["diff"].items()}
    notiz = f"sub={p.sub}; perm={write_permission(e.name, pl['action'])}" + (f"; grund={grund}" if grund else "")
    db.execute(cur, "INSERT INTO mcp_aenderung (a_zeit, a_werkzeug, a_aktion, a_tabelle, a_datensatz_id, a_vorher, a_nachher, "
               "a_kandidat_id, a_art, a_zustand, a_freigabe_code, a_freigabe_zeit, a_ausgefuehrt_zeit, a_notiz) "
               "VALUES (NOW(), %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW(), %s)",
               (tool, pl["action"][:10], e.table, record_id, json.dumps(vorher, ensure_ascii=False, default=str),
                json.dumps(nachher, ensure_ascii=False, default=str), pl["kandidat_id"] or (record_id if e.candidate_ref == e.pk else None),
                "Agent", "ausgefuehrt", pl["preview_hash"], notiz[:500]))
    return int(cur.lastrowid)


def _log_error(cfg: Config, tool: str, ex: Exception, ctx: dict) -> None:
    """Best effort: record the failure in mcp_fehler (own connection, autocommit). Never raises."""
    if isinstance(ex, (WritesDisabled,)) or not cfg.db_ready():
        return
    art = "validierung" if isinstance(ex, (InputError, PermissionError, ConflictError)) else "db"
    try:
        conn = db.connect(cfg)
        try:
            with conn.cursor() as cur:
                db.execute(cur, "INSERT INTO mcp_fehler (f_zeit, f_werkzeug, f_art, f_meldung, f_kontext) VALUES (NOW(), %s, %s, %s, %s)",
                           (tool, art, str(ex)[:2000], json.dumps(ctx, default=str)))
            conn.commit()
        finally:
            conn.close()
    except Exception as e2:  # pragma: no cover - logging must not mask the original error
        log.warning("mcp_fehler insert failed: %s", type(e2).__name__)


# ---------------------------------------------------------------- set_application_status
def set_application_status(cfg: Config, p: Principal, kandidat_id: int, status_id: int, projekt_id: int | None = None,
                           dry_run: bool = True, preview_hash: str | None = None, grund: str | None = None) -> dict:
    require(p, [write_permission("application_status", "update")])
    for name, v in (("kandidat_id", kandidat_id), ("status_id", status_id)):
        if isinstance(v, bool) or not isinstance(v, int) or v <= 0:
            raise InputError(f"{name} muss eine positive Ganzzahl sein")
    if projekt_id is not None and (isinstance(projekt_id, bool) or not isinstance(projekt_id, int) or projekt_id <= 0):
        raise InputError("projekt_id muss eine positive Ganzzahl sein")
    if dry_run:
        with db.read_cursor(cfg) as cur:
            pl = _status_plan(cur, kandidat_id, status_id, projekt_id, lock=False)
        return _status_public(pl, True, cfg)
    _gate(cfg)
    try:
        with db.write_conn(cfg) as conn:
            with conn.cursor() as cur:
                pl = _status_plan(cur, kandidat_id, status_id, projekt_id, lock=True)
                if preview_hash and preview_hash != pl["preview_hash"]:
                    raise ConflictError("Status hat sich seit der Vorschau geändert / Status je promijenjen – neu prüfen.")
                if pl["problems"]:
                    raise InputError("Prüfung fehlgeschlagen: " + "; ".join(pl["problems"]))
                if pl["old_status"] == status_id:
                    conn.rollback()
                    out = _status_public(pl, False, cfg)
                    out.update(ausgefuehrt=False, hinweis="Status ist bereits gesetzt / Status je već postavljen.")
                    return out
                _status_apply(cur, cfg, pl)
                e = REGISTRY["application_status"]
                audit_pl = {"entity": e, "action": "update", "diff": pl["diff"], "kandidat_id": kandidat_id,
                            "preview_hash": pl["preview_hash"]}
                audit_id = _audit(cur, "set_application_status", audit_pl, kandidat_id, p, grund)
            conn.commit()
    except Exception as ex:
        _log_error(cfg, "set_application_status", ex, {"kandidat_id": kandidat_id, "status_id": status_id, "sub": p.sub})
        raise
    out = _status_public(pl, False, cfg)
    out.update(ausgefuehrt=True, audit_id=audit_id)
    return out


def _status_plan(cur, kandidat_id: int, status_id: int, projekt_id: int | None, lock: bool) -> dict:
    db.execute(cur, "SELECT kandidat_id, kandidat_status, kandidat_status_prijave, kandidat_latest_reserved_time "
               "FROM idk_kandidati WHERE kandidat_id = %s" + (" FOR UPDATE" if lock else ""), (kandidat_id,))
    k = cur.fetchone()
    if not k:
        raise InputError(f"Kandidat {kandidat_id} nicht gefunden")
    db.execute(cur, "SELECT status_id, status_naziv, status_aktivan, rezervisanje, redoslijed_statusa "
               "FROM idk_kandidat_status_prijave WHERE status_id = %s", (status_id,))
    st = cur.fetchone()
    problems = []
    if not st:
        raise InputError(f"status_id {status_id} existiert nicht in idk_kandidat_status_prijave")
    if not st["status_aktivan"]:
        problems.append(f"Status {status_id} ({st['status_naziv']}) ist nicht aktiv (status_aktivan=0)")
    if k["kandidat_status"] == 3:
        problems.append("Kandidat ist archiviert (kandidat_status=3)")
    if projekt_id is not None:
        db.execute(cur, "SELECT 1 FROM idk_projects WHERE project_id = %s", (projekt_id,))
        if cur.fetchone() is None:
            problems.append(f"Projekt {projekt_id} nicht gefunden")
    db.execute(cur, "SELECT lsp_id, lsp_datetime, lsp_status_prijave_id FROM idk_log_statusi_prijave WHERE lsp_kandidat_id = %s "
               "ORDER BY lsp_datetime DESC, lsp_id DESC LIMIT 1" + (" FOR UPDATE" if lock else ""), (kandidat_id,))
    last = cur.fetchone()
    old = k["kandidat_status_prijave"]
    diff = {"kandidat_status_prijave": {"vorher": old, "nachher": status_id}}
    if st["rezervisanje"] == 1:
        diff["kandidat_latest_reserved_time"] = {"vorher": db.jsonable(k["kandidat_latest_reserved_time"]), "nachher": "NOW()"}
    return {
        "kandidat_id": kandidat_id, "status": db.clean_rows([st])[0], "old_status": old, "projekt_id": projekt_id,
        "last_log": db.clean_rows([last])[0] if last else None, "diff": diff, "problems": problems,
        "preview_hash": _hash("set_application_status", kandidat_id, status_id, projekt_id, old,
                              last["lsp_id"] if last else None),
    }


def _status_apply(cur, cfg: Config, pl: dict) -> None:
    kid, sid = pl["kandidat_id"], pl["status"]["status_id"]
    reserve = ", kandidat_latest_reserved_time = NOW()" if pl["status"]["rezervisanje"] == 1 else ""
    n = db.execute(cur, f"UPDATE idk_kandidati SET kandidat_status_prijave = %s{reserve} WHERE kandidat_id = %s", (sid, kid))
    if n != 1:
        raise WriteError(f"UPDATE betraf {n} Zeilen statt 1 – abgebrochen")
    # lsp_broj_dana = days spent in the previous status, written onto the previous log row
    # (measured 2026-10-30: 27,300 of 27,313 rows since 2025 match DATEDIFF(next, this) ±1; last row is always NULL).
    if pl["last_log"]:
        db.execute(cur, "UPDATE idk_log_statusi_prijave SET lsp_broj_dana = DATEDIFF(NOW(), lsp_datetime) "
                   "WHERE lsp_id = %s AND lsp_broj_dana IS NULL", (pl["last_log"]["lsp_id"],))
    db.execute(cur, "INSERT INTO idk_log_statusi_prijave (lsp_kandidat_id, lsp_projekt_id, lsp_status_prijave_id, lsp_employee_id, "
               "lsp_izvor, lsp_datetime, lsp_broj_dana) VALUES (%s, %s, %s, %s, %s, NOW(), NULL)",
               (kid, pl["projekt_id"], sid, cfg.write_employee_id or None, cfg.lsp_izvor))


def _status_public(pl: dict, dry_run: bool, cfg: Config) -> dict:
    return {
        "dry_run": dry_run, "kandidat_id": pl["kandidat_id"], "novi_status": pl["status"], "stari_status_id": pl["old_status"],
        "promjene": pl["diff"], "pipeline_log": {
            "novi_red": {"lsp_status_prijave_id": pl["status"]["status_id"], "lsp_projekt_id": pl["projekt_id"],
                         "lsp_izvor": cfg.lsp_izvor, "lsp_employee_id": cfg.write_employee_id or None},
            "prethodni_red_broj_dana": pl["last_log"]["lsp_id"] if pl["last_log"] else None},
        "problemi": pl["problems"], "preview_hash": pl["preview_hash"], "schreiben_aktiv": cfg.writes_allowed,
        "permission": write_permission("application_status", "update"),
    }
