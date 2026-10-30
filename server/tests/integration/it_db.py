"""Integration DB setup: local MySQL 8.4 (Docker) with the real schema structure + synthetic data.

Enable with JSI_IT_MYSQL=host:port and JSI_IT_ROOT_PASSWORD. Example:
  docker run -d --name jsi-mysql -e MYSQL_ROOT_PASSWORD=rootpw -p 13306:3306 mysql:8.4
  JSI_IT_MYSQL=127.0.0.1:13306 JSI_IT_ROOT_PASSWORD=rootpw uv run pytest tests/integration
No real personal data: all names/phones below are invented.
"""
import os
import subprocess
import sys

import pymysql
import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import schema_ddl  # noqa: E402

from jsi_mcp import config  # noqa: E402

DB = "jsicrm_it"
RO_USER, RW_USER = "jsi_it_ro", "jsi_it_rw"
PW = "it-only-password-1"

STATUS_PRIJAVE = [  # (id, naziv, aktivan, rezervisanje, redoslijed) – synthetic ordering for tests
    (1, "Slobodan", 1, 0, 1), (2, "U projektu NR", 1, 0, 2), (3, "Casting", 1, 1, 3), (4, "Završen", 1, 1, 12),
    (5, "Odbijen", 1, 0, 0), (6, "U projektu RZ", 1, 1, 4), (7, "Čeka ugovor", 1, 1, 5), (8, "Poslan ugovor", 1, 1, 6),
    (9, "Potpisan ugovor", 1, 1, 7), (10, "Početak rada", 1, 1, 11), (12, "Prikupljanje dokumentacije", 1, 1, 8),
    (15, "Čeka termin", 1, 1, 9), (18, "Čeka vizu", 1, 1, 10), (21, "Dopuna dokumenata", 0, 1, 9),
]

SEED = [
    "INSERT INTO idk_kandidat_status (id, status_id, status_naziv) VALUES (1,0,'Na provjeri'),(2,1,'U obradi'),(3,2,'Obrađen'),(4,3,'Arhiviran'),(5,4,'Kontrola'),(6,5,'Dopuna'),(7,6,'Odbio Messenger')",
    "INSERT INTO idk_kandidati_grupe (kg_id, kg_title, kg_date, kg_employeeid, kg_status) VALUES (7,'Ostalo',NOW(),1,1),(38,'Električar',NOW(),1,1),(50,'Vozač',NOW(),1,1)",
    "INSERT INTO beruf_mapping (freitext_wert, berufsgruppe_id) VALUES ('Električar','elektriker'),('Vozač C','lkw_fahrer'),('Elektroinstalater','elektriker')",
    "INSERT INTO idk_skole (skola_id, skola_naziv) VALUES (1,'Test škola')",
    "INSERT INTO idk_skole_smjerovi (ss_id, ss_naziv, ss_skola_id) VALUES (1,'Elektrotehničar energetike',1),(2,'Kuhar',1)",
    # candidates (all synthetic)
    """INSERT INTO idk_kandidati (kandidat_id, kandidat_check, kandidat_ime, kandidat_prezime, kandidat_prijava_na, kandidat_slika,
         kandidat_status, kandidat_datetime, kandidat_group, kandidat_vozacka_kategorija, kandidat_vozacka_dozvola, kandidat_drzava,
         kandidat_datumrodjenja, kandidat_mobitel, kandidat_email, kandidat_status_prijave, kandidat_jmbg, kandidat_password) VALUES
     (1,'','Testa','Jedan','Električar','',1,'2024-01-10 10:00:00',38,'B,C',NULL,'BIH','1990-05-01','+000 111','t1@example.invalid',1,'0000000000001','x'),
     (2,'','Testa','Dva','Ostalo','',2,'2024-02-10 10:00:00',7,'B,C,CE',NULL,'Srbija','1985-01-01','+000 222',NULL,NULL,NULL,NULL),
     (3,'','Testa','Tri','Električar','',1,'2024-03-10 10:00:00',38,'B',NULL,'BiH','1999-01-01','+000 333',NULL,1,NULL,NULL),
     (4,'','Testa','Četiri','Električar','',3,'2024-04-10 10:00:00',38,'C',NULL,NULL,NULL,'+000 444',NULL,NULL,NULL,NULL),
     (5,'','Testa','Pet','Vozač C','',1,'2025-01-10 10:00:00',50,'CE',NULL,'BIH','1980-01-01','+000 555',NULL,9,NULL,NULL),
     (6,'','Testa','Šest','Elektroinstalater','',4,'2025-02-10 10:00:00',7,NULL,'C',NULL,NULL,'+000 666',NULL,2,NULL,NULL)""",
    "INSERT INTO idk_kandidat_radno_iskustvo (kri_id, kri_darum_od, kri_pozicija, kri_naziv, kri_kandidat_id) VALUES (1,'2015-01-01','Električar','Firma A',2),(2,'2016-01-01','Vozač C','Firma B',5)",
    "INSERT INTO idk_kandidat_edukacija (ke_id, ke_naziv_kvalifikacije, ke_kandidat_id, ke_vrsta_obrazovanja, ke_smjer_id) VALUES (1,'Elektrotehničar',1,'srednje',1),(2,'Kuhar',3,'srednje',2)",
    "INSERT INTO idk_kandidat_jezici (kj_id, kj_naziv, kj_slusanje, kj_citanje, kj_govorna_interakcija, kj_govorna_produkcija, kj_pisanje, kj_kandidatid) VALUES (1,'Njemački','B1','B1','B1','A2','A2',6),(2,'Njemački','A1','A1','A1','A1','A1',1)",
    "INSERT INTO idk_candidate_verified_languages (cvl_id, cvl_status, cvl_active, cvl_certificate_path) VALUES (1, 8, 1, 'cert/test.pdf')",
    "INSERT INTO idk_companies (company_id, company_name, company_datetime, company_status) VALUES (1,'Test GmbH',NOW(),1)",
    "INSERT INTO idk_nalozi (nalog_id, kompanija_id, nalog_naziv, nalog_status, nalog_potrebno_kandidata) VALUES (10,1,'Elektriker DE',10,5)",
    "UPDATE idk_kandidati SET kandidat_nalog_id = 10 WHERE kandidat_id IN (1,5)",
    "INSERT INTO idk_projects (project_id, project_name, project_companyid, project_employeeid, project_datetime, project_status, project_nalogid) VALUES (100,'Projekt Test',1,1,NOW(),1,'10')",
    "INSERT INTO idk_project_kandidati (pk_id, pk_projectid, pk_kandidatid) VALUES (1,100,1)",
    "INSERT INTO idk_log_statusi_prijave (lsp_kandidat_id, lsp_projekt_id, lsp_status_prijave_id, lsp_izvor, lsp_datetime, lsp_broj_dana) VALUES (5,100,3,1,'2023-01-01 10:00:00',30),(5,100,9,1,'2023-01-31 10:00:00',NULL),(1,NULL,1,1,'2025-06-01 10:00:00',NULL)",
    "INSERT INTO idk_notes (note_txt, note_datetime, note_group, note_dataid, note_employeeid) VALUES ('Synthetische Notiz', NOW(), 2, 1, 1)",
    "INSERT INTO idk_nd_kandidata (id_broj_nd_kandidata, vrijeme_kreiranja_nd_kandidata, status_nd_kandidata) VALUES (500,'2022-03-01',6),(501,'2023-03-01',1)",
    "UPDATE idk_kandidati SET kandidat_dipl_id = 500, povezan_na_dipl = 1 WHERE kandidat_id = 2",
    "INSERT INTO idk_predracuni (pr_id, pr_kandidat_id, pr_status, pr_stornirano, pr_datum_uplate, pr_vrijednost_EUR) VALUES (1,500,2,0,'2022-04-01',300)",
    "INSERT INTO idk_kandidat_financije (kandidat_id, kf_iznos, kf_placeno, kf_datum_placanja) VALUES (5, 1000, 3, '2023-02-01')",
    "INSERT INTO idk_nalog_financije (nf_iznos, nf_placeno, nf_datum_placanja) VALUES (2000, 3, '2023-03-01')",
    "INSERT INTO idk_employees (employee_id, employee_firstname, employee_lastname) VALUES (1,'Agent','Test')",
    "INSERT INTO idk_tf_vrste (id, name, status, category) VALUES (1,'Casting poziv',1,1)",
    "INSERT INTO idk_tf_statusi (tfs_id, tfs_is_positive) VALUES (1,1),(2,0)",
    "INSERT INTO idk_task_force (tf_agent_id, tf_candidate_id, tf_vrsta_id, tf_status_id, tf_doe) VALUES (1,1,1,1,'2025-03-01'),(1,3,1,2,'2025-03-02')",
    "INSERT INTO idk_pp_appointment_groups (ppaq_id, ppaq_start_date) VALUES (1,'2025-04-01')",
    "INSERT INTO idk_tf_stats_reservations (tsr_candidate_id, tsr_interview_id, tsr_status) VALUES (1,1,1),(3,1,2),(5,1,4)",
]


def _root_conn(db=None):
    host, port = os.environ["JSI_IT_MYSQL"].split(":")
    return pymysql.connect(host=host, port=int(port), user="root", password=os.environ.get("JSI_IT_ROOT_PASSWORD", ""),
                           database=db, autocommit=True, charset="utf8mb4")


@pytest.fixture(scope="session")
def mysql_db():
    if not os.environ.get("JSI_IT_MYSQL"):
        pytest.skip("JSI_IT_MYSQL not set – integration tests need a local MySQL 8.4")
    tables, defaults = schema_ddl.load()
    conn = _root_conn()
    with conn.cursor() as cur:
        cur.execute(f"DROP DATABASE IF EXISTS {DB}")
        cur.execute(f"CREATE DATABASE {DB} CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci")
        cur.execute(f"USE {DB}")
        for t, rows in tables.items():
            cur.execute(schema_ddl.ddl(t, rows, defaults, auto_increment_int_pk=True))
        # seed with relaxed strictness only for NOT NULL columns we do not care about in tests
        cur.execute("SET SESSION sql_mode = 'ONLY_FULL_GROUP_BY,NO_ENGINE_SUBSTITUTION'")
        cur.executemany("INSERT INTO idk_kandidat_status_prijave (status_id, status_naziv, status_aktivan, rezervisanje, redoslijed_statusa) "
                        "VALUES (%s,%s,%s,%s,%s)", STATUS_PRIJAVE)
        for s in SEED:
            cur.execute(s)
        for u in (RO_USER, RW_USER):
            cur.execute(f"DROP USER IF EXISTS '{u}'@'%'")
            cur.execute(f"CREATE USER '{u}'@'%' IDENTIFIED BY '{PW}'")
        for mode, user in (("readonly", RO_USER), ("write", RW_USER)):
            out = subprocess.run([sys.executable, "-I", os.path.join(ROOT, "scripts", "gen_grants.py"), mode, DB, user],
                                 check=True, capture_output=True, text=True).stdout
            for line in out.splitlines():
                if line.startswith("GRANT"):
                    cur.execute(line)
    conn.close()
    yield DB


def _cfg(user, writes=False, **extra):
    host, port = os.environ["JSI_IT_MYSQL"].split(":")
    env = {"JSI_AUTH_DISABLED": "true", "JSI_MCP_PUBLIC_URL": "http://localhost:3000/mcp", "JSI_DB_TARGET": "mirror",
           "JSI_MIRROR_DB_HOST": host, "JSI_MIRROR_DB_PORT": port, "JSI_MIRROR_DB_NAME": DB, "JSI_MIRROR_DB_USER": user,
           "JSI_MIRROR_DB_PASSWORD": PW, "JSI_DB_SSL_REQUIRED": "false", "JSI_WRITES_ENABLED": "true" if writes else "false",
           "JSI_WRITE_EMPLOYEE_ID": "1"}
    env.update(extra)
    return config.load(env)


@pytest.fixture
def ro_cfg(mysql_db):
    return _cfg(RO_USER)


@pytest.fixture
def rw_cfg(mysql_db):
    return _cfg(RW_USER, writes=True)


@pytest.fixture
def root_cur(mysql_db):
    conn = _root_conn(DB)
    with conn.cursor(pymysql.cursors.DictCursor) as cur:
        yield cur
    conn.close()
