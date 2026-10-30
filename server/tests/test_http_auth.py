"""HTTP layer: 401 + WWW-Authenticate(resource_metadata), protected-resource metadata, bearer tokens."""
import pytest
from starlette.testclient import TestClient

from jsi_mcp import auth, config, server

from jwt_helpers import AUDIENCE, FakeJWKClient, mint

ENV = {"WORKOS_AUTHKIT_DOMAIN": "test-authkit.example.com", "JSI_MCP_PUBLIC_URL": AUDIENCE}
INIT = {"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}
HDR = {"Accept": "application/json, text/event-stream", "Content-Type": "application/json",
       "MCP-Protocol-Version": "2025-06-18"}


@pytest.fixture
def client(monkeypatch):
    orig = auth.WorkOSTokenVerifier.__init__

    def fake_init(self, issuer, audience, jwks_url, jwk_client=None):
        orig(self, issuer, audience, jwks_url, jwk_client=FakeJWKClient())

    monkeypatch.setattr(auth.WorkOSTokenVerifier, "__init__", fake_init)
    cfg = config.load(ENV)
    with TestClient(server.build_app(cfg), base_url="https://jsi-mcp.example.com") as c:
        yield c


def test_401_with_resource_metadata(client):
    r = client.post("/mcp", json=INIT, headers=HDR)
    assert r.status_code == 401
    www = r.headers["www-authenticate"]
    assert www.startswith("Bearer") and 'resource_metadata="https://jsi-mcp.example.com/.well-known/oauth-protected-resource/mcp"' in www


def test_invalid_token_401(client):
    r = client.post("/mcp", json=INIT, headers={**HDR, "Authorization": "Bearer " + mint(aud="https://x/mcp")})
    assert r.status_code == 401


def test_protected_resource_metadata(client):
    for path in ("/.well-known/oauth-protected-resource/mcp", "/.well-known/oauth-protected-resource"):
        r = client.get(path)
        assert r.status_code == 200, path
        d = r.json()
        assert d["resource"].rstrip("/") == AUDIENCE
        assert [s.rstrip("/") for s in d["authorization_servers"]] == ["https://test-authkit.example.com"]


def test_health_is_public(client):
    assert client.get("/health").status_code == 200


def test_valid_token_lists_tools_and_permissions_apply(client):
    tok = mint(permissions=["jsi:kandidati:read"])
    r = client.post("/mcp", json=INIT, headers={**HDR, "Authorization": "Bearer " + tok})
    assert r.status_code == 200, r.text
    names = {t["name"] for t in r.json()["result"]["tools"]}
    assert "search_candidates" in names
    call = {"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "whoami", "arguments": {}}}
    r = client.post("/mcp", json=call, headers={**HDR, "Authorization": "Bearer " + tok})
    body = r.json()["result"]
    assert "user_01TEST" in body["content"][0]["text"] and "jsi:kandidati:read" in body["content"][0]["text"]
    call["params"] = {"name": "kpis", "arguments": {"bereich": "vermittlungen"}}
    r = client.post("/mcp", json=call, headers={**HDR, "Authorization": "Bearer " + tok})
    assert r.json()["result"]["isError"] is True and "jsi:kennzahlen:read" in r.json()["result"]["content"][0]["text"]
