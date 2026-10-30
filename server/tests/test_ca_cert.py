"""JSI_DB_CA_CERT pasted into a hosting dashboard often loses its line breaks – the server must repair it."""
import datetime as dt

import pytest
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.x509.oid import NameOID

from jsi_mcp import config

DB_ENV = {
    "JSI_AUTH_DISABLED": "true",
    "JSI_MCP_PUBLIC_URL": "http://localhost:3000/mcp",
    "JSI_DB_TARGET": "mirror",
    "JSI_MIRROR_DB_HOST": "db.example",
    "JSI_MIRROR_DB_NAME": "jsicrm",
    "JSI_MIRROR_DB_USER": "u",
    "JSI_MIRROR_DB_PASSWORD": "p",
}


@pytest.fixture(scope="module")
def pem() -> str:
    key = ec.generate_private_key(ec.SECP256R1())
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "test-ca")])
    now = dt.datetime.now(dt.timezone.utc)
    cert = (x509.CertificateBuilder().subject_name(name).issuer_name(name).public_key(key.public_key())
            .serial_number(1).not_valid_before(now).not_valid_after(now + dt.timedelta(days=1))
            .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
            .sign(key, hashes.SHA256()))
    return cert.public_bytes(serialization.Encoding.PEM).decode()


def variants(pem: str) -> dict[str, str]:
    body = "".join(pem.strip().splitlines()[1:-1])
    return {
        "original": pem,
        "eine_zeile_mit_leerzeichen": pem.replace("\n", " "),
        "eine_zeile_ohne_trenner": pem.replace("\n", ""),
        "literal_backslash_n": pem.replace("\n", "\\n"),
        "in_anfuehrungszeichen": '"' + pem.strip() + '"',
        "crlf": pem.replace("\n", "\r\n"),
        "nur_base64": body,
    }


@pytest.mark.parametrize("variant", list(variants("-----BEGIN CERTIFICATE-----\nx\n-----END CERTIFICATE-----\n")))
def test_pasted_variants_are_repaired(pem, variant):
    raw = variants(pem)[variant]
    fixed = config.normalize_pem(raw)
    assert fixed and config.pem_is_valid(fixed), variant
    cfg = config.load({**DB_ENV, "JSI_DB_CA_CERT": raw})
    assert cfg.db.ca_pem == fixed
    assert not [e for e in cfg.errors if "CA" in e or "TLS" in e], cfg.errors


def test_garbage_is_reported_without_echoing_value():
    cfg = config.load({**DB_ENV, "JSI_DB_CA_CERT": "geheim-kein-zertifikat"})
    assert cfg.db.ca_pem is None
    msgs = " ".join(cfg.errors)
    assert "kein gültiges PEM" in msgs
    assert "geheim-kein-zertifikat" not in msgs


def test_invalid_base64_inside_markers_is_reported():
    raw = "-----BEGIN CERTIFICATE-----\nAAAA\n-----END CERTIFICATE-----"
    cfg = config.load({**DB_ENV, "JSI_DB_CA_CERT": raw})
    assert cfg.db.ca_pem is None
    assert any("kein gültiges PEM" in e for e in cfg.errors)
