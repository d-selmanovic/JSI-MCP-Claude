"""sql_query against MySQL 8.4 with the read-only user: checked statements run, limits and GRANTs hold."""
import pytest

from jsi_mcp import db, tools_sql
from jsi_mcp.sensitive import SensitiveColumnError


def run(cfg, sql, pii=False, limit=10):
    return db.query(cfg, tools_sql.check(sql, pii), None, limit + 1)


def test_count_and_group(ro_cfg):
    rows = run(ro_cfg, "SELECT kandidat_status, COUNT(*) AS n FROM idk_kandidati GROUP BY kandidat_status")
    assert rows and all("n" in r for r in rows)


def test_cte_and_join_outside_catalog_areas(ro_cfg):
    rows = run(ro_cfg, "WITH t AS (SELECT employee_id FROM idk_employees) SELECT COUNT(*) AS n FROM t")
    assert rows[0]["n"] >= 0


def test_row_limit(ro_cfg):
    assert len(run(ro_cfg, "SELECT kandidat_id FROM idk_kandidati", limit=1)) <= 2


def test_secret_column_refused_by_server_and_by_grant(ro_cfg):
    with pytest.raises(SensitiveColumnError):
        run(ro_cfg, "SELECT employee_password FROM idk_employees")
    conn = db.connect(ro_cfg)  # bypass the server check: MySQL itself refuses the column
    try:
        with conn.cursor() as cur, pytest.raises(Exception, match="(?i)denied"):
            cur.execute("SELECT employee_password FROM idk_employees LIMIT 1")
    finally:
        conn.close()


def test_read_only_transaction(ro_cfg):
    with pytest.raises(db.DbError):
        db.query(ro_cfg, "SELECT kandidat_id FROM idk_kandidati FOR UPDATE")
