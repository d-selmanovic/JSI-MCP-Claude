"""Unit tests for build_query.py. Run: python3 -I -m unittest discover -s scripts -p 'test_*.py'"""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src", "jsi_mcp"))
from build_query import build, SpecError, resolve_occupation, load_occupations  # noqa: E402


class TestBuild(unittest.TestCase):
    def test_electrician_licence_c(self):
        sql, notes = build({"zanimanje": "Elektriker", "vozacka": "C"})
        self.assertIn("berufsgruppe_id IN ('elektriker')", sql)
        self.assertIn("kandidat_group IN (38, 39, 41)", sql)
        self.assertIn("FIND_IN_SET('CE'", sql)            # CE implies C
        self.assertNotIn("FIND_IN_SET('C1'", sql)         # C1 does not imply C
        self.assertIn("k.kandidat_status <> 3", sql)       # archive excluded by default
        self.assertTrue(sql.startswith("WITH"))
        self.assertIn("COUNT(*) AS broj_kandidata", sql)

    def test_strict_licence(self):
        sql, _ = build({"vozacka": {"kategorije": ["C"], "strict": True}})
        self.assertIn("FIND_IN_SET('C',", sql)
        self.assertNotIn("FIND_IN_SET('CE'", sql)

    def test_licence_b_implied_by_c(self):
        sql, _ = build({"vozacka": "B"})
        for t in ("B", "BE", "C1", "C", "CE"):
            self.assertIn(f"FIND_IN_SET('{t}'", sql)

    def test_any_licence(self):
        sql, _ = build({"vozacka": True})
        self.assertIn("kandidat_vozacka_dozvola IN ('Da'", sql)

    def test_synonyms_resolve(self):
        cat = load_occupations()
        for term in ("električar", "Elektricar", "electrician", "ELEKTRIKER"):
            self.assertEqual(resolve_occupation(term, cat), "elektriker", term)
        self.assertEqual(resolve_occupation("automehaničar", cat), "kfz_mechaniker")
        self.assertEqual(resolve_occupation("viljuškarista", cat), "staplerfahrer")

    def test_unknown_occupation_falls_back_to_keyword(self):
        sql, notes = build({"zanimanje": "Dimnjacar"})
        self.assertIn("LIKE '%Dimnjacar%'", sql)
        self.assertTrue(any("nije u katalogu" in n for n in notes))

    def test_broad_adds_neighbours(self):
        sql, _ = build({"zanimanje": {"name": "elektriker", "broad": True}})
        self.assertIn("'hilfselektriker'", sql)
        self.assertIn("73", sql)

    def test_sources_restrict(self):
        sql, _ = build({"zanimanje": {"name": "elektriker", "sources": ["grupa"]}})
        self.assertIn("'grupa'", sql)
        self.assertNotIn("'iskustvo'", sql)
        with self.assertRaises(SpecError):
            build({"zanimanje": {"name": "elektriker", "sources": ["xyz"]}})

    def test_language(self):
        sql, _ = build({"jezik": {"jezik": "deutsch", "min_nivo": "B1"}})
        self.assertIn("kj_naziv LIKE 'Njema%'", sql)
        self.assertIn(">= 3", sql)
        sql, _ = build({"jezik": {"jezik": "de", "min_nivo": "A2", "certifikat": True}})
        self.assertIn("cvl_certificate_path", sql)
        sql, _ = build({"jezik": {"jezik": "de", "min_nivo": "A2", "certifikat": "vazeci"}})
        self.assertIn("cvl_certificate_expiration_date >= CURDATE()", sql)
        with self.assertRaises(SpecError):
            build({"jezik": {"jezik": "de", "min_nivo": "B3"}})

    def test_injection_is_escaped(self):
        sql, _ = build({"zanimanje": {"keywords": ["x' OR 1=1 -- "]}})
        self.assertIn("x'' OR 1=1 --", sql)
        self.assertNotIn("x' OR", sql)
        with self.assertRaises(SpecError):
            build({"zanimanje": {"berufsgruppen": ["elektriker'); DROP TABLE x; --"]}})
        with self.assertRaises(SpecError):
            build({"nalog_id": ["1 OR 1=1"]})
        with self.assertRaises(SpecError):
            build({"registriran": {"od": "2024-01-01' OR '1'='1"}})

    def test_unknown_key_rejected(self):
        with self.assertRaises(SpecError):
            build({"lozinka": "x"})

    def test_list_without_pii_has_no_personal_columns(self):
        sql, _ = build({"zanimanje": "elektriker", "izlaz": "lista"})
        for col in ("kandidat_ime", "kandidat_prezime", "kandidat_mobitel", "kandidat_email", "password", "jmbg"):
            self.assertNotIn(col, sql)
        sql, _ = build({"zanimanje": "elektriker", "izlaz": "lista", "pii": True})
        self.assertIn("kandidat_ime", sql)
        self.assertNotIn("password", sql)

    def test_no_correlated_exists(self):
        sql, _ = build({"zanimanje": "elektriker", "vozacka": "C", "jezik": {"min_nivo": "A2"},
                        "obrazovanje": {"vrsta": "srednje"}, "nostrifikacija": True, "izlaz": "lista"})
        self.assertNotIn("EXISTS", sql.upper())

    def test_country_and_misc(self):
        sql, _ = build({"drzava": ["BIH", "SRB"], "spol": "m", "starost": {"od": 20, "do": 45},
                        "slobodni": True, "kontaktabilni": True, "izlaz": "id", "limit": 50})
        self.assertIn("REGEXP", sql)
        self.assertIn("'Muško'", sql)
        self.assertIn("LIMIT 50", sql)
        with self.assertRaises(SpecError):
            build({"drzava": "Narnia"})

    def test_izvori_requires_occupation(self):
        with self.assertRaises(SpecError):
            build({"vozacka": "C", "izlaz": "izvori"})


if __name__ == "__main__":
    unittest.main()
