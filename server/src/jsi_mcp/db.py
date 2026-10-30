"""MySQL access (PyMySQL). Reads run in READ ONLY transactions with MAX_EXECUTION_TIME."""
from __future__ import annotations

import datetime as dt
import decimal
import os
import tempfile
from contextlib import contextmanager
from typing import Any, Iterator

import pymysql
import pymysql.cursors

from .config import QUERY_TIMEOUT_S, Config
from .sensitive import assert_clean_sql


class DbNotConfigured(RuntimeError):
    pass


class DbError(RuntimeError):
    pass


_CA_TMP: str | None = None


def _ca_path(cfg: Config) -> str | None:
    global _CA_TMP
    if cfg.db.ca_pem:
        if _CA_TMP is None or not os.path.exists(_CA_TMP):
            fd, path = tempfile.mkstemp(prefix="jsi-ca-", suffix=".pem")
            with os.fdopen(fd, "w") as f:
                pem = cfg.db.ca_pem.replace("\\n", "\n")
                f.write(pem if pem.endswith("\n") else pem + "\n")
            _CA_TMP = path
        return _CA_TMP
    return cfg.db.ca_file


def connect(cfg: Config) -> pymysql.connections.Connection:
    if not cfg.db_ready():
        raise DbNotConfigured(
            "Datenbank nicht konfiguriert / Baza nije konfigurisana: "
            + "; ".join(e for e in cfg.errors if "Datenbank" in e or "TLS" in e or "JSI_DB_TARGET" in e)
        )
    kwargs: dict[str, Any] = dict(
        host=cfg.db.host,
        port=cfg.db.port,
        user=cfg.db.user,
        password=cfg.db.password,
        database=cfg.db.name,
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
        connect_timeout=10,
        read_timeout=QUERY_TIMEOUT_S + 5,
        write_timeout=QUERY_TIMEOUT_S + 5,
        autocommit=False,
    )
    if cfg.db.ssl_required:
        ca = _ca_path(cfg)
        if not ca:
            raise DbNotConfigured("TLS verlangt, aber kein CA-Zertifikat (JSI_DB_CA_CERT / certs/aiven-ca.pem).")
        kwargs.update(ssl_ca=ca, ssl_verify_cert=True, ssl_verify_identity=True)
    try:
        return pymysql.connect(**kwargs)
    except pymysql.err.OperationalError as e:
        # error text from MySQL never contains the password
        raise DbError(f"DB-Verbindung fehlgeschlagen / Konekcija nije uspjela: {e.args[0]} {e.args[1] if len(e.args) > 1 else ''}") from None


def jsonable(v: Any) -> Any:
    if isinstance(v, decimal.Decimal):
        return float(v) if v != v.to_integral_value() else int(v)
    if isinstance(v, (dt.datetime, dt.date, dt.time)):
        return v.isoformat()
    if isinstance(v, dt.timedelta):
        return v.total_seconds()
    if isinstance(v, (bytes, bytearray)):
        try:
            return v.decode("utf-8")
        except UnicodeDecodeError:
            return None
    return v


def clean_rows(rows: list[dict]) -> list[dict]:
    return [{k: jsonable(v) for k, v in r.items()} for r in rows]


@contextmanager
def read_cursor(cfg: Config) -> Iterator[pymysql.cursors.DictCursor]:
    conn = connect(cfg)
    try:
        with conn.cursor() as cur:
            cur.execute(f"SET SESSION MAX_EXECUTION_TIME = {QUERY_TIMEOUT_S * 1000}")
            cur.execute("START TRANSACTION READ ONLY")
            yield cur
        conn.rollback()
    finally:
        conn.close()


def query(cfg: Config, sql: str, params: Any = None, max_rows: int | None = None) -> list[dict]:
    assert_clean_sql(sql)
    with read_cursor(cfg) as cur:
        try:
            cur.execute(sql, params)
        except pymysql.err.MySQLError as e:
            code = e.args[0] if e.args else None
            if code == 3024:
                raise DbError(f"Abfrage-Timeout nach {QUERY_TIMEOUT_S} s / Upit prekinut nakon {QUERY_TIMEOUT_S} s") from None
            raise DbError(f"SQL-Fehler {code}: {e.args[1] if len(e.args) > 1 else e}") from None
        rows = cur.fetchmany(max_rows) if max_rows else cur.fetchall()
    return clean_rows(list(rows))


@contextmanager
def write_conn(cfg: Config) -> Iterator[pymysql.connections.Connection]:
    """Connection for one write transaction; caller commits, rollback on exception."""
    conn = connect(cfg)
    try:
        with conn.cursor() as cur:
            cur.execute("SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED")
            cur.execute(f"SET SESSION innodb_lock_wait_timeout = {QUERY_TIMEOUT_S}")
        conn.begin()
        yield conn
    except BaseException:
        try:
            conn.rollback()
        finally:
            conn.close()
        raise
    else:
        conn.close()


def execute(cur, sql: str, params: Any = None) -> int:
    assert_clean_sql(sql)
    return cur.execute(sql, params)
