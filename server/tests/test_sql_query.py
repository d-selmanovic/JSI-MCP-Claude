"""sql_query: permission, human confirmation (form elicitation), refusal without a dialog, statement checks.

In-process MCP client, db.query replaced by a fake (no DB needed). Against MySQL: tests/integration/test_sql.py.
"""
import json

import pytest
from mcp import Client, types

from jsi_mcp import config, db, server, tools_sql
from jsi_mcp.sensitive import SensitiveColumnError
from jsi_mcp.tools_read import InputError

from testenv import LOCAL_ENV

ADMIN = "jsi:sql:read,jsi:kandidati:pii"


def mcp_for(perms: str):
    return server.build_mcp(config.load({**LOCAL_ENV, "JSI_DEV_PERMISSIONS": perms}))


def text(res):
    return "".join(c.text for c in res.content if getattr(c, "type", "") == "text")


@pytest.fixture
def fake_db(monkeypatch):
    calls = []

    def query(cfg, sql, params=None, max_rows=None):
        calls.append((sql, max_rows))
        return [{"n": i} for i in range(min(max_rows or 3, 3))]

    monkeypatch.setattr(db, "query", query)
    return calls


def dialog(answer: str, ausfuehren: bool = True, seen: list | None = None):
    async def cb(ctx, params):
        if seen is not None:
            seen.append(params.message)
        if answer == "accept":
            return types.ElicitResult(action="accept", content={"ausfuehren": ausfuehren})
        return types.ElicitResult(action=answer)
    return cb


SQL = "SELECT kandidat_status, COUNT(*) AS n FROM idk_kandidati GROUP BY kandidat_status"


async def test_confirmed_query_runs_and_shows_the_statement(fake_db):
    seen = []
    async with Client(mcp_for(ADMIN), elicitation_callback=dialog("accept", seen=seen)) as c:
        assert c.protocol_version >= tools_sql.MIN_PROTOCOL
        res = await c.call_tool("sql_query", {"sql": SQL + ";", "limit": 2})
    out = json.loads(text(res))
    assert out["izvrseno"] is True and out["broj_redova"] == 2 and out["stranica"]["ima_jos"] is True
    assert fake_db == [(SQL, 3)]  # limit + 1 to detect more rows; trailing ';' removed
    assert len(seen) == 1 and SQL in seen[0]


@pytest.mark.parametrize("answer,ausfuehren", [("decline", True), ("cancel", True), ("accept", False)])
async def test_not_confirmed_nothing_runs(fake_db, answer, ausfuehren):
    async with Client(mcp_for(ADMIN), elicitation_callback=dialog(answer, ausfuehren)) as c:
        out = json.loads(text(await c.call_tool("sql_query", {"sql": SQL})))
    assert out["izvrseno"] is False and fake_db == []


async def test_client_without_dialog_is_refused(fake_db):
    async with Client(mcp_for(ADMIN)) as c:  # no elicitation capability
        res = await c.call_tool("sql_query", {"sql": SQL})
    assert res.is_error and "Bestätigung" in text(res) and fake_db == []


async def test_legacy_protocol_is_refused(fake_db):
    seen = []
    async with Client(mcp_for(ADMIN), mode="legacy", elicitation_callback=dialog("accept", seen=seen)) as c:
        res = await c.call_tool("sql_query", {"sql": SQL})
    assert res.is_error and "Protokoll 2025-11-25" in text(res) and fake_db == [] and seen == []


@pytest.mark.parametrize("perms,args", [
    ("jsi:kandidati:read,jsi:kandidati:pii", {"sql": SQL}),                     # no jsi:sql:read
    ("jsi:sql:read", {"sql": "SELECT kandidat_id FROM idk_kandidati", "pii": True}),  # pii without permission
])
async def test_permissions_checked_before_the_dialog(fake_db, perms, args):
    seen = []
    async with Client(mcp_for(perms), elicitation_callback=dialog("accept", seen=seen)) as c:
        res = await c.call_tool("sql_query", args)
    assert res.is_error and seen == [] and fake_db == []


async def test_only_admin_role_has_sql():
    from jsi_mcp.permissions import ROLE_PERMISSIONS, SQL_READ
    assert [r for r, perms in ROLE_PERMISSIONS.items() if SQL_READ in perms] == ["jsi-admin-test"]


async def test_tool_is_not_marked_read_only():
    async with Client(mcp_for(ADMIN)) as c:
        tool = next(t for t in (await c.list_tools()).tools if t.name == "sql_query")
    assert tool.annotations.read_only_hint is False and "ok" not in tool.input_schema["properties"]


@pytest.mark.parametrize("sql", [
    "SELECT * FROM idk_kandidati",
    "SELECT k.* FROM idk_kandidati k",
    "SELECT DISTINCT * FROM idk_nalozi",
    "SELECT 1; DROP TABLE idk_kandidati",
    "DELETE FROM idk_kandidati",
    "WITH x AS (SELECT 1) DELETE FROM idk_kandidati",
    "UPDATE idk_kandidati SET kandidat_status = 3",
    "SELECT kandidat_id INTO OUTFILE '/tmp/x' FROM idk_kandidati",
    "SELECT kandidat_id FROM idk_kandidati FOR UPDATE",
    "SELECT SLEEP(100)",
    "SELECT LOAD_FILE('/etc/passwd')",
    "SELECT 1 /*!50000 , kandidat_password */",
    "EXPLAIN ANALYZE SELECT 1",
    "SHOW TABLES",
    "",
])
def test_rejected_statements(sql):
    with pytest.raises((InputError, SensitiveColumnError)):
        tools_sql.check(sql, pii=True)


def test_secret_and_pii_columns():
    with pytest.raises(SensitiveColumnError):
        tools_sql.check("SELECT employee_password FROM idk_employees", pii=True)
    with pytest.raises(InputError, match="Personendaten"):
        tools_sql.check("SELECT kandidat_ime FROM idk_kandidati", pii=False)
    assert tools_sql.check("SELECT kandidat_ime FROM idk_kandidati", pii=True)


@pytest.mark.parametrize("sql", [
    SQL,
    "WITH n AS (SELECT kandidat_id FROM idk_kandidati) SELECT COUNT(*) FROM n",
    "EXPLAIN SELECT kandidat_id FROM idk_kandidati WHERE kandidat_status <> 3",
    "SELECT kandidat_id FROM idk_kandidati WHERE kandidat_porijeklo = 'a;b' -- Kommentar",
    "SELECT 2 * 3 AS x",
    "(SELECT kandidat_id FROM idk_kandidati LIMIT 1)",
])
def test_allowed_statements(sql):
    assert tools_sql.check(sql, pii=False)
