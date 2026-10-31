"""Read tools. All SQL is fixed or built by build_query.py (free SQL only in tools_sql.sql_query).

Convention: our own SQL is always executed with a params tuple, so literal % is written as %%.
"""
from __future__ import annotations

import datetime as dt
import re
from typing import Any

from . import build_query as bq
from . import db
from .config import ROW_LIMIT_DEFAULT, ROW_LIMIT_MAX, Config
from .permissions import (
    DIPL_READ,
    KANDIDATI_PII,
    KPI_AREA_PERMISSIONS,
    Principal,
    require,
)

DATA_NOTE = "Kandidatska aktivnost u bazi uglavnom prestaje u februaru 2026 (stanje podataka). / Kandidatenaktivität endet weitgehend im Feb 2026."

LSP_IZVOR = {1: "CRM", 2: "PP", 3: "bot", 4: "queue", 5: "cron", 6: "transfer"}


class InputError(ValueError):
    pass


def _page_info(total: int | None, offset: int, n: int, unit: str, sort: str | None = None,
               more: bool | None = None) -> dict:
    """Where this page sits in the full result, so the agent never mistakes a page for the whole set."""
    shown_to = offset + n
    has_more = (shown_to < total) if total is not None else bool(more)
    info: dict[str, Any] = {"ukupno": total, "prikazano_od": offset + 1 if n else 0, "prikazano_do": shown_to,
                            "ima_jos": has_more}
    if total is not None:
        info["sljedeci_offset"] = shown_to if has_more else None
    if sort:
        info["sortirano"] = sort
    if total is not None:
        txt = f"Prikazano {offset + 1}–{shown_to} od {total} {unit}" if n else f"Prikazano 0 od {total} {unit}"
        if has_more:
            txt += f"; sljedeća stranica: offset={shown_to}"
    else:
        txt = f"Prikazano {n} {unit}" + ("; ima još – povećaj limit ili suzi filter" if has_more else " (sve)")
    info["pregled"] = txt + "."
    return info


def _cut(rows: list[dict], lim: int) -> tuple[list[dict], bool]:
    """Queries fetch lim+1 rows; the extra row only signals that more exist."""
    return rows[:lim], len(rows) > lim


def _limit(limit: int | None) -> int:
    if limit is None:
        return ROW_LIMIT_DEFAULT
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= ROW_LIMIT_MAX:
        raise InputError(f"limit muss 1..{ROW_LIMIT_MAX} sein")
    return limit


def _date(v: str | None, name: str) -> str | None:
    if v is None or v == "":
        return None
    if not isinstance(v, str) or not re.match(r"^\d{4}-\d{2}-\d{2}$", v):
        raise InputError(f"{name} muss YYYY-MM-DD sein")
    try:
        dt.date.fromisoformat(v)
    except ValueError:
        raise InputError(f"{name} ist kein gültiges Datum") from None
    return v


def _period(col: str, grouping: str) -> str:
    fmt = {"jahr": "%%Y", "monat": "%%Y-%%m", "tag": "%%Y-%%m-%%d"}.get(grouping)
    if fmt is None:
        raise InputError("gruppierung muss jahr|monat|tag sein")
    return f"DATE_FORMAT({col}, '{fmt}')"


def _range(col: str, od: str | None, do: str | None, params: list) -> str:
    conds = []
    if od:
        conds.append(f"{col} >= %s")
        params.append(od)
    if do:
        conds.append(f"{col} < %s")
        params.append(do)
    return (" AND " + " AND ".join(conds)) if conds else ""


# ---------------------------------------------------------------- search_candidates
SPEC_KEYS = ["zanimanje", "vozacka", "jezik", "jezici", "obrazovanje", "iskustvo_u_struci", "drzava",
             "drzavljanstvo", "spol", "starost", "registriran", "status_prijave", "slobodni", "kandidat_status",
             "ukljuci_arhivu", "kontaktabilni", "nacin_odlaska", "nalog_id", "projekt_id", "nostrifikacija",
             "izlaz", "limit", "offset", "pii", "sortiraj",
             # filter catalogue 2026-10-30 (filter_catalog.json)
             "porijeklo", "messenger_status", "bracno_stanje", "viza", "termin_za_vizu", "casting", "intervju", "odbijen",
             "dokument_status", "makler", "pp_partner_id", "tf_agent_id", "tf_status", "vjestina", "aktivan",
             "status_historija", "faza_min", "ima_biljeske", "ima_dokumente", "firma_id", "dipl", "cv_de", "profil_de",
             "ugovor", "pocetak_rada_potvrden", "grupa_id", "radno_iskustvo", "glossa", "nalog_izvor"]
# Not exposed over MCP: free-text place of residence is location-linked personal data (OpenAI plugin guidelines,
# tool data handling). Country-level filtering stays available via `drzava`.
MCP_EXCLUDED_KEYS = frozenset({"grad"})


def search_candidates(cfg: Config, p: Principal, spec: dict[str, Any], include_sql: bool = False) -> dict:
    spec = {k: v for k, v in spec.items() if v is not None}
    if spec.get("pii"):
        require(p, [KANDIDATI_PII])
        if spec.get("izlaz", "broj") != "lista":
            raise InputError("pii=true ist nur mit izlaz='lista' sinnvoll")
    blocked = sorted(MCP_EXCLUDED_KEYS & set(spec))
    if blocked:
        raise InputError(f"Filter nicht verfügbar / Filter nije dostupan: {blocked} – Wohnort nur auf Länderebene (drzava)")
    if isinstance(spec.get("dipl"), dict) and spec["dipl"].get("status") is not None:
        require(p, [DIPL_READ])  # DIPL status is DIPL data, even as a filter
    spec.setdefault("izlaz", "broj")
    if spec["izlaz"] in ("lista", "id"):
        spec["limit"] = _limit(spec.get("limit"))
    try:
        sql, notes = bq.build(spec)
    except bq.SpecError as e:
        raise InputError(f"Ungültiger Filter / Neispravan filter: {e}") from None
    rows = db.query(cfg, sql, None, max_rows=ROW_LIMIT_MAX)
    out = {"rezultat": rows, "broj_redova": len(rows), "napomene": notes, "filter": spec, "stanje_podataka": DATA_NOTE}
    if spec["izlaz"] in ("lista", "id"):
        count_spec = {k: v for k, v in spec.items() if k not in ("limit", "offset", "sortiraj", "pii")}
        count_sql, _ = bq.build({**count_spec, "izlaz": "broj"})
        total = int(db.query(cfg, count_sql, None)[0]["broj_kandidata"])
        sort = ("kandidat_id" if spec["izlaz"] == "id" else
                "relevantnost (broj izvora zanimanja), zatim najnoviji" if spec.get("sortiraj", "relevantnost") == "relevantnost"
                and spec.get("zanimanje") else "najnoviji registrirani prvi")
        out["stranica"] = _page_info(total, spec.get("offset", 0), len(rows), "kandidata", sort)
    if include_sql:
        out["sql"] = sql
    return out


# ---------------------------------------------------------------- filter_options
def load_filter_catalog() -> dict:
    import json
    import os

    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "filter_catalog.json"), encoding="utf-8") as f:
        cat = json.load(f)
    cat["filter"] = [x for x in cat.get("filter", []) if x.get("schluessel") not in MCP_EXCLUDED_KEYS]
    return cat


def filter_options(cfg: Config, p: Principal, section: str | None = None) -> dict:
    catalog = bq.load_occupations()
    static = {
        "zanimanje": {
            "katalog": {k: {"sinonimi": v.get("synonyms", []), "berufsgruppen": v.get("berufsgruppen", []),
                            "siroko_dodaje": v.get("broad", [])} for k, v in catalog.items()},
            "izvori": bq.OCC_SOURCES,
            "napomena": "Nepoznata zanimanja -> pretraga po ključnoj riječi; preciznije: {'berufsgruppen': [...]}",
        },
        "vozacka": {"kategorije": sorted(bq.LICENCE_IMPLIED), "eu_pravilo": bq.LICENCE_IMPLIED,
                    "opcije": {"mode": ["any", "all"], "strict": "bool"}},
        "jezik": {"jezici": sorted(set(bq.LANG_ALIASES.values())), "aliasi": bq.LANG_ALIASES, "nivoi": bq.LEVELS,
                  "vjestine": list(bq.LANG_SKILLS) + ["bilo_koja"], "certifikat": [True, "postoji", "vazeci"]},
        "obrazovanje": {"vrsta": ["srednje", "visoko", "ostalo"], "smjer": "ključna riječ"},
        "drzava": {k: v for k, v in bq.COUNTRY_REGEX.items()},
        "drzavljanstvo": ["EU", "NON-EU"],
        "spol": ["m", "z"],
        "kandidat_status": bq.KANDIDAT_STATUS,
        "status_prijave": bq.STATUS_PRIJAVE,
        "slobodni_statusi": bq.FREE_STATUSES,
        "nacin_odlaska": {0: "Stručni kadar / EU", 2: "Zapadno-balkanski sistem"},
        "drzavljanstvo_zemlje": {k: v for k, v in bq.CITIZENSHIP_REGEX.items()},
        "porijeklo": bq.PORIJEKLO,
        "messenger_status": bq.MESSENGER_STATUS,
        "bracno_stanje": bq.BRACNO_STANJE,
        "viza": ["ima", "nema", "dobio", "odbijena", "dopuna"],
        "casting_status": bq.CASTING_STATUS,
        "intervju_preporuka": list(bq.INTERVJU_PREPORUKA),
        "odbio": list(bq.ODBIO),
        "nostrifikacija": list(bq.NOSTR_PRIZNANJE),
        "glossa": bq.GLOSSA,
        "nalog_izvor": ["kandidat", "projekt", "oba"],
        "ugovor": ["potpisan", "postoji"],
        "berufsgruppen_svih": bq.load_berufsgruppen(),
        "katalog_filtera": "filter_catalog.json (izvor, join, fill rate, zamke) – section='katalog'",
        "izlaz": ["broj", "izvori", "lista", "id"],
        "sortiraj": ["relevantnost", "novi"],
        "limit": {"default": ROW_LIMIT_DEFAULT, "max": ROW_LIMIT_MAX},
    }
    if section == "katalog":
        return {"katalog": load_filter_catalog()}
    db_sections = ("berufsgruppen", "grupe", "db", "razlozi_odbijanja", "dokument_status", "tf_status", "makleri", "dipl_status")
    if section and section not in static and section not in db_sections:
        raise InputError(f"section unbekannt; erlaubt: {sorted(static) + list(db_sections) + ['katalog']}")
    out: dict[str, Any] = {k: v for k, v in static.items() if not section or k == section}
    want_db = section in (None, "status_prijave", "kandidat_status") + db_sections
    if want_db:
        try:
            if section in (None, "berufsgruppen", "db"):
                out["berufsgruppen"] = db.query(cfg, "SELECT berufsgruppe_id, COUNT(*) AS broj_tekstova FROM beruf_mapping "
                                                     "GROUP BY berufsgruppe_id ORDER BY berufsgruppe_id", ())
            if section in (None, "grupe", "db"):
                out["grupe"] = db.query(cfg, "SELECT kg_id, TRIM(kg_title) AS naziv, kg_status FROM idk_kandidati_grupe "
                                             "ORDER BY kg_id", ())
            if section in (None, "status_prijave", "db"):
                out["status_prijave_db"] = db.query(cfg, "SELECT status_id, status_naziv, status_aktivan, rezervisanje, "
                                                         "redoslijed_statusa FROM idk_kandidat_status_prijave ORDER BY redoslijed_statusa, status_id", ())
            if section in (None, "razlozi_odbijanja", "db"):
                out["razlozi_odbijanja"] = db.query(cfg, "SELECT rr_id, rr_name_bs, rr_name_de, rr_rejected_by, rr_status "
                                                         "FROM idk_reject_reasons ORDER BY rr_id", ())
            if section in (None, "dokument_status", "db"):
                out["dokument_status"] = db.query(cfg, "SELECT ds_id, ds_name, ds_name_de FROM idk_pp_documents_statuses ORDER BY ds_id", ())
            if section in (None, "tf_status", "db"):
                out["tf_status"] = db.query(cfg, "SELECT s.tfs_id, s.tfs_name, s.tfs_vrsta_id, v.name AS vrsta, s.tfs_status_prijave "
                                                 "FROM idk_tf_statusi s LEFT JOIN idk_tf_vrste v ON v.id = s.tfs_vrsta_id ORDER BY s.tfs_id", ())
            if section in ("makleri", "db"):  # only IDs + number of candidates, no partner names (PII)
                out["makleri"] = db.query(cfg, "SELECT kandidat_partnerid AS makler_id, COUNT(*) AS kandidata FROM idk_kandidati "
                                               "WHERE kandidat_partnerid > 0 GROUP BY kandidat_partnerid ORDER BY kandidata DESC LIMIT 200", ())
            if section in ("dipl_status", "db"):
                require(p, [DIPL_READ])
                out["dipl_status"] = db.query(cfg, "SELECT nd.status_nd_kandidata AS status, COUNT(*) AS kandidata FROM idk_kandidati k "
                                                   "JOIN idk_nd_kandidata nd ON nd.id_broj_nd_kandidata = k.kandidat_dipl_id "
                                                   "GROUP BY nd.status_nd_kandidata ORDER BY status", ())
        except (db.DbNotConfigured, db.DbError) as e:
            out["db_hinweis"] = f"Werte aus der DB nicht verfügbar: {e}"
    return out


# ---------------------------------------------------------------- candidate_profile
PROFILE_COLS = [
    "k.kandidat_id", "DATE(k.kandidat_datetime) AS registriran", "k.kandidat_status", "ks.status_naziv AS kandidat_status_naziv",
    "k.kandidat_status_prijave", "sp.status_naziv AS status_prijave_naziv", "k.kandidat_group", "TRIM(g.kg_title) AS grupa",
    "TRIM(k.kandidat_prijava_na) AS prijava_na", "k.kandidat_pp_pozicija AS pp_pozicija", "k.kandidat_spol AS spol",
    "IF(k.kandidat_datumrodjenja > '1940-01-01', TIMESTAMPDIFF(YEAR, k.kandidat_datumrodjenja, CURDATE()), NULL) AS starost",
    "k.kandidat_drzavljanstvo_vrsta AS drzavljanstvo_vrsta", "k.kandidat_drzavljanstvo AS drzavljanstvo",
    "TRIM(k.kandidat_drzava) AS drzava", "k.kandidat_vozacka_kategorija AS vozacka_kategorija",
    "k.kandidat_vozacka_dozvola AS vozacka_dozvola", "k.kandidat_iskustvo_u_struci AS iskustvo_u_struci",
    "k.kandidat_iskustvo_u_struci_trajanje AS iskustvo_trajanje", "k.kandidat_nacin_odlaska AS nacin_odlaska",
    "k.kandidat_porijeklo AS porijeklo", "k.kandidat_nalog_id AS nalog_id", "k.kandidat_ima_nostrifikaciju AS ima_nostrifikaciju",
    "k.kandidat_dipl_id AS dipl_id", "k.povezan_na_dipl", "k.kandidat_tf_status AS tf_status",
    "k.kandidat_datum_ugovora AS datum_ugovora", "k.kandidat_dogovoreni_pocetak_rada AS dogovoreni_pocetak_rada",
    "k.kandidat_viza AS viza", "k.kandidat_termin_za_vizu AS termin_za_vizu",
    "IFNULL(k.kandidat_pogresan_broj,0) AS pogresan_broj", "IFNULL(k.kandidat_nedostupan,0) AS nedostupan",
]
PROFILE_PII_COLS = ["k.kandidat_ime AS ime", "k.kandidat_prezime AS prezime", "k.kandidat_mobitel AS mobitel",
                    "k.kandidat_email AS email", "k.kandidat_grad AS grad"]


def candidate_profile(cfg: Config, p: Principal, kandidat_id: int, pii: bool = False) -> dict:
    if isinstance(kandidat_id, bool) or not isinstance(kandidat_id, int) or kandidat_id <= 0:
        raise InputError("kandidat_id muss eine positive Ganzzahl sein")
    if pii:
        require(p, [KANDIDATI_PII])
    cols = PROFILE_COLS + (PROFILE_PII_COLS if pii else [])
    base = db.query(cfg, "SELECT " + ", ".join(cols) + " FROM idk_kandidati k "
                    "LEFT JOIN idk_kandidat_status ks ON ks.status_id = k.kandidat_status "
                    "LEFT JOIN idk_kandidat_status_prijave sp ON sp.status_id = k.kandidat_status_prijave "
                    "LEFT JOIN idk_kandidati_grupe g ON g.kg_id = k.kandidat_group WHERE k.kandidat_id = %s", (kandidat_id,))
    if not base:
        return {"pronadjen": False, "kandidat_id": kandidat_id}
    out: dict[str, Any] = {"pronadjen": True, "kandidat": base[0], "pii_ukljuceno": bool(pii)}
    out["jezici"] = db.query(cfg, "SELECT j.kj_id, j.kj_naziv AS jezik, j.kj_slusanje AS slusanje, j.kj_citanje AS citanje, "
                             "j.kj_govorna_interakcija AS govorna_interakcija, j.kj_govorna_produkcija AS govorna_produkcija, "
                             "j.kj_pisanje AS pisanje, v.cvl_status AS provjereni_status, v.cvl_active AS provjereni_aktivan, "
                             "(NULLIF(TRIM(v.cvl_certificate_path),'') IS NOT NULL) AS ima_certifikat, "
                             "v.cvl_certificate_expiration_date AS certifikat_istice "
                             "FROM idk_kandidat_jezici j LEFT JOIN idk_candidate_verified_languages v ON v.cvl_id = j.kj_id "
                             "WHERE j.kj_kandidatid = %s ORDER BY j.kj_id", (kandidat_id,), max_rows=50)
    out["obrazovanje"] = db.query(cfg, "SELECT e.ke_id, e.ke_vrsta_obrazovanja AS vrsta, e.ke_naziv_kvalifikacije AS kvalifikacija, "
                                  "e.ke_naziv AS skola, s.ss_naziv AS smjer, e.ke_datumod AS od, e.ke_datumdo AS do_, "
                                  "e.ke_aktuelno AS aktuelno, e.ke_drzava AS drzava, bm.berufsgruppe_id "
                                  "FROM idk_kandidat_edukacija e LEFT JOIN idk_skole_smjerovi s ON s.ss_id = e.ke_smjer_id "
                                  "LEFT JOIN beruf_mapping bm ON bm.freitext_wert = e.ke_naziv_kvalifikacije "
                                  "WHERE e.ke_kandidat_id = %s ORDER BY e.ke_datumod", (kandidat_id,), max_rows=50)
    out["radno_iskustvo"] = db.query(cfg, "SELECT r.kri_id, r.kri_pozicija AS pozicija, r.kri_naziv AS poslodavac, "
                                     "r.kri_darum_od AS od, r.kri_datum_do AS do_, r.kri_aktuelno AS aktuelno, "
                                     "r.kri_drzava AS drzava, bm.berufsgruppe_id FROM idk_kandidat_radno_iskustvo r "
                                     "LEFT JOIN beruf_mapping bm ON bm.freitext_wert = r.kri_pozicija "
                                     "WHERE r.kri_kandidat_id = %s ORDER BY r.kri_darum_od", (kandidat_id,), max_rows=50)
    out["projekti"] = db.query(cfg, "SELECT pk.pk_projectid AS projekt_id, pr.project_name AS projekt, pr.project_nalogid AS nalog_id "
                               "FROM idk_project_kandidati pk LEFT JOIN idk_projects pr ON pr.project_id = pk.pk_projectid "
                               "WHERE pk.pk_kandidatid = %s ORDER BY pk.pk_id", (kandidat_id,), max_rows=50)
    out["pipeline_zadnjih_20"] = _history_rows(cfg, kandidat_id, 20)
    out["biljeske_broj"] = db.query(cfg, "SELECT COUNT(*) AS n FROM idk_notes WHERE note_group = 2 AND note_dataid = %s",
                                    (kandidat_id,))[0]["n"]
    if pii:
        out["biljeske_zadnjih_10"] = db.query(cfg, "SELECT note_id, note_datetime, note_txt FROM idk_notes "
                                              "WHERE note_group = 2 AND note_dataid = %s ORDER BY note_datetime DESC LIMIT 10",
                                              (kandidat_id,))
    if out["kandidat"].get("dipl_id") and p.has(DIPL_READ):
        out["dipl"] = db.query(cfg, "SELECT id_broj_nd_kandidata AS dipl_id, status_nd_kandidata, pstatus_nd_kandidata, "
                               "DATE(vrijeme_kreiranja_nd_kandidata) AS kreiran FROM idk_nd_kandidata "
                               "WHERE id_broj_nd_kandidata = %s", (out["kandidat"]["dipl_id"],))
    out["napomena"] = "Bez [TAJNO] polja. Lični podaci samo uz pii=true i ovlaštenje jsi:kandidati:pii."
    return out


def _history_rows(cfg: Config, kandidat_id: int, limit: int) -> list[dict]:
    rows = db.query(cfg, "SELECT l.lsp_datetime AS vrijeme, l.lsp_status_prijave_id AS status_id, sp.status_naziv AS status, "
                    "l.lsp_projekt_id AS projekt_id, pr.project_name AS projekt, l.lsp_izvor AS izvor, l.lsp_broj_dana AS broj_dana, "
                    "l.lsp_employee_id AS zaposlenik_id FROM idk_log_statusi_prijave l "
                    "LEFT JOIN idk_kandidat_status_prijave sp ON sp.status_id = l.lsp_status_prijave_id "
                    "LEFT JOIN idk_projects pr ON pr.project_id = l.lsp_projekt_id "
                    "WHERE l.lsp_kandidat_id = %s ORDER BY l.lsp_datetime DESC, l.lsp_id DESC LIMIT %s",
                    (kandidat_id, limit))
    for r in rows:
        r["izvor_naziv"] = LSP_IZVOR.get(r.get("izvor"))
    return rows


# ---------------------------------------------------------------- kpis
def kpis(cfg: Config, p: Principal, bereich: str, od: str | None = None, do: str | None = None,
         gruppierung: str = "jahr", limit: int | None = None) -> dict:
    if bereich not in KPI_AREA_PERMISSIONS:
        raise InputError(f"bereich muss einer von {sorted(KPI_AREA_PERMISSIONS)} sein")
    require(p, KPI_AREA_PERMISSIONS[bereich])
    od, do = _date(od, "od"), _date(do, "do")
    lim = _limit(limit)
    params: list = []
    notes: list[str] = []
    if bereich == "vermittlungen":
        per = _period("prvi.datum", gruppierung)
        sql = ("WITH prvi AS (SELECT lsp_kandidat_id, MIN(lsp_datetime) AS datum FROM idk_log_statusi_prijave "
               "WHERE lsp_status_prijave_id = 9 GROUP BY lsp_kandidat_id) "
               f"SELECT {per} AS period, COUNT(*) AS potpisanih_ugovora FROM prvi WHERE 1=1"
               + _range("prvi.datum", od, do, params) + " GROUP BY period ORDER BY period LIMIT %s")
        params.append(lim + 1)
        rows = db.query(cfg, sql, tuple(params))
        stock = db.query(cfg, "SELECT COUNT(*) AS plasirani_trenutno FROM idk_kandidati k JOIN idk_kandidat_status_prijave sp "
                         "ON sp.status_id = k.kandidat_status_prijave WHERE sp.redoslijed_statusa >= 7 AND k.kandidat_status <> 3", ())
        notes += ["Tok: prvi ulazak u status 9 'Potpisan ugovor' (idk_log_statusi_prijave, log od 2021-12-07).",
                  "Stanje: trenutni status redoslijed >= 7, bez arhive."]
        return _kpi_out(lim, bereich, rows, notes, extra={"stanje": stock[0] if stock else None})
    if bereich == "neue_kandidaten":
        per = _period("kandidat_datetime", gruppierung)
        sql = (f"SELECT {per} AS period, kandidat_porijeklo AS porijeklo, COUNT(*) AS novih FROM idk_kandidati "
               "WHERE kandidat_datetime >= '2000-01-01' AND kandidat_status <> 3" + _range("kandidat_datetime", od, do, params)
               + " GROUP BY period, porijeklo ORDER BY period, novih DESC LIMIT %s")
        params.append(lim + 1)
        notes.append("kandidat_porijeklo: 0 stari put, 1 DIPL, 2 DAK, 4 SveZaVize (ostali kodovi nedokumentovani).")
        return _kpi_out(lim, bereich, db.query(cfg, sql, tuple(params)), notes)
    if bereich == "pipeline_bestand":
        sql = ("SELECT sp.redoslijed_statusa, sp.status_id, sp.status_naziv, COUNT(*) AS kandidata FROM idk_kandidati k "
               "LEFT JOIN idk_kandidat_status_prijave sp ON sp.status_id = k.kandidat_status_prijave "
               "WHERE k.kandidat_status <> 3 GROUP BY sp.redoslijed_statusa, sp.status_id, sp.status_naziv "
               "ORDER BY sp.redoslijed_statusa LIMIT %s")
        return _kpi_out(lim, bereich, db.query(cfg, sql, (lim + 1,)), ["Trenutno stanje (bez vremenskog filtera), bez arhive."])
    if bereich == "umsatz":
        p1, p2, p3 = [], [], []
        q1 = (f"SELECT 'kandidat_financije' AS izvor, {_period('kf_datum_placanja', gruppierung)} AS period, ROUND(SUM(kf_iznos),2) AS iznos, "
              "COUNT(*) AS uplata FROM idk_kandidat_financije WHERE kf_placeno = 3" + _range("kf_datum_placanja", od, do, p1)
              + " GROUP BY period")
        q2 = (f"SELECT 'nalog_financije', {_period('nf_datum_placanja', gruppierung)}, ROUND(SUM(nf_iznos),2), COUNT(*) "
              "FROM idk_nalog_financije WHERE nf_placeno = 3" + _range("nf_datum_placanja", od, do, p2) + " GROUP BY 2")
        q3 = (f"SELECT 'dipl_predracuni', {_period('pr_datum_uplate', gruppierung)}, ROUND(SUM(pr_vrijednost_EUR),2), COUNT(*) "
              "FROM idk_predracuni WHERE pr_status = 2 AND IFNULL(pr_stornirano,0) = 0" + _range("pr_datum_uplate", od, do, p3)
              + " GROUP BY 2")
        sql = f"SELECT * FROM ({q1} UNION ALL {q2} UNION ALL {q3}) u ORDER BY period, izvor LIMIT %s"
        rows = db.query(cfg, sql, tuple(p1 + p2 + p3 + [lim + 1]))
        notes += ["Plaćeno: kf_placeno=3, nf_placeno=3, predračuni pr_status=2 i nisu stornirani.",
                  "Valuta kf_iznos/nf_iznos nije dokumentovana (pretpostavka EUR). idk_racuni se ne sabiraju (konačni računi za predračune)."]
        return _kpi_out(lim, bereich, rows, notes)
    if bereich == "task_force":
        sql = ("SELECT tf.tf_agent_id AS agent_id, CONCAT(e.employee_firstname, ' ', LEFT(e.employee_lastname, 1), '.') AS agent, "
               "v.category AS kategorija, COUNT(*) AS taskova, ROUND(100 * SUM(s.tfs_is_positive = 1) / COUNT(*), 1) AS pct_pozitivno "
               "FROM idk_task_force tf LEFT JOIN idk_employees e ON e.employee_id = tf.tf_agent_id "
               "LEFT JOIN idk_tf_vrste v ON v.id = tf.tf_vrsta_id LEFT JOIN idk_tf_statusi s ON s.tfs_id = tf.tf_status_id "
               "WHERE tf.tf_agent_id IS NOT NULL" + _range("tf.tf_doe", od, do, params)
               + " GROUP BY tf.tf_agent_id, agent, v.category ORDER BY taskova DESC LIMIT %s")
        params.append(lim + 1)
        notes += ["'Pozitivno' = kandidat nastavlja proces (npr. 'Ne javlja se' je pozitivno), ne znači uspjeh.",
                  "Kategorije: 1 Casting, 2 Posredovanje, 3 Obrada."]
        return _kpi_out(lim, bereich, db.query(cfg, sql, tuple(params)), notes)
    if bereich == "casting":
        per = _period("g.ppaq_start_date", gruppierung)
        sql = (f"SELECT {per} AS period, COUNT(*) AS rezervacija, SUM(r.tsr_status = 1) AS dosao, SUM(r.tsr_status = 2) AS nije_dosao, "
               "SUM(r.tsr_status = 3) AS odustao, SUM(r.tsr_status NOT IN (1,2,3)) AS nedokumentovan_status, "
               "ROUND(100 * SUM(r.tsr_status = 1) / NULLIF(COUNT(*), 0), 1) AS pct_dosao FROM idk_tf_stats_reservations r "
               "JOIN idk_pp_appointment_groups g ON g.ppaq_id = r.tsr_interview_id WHERE 1=1"
               + _range("g.ppaq_start_date", od, do, params) + " GROUP BY period ORDER BY period LIMIT %s")
        params.append(lim + 1)
        notes.append("Status 4/5 nedokumentovan (zasebno). Castinzi 2026 pokazuju 0 % 'Došao' – provjeriti da li je evidentirano.")
        return _kpi_out(lim, bereich, db.query(cfg, sql, tuple(params)), notes)
    # dipl_funnel
    per = _period("d.vrijeme_kreiranja_nd_kandidata", gruppierung)
    sql = (f"SELECT {per} AS period, COUNT(*) AS novih_dipl, SUM(d.status_nd_kandidata = 6) AS zavrseno, "
           "SUM(d.status_nd_kandidata = 7) AS arhivirano, COUNT(DISTINCT p.pr_kandidat_id) AS sa_uplacenim_predracunom "
           "FROM idk_nd_kandidata d LEFT JOIN idk_predracuni p ON p.pr_kandidat_id = d.id_broj_nd_kandidata "
           "AND p.pr_status = 2 AND IFNULL(p.pr_stornirano, 0) = 0 WHERE 1=1"
           + _range("d.vrijeme_kreiranja_nd_kandidata", od, do, params) + " GROUP BY period ORDER BY period LIMIT %s")
    params.append(lim + 1)
    notes.append("DIPL ID prostor (idk_nd_kandidata.id_broj_nd_kandidata) – nije kandidat_id. DIPL posao praktično prestao 2024.")
    return _kpi_out(lim, bereich, db.query(cfg, sql, tuple(params)), notes)


def _kpi_out(lim: int, bereich: str, rows: list[dict], notes: list[str], extra: dict | None = None) -> dict:
    rows, more = _cut(rows, lim)
    out = {"bereich": bereich, "rezultat": rows, "broj_redova": len(rows), "napomene": notes, "stanje_podataka": DATA_NOTE,
           "stranica": _page_info(None, 0, len(rows), "redova", more=more)}
    if extra:
        out.update(extra)
    return out


# ---------------------------------------------------------------- orders_overview
def orders_overview(cfg: Config, p: Principal, nalog_status: list[int] | None = None, firma: str | None = None,
                    nalog_id: list[int] | None = None, samo_sa_kandidatima: bool = False, limit: int | None = None) -> dict:
    lim = _limit(limit)
    params: list = []
    where = []
    if nalog_status:
        where.append("n.nalog_status IN (" + ", ".join(["%s"] * len(nalog_status)) + ")")
        params += [_int(v, "nalog_status") for v in nalog_status]
    if nalog_id:
        where.append("n.nalog_id IN (" + ", ".join(["%s"] * len(nalog_id)) + ")")
        params += [_int(v, "nalog_id") for v in nalog_id]
    if firma:
        if not isinstance(firma, str) or len(firma.strip()) > 60:
            raise InputError("firma: max. 60 Zeichen")
        where.append("c.company_name LIKE %s")
        params.append("%" + firma.strip().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%")
    having = " HAVING kandidata_na_nalogu > 0" if samo_sa_kandidatima else ""
    sql = ("SELECT n.nalog_id, n.nalog_broj, n.nalog_naziv, c.company_id, c.company_name AS firma, n.nalog_status, "
           "DATE(n.nalog_kreirano) AS kreiran, n.nalog_potrebno_kandidata AS potrebno, "
           "COUNT(DISTINCT k.kandidat_id) AS kandidata_na_nalogu, "
           "COUNT(DISTINCT IF(sp.redoslijed_statusa >= 7, k.kandidat_id, NULL)) AS potpisano_ili_dalje "
           "FROM idk_nalozi n LEFT JOIN idk_companies c ON c.company_id = n.kompanija_id "
           "LEFT JOIN idk_kandidati k ON k.kandidat_nalog_id = n.nalog_id AND k.kandidat_status <> 3 "
           "LEFT JOIN idk_kandidat_status_prijave sp ON sp.status_id = k.kandidat_status_prijave "
           + ("WHERE " + " AND ".join(where) + " " if where else "")
           + "GROUP BY n.nalog_id, n.nalog_broj, n.nalog_naziv, c.company_id, c.company_name, n.nalog_status, kreiran, potrebno"
           + having + " ORDER BY potpisano_ili_dalje DESC, n.nalog_id DESC LIMIT %s")
    params.append(lim + 1)
    rows, more = _cut(db.query(cfg, sql, tuple(params)), lim)
    return {"rezultat": rows, "broj_redova": len(rows), "stranica": _page_info(None, 0, len(rows), "naloga", more=more),
            "napomene": ["nalog_status kodovi 1,3–8,10–12 nisu dokumentovani u bazi (pitati korisnika).",
                         "Kandidati po kandidat_nalog_id, bez arhive; 'potpisano_ili_dalje' = redoslijed_statusa >= 7."]}


def _int(v: Any, name: str) -> int:
    if isinstance(v, bool) or not isinstance(v, int):
        raise InputError(f"{name}: Ganzzahl erwartet")
    return v


# ---------------------------------------------------------------- pipeline_history
def pipeline_history(cfg: Config, p: Principal, kandidat_id: int | None = None, status_id: list[int] | None = None,
                     projekt_id: int | None = None, od: str | None = None, do: str | None = None,
                     gruppierung: str = "monat", limit: int | None = None) -> dict:
    lim = _limit(limit)
    od, do = _date(od, "od"), _date(do, "do")
    if kandidat_id is not None:
        _int(kandidat_id, "kandidat_id")
        rows, more = _cut(_history_rows(cfg, kandidat_id, lim + 1), lim)
        return {"kandidat_id": kandidat_id, "rezultat": rows, "broj_redova": len(rows),
                "stranica": _page_info(None, 0, len(rows), "promjena statusa", more=more),
                "napomene": ["Log statusa prijave od 2021-12-07 (idk_log_statusi_prijave)."]}
    params: list = []
    where = ["1=1"]
    if status_id:
        where.append("l.lsp_status_prijave_id IN (" + ", ".join(["%s"] * len(status_id)) + ")")
        params += [_int(v, "status_id") for v in status_id]
    if projekt_id is not None:
        where.append("l.lsp_projekt_id = %s")
        params.append(_int(projekt_id, "projekt_id"))
    per = _period("l.lsp_datetime", gruppierung)
    sql = (f"SELECT {per} AS period, l.lsp_status_prijave_id AS status_id, sp.status_naziv AS status, "
           "COUNT(*) AS prelaza, COUNT(DISTINCT l.lsp_kandidat_id) AS kandidata FROM idk_log_statusi_prijave l "
           "LEFT JOIN idk_kandidat_status_prijave sp ON sp.status_id = l.lsp_status_prijave_id WHERE "
           + " AND ".join(where) + _range("l.lsp_datetime", od, do, params)
           + " GROUP BY period, l.lsp_status_prijave_id, sp.status_naziv ORDER BY period, status_id LIMIT %s")
    params.append(lim + 1)
    rows, more = _cut(db.query(cfg, sql, tuple(params)), lim)
    return {"rezultat": rows, "broj_redova": len(rows), "stranica": _page_info(None, 0, len(rows), "redova", more=more),
            "napomene": ["Broj prelaza u status po periodu (log od 2021-12-07).", DATA_NOTE]}


# ---------------------------------------------------------------- change_log (mcp_aenderung)
def change_log(cfg: Config, p: Principal, tabelle: str | None = None, kandidat_id: int | None = None,
               limit: int | None = None, mit_werten: bool = False) -> dict:
    lim = _limit(limit)
    if mit_werten:
        require(p, [KANDIDATI_PII])
    params: list = []
    where = ["1=1"]
    if tabelle:
        if not re.match(r"^[a-z0-9_]{1,64}$", tabelle):
            raise InputError("tabelle ungültig")
        where.append("a_tabelle = %s")
        params.append(tabelle)
    if kandidat_id is not None:
        where.append("a_kandidat_id = %s")
        params.append(_int(kandidat_id, "kandidat_id"))
    cols = "a_id, a_zeit, a_werkzeug, a_aktion, a_tabelle, a_datensatz_id, a_kandidat_id, a_art, a_zustand, a_freigabe_code, a_ausgefuehrt_zeit, a_notiz"
    if mit_werten:
        cols += ", a_vorher, a_nachher"
    params.append(lim + 1)
    rows = db.query(cfg, f"SELECT {cols} FROM mcp_aenderung WHERE " + " AND ".join(where) + " ORDER BY a_id DESC LIMIT %s",
                    tuple(params))
    rows, more = _cut(rows, lim)
    return {"rezultat": rows, "broj_redova": len(rows), "stranica": _page_info(None, 0, len(rows), "promjena", more=more)}
