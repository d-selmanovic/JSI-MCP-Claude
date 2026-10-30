"""Test RSA keys + JWT minting (own test keys, never real WorkOS keys)."""
import time

import jwt
from cryptography.hazmat.primitives.asymmetric import rsa

ISSUER = "https://test-authkit.example.com"
AUDIENCE = "https://jsi-mcp.example.com/mcp"

_KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)
_OTHER = rsa.generate_private_key(public_exponent=65537, key_size=2048)


class FakeJWKClient:
    def __init__(self, key=_KEY):
        self.key = key.public_key()

    def get_signing_key_from_jwt(self, token):
        class K:
            pass

        k = K()
        k.key = self.key
        return k


def mint(sub="user_01TEST", permissions=None, aud=AUDIENCE, iss=ISSUER, exp_in=600, key=_KEY, **extra):
    now = int(time.time())
    claims = {"sub": sub, "iss": iss, "aud": aud, "iat": now, "exp": now + exp_in, "client_id": "client_test"}
    if permissions is not None:
        claims["permissions"] = permissions
    claims.update(extra)
    return jwt.encode(claims, key, algorithm="RS256", headers={"kid": "test"})


OTHER_KEY = _OTHER
