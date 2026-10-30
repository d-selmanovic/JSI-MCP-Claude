"""SQL-Injection gegen echte MySQL: jeder Filter-Schlüssel von search_candidates mit Angriffs-Strings.

build_query setzt Werte als Literale ein (für BlazeSQL-Kompatibilität). Dieser Test belegt, dass
Freigabelisten, int()-Umwandlung und Escaping keinen Ausbruch aus dem Literal erlauben.
"""
import time

import pymysql

from jsi_mcp import build_query as bq
from jsi_mcp.tools_read import SPEC_KEYS
from it_db import DB, _root_conn

PAYLOADS = ["x' OR '1'='1", "1; DROP TABLE idk_kandidati; --", "') UNION SELECT 1 -- ", "\\' OR 1=1 #",
            "1 OR 1=1", "%' AND SLEEP(3) AND '%'='", "\\'; DROP TABLE idk_kandidati; #", "x\\\\' OR '1'='1"]
FLAGS = {"ukljuci_arhivu"}  # boolesche Schalter: jeder nicht leere Wert ist „wahr“, kein Ausbruch


def _shapes(p):
    return [p, [p], {"naziv": p, "nivo": p, "status": p, "nalog_id": p, "kljucne_rijeci": [p], "id": p},
            {"od": p, "do": p}]


def test_no_injection_on_any_filter_key(mysql_db):
    conn = _root_conn(DB)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM idk_kandidati")
    total = cur.fetchone()[0]
    assert total > 0
    executed, problems = 0, []
    for key in sorted(SPEC_KEYS):
        for p in PAYLOADS:
            for v in _shapes(p):
                try:
                    sql, _ = bq.build({"izlaz": "broj", key: v})  # key last: izlaz itself gets fuzzed too
                except Exception:
                    continue  # abgelehnt = sicher
                t0 = time.monotonic()
                try:
                    cur.execute(sql)
                    n = cur.fetchone()[0]
                except pymysql.err.MySQLError as e:
                    problems.append((key, p, f"SQL-Fehler {e.args[0]}"))
                    continue
                executed += 1
                if time.monotonic() - t0 > 2.5:
                    problems.append((key, p, "SLEEP ausgeführt"))
                if key not in FLAGS and n == total:
                    problems.append((key, p, "liefert alle Zeilen"))
    cur.execute("SELECT COUNT(*) FROM idk_kandidati")
    assert cur.fetchone()[0] == total
    assert executed > 300
    assert not problems, problems[:10]


def test_unknown_occupation_keyword_runs(mysql_db):
    """Freitext ohne Katalogtreffer: jede UNION-Zeile braucht die Aliase kid/izvor."""
    conn = _root_conn(DB)
    cur = conn.cursor()
    sql, _ = bq.build({"zanimanje": "zzzz-unbekannt", "izlaz": "broj"})
    cur.execute(sql)
    assert cur.fetchone()[0] == 0
