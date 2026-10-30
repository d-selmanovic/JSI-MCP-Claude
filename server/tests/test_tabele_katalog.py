"""tabele_katalog.json: [TAJNO] never present, known personal-data columns marked pii, catalog up to date."""
import json
import os
import subprocess
import sys

from jsi_mcp import tools_tables
from jsi_mcp.sensitive import SENSITIVE

HERE = os.path.dirname(os.path.abspath(__file__))
MUST_BE_PII = [
    ("idk_kandidati", c) for c in ("kandidat_ime", "kandidat_prezime", "kandidat_email", "kandidat_mobitel",
                                   "kandidat_adresa", "kandidat_datumrodjenja", "kandidat_djevojackoprezime",
                                   "kandidat_mjestorodjenja", "kandidat_korisnickoime")
] + [("idk_kandidat_kontakt_info", "kki_podatak"), ("idk_contacts_info", "ci_data"), ("idk_companies_info", "comi_data"),
     ("idk_clients", "client_telephone"), ("idk_clients", "client_email"), ("idk_contacts", "contact_firstname"),
     ("idk_sms_messages", "sms_number"), ("idk_sms_messages", "sms_content"), ("idk_notes", "note_txt"),
     ("idk_nd_kandidata", "ime_nd_kandidata"), ("idk_dak_kandidati", "tel_dak_kandidat"), ("idk_pp_users", "pu_email"),
     ("users", "phone"), ("users", "email")]


def _cols():
    return {(t, c): m for a in tools_tables.catalog()["podrucja"].values() for t, e in a["tabele"].items()
            for c, m in e["kolone"].items()}


def test_no_tajno_columns():
    cols = _cols()
    leaked = [(t, c) for t, cs in SENSITIVE.items() for c in cs if (t, c) in cols]
    assert not leaked


def test_known_personal_data_is_pii():
    cols = _cols()
    missing = [x for x in MUST_BE_PII if x in cols and not cols[x]["pii"]]
    assert not missing
    assert all(x in cols for x in MUST_BE_PII), [x for x in MUST_BE_PII if x not in cols]


def test_free_text_is_pii():
    cols = _cols()
    for (t, c), m in cols.items():
        if m["tip"].split("(")[0] in ("text", "mediumtext", "longtext") and t not in (
                "idk_email_text", "idk_reject_reasons", "idk_razlozi_odbijanja", "idk_pp_reminder_types", "idk_chat_type",
                "idk_provider_for_sending_messages", "idk_pp_document_types", "idk_pp_documents_statuses",
                "idk_kandidat_pozicija"):
            assert m["pii"], (t, c)


def test_catalog_matches_generator(tmp_path):
    """The committed JSON is exactly what scripts/gen_tabele.py produces."""
    path = os.path.join(HERE, "..", "src", "jsi_mcp", "tabele_katalog.json")
    before = open(path, encoding="utf-8").read()
    subprocess.run([sys.executable, "-I", os.path.join(HERE, "..", "scripts", "gen_tabele.py")], check=True,
                   capture_output=True)
    assert open(path, encoding="utf-8").read() == before, "tabele_katalog.json veraltet – gen_tabele.py ausführen"
    assert json.loads(before)["podrucja"]


def test_filter_catalog_matches_generator():
    """filter_catalog.json (server) and filteri.md (skill doc) are exactly what scripts/filter_catalog.py writes."""
    repo = os.path.join(HERE, "..", "..")
    files = [os.path.join(repo, "server", "src", "jsi_mcp", "filter_catalog.json"),
             os.path.join(repo, "server", "src", "jsi_mcp", "skills", "jsi-kandidat-filter", "references", "filteri.md")]
    before = [open(f, encoding="utf-8").read() for f in files]
    subprocess.run([sys.executable, "-I", os.path.join(HERE, "..", "scripts", "filter_catalog.py")], check=True,
                   capture_output=True)
    assert [open(f, encoding="utf-8").read() for f in files] == before, "Filterkatalog veraltet – filter_catalog.py ausführen"
