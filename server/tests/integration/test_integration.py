"""Integration tests against local MySQL 8.4 (strict mode, ONLY_FULL_GROUP_BY) with generated GRANTs."""
import json

import pymysql
import pytest

from jsi_mcp import db, tools_read, writes
from jsi_mcp.permissions import Principal
from jsi_mcp.tools_read import InputError

from it_db import DB, PW, RO_USER, _cfg

ALL = Principal(sub="it-admin", permissions=frozenset({"*"}))
READER = Principal(sub="it-reader", permissions=frozenset({"jsi:kandidati:read", "jsi:kennzahlen:read"}))


# ------------------------------------------------------------------ read tools
def test_elektriker_c_count(ro_cfg):
    r = tools_read.search_candidates(ro_cfg, READER, {"zanimanje": "Elektriker", "vozacka": "C"})
    # 1 (prijava+grupa, B,C), 2 (iskustvo, CE), 6 (prijava via beruf_mapping, legacy 'C'); 3 has only B, 4 archived
    assert r["rezultat"] == [{"broj_kandidata": 3}]


def test_izvori_and_lista(ro_cfg):
    r = tools_read.search_candidates(ro_cfg, READER, {"zanimanje": "Elektriker", "vozacka": "C", "izlaz": "izvori"})
    assert sum(x["broj_kandidata"] for x in r["rezultat"]) == 3
    r = tools_read.search_candidates(ro_cfg, READER, {"zanimanje": "Elektriker", "izlaz": "lista", "limit": 10,
                                                       "jezik": {"jezik": "de", "min_nivo": "A1"}})
    ids = {x["kandidat_id"] for x in r["rezultat"]}
    assert ids == {1, 6}
    assert all("kandidat_ime" not in x and "kandidat_mobitel" not in x for x in r["rezultat"])


def test_lista_pii(ro_cfg):
    p = Principal(sub="x", permissions=frozenset({"jsi:kandidati:read", "jsi:kandidati:pii"}))
    r = tools_read.search_candidates(ro_cfg, p, {"vozacka": "CE", "izlaz": "lista", "pii": True})
    assert {x["kandidat_id"] for x in r["rezultat"]} == {2, 5}
    assert all("kandidat_ime" in x for x in r["rezultat"])


def test_certificate_and_other_filters(ro_cfg):
    r = tools_read.search_candidates(ro_cfg, READER, {"jezik": {"jezik": "de", "min_nivo": "A1", "certifikat": True}})
    assert r["rezultat"] == [{"broj_kandidata": 1}]
    for spec in ({"drzava": ["BIH", "SRB"]}, {"starost": {"od": 20, "do": 45}}, {"slobodni": True},
                 {"obrazovanje": {"vrsta": "srednje", "smjer": "elektro"}}, {"kontaktabilni": True},
                 {"registriran": {"od": "2024-01-01", "do": "2025-01-01"}}, {"projekt_id": [100]}, {"nalog_id": [10]},
                 {"nostrifikacija": True}, {"drzavljanstvo": "EU"}, {"iskustvo_u_struci": {"min_godina": 2}},
                 {"izlaz": "id", "ukljuci_arhivu": True}):
        tools_read.search_candidates(ro_cfg, READER, spec)  # must execute in strict mode


NEW_FILTER_SPECS = [
    {"drzavljanstvo": ["BIH", "NON-EU"]}, {"porijeklo": [0, 4]}, {"messenger_status": [2]}, {"bracno_stanje": [1, 2]},
    {"viza": "ima"}, {"viza": "dobio"}, {"viza": "odbijena"}, {"termin_za_vizu": True},
    {"casting": {"status": [1], "nalog_id": [10], "od": "2023-01-01"}}, {"intervju": {"preporuka": ["hire"], "nalog_id": [10]}},
    {"odbijen": {"odbio": "poslodavac", "razlog_id": [4]}}, {"dokument_status": [18]}, {"makler": True}, {"makler": [1]},
    {"pp_partner_id": [1]}, {"tf_agent_id": [1]}, {"tf_status": True}, {"tf_status": [8]}, {"vjestina": "office"},
    {"grad": "Sarajevo"}, {"aktivan": {"od": "2024-01-01"}}, {"status_historija": {"status": [9], "nalog_id": [10]}},
    {"status_historija": {"status": [9], "projekt_id": [100], "od": "2022-01-01", "do": "2026-01-01"}}, {"faza_min": 7},
    {"ima_biljeske": True}, {"ima_dokumente": True}, {"firma_id": [1]}, {"dipl": True}, {"dipl": {"povezan": False}},
    {"cv_de": True}, {"profil_de": True}, {"ugovor": "potpisan"}, {"ugovor": "postoji"}, {"pocetak_rada_potvrden": True},
    {"grupa_id": [38]}, {"radno_iskustvo": {"min_godina": 1, "zanimanje": "elektriker"}}, {"radno_iskustvo": {"min_godina": 0.5}},
    {"glossa": [1]}, {"nalog_id": [10], "nalog_izvor": "projekt"}, {"nalog_id": [10], "nalog_izvor": "oba"},
    {"nostrifikacija": "bilo_koje"}, {"nostrifikacija": "djelimicno"}, {"obrazovanje": {"skola_id": [1], "smjer_id": [1]}},
    {"zanimanje": "dachdecker"}, {"jezik": {"jezik": "francuski", "min_nivo": "A1"}},
    {"zanimanje": "Elektriker", "jezik": {"jezik": "de", "min_nivo": "A2"}, "vozacka": "B", "casting": {"status": [1]},
     "status_historija": {"status": [9]}, "radno_iskustvo": {"min_godina": 1}, "izlaz": "lista", "limit": 5},
]


@pytest.mark.parametrize("spec", NEW_FILTER_SPECS, ids=[next(iter(s)) for s in NEW_FILTER_SPECS])
def test_new_filters_execute_strict(ro_cfg, spec):
    """Every filter from the 2026-10-30 catalogue must run on MySQL 8.4 strict mode as the read-only GRANT user."""
    r = tools_read.search_candidates(ro_cfg, READER, dict(spec))
    assert "rezultat" in r and (spec.get("izlaz") == "lista" or r["broj_redova"] == 1)


def test_dipl_status_filter_needs_dipl_permission(ro_cfg):
    from jsi_mcp.permissions import PermissionDenied
    with pytest.raises(PermissionDenied):
        tools_read.search_candidates(ro_cfg, READER, {"dipl": {"status": [1]}})
    p = Principal(sub="it-dipl", permissions=frozenset({"jsi:kandidati:read", "jsi:dipl:read"}))
    tools_read.search_candidates(ro_cfg, p, {"dipl": {"status": [1]}})


def test_filter_options_new_sections(ro_cfg):
    for sec in ("razlozi_odbijanja", "dokument_status", "tf_status", "makleri", "katalog", "porijeklo"):
        assert tools_read.filter_options(ro_cfg, READER, sec)
    with pytest.raises(Exception):
        tools_read.filter_options(ro_cfg, READER, "dipl_status")


def test_filter_options_db(ro_cfg):
    r = tools_read.filter_options(ro_cfg, READER)
    assert {"berufsgruppen", "grupe", "status_prijave_db", "zanimanje", "vozacka"} <= set(r)
    assert "db_hinweis" not in r


def test_candidate_profile(ro_cfg):
    r = tools_read.candidate_profile(ro_cfg, READER, 1)
    assert r["pronadjen"] and r["kandidat"]["kandidat_id"] == 1
    flat = json.dumps(r, ensure_ascii=False)
    for forbidden in ("Testa", "+000 111", "t1@example.invalid", "0000000000001", "jmbg", "password"):
        assert forbidden not in flat
    assert r["biljeske_broj"] == 1 and "biljeske_zadnjih_10" not in r
    p = Principal(sub="x", permissions=frozenset({"jsi:kandidati:read", "jsi:kandidati:pii", "jsi:dipl:read"}))
    r2 = tools_read.candidate_profile(ro_cfg, p, 2, pii=True)
    assert r2["kandidat"]["ime"] == "Testa" and r2["dipl"][0]["dipl_id"] == 500
    assert tools_read.candidate_profile(ro_cfg, READER, 999)["pronadjen"] is False


@pytest.mark.parametrize("bereich", ["vermittlungen", "neue_kandidaten", "pipeline_bestand", "umsatz", "task_force",
                                     "casting", "dipl_funnel"])
@pytest.mark.parametrize("gruppierung", ["jahr", "monat"])
def test_kpis_execute(ro_cfg, bereich, gruppierung):
    r = tools_read.kpis(ro_cfg, ALL, bereich, od="2020-01-01", do="2027-01-01", gruppierung=gruppierung)
    assert r["bereich"] == bereich


def test_kpi_values(ro_cfg):
    v = tools_read.kpis(ro_cfg, ALL, "vermittlungen")
    assert v["rezultat"] == [{"period": "2023", "potpisanih_ugovora": 1}] and v["stanje"]["plasirani_trenutno"] == 1
    u = tools_read.kpis(ro_cfg, ALL, "umsatz")
    assert {(x["izvor"], x["period"], x["iznos"]) for x in u["rezultat"]} == {
        ("kandidat_financije", "2023", 1000), ("nalog_financije", "2023", 2000), ("dipl_predracuni", "2022", 300)}
    c = tools_read.kpis(ro_cfg, ALL, "casting")["rezultat"][0]
    assert (c["rezervacija"], c["dosao"], c["nedokumentovan_status"]) == (3, 1, 1)


def test_orders_and_history(ro_cfg):
    o = tools_read.orders_overview(ro_cfg, READER, firma="Test")
    assert o["rezultat"][0]["nalog_id"] == 10 and o["rezultat"][0]["kandidata_na_nalogu"] == 2
    assert o["rezultat"][0]["potpisano_ili_dalje"] == 1
    assert tools_read.orders_overview(ro_cfg, READER, firma="100%_")["rezultat"] == []
    h = tools_read.pipeline_history(ro_cfg, READER, kandidat_id=5)
    assert [x["status_id"] for x in h["rezultat"]] == [9, 3]
    agg = tools_read.pipeline_history(ro_cfg, READER, od="2023-01-01", do="2024-01-01")
    assert sum(x["prelaza"] for x in agg["rezultat"]) == 2


def test_read_is_really_read_only(ro_cfg):
    with db.read_cursor(ro_cfg) as cur:
        with pytest.raises(pymysql.err.MySQLError):
            cur.execute("UPDATE idk_kandidati SET kandidat_status = 1 WHERE kandidat_id = 1")


# ------------------------------------------------------------------ GRANTs
def test_grants_block_sensitive_columns_and_writes(ro_cfg):
    host, port = ro_cfg.db.host, ro_cfg.db.port
    conn = pymysql.connect(host=host, port=port, user=RO_USER, password=PW, database=DB)
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT kandidat_id, kandidat_vozacka_kategorija FROM idk_kandidati LIMIT 1")
            for sql in ("SELECT kandidat_jmbg FROM idk_kandidati", "SELECT * FROM idk_kandidati",
                        "SELECT employee_password FROM idk_employees", "UPDATE idk_kandidati SET kandidat_status=1",
                        "DELETE FROM idk_notes", "INSERT INTO mcp_aenderung (a_zeit) VALUES (NOW())"):
                with pytest.raises(pymysql.err.OperationalError):
                    cur.execute(sql)
    finally:
        conn.close()


def test_write_user_cannot_delete(rw_cfg):
    conn = pymysql.connect(host=rw_cfg.db.host, port=rw_cfg.db.port, user=rw_cfg.db.user, password=PW, database=DB)
    try:
        with conn.cursor() as cur:
            for sql in ("DELETE FROM idk_kandidati WHERE kandidat_id = 3", "DROP TABLE idk_notes",
                        "UPDATE idk_kandidati SET kandidat_jmbg = '1'", "UPDATE mcp_aenderung SET a_notiz = 'x'"):
                with pytest.raises(pymysql.err.OperationalError):
                    cur.execute(sql)
    finally:
        conn.close()


# ------------------------------------------------------------------ writes
def _audits(root_cur, tool=None):
    root_cur.execute("SELECT * FROM mcp_aenderung" + (" WHERE a_werkzeug = %s" if tool else "") + " ORDER BY a_id",
                     (tool,) if tool else None)
    return root_cur.fetchall()


def test_create_company_with_audit(rw_cfg, root_cur):
    pv = writes.record_preview(rw_cfg, ALL, "company", "create", values={"company_name": "  Neue Firma IT  "})
    assert pv["dry_run"] and pv["promjene"]["company_name"]["nachher"] == "Neue Firma IT"
    root_cur.execute("SELECT COUNT(*) AS n FROM idk_companies")
    before = root_cur.fetchone()["n"]
    out = writes.record_write(rw_cfg, ALL, "company", "create", values={"company_name": "  Neue Firma IT  "},
                              dry_run=False, preview_hash=pv["preview_hash"], grund="IT-Test")
    assert out["ausgefuehrt"] and out["record_id"] > 1
    root_cur.execute("SELECT company_name, company_status, company_datetime FROM idk_companies WHERE company_id = %s", (out["record_id"],))
    row = root_cur.fetchone()
    assert row["company_name"] == "Neue Firma IT" and row["company_status"] == 1 and row["company_datetime"] is not None
    a = [x for x in _audits(root_cur) if x["a_id"] == out["audit_id"]][0]
    assert (a["a_aktion"], a["a_tabelle"], a["a_datensatz_id"], a["a_zustand"]) == ("create", "idk_companies", out["record_id"], "ausgefuehrt")
    assert "sub=it-admin" in a["a_notiz"] and "grund=IT-Test" in a["a_notiz"]
    assert json.loads(a["a_nachher"])["company_name"] == "Neue Firma IT"
    root_cur.execute("SELECT COUNT(*) AS n FROM idk_companies")
    assert root_cur.fetchone()["n"] == before + 1


def test_dry_run_default_writes_nothing(rw_cfg, root_cur):
    n0 = len(_audits(root_cur))
    out = writes.record_write(rw_cfg, ALL, "candidate", "update", record_id=3, values={"kandidat_drzava": "HRV"})
    assert out["dry_run"] is True
    root_cur.execute("SELECT kandidat_drzava FROM idk_kandidati WHERE kandidat_id = 3")
    assert root_cur.fetchone()["kandidat_drzava"] == "BiH" and len(_audits(root_cur)) == n0


def test_update_candidate_and_conflict(rw_cfg, root_cur):
    pv = writes.record_preview(rw_cfg, ALL, "candidate_driving_licence", "update", record_id=3,
                               values={"kandidat_vozacka_kategorija": ["b", "C", "C"]})
    assert pv["promjene"] == {"kandidat_vozacka_kategorija": {"vorher": "B", "nachher": "B,C"}}
    root_cur.execute("UPDATE idk_kandidati SET kandidat_vozacka_kategorija = 'B,C1' WHERE kandidat_id = 3")  # concurrent change
    with pytest.raises(writes.ConflictError):
        writes.record_write(rw_cfg, ALL, "candidate_driving_licence", "update", record_id=3,
                            values={"kandidat_vozacka_kategorija": "B,C"}, dry_run=False, preview_hash=pv["preview_hash"])
    root_cur.execute("SELECT kandidat_vozacka_kategorija FROM idk_kandidati WHERE kandidat_id = 3")
    assert root_cur.fetchone()["kandidat_vozacka_kategorija"] == "B,C1"
    root_cur.execute("SELECT f_werkzeug, f_art FROM mcp_fehler ORDER BY f_id DESC LIMIT 1")
    assert root_cur.fetchone() == {"f_werkzeug": "record_write", "f_art": "validierung"}
    out = writes.record_write(rw_cfg, ALL, "candidate_driving_licence", "update", record_id=3,
                              values={"kandidat_vozacka_kategorija": "B,C"}, dry_run=False)
    assert out["ausgefuehrt"]
    again = writes.record_write(rw_cfg, ALL, "candidate_driving_licence", "update", record_id=3,
                                values={"kandidat_vozacka_kategorija": "B,C"}, dry_run=False)
    assert again["ausgefuehrt"] is False and again["bez_promjene"]


def test_pii_redaction_in_preview(rw_cfg):
    p = Principal(sub="w", permissions=frozenset({"jsi:write:candidate:update"}))
    pv = writes.record_preview(rw_cfg, p, "candidate", "update", record_id=1, values={"kandidat_drzava": "SRB"})
    assert pv["vorher"]["kandidat_ime"] == "***" and pv["vorher"]["kandidat_drzava"] == "BIH"
    with pytest.raises(PermissionError):
        writes.record_preview(rw_cfg, p, "candidate", "update", record_id=1, values={"kandidat_ime": "X"})


def test_archive_candidate(rw_cfg, root_cur):
    out = writes.record_write(rw_cfg, ALL, "candidate", "archive", record_id=3, dry_run=False)
    assert out["promjene"] == {"kandidat_status": {"vorher": 1, "nachher": 3}}
    root_cur.execute("SELECT kandidat_status FROM idk_kandidati WHERE kandidat_id = 3")
    assert root_cur.fetchone()["kandidat_status"] == 3
    writes.record_write(rw_cfg, ALL, "candidate", "update", record_id=3, values={"kandidat_status": 1}, dry_run=False)


def test_create_children_and_references(rw_cfg, root_cur):
    out = writes.record_write(rw_cfg, ALL, "candidate_language", "create", dry_run=False, values={
        "kj_kandidatid": 3, "kj_naziv": "Njemački", "kj_slusanje": "A2", "kj_citanje": "A2", "kj_govorna_interakcija": "A2",
        "kj_govorna_produkcija": "A1", "kj_pisanje": "A1"})
    assert out["kandidat_id"] == 3
    with pytest.raises(InputError, match="kein Datensatz"):
        writes.record_write(rw_cfg, ALL, "candidate_note", "create", dry_run=False,
                            values={"note_dataid": 99999, "note_txt": "x"})
    n = writes.record_write(rw_cfg, ALL, "candidate_note", "create", dry_run=False, values={"note_dataid": 3, "note_txt": "Test"})
    root_cur.execute("SELECT note_group, note_employeeid FROM idk_notes WHERE note_id = %s", (n["record_id"],))
    assert root_cur.fetchone() == {"note_group": 2, "note_employeeid": 1}
    with pytest.raises(InputError, match="nach Anlage nicht änderbar"):
        writes.record_preview(rw_cfg, ALL, "candidate_language", "update", record_id=1, values={"kj_kandidatid": 2})
    with pytest.raises(InputError, match="Pflichtfelder"):
        writes.record_preview(rw_cfg, ALL, "candidate_experience", "create", values={"kri_kandidat_id": 3})
    with pytest.raises(InputError, match="existiert bereits"):
        writes.record_write(rw_cfg, ALL, "project_member", "create", dry_run=False, values={"pk_projectid": 100, "pk_kandidatid": 1})
    writes.record_write(rw_cfg, ALL, "candidate_order", "update", record_id=3, values={"kandidat_nalog_id": 10}, dry_run=False)
    for ent, vals in (("candidate_education", {"ke_kandidat_id": 3, "ke_naziv_kvalifikacije": "Elektromonter", "ke_vrsta_obrazovanja": "srednje"}),
                      ("candidate_experience", {"kri_kandidat_id": 3, "kri_pozicija": "Monter", "kri_naziv": "Firma C", "kri_darum_od": "2020-01-01"}),
                      ("project_member", {"pk_projectid": 100, "pk_kandidatid": 3}),
                      ("contact", {"contact_firstname": "Kontakt", "contact_companyid": 1}),
                      ("candidate", {"kandidat_ime": "Neu", "kandidat_prezime": "Kandidat", "kandidat_prijava_na": "Električar"})):
        assert writes.record_write(rw_cfg, ALL, ent, "create", values=vals, dry_run=False)["ausgefuehrt"], ent


def test_dipl_link_unique(rw_cfg):
    with pytest.raises(InputError, match="bereits mit kandidat_id=2"):
        writes.record_write(rw_cfg, ALL, "candidate_dipl_link", "update", record_id=1,
                            values={"kandidat_dipl_id": 500, "povezan_na_dipl": 1}, dry_run=False)
    with pytest.raises(InputError, match="kein Datensatz"):
        writes.record_write(rw_cfg, ALL, "candidate_dipl_link", "update", record_id=1, values={"kandidat_dipl_id": 777}, dry_run=False)
    out = writes.record_write(rw_cfg, ALL, "candidate_dipl_link", "update", record_id=1,
                              values={"kandidat_dipl_id": 501, "povezan_na_dipl": 1}, dry_run=False)
    assert out["ausgefuehrt"]


def test_set_application_status(rw_cfg, root_cur):
    pv = writes.set_application_status(rw_cfg, ALL, 1, 3, projekt_id=100)
    assert pv["dry_run"] and pv["promjene"]["kandidat_status_prijave"] == {"vorher": 1, "nachher": 3}
    assert "kandidat_latest_reserved_time" in pv["promjene"]
    out = writes.set_application_status(rw_cfg, ALL, 1, 3, projekt_id=100, dry_run=False, preview_hash=pv["preview_hash"])
    assert out["ausgefuehrt"]
    root_cur.execute("SELECT lsp_status_prijave_id, lsp_projekt_id, lsp_izvor, lsp_broj_dana, lsp_employee_id FROM idk_log_statusi_prijave "
                     "WHERE lsp_kandidat_id = 1 ORDER BY lsp_id")
    rows = root_cur.fetchall()
    assert rows[0]["lsp_status_prijave_id"] == 1 and rows[0]["lsp_broj_dana"] is not None and rows[0]["lsp_broj_dana"] > 100
    assert rows[1] == {"lsp_status_prijave_id": 3, "lsp_projekt_id": 100, "lsp_izvor": 1, "lsp_broj_dana": None, "lsp_employee_id": 1}
    root_cur.execute("SELECT kandidat_status_prijave, kandidat_latest_reserved_time FROM idk_kandidati WHERE kandidat_id = 1")
    k = root_cur.fetchone()
    assert k["kandidat_status_prijave"] == 3 and k["kandidat_latest_reserved_time"] is not None
    a = _audits(root_cur, "set_application_status")[-1]
    assert a["a_kandidat_id"] == 1 and json.loads(a["a_vorher"])["kandidat_status_prijave"] == 1
    same = writes.set_application_status(rw_cfg, ALL, 1, 3, dry_run=False)
    assert same["ausgefuehrt"] is False
    with pytest.raises(writes.ConflictError):
        writes.set_application_status(rw_cfg, ALL, 1, 7, dry_run=False, preview_hash=pv["preview_hash"])
    with pytest.raises(InputError, match="nicht aktiv"):
        writes.set_application_status(rw_cfg, ALL, 1, 21, dry_run=False)
    with pytest.raises(InputError, match="existiert nicht"):
        writes.set_application_status(rw_cfg, ALL, 1, 99, dry_run=False)


def test_writes_disabled_and_prod_target(mysql_db):
    cfg = _cfg("jsi_it_rw", writes=False)
    with pytest.raises(writes.WritesDisabled):
        writes.record_write(cfg, ALL, "company", "create", values={"company_name": "X"}, dry_run=False)
    assert writes.record_preview(cfg, ALL, "company", "create", values={"company_name": "X"})["schreiben_aktiv"] is False


def test_readonly_db_user_write_fails_cleanly(mysql_db):
    cfg = _cfg(RO_USER, writes=True)
    with pytest.raises(pymysql.err.MySQLError):
        writes.record_write(cfg, ALL, "company", "create", values={"company_name": "X"}, dry_run=False)


def test_change_log(rw_cfg):
    r = tools_read.change_log(rw_cfg, ALL, tabelle="idk_companies")
    assert r["broj_redova"] >= 1 and "a_vorher" not in r["rezultat"][0]
    r = tools_read.change_log(rw_cfg, ALL, mit_werten=True, limit=1)
    assert "a_nachher" in r["rezultat"][0]
