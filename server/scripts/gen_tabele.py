"""Generate src/jsi_mcp/tabele_katalog.json: readable tables per area for table_read/table_describe.

Sources: docs/rohdaten/columns.json (schema), docs/rohdaten/counts.tsv (row counts),
src/jsi_mcp/skills/jsi-data-analyst/references/schema/NN_*.md (area of each table), sensitive.SENSITIVE ([TAJNO]).
[TAJNO] columns are left out entirely. Columns holding personal data are marked "pii" (shown only with
jsi:kandidati:pii). Review the printed PII list after changes – the rules are name based.

Usage: python3 -I scripts/gen_tabele.py            (writes the JSON, prints the PII columns)
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
REPO = os.path.abspath(os.path.join(ROOT, ".."))
sys.path.insert(0, os.path.join(ROOT, "src"))
from jsi_mcp.sensitive import SENSITIVE  # noqa: E402

AREAS = {  # schema doc → (key, label, extra permissions for some tables)
    "01_kandidati": ("kandidati", "Kandidaten / Kandidati"),
    "02_pipeline_logovi": ("pipeline", "Pipeline-Logs / Logovi statusa"),
    "03_task_force_casting": ("taskforce", "Task Force & Casting"),
    "04_komunikacija": ("komunikacija", "Kommunikation / Komunikacija"),
    "05_nalozi_projekti_firme": ("firme", "Aufträge, Projekte, Firmen, Kontakte / Nalozi, projekti, firme"),
    "06_partner_portal_poslodavci": ("partner_portal", "Partnerportal, Unterlagen / Partner portal, dokumenti"),
    "08_dipl_nostrifikacija": ("dipl", "DIPL / Nostrifikacija"),
}
FINANCE_TABLE = re.compile(r"financ|racun|predracun|provizij|uplat|cijen|price", re.I)

# personal data: tokens of the column name (split at "_" and camelCase)
PII_TOKENS = {
    "ime", "prezime", "firstname", "lastname", "nickname", "fullname", "mobitel", "mobile", "telefon", "telefona",
    "tel", "phone", "email", "mail", "adresa", "address", "ulica", "street", "postanski", "zipcode", "zip", "skype",
    "viber", "whatsapp", "facebook", "linkedin", "instagram", "jmbg", "pasos", "passport", "dob", "birth",
    "datumrodjenja", "rodjenja", "ip", "image", "slika", "foto", "photo", "fname", "lname", "file", "files",
    "prilog", "slike",
}
PII_EXACT = {  # names that the token rule does not catch
    ("users", "name"), ("idk_dak_kandidati", "name_dak_kandidat"), ("idk_companies", "company_contact"),
    ("idk_contacts", "contact_info"), ("idk_contacts", "contact_inote"), ("idk_contacts", "contact_city"),
    ("idk_kandidati", "kandidat_destinacija_postanski_broj"),
    ("idk_kandidat_kontakt_info", "kki_podatak"),  # the contact value itself (phone, e-mail, …)
    ("idk_sms_messages", "sms_number"), ("idk_kandidat_cv", "kcv_ba"), ("idk_kandidat_cv", "kcv_de"),
    ("idk_documents", "document_desc"),
    ("idk_contacts_info", "ci_data"), ("idk_companies_info", "comi_data"),  # contact values (phone, e-mail, …)
}
# stems inside compound names (kandidat_djevojackoprezime, kandidat_mjestorodjenja, client_telephone, …)
PII_SUBSTR = ("prezime", "rodjenj", "korisnickoime", "telephone", "telefon", "mobitel", "adresa", "email", "passport",
              "pasos", "jmbg")
NOT_PII = {  # lookup / template tables: "name"/"email" columns are labels, not people
    "idk_email_text", "idk_reject_reasons", "idk_razlozi_odbijanja", "idk_pp_reminder_types", "idk_chat_type",
    "idk_provider_for_sending_messages", "idk_pp_document_types", "idk_pp_documents_statuses",
    "idk_kandidat_pozicija",  # catalogue of positions, not people
}
FILE_NAME = re.compile(r"(file_?name|document_name|_path$|url$)", re.I)
TEXT_TYPES = ("text", "mediumtext", "longtext", "tinytext", "json", "blob", "longblob", "mediumblob")


def tokens(col: str) -> set[str]:
    s = re.sub(r"([a-z])([A-Z])", r"\1_\2", col).lower()
    return set(filter(None, s.split("_")))


def is_pii(table: str, col: str, typ: str, table_cols: list[str]) -> bool:
    if (table, col) in PII_EXACT:
        return True
    if table in NOT_PII:
        return False
    if tokens(col) & PII_TOKENS or any(s in col.lower() for s in PII_SUBSTR):
        return True
    if FILE_NAME.search(col):
        return True
    # free text (notes, messages, logs, descriptions) may contain personal data – privacy by default
    if typ.lower().split("(")[0] in TEXT_TYPES:
        return True
    return False


def main() -> None:
    rows = json.load(open(os.path.join(REPO, "docs", "rohdaten", "columns.json"), encoding="utf-8"))["rows"]
    cols: dict[str, list[dict]] = {}
    for r in sorted(rows, key=lambda r: (r["t"], int(r["pos"]))):
        cols.setdefault(r["t"], []).append(r)
    counts = {}
    for line in open(os.path.join(REPO, "docs", "rohdaten", "counts.tsv"), encoding="utf-8"):
        p = line.rstrip("\n").split("\t")
        if len(p) >= 2 and p[1].isdigit():
            counts[p[0]] = int(p[1])
    schema_dir = os.path.join(ROOT, "src", "jsi_mcp", "skills", "jsi-data-analyst", "references", "schema")
    out = {"_doc": "Generiert von scripts/gen_tabele.py – nicht von Hand ändern. [TAJNO]-Spalten fehlen absichtlich.",
           "podrucja": {}}
    pii_list = []
    for stem, (key, label) in AREAS.items():
        text = open(os.path.join(schema_dir, stem + ".md"), encoding="utf-8").read()
        tables = [t for t in dict.fromkeys(re.findall(r"^#+\s*`?(\w+)`?", text, re.M)) if t in cols]
        area = {"naziv": label, "permission": f"jsi:tabele:{key}", "tabele": {}}
        for t in tables:
            names = [c["col"] for c in cols[t]]
            secret = SENSITIVE.get(t, frozenset())
            entry = {"redova_cca": counts.get(t), "pk": [c["col"] for c in cols[t] if c.get("ckey") == "PRI"], "kolone": {}}
            if FINANCE_TABLE.search(t):
                entry["dodatna_permission"] = "jsi:finansije:read"
            for c in cols[t]:
                if c["col"] in secret:
                    continue
                pii = is_pii(t, c["col"], c["typ"], names)
                entry["kolone"][c["col"]] = {"tip": c["typ"], "opis": (c.get("cmt") or "")[:300], "pii": pii}
                if pii:
                    pii_list.append(f"{t}.{c['col']}")
            area["tabele"][t] = entry
        out["podrucja"][key] = area
    path = os.path.join(ROOT, "src", "jsi_mcp", "tabele_katalog.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1, sort_keys=False)
        f.write("\n")
    n_t = sum(len(a["tabele"]) for a in out["podrucja"].values())
    print(f"{path}: {len(out['podrucja'])} Bereiche, {n_t} Tabellen, {len(pii_list)} PII-Spalten")
    for x in pii_list:
        print("PII", x)


if __name__ == "__main__":
    main()
