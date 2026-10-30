"""Tool schemas + permission matrix through an in-process MCP client (no DB needed)."""
import json

import pytest
from mcp import Client

from jsi_mcp import config, server, tools_read
from jsi_mcp.permissions import KPI_AREA_PERMISSIONS, TOOL_PERMISSIONS

from testenv import LOCAL_ENV

EXPECTED = {"whoami", "search_candidates", "filter_options", "candidate_profile", "kpis", "orders_overview",
            "pipeline_history", "change_log", "record_preview", "record_write", "set_application_status"}


def mcp_for(perms: str, **env):
    cfg = config.load({**LOCAL_ENV, "JSI_DEV_PERMISSIONS": perms, **env})
    return server.build_mcp(cfg)


def text(res):
    return "".join(c.text for c in res.content if getattr(c, "type", "") == "text")


async def test_tool_list_and_schemas():
    async with Client(mcp_for("*")) as c:
        tools = {t.name: t for t in (await c.list_tools()).tools}
    assert set(tools) == EXPECTED == set(TOOL_PERMISSIONS)
    for t in tools.values():
        assert " / " in t.description, f"{t.name}: description must be DE / BS"
        props = t.input_schema.get("properties", {})
        assert "cfg" not in props and "p" not in props
    sc = tools["search_candidates"].input_schema["properties"]
    for key in tools_read.SPEC_KEYS:
        assert key in sc, f"search_candidates misses filter key {key}"
    assert sc["izlaz"]["enum"] == ["broj", "izvori", "lista", "id"] or "enum" in json.dumps(sc["izlaz"])
    assert tools["candidate_profile"].input_schema["required"] == ["kandidat_id"]
    assert tools["search_candidates"].annotations.read_only_hint is True
    assert tools["record_write"].annotations.read_only_hint is False
    assert set(json.dumps(tools["kpis"].input_schema).split('"')) >= set(KPI_AREA_PERMISSIONS)


async def test_whoami_without_db():
    async with Client(mcp_for("jsi:kandidati:read")) as c:
        res = await c.call_tool("whoami", {})
    data = json.loads(text(res))
    assert data["sub"] == "local-dev" and data["permissions"] == ["jsi:kandidati:read"]
    assert data["db_konfiguriert"] is False and data["schreiben_aktiv"] is False


@pytest.mark.parametrize("tool,args,perm", [
    ("search_candidates", {}, "jsi:kandidati:read"),
    ("filter_options", {}, "jsi:kandidati:read"),
    ("candidate_profile", {"kandidat_id": 1}, "jsi:kandidati:read"),
    ("kpis", {"bereich": "vermittlungen"}, "jsi:kennzahlen:read"),
    ("orders_overview", {}, "jsi:kennzahlen:read"),
    ("pipeline_history", {}, "jsi:kennzahlen:read"),
    ("change_log", {}, "jsi:audit:read"),
])
async def test_base_permission_denied(tool, args, perm):
    async with Client(mcp_for("jsi:nothing")) as c:
        res = await c.call_tool(tool, args)
    assert res.is_error and perm in text(res)


@pytest.mark.parametrize("bereich,perm", [("umsatz", "jsi:finansije:read"), ("dipl_funnel", "jsi:dipl:read")])
async def test_kpi_area_permission(bereich, perm):
    async with Client(mcp_for("jsi:kennzahlen:read")) as c:
        res = await c.call_tool("kpis", {"bereich": bereich})
    assert res.is_error and perm in text(res)


async def test_pii_needs_permission():
    async with Client(mcp_for("jsi:kandidati:read")) as c:
        r1 = await c.call_tool("search_candidates", {"izlaz": "lista", "pii": True})
        r2 = await c.call_tool("candidate_profile", {"kandidat_id": 5, "pii": True})
    assert r1.is_error and "jsi:kandidati:pii" in text(r1)
    assert r2.is_error and "jsi:kandidati:pii" in text(r2)


async def test_write_permission_per_entity_action():
    async with Client(mcp_for("jsi:write:candidate:update")) as c:
        r1 = await c.call_tool("record_preview", {"entity": "company", "action": "create", "values": {"company_name": "X"}})
        r2 = await c.call_tool("set_application_status", {"kandidat_id": 1, "status_id": 3})
        r3 = await c.call_tool("record_preview", {"entity": "application_status", "action": "update", "record_id": 1,
                                                  "values": {"kandidat_status_prijave": 3}})
    assert r1.is_error and "jsi:write:company:create" in text(r1)
    assert r2.is_error and "jsi:write:application_status:update" in text(r2)
    assert r3.is_error and "set_application_status" in text(r3)


async def test_db_not_configured_is_clear_error():
    async with Client(mcp_for("*")) as c:
        res = await c.call_tool("search_candidates", {"zanimanje": "Elektriker", "vozacka": "C"})
    assert res.is_error and "JSI_MIRROR_DB_HOST" in text(res)


async def test_invalid_filter_is_input_error():
    async with Client(mcp_for("*")) as c:
        res = await c.call_tool("search_candidates", {"vozacka": "Q"})
    assert res.is_error and "unknown licence category" in text(res)


async def test_record_write_refused_when_writes_disabled():
    async with Client(mcp_for("*", JSI_MIRROR_DB_HOST="h", JSI_MIRROR_DB_NAME="d", JSI_MIRROR_DB_USER="u",
                              JSI_MIRROR_DB_PASSWORD="p")) as c:
        res = await c.call_tool("record_write", {"entity": "company", "action": "create",
                                                 "values": {"company_name": "X"}, "dry_run": False})
    assert res.is_error and "JSI_WRITES_ENABLED" in text(res)


def test_unconfigured_app_reports_errors():
    from starlette.testclient import TestClient
    app = server.build_app(config.load({}))
    c = TestClient(app)
    h = c.get("/health").json()
    assert h["status"] == "degraded" and any("WORKOS_AUTHKIT_DOMAIN" in e for e in h["konfigurationsfehler"])
    r = c.post("/mcp", json={})
    assert r.status_code == 401 and "WORKOS_AUTHKIT_DOMAIN" in r.json()["error_description"]
    assert "WORKOS_AUTHKIT_DOMAIN" in r.headers["www-authenticate"]
