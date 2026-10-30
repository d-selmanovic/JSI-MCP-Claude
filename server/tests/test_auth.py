import pytest

from jsi_mcp import config
from jsi_mcp.auth import WorkOSTokenVerifier
from jsi_mcp.permissions import Principal

from jwt_helpers import AUDIENCE, ISSUER, OTHER_KEY, FakeJWKClient, mint


@pytest.fixture
def verifier():
    return WorkOSTokenVerifier(ISSUER, AUDIENCE, "unused", jwk_client=FakeJWKClient())


async def test_valid_token(verifier):
    tok = await verifier.verify_token(mint(permissions=["jsi:kandidati:read"], org_id="org_1"))
    assert tok is not None
    assert tok.subject == "user_01TEST"
    assert tok.resource == AUDIENCE
    assert tok.claims["permissions"] == ["jsi:kandidati:read"]
    assert tok.claims["org_id"] == "org_1"


async def test_trailing_slash_audience_accepted(verifier):
    assert await verifier.verify_token(mint(aud=AUDIENCE + "/")) is not None


@pytest.mark.parametrize("kw", [
    {"aud": "https://other.example.com/mcp"},
    {"iss": "https://evil.example.com"},
    {"exp_in": -120},
    {"key": OTHER_KEY},
])
async def test_rejected(verifier, kw):
    assert await verifier.verify_token(mint(**kw)) is None


async def test_garbage_rejected(verifier):
    assert await verifier.verify_token("not-a-jwt") is None


def test_principal_wildcards():
    p = Principal(sub="x", permissions=frozenset({"jsi:write:candidate:*", "jsi:kandidati:read"}))
    assert p.has("jsi:write:candidate:update") and p.has("jsi:kandidati:read")
    assert not p.has("jsi:write:company:update") and not p.has("jsi:kandidati:pii")
    assert Principal(sub="a", permissions=frozenset({"jsi:write:*"})).has("jsi:write:company:create")
    assert Principal(sub="a", permissions=frozenset({"*"})).has("jsi:finansije:read")


def test_auth_disabled_refused_for_public_url():
    with pytest.raises(config.StartupRefused):
        config.load({"JSI_AUTH_DISABLED": "true", "JSI_MCP_PUBLIC_URL": "https://jsi.example.com/mcp"})
    with pytest.raises(config.StartupRefused):
        config.load({"JSI_AUTH_DISABLED": "true"})  # no URL -> not provably local


def test_auth_disabled_local_ok():
    cfg = config.load({"JSI_AUTH_DISABLED": "true", "JSI_MCP_PUBLIC_URL": "http://127.0.0.1:3000/mcp"})
    assert cfg.auth_disabled


def test_missing_config_is_reported_not_fatal():
    cfg = config.load({})
    assert any("WORKOS_AUTHKIT_DOMAIN" in e for e in cfg.errors)
    assert any("JSI_MIRROR_DB_HOST" in e for e in cfg.errors)
    assert not cfg.db_ready()
    assert not cfg.writes_allowed


def test_writes_only_on_mirror():
    base = {"WORKOS_AUTHKIT_DOMAIN": "x.authkit.app", "JSI_MCP_PUBLIC_URL": "https://a/mcp", "JSI_WRITES_ENABLED": "true"}
    assert config.load({**base, "JSI_DB_TARGET": "mirror"}).writes_allowed
    cfg = config.load({**base, "JSI_DB_TARGET": "prod"})
    assert not cfg.writes_allowed
    assert any("ignoriert" in e for e in cfg.errors)


def test_domain_normalised():
    cfg = config.load({"WORKOS_AUTHKIT_DOMAIN": "https://x.authkit.app/", "JSI_MCP_PUBLIC_URL": "https://a/mcp"})
    assert cfg.issuer == "https://x.authkit.app" and cfg.jwks_url == "https://x.authkit.app/oauth2/jwks"
