"""/admin status page: off without password, HTTP Basic, no secret values, works next to WorkOS bearer auth."""
import base64

import pytest
from starlette.testclient import TestClient

from jsi_mcp import admin, auth, config, server

from jwt_helpers import AUDIENCE, FakeJWKClient

PW = "admin-test-passwort-1234"
ENV = {"WORKOS_AUTHKIT_DOMAIN": "test-authkit.example.com", "JSI_MCP_PUBLIC_URL": AUDIENCE,
       "JSI_MIRROR_DB_HOST": "db.example", "JSI_MIRROR_DB_NAME": "jsicrm", "JSI_MIRROR_DB_USER": "u",
       "JSI_MIRROR_DB_PASSWORD": "geheimes-db-passwort", "JSI_DB_SSL_REQUIRED": "false", "JSI_DB_TARGET": "mirror"}


def basic(user, pw):
    return {"Authorization": "Basic " + base64.b64encode(f"{user}:{pw}".encode()).decode()}


@pytest.fixture
def make_client(monkeypatch):
    orig = auth.WorkOSTokenVerifier.__init__
    monkeypatch.setattr(auth.WorkOSTokenVerifier, "__init__",
                        lambda self, i, a, j, jwk_client=None: orig(self, i, a, j, jwk_client=FakeJWKClient()))
    monkeypatch.setattr(admin, "_db_check", lambda cfg: {"ok": False, "fehler": "OperationalError"})
    monkeypatch.setattr(admin, "_writes", lambda cfg: {"verfuegbar": False})

    def make(**env):
        cfg = config.load({**ENV, **env})
        return TestClient(server.build_app(cfg), base_url="https://jsi-mcp.example.com")
    return make


def test_off_without_password(make_client):
    with make_client() as c:
        assert c.get("/admin").status_code == 404
        assert c.get("/admin/status.json").status_code == 404


def test_short_password_disables_and_reports(make_client):
    with make_client(JSI_ADMIN_PASSWORD="kurz") as c:
        assert c.get("/admin", headers=basic("admin", "kurz")).status_code == 404
    cfg = config.load({**ENV, "JSI_ADMIN_PASSWORD": "kurz"})
    assert any("JSI_ADMIN_PASSWORD" in e for e in cfg.errors) and "kurz" not in " ".join(cfg.errors)


def test_basic_auth_required(make_client):
    with make_client(JSI_ADMIN_PASSWORD=PW) as c:
        r = c.get("/admin")
        assert r.status_code == 401 and r.headers["www-authenticate"].startswith("Basic")
        assert c.get("/admin", headers=basic("admin", PW + "x")).status_code == 401
        assert c.get("/admin", headers=basic("root", PW)).status_code == 401
        assert c.get("/admin", headers={"Authorization": "Bearer abc"}).status_code == 401


def test_page_and_json_without_secret_values(make_client):
    admin.record("user_123", "search_candidates", "ok", 12, 3)
    with make_client(JSI_ADMIN_PASSWORD=PW) as c:
        r = c.get("/admin", headers=basic("admin", PW))
        assert r.status_code == 200 and "JSI MCP – Status" in r.text
        assert r.headers["cache-control"] == "no-store" and r.headers["x-frame-options"] == "DENY"
        j = c.get("/admin/status.json", headers=basic("admin", PW)).json()
    for body in (r.text, str(j)):
        assert "geheimes-db-passwort" not in body and PW not in body
    assert j["konfiguration"]["db_ziel"] == "mirror" and j["datenbank"]["ok"] is False
    assert "table_read" in j["tools"] and "candidate_update" in j["tools"]
    assert j["aufrufe_zaehler"]["search_candidates"]["ok"] >= 1
    assert j["letzte_aufrufe"][0]["tool"] == "search_candidates"


def test_mcp_still_needs_bearer(make_client):
    with make_client(JSI_ADMIN_PASSWORD=PW) as c:
        r = c.post("/mcp", json={"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}},
                   headers={**basic("admin", PW), "Accept": "application/json, text/event-stream",
                            "Content-Type": "application/json"})
        assert r.status_code == 401  # the admin password never opens the MCP endpoint
