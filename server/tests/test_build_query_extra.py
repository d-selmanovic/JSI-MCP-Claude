"""Unit tests for the filters added 2026-10-30 (filter catalogue). Run: python3 -I -m unittest discover -s scripts -p 'test_*.py'"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
for p in (HERE, os.path.join(HERE, "..", "src", "jsi_mcp")):
    if os.path.exists(os.path.join(p, "build_query.py")):
        sys.path.insert(0, p)
        break
from build_query import build, SpecError  # noqa: E402


def sql_of(spec):
    return build(spec)[0]


class TestExtraFilters(unittest.TestCase):
    def test_acceptance_electrician_german_a2_licence_b(self):
        sql = sql_of({"zanimanje": "Elektriker", "jezik": {"jezik": "deutsch", "min_nivo": "A2"}, "vozacka": "B"})
        self.assertIn("berufsgruppe_id IN ('elektriker')", sql)
        self.assertIn("kj_naziv LIKE 'Njema%'", sql)
        self.assertIn(">= 2 GROUP BY", sql)
        self.assertIn("FIND_IN_SET('CE'", sql)

    def test_acceptance_welder_bih_age_free_c_ce(self):
        sql = sql_of({"zanimanje": "Schweißer", "drzava": "BIH", "starost": {"od": 25, "do": 45}, "slobodni": True,
                      "vozacka": ["C", "CE"]})
        self.assertIn("'schweisser'", sql)
        self.assertIn("REGEXP", sql)
        self.assertIn("INTERVAL 25 YEAR", sql)
        self.assertIn("kandidat_status_prijave IN (0, 1, 2, 5)", sql)

    def test_acceptance_nurses_certificate_b1_nostrification(self):
        sql = sql_of({"zanimanje": ["krankenpfleger", "pflegehelfer"], "jezik": {"jezik": "de", "min_nivo": "B1", "certifikat": True},
                      "nostrifikacija": True})
        self.assertIn("'krankenpfleger'", sql)
        self.assertIn("cvl_certificate_path", sql)
        self.assertIn("full_recognition IN (1)", sql)

    def test_acceptance_order_signed_contract(self):
        sql = sql_of({"nalog_id": [254], "status_prijave": [9]})
        self.assertIn("k.kandidat_nalog_id IN (254)", sql)
        self.assertIn("k.kandidat_status_prijave IN (9)", sql)
        sql = sql_of({"status_historija": {"status": [9], "nalog_id": [254]}})
        self.assertIn("lsp_status_prijave_id IN (9)", sql)
        self.assertIn("project_nalogid", sql)

    def test_nalog_izvor(self):
        self.assertIn("idk_project_kandidati", sql_of({"nalog_id": [254], "nalog_izvor": "projekt"}))
        self.assertIn("UNION SELECT kandidat_id FROM idk_kandidati", sql_of({"nalog_id": [254], "nalog_izvor": "oba"}))
        with self.assertRaises(SpecError):
            build({"nalog_id": [254], "nalog_izvor": "x"})

    def test_citizenship_country(self):
        sql = sql_of({"drzavljanstvo": ["BIH", "NON-EU"]})
        self.assertIn("kandidat_drzavljanstvo)) REGEXP '^(BOSAN", sql)
        self.assertIn("LIKE 'NONEU%'", sql)
        with self.assertRaises(SpecError):
            build({"drzavljanstvo": "Narnia"})

    def test_codes_are_validated(self):
        self.assertIn("kandidat_porijeklo IN (4, 5)", sql_of({"porijeklo": [4, 5]}))
        self.assertIn("kandidat_status_messenger IN (2)", sql_of({"messenger_status": 2}))
        self.assertIn("kandidat_bracno_stanje IN (2)", sql_of({"bracno_stanje": [2]}))
        for bad in ({"porijeklo": [99]}, {"messenger_status": ["1"]}, {"glossa": [7]}, {"casting": {"status": [9]}}):
            with self.assertRaises(SpecError, msg=bad):
                build(bad)

    def test_visa(self):
        self.assertIn("k.kandidat_viza = 1", sql_of({"viza": "ima"}))
        self.assertIn("lsp_status_prijave_id = 27", sql_of({"viza": "dobio"}))
        self.assertIn("vi_type = 2", sql_of({"viza": "odbijena"}))
        self.assertIn("kandidat_termin_za_vizu = 1", sql_of({"termin_za_vizu": True}))
        with self.assertRaises(SpecError):
            build({"viza": "maybe"})

    def test_casting_interview_rejection(self):
        sql = sql_of({"casting": {"status": [1], "nalog_id": [254], "od": "2023-01-01"}})
        self.assertIn("r.tsr_status IN (1)", sql)
        self.assertIn("g.ppaq_start_date >= '2023-01-01'", sql)
        self.assertIn("pca_recommendation IN (1)", sql_of({"intervju": {"preporuka": "hire"}}))
        sql = sql_of({"odbijen": {"odbio": "poslodavac", "razlog_id": [4]}})
        self.assertIn("rr.rr_rejected_by = 2", sql)
        self.assertIn("krr_reason_id IN (4)", sql)
        with self.assertRaises(SpecError):
            build({"intervju": {"preporuka": "maybe"}})

    def test_status_history_and_phase(self):
        sql = sql_of({"status_historija": {"status": [9], "od": "2023-01-01", "do": "2024-01-01"}, "faza_min": 7})
        self.assertIn("l.lsp_datetime >= '2023-01-01'", sql)
        self.assertIn("spf.redoslijed_statusa >= 7", sql)
        with self.assertRaises(SpecError):
            build({"status_historija": {"status": [999]}})
        with self.assertRaises(SpecError):
            build({"faza_min": 0})

    def test_presence_flags(self):
        self.assertIn("note_group = 2", sql_of({"ima_biljeske": True}))
        self.assertIn("document_group = 2", sql_of({"ima_dokumente": True}))
        self.assertIn("kc_signed = 1", sql_of({"ugovor": "potpisan"}))
        self.assertIn("k.cv_de = 1", sql_of({"cv_de": True}))
        self.assertIn("kandidat_partnerid, 0) > 0", sql_of({"makler": True}))
        self.assertIn("kandidat_tf_status IS NOT NULL", sql_of({"tf_status": True}))

    def test_dipl_uses_dipl_id_space(self):
        sql = sql_of({"dipl": {"status": [5]}})
        self.assertIn("nd.id_broj_nd_kandidata = k.kandidat_dipl_id", sql)
        self.assertNotIn("id_broj_nd_kandidata = k.kandidat_id", sql)

    def test_work_experience_years(self):
        sql = sql_of({"radno_iskustvo": {"min_godina": 2, "zanimanje": "elektriker"}})
        self.assertIn("HAVING mjeseci >= 24", sql)
        self.assertIn("bm.berufsgruppe_id IN ('elektriker')", sql)
        with self.assertRaises(SpecError):
            build({"radno_iskustvo": {"min_godina": 99}})

    def test_free_text_filters_are_escaped(self):
        sql = sql_of({"vjestina": "Ms Office' OR 1=1 --", "grad": "Sara%jevo"})
        self.assertIn("Ms Office'' OR 1=1 --", sql)
        self.assertIn("Sara\\%jevo", sql)
        with self.assertRaises(SpecError):
            build({"grad": "ab"})

    def test_all_194_berufsgruppen_usable(self):
        sql, notes = build({"zanimanje": "dachdecker"})
        self.assertIn("berufsgruppe_id IN ('dachdecker')", sql)
        self.assertTrue(any("berufsgruppe 'dachdecker'" in n for n in notes))
        with self.assertRaises(SpecError):
            build({"zanimanje": {"berufsgruppen": ["gibtsnicht"]}})

    def test_more_languages(self):
        self.assertIn("kj_naziv LIKE 'Franc%'", sql_of({"jezik": {"jezik": "französisch", "min_nivo": "A1"}}))

    def test_no_correlated_exists_with_all_new_filters(self):
        sql = sql_of({"zanimanje": "elektriker", "casting": {"status": [1]}, "intervju": {"preporuka": "hire"},
                      "odbijen": {"odbio": "kandidat"}, "dokument_status": [18], "ima_biljeske": True, "aktivan": {"od": "2024-01-01"},
                      "firma_id": [1], "radno_iskustvo": {"min_godina": 1}, "vjestina": "office", "izlaz": "lista"})
        self.assertNotIn("EXISTS", sql.upper())
        for col in ("kandidat_ime", "kandidat_mobitel", "jmbg", "password"):
            self.assertNotIn(col, sql)


class TestCatalogComplete(unittest.TestCase):
    def test_every_filter_key_is_documented(self):
        import json
        import re
        src = open(os.path.join(os.path.dirname(sys.modules["build_query"].__file__), "build_query.py"), encoding="utf-8").read()
        block = src[src.index("allowed = {"):src.index("}", src.index("allowed = {"))]
        keys = set(re.findall(r'"([a-z_]+)"', block)) - {"jezici", "nalog_izvor"}  # alias of jezik / option of nalog_id
        base = os.path.dirname(sys.modules["build_query"].__file__)
        for cand in (os.path.join(base, "filter_catalog.json"), os.path.join(base, "..", "references", "filter_catalog.json")):
            if os.path.exists(cand):
                cat = json.load(open(cand, encoding="utf-8"))
                break
        documented = {f["schluessel"] for f in cat["filter"]} | set(cat["ausgabe"])
        self.assertEqual(sorted(keys - documented), [])
        for f in cat["filter"]:
            build(dict(f["beispiel"]))  # every documented example must build


if __name__ == "__main__":
    unittest.main()


def test_offset_paging_sql():
    from jsi_mcp import build_query as bq
    sql, _ = bq.build({"izlaz": "lista", "limit": 20, "offset": 40})
    assert sql.rstrip().endswith("LIMIT 20 OFFSET 40")
    assert "k.kandidat_id DESC" in sql  # tie-breaker keeps pages stable
    sql0, _ = bq.build({"izlaz": "lista", "limit": 20})
    assert "OFFSET" not in sql0
    for bad in (-1, True, "5", 2_000_000):
        try:
            bq.build({"izlaz": "lista", "offset": bad})
        except bq.SpecError:
            continue
        raise AssertionError(f"offset {bad!r} accepted")
