"""Render the read-tool SQL with literal parameters (for checking against the real DB, e.g. with the mysql client).

No DB connection is made: db.query is replaced by a recorder. Usage: python3 scripts/render_sql.py > out.sql
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

from pymysql.converters import escape_item  # noqa: E402

from jsi_mcp import config, db, tools_read  # noqa: E402
from jsi_mcp.permissions import Principal  # noqa: E402

CAPTURED = []


def fake_query(cfg, sql, params=None, max_rows=None):
    db.assert_clean_sql(sql)
    if params is not None:
        sql = sql % tuple(escape_item(p, "utf8mb4") for p in params)
    CAPTURED.append(sql)
    return [{"n": 0, "dipl_id": None}]


db.query = fake_query
cfg = config.load({"JSI_AUTH_DISABLED": "true", "JSI_MCP_PUBLIC_URL": "http://localhost:1/mcp"})
P = Principal(sub="render", permissions=frozenset({"*"}))
for b in ("vermittlungen", "neue_kandidaten", "pipeline_bestand", "umsatz", "task_force", "casting", "dipl_funnel"):
    tools_read.kpis(cfg, P, b, od="2023-01-01", do="2024-01-01", gruppierung="jahr" if b != "casting" else "monat")
tools_read.orders_overview(cfg, P, firma="CARGLASS")
tools_read.pipeline_history(cfg, P, od="2023-01-01", do="2023-04-01")
tools_read.filter_options(cfg, P, "db")
for i, s in enumerate(CAPTURED):
    print(f"-- [{i}]\n{s};\n")
