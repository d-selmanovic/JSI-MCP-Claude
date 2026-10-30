"""WorkOS AuthKit token verification (this server is an OAuth Resource Server).

Tokens are JWTs signed by AuthKit. We check signature (JWKS), `iss`, `aud` (= JSI_MCP_PUBLIC_URL)
and `exp`. Permissions come from the `permissions` claim.
"""
from __future__ import annotations

import logging
from typing import Any

import anyio
import jwt
from mcp.server.auth.middleware.auth_context import get_access_token
from mcp.server.auth.provider import AccessToken

from .config import Config
from .permissions import Principal

log = logging.getLogger("jsi_mcp.auth")

ALGORITHMS = ["RS256", "RS384", "RS512", "ES256", "ES384"]


def _audiences(public_url: str) -> list[str]:
    u = public_url.rstrip("/")
    # Accept the URL with and without trailing slash; clients differ in how they send `resource`.
    out = [u, u + "/"]
    # Hosts like Manufact also publish the origin (without /mcp) as resource; same server, so accept it too.
    if u.endswith("/mcp"):
        base = u[: -len("/mcp")]
        out += [base, base + "/"]
    return out


class WorkOSTokenVerifier:
    def __init__(self, issuer: str, audience: str, jwks_url: str, jwk_client: Any | None = None):
        self.issuer = issuer
        self.audience = audience
        self._jwks = jwk_client or jwt.PyJWKClient(jwks_url, cache_keys=True, lifespan=3600, timeout=10)

    def _decode(self, token: str) -> dict[str, Any]:
        key = self._jwks.get_signing_key_from_jwt(token).key
        return jwt.decode(
            token,
            key,
            algorithms=ALGORITHMS,
            audience=_audiences(self.audience),
            issuer=self.issuer,
            options={"require": ["exp", "iss", "aud", "sub"]},
            leeway=30,
        )

    async def verify_token(self, token: str) -> AccessToken | None:
        try:
            claims = await anyio.to_thread.run_sync(self._decode, token)
        except Exception as e:  # invalid signature, expired, wrong aud/iss, JWKS unreachable
            log.info("token rejected: %s", type(e).__name__)
            return None
        aud = claims.get("aud")
        auds = aud if isinstance(aud, list) else [aud]
        resource = self.audience if any(a in _audiences(self.audience) for a in auds) else None
        scope = claims.get("scope") or ""
        return AccessToken(
            token=token,
            client_id=str(claims.get("client_id") or claims.get("azp") or ""),
            scopes=scope.split() if isinstance(scope, str) else list(scope),
            expires_at=claims.get("exp"),
            resource=resource,
            subject=str(claims.get("sub")),
            claims={k: claims.get(k) for k in ("iss", "org_id", "permissions", "role", "roles", "sid") if k in claims},
        )


def current_principal(cfg: Config) -> Principal:
    if cfg.auth_disabled:
        return Principal(sub="local-dev", permissions=frozenset(cfg.dev_permissions), client_id="local")
    tok = get_access_token()
    if tok is None:
        # The bearer middleware rejects unauthenticated requests before tools run; this is a safeguard.
        return Principal(sub="anonymous", permissions=frozenset())
    claims = tok.claims or {}
    perms = claims.get("permissions") or []
    if isinstance(perms, str):
        perms = perms.split()
    return Principal(
        sub=tok.subject or "unknown",
        permissions=frozenset(str(p) for p in perms),
        client_id=tok.client_id,
        org_id=claims.get("org_id"),
    )
