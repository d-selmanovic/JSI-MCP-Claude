"""Configuration from environment variables. Secrets are read here and never logged."""
from __future__ import annotations

import os
import re
import ssl
from dataclasses import dataclass, field
from urllib.parse import urlparse

PACKAGE_DIR = os.path.dirname(os.path.abspath(__file__))
SERVER_DIR = os.path.abspath(os.path.join(PACKAGE_DIR, "..", ".."))

ROW_LIMIT_DEFAULT = 200
ROW_LIMIT_MAX = 5000
QUERY_TIMEOUT_S = 30

ALL_PERMISSIONS_DEV = "*"


def _bool(name: str, default: bool = False) -> bool:
    v = os.environ.get(name)
    if v is None or v.strip() == "":
        return default
    return v.strip().lower() in ("1", "true", "yes", "on")


_PEM_BLOCK = re.compile(r"-----BEGIN CERTIFICATE-----(.*?)-----END CERTIFICATE-----", re.S)


def normalize_pem(raw: str | None) -> str | None:
    """Repairs a CA certificate pasted into an env var (quotes, literal \\n, newlines replaced by spaces,
    body without BEGIN/END lines). Returns a clean PEM string or None if nothing certificate-like is found."""
    if not raw:
        return None
    s = raw.strip().strip("'\"").replace("\\r", "").replace("\\n", "\n").replace("\r", "")
    bodies = _PEM_BLOCK.findall(s)
    if not bodies and re.fullmatch(r"[A-Za-z0-9+/=\s]+", s):
        bodies = [s]
    out = []
    for b in bodies:
        b64 = re.sub(r"\s+", "", b)
        if b64:
            out.append("-----BEGIN CERTIFICATE-----\n" + "\n".join(b64[i:i + 64] for i in range(0, len(b64), 64))
                       + "\n-----END CERTIFICATE-----\n")
    return "".join(out) or None


def pem_is_valid(pem: str) -> bool:
    try:
        ssl.create_default_context(cadata=pem)
        return True
    except (ssl.SSLError, ValueError):
        return False


@dataclass
class DbConfig:
    host: str | None
    port: int
    name: str | None
    user: str | None
    password: str | None = field(repr=False)
    ca_pem: str | None = field(repr=False)
    ca_file: str | None
    ssl_required: bool

    def missing(self) -> list[str]:
        return [k for k in ("host", "name", "user", "password") if not getattr(self, k)]


@dataclass
class Config:
    port: int
    db_target: str
    db: DbConfig
    db_prefix: str
    writes_enabled: bool
    auth_disabled: bool
    authkit_domain: str | None
    client_id: str | None
    public_url: str | None
    dev_permissions: list[str]
    write_employee_id: int
    lsp_izvor: int
    errors: list[str] = field(default_factory=list)

    @property
    def writes_allowed(self) -> bool:
        return self.writes_enabled and self.db_target == "mirror"

    @property
    def issuer(self) -> str | None:
        return f"https://{self.authkit_domain}" if self.authkit_domain else None

    @property
    def jwks_url(self) -> str | None:
        return f"https://{self.authkit_domain}/oauth2/jwks" if self.authkit_domain else None

    def db_ready(self) -> bool:
        return not self.db.missing() and self.db_target in ("mirror", "prod")


class StartupRefused(RuntimeError):
    pass


def _is_local_url(url: str | None) -> bool:
    if not url:
        return False
    p = urlparse(url)
    return p.scheme == "http" and (p.hostname in ("localhost", "127.0.0.1", "::1"))


def load(env: dict[str, str] | None = None) -> Config:
    if env is not None:
        old = dict(os.environ)
        os.environ.clear()
        os.environ.update(env)
    try:
        return _load()
    finally:
        if env is not None:
            os.environ.clear()
            os.environ.update(old)


def _load() -> Config:
    errors: list[str] = []
    target = (os.environ.get("JSI_DB_TARGET") or "mirror").strip().lower()
    if target not in ("mirror", "prod"):
        errors.append(f"JSI_DB_TARGET muss 'mirror' oder 'prod' sein (ist: {target!r}).")
    prefix = "JSI_MIRROR_DB_" if target == "mirror" else "JSI_DB_"
    try:
        db_port = int(os.environ.get(prefix + "PORT") or 3306)
    except ValueError:
        errors.append(f"{prefix}PORT ist keine Zahl.")
        db_port = 3306
    ca_file = os.environ.get("JSI_DB_CA_FILE") or os.path.join(SERVER_DIR, "certs", "aiven-ca.pem")
    db = DbConfig(
        host=os.environ.get(prefix + "HOST") or None,
        port=db_port,
        name=os.environ.get(prefix + "NAME") or None,
        user=os.environ.get(prefix + "USER") or None,
        password=os.environ.get(prefix + "PASSWORD") or None,
        ca_pem=normalize_pem(os.environ.get("JSI_DB_CA_CERT")),
        ca_file=ca_file if os.path.isfile(ca_file) else None,
        ssl_required=_bool("JSI_DB_SSL_REQUIRED", True),
    )
    for m in db.missing():
        errors.append(f"Datenbank nicht konfiguriert: {prefix}{m.upper()} fehlt.")
    if os.environ.get("JSI_DB_CA_CERT") and not (db.ca_pem and pem_is_valid(db.ca_pem)):
        errors.append("JSI_DB_CA_CERT ist gesetzt, enthält aber kein gültiges PEM-Zertifikat "
                      "(-----BEGIN CERTIFICATE----- … -----END CERTIFICATE-----).")
        db = DbConfig(**{**db.__dict__, "ca_pem": None})
    if db.ssl_required and not (db.ca_pem or db.ca_file):
        errors.append("TLS verlangt, aber kein CA-Zertifikat: JSI_DB_CA_CERT (PEM-Inhalt) oder certs/aiven-ca.pem fehlt.")

    auth_disabled = _bool("JSI_AUTH_DISABLED")
    public_url = (os.environ.get("JSI_MCP_PUBLIC_URL") or "").strip() or None
    domain = (os.environ.get("WORKOS_AUTHKIT_DOMAIN") or "").strip() or None
    if domain:
        domain = domain.removeprefix("https://").removeprefix("http://").rstrip("/")
    if auth_disabled and not _is_local_url(public_url):
        raise StartupRefused(
            "JSI_AUTH_DISABLED=true ist nur lokal erlaubt (JSI_MCP_PUBLIC_URL muss http://localhost:<port>/mcp "
            "oder http://127.0.0.1:<port>/mcp sein). Start verweigert."
        )
    if not auth_disabled:
        if not domain:
            errors.append("Auth nicht konfiguriert: WORKOS_AUTHKIT_DOMAIN fehlt.")
        if not public_url:
            errors.append("Auth nicht konfiguriert: JSI_MCP_PUBLIC_URL fehlt (Resource Indicator / Token-Audience).")

    writes_enabled = _bool("JSI_WRITES_ENABLED")
    if writes_enabled and target != "mirror":
        errors.append("JSI_WRITES_ENABLED=true wird ignoriert: Schreiben nur bei JSI_DB_TARGET=mirror.")

    dev_perms = [p.strip() for p in (os.environ.get("JSI_DEV_PERMISSIONS") or ALL_PERMISSIONS_DEV).split(",") if p.strip()]

    def _int(name: str, default: int) -> int:
        try:
            return int(os.environ.get(name) or default)
        except ValueError:
            errors.append(f"{name} ist keine Zahl.")
            return default

    return Config(
        port=_int("PORT", 3000),
        db_target=target,
        db=db,
        db_prefix=prefix,
        writes_enabled=writes_enabled,
        auth_disabled=auth_disabled,
        authkit_domain=domain,
        client_id=os.environ.get("WORKOS_CLIENT_ID") or None,
        public_url=public_url,
        dev_permissions=dev_perms,
        write_employee_id=_int("JSI_WRITE_EMPLOYEE_ID", 0),
        lsp_izvor=_int("JSI_LSP_IZVOR", 1),
        errors=errors,
    )
