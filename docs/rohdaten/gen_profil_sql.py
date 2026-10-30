#!/usr/bin/env python3
"""Mess-SQL für das Spaltenprofil (Punkt 18) und die Code-Statistik aller übrigen CODE-Spalten (read-only).

A) Statistik je Tabelle in EINER Abfrage: je Spalte befüllt (nicht NULL/''/Null-Datum), distinct,
   min/max nur für Zahlen/Datum (nie für Text -> keine Personendaten).
   - Profil-Tabellen (PROFIL): alle Spalten außer [TAJNO]
   - übrige Tabellen: nur CODE-Spalten
B) Top-12-Werte je CODE-Spalte der Profil-Tabellen (Text-Codes nur Werte mit Häufigkeit >= 5).
Ausgabe: stat_XX.sql / top_XX.sql, Schlüssel in profil_keys.tsv.
"""
import csv
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PROFIL = ["idk_kandidati", "idk_kandidat_jezici", "idk_candidate_verified_languages", "idk_candidate_language_logs",
          "idk_kandidat_edukacija", "idk_kandidat_radno_iskustvo", "idk_kandidat_de", "idk_kandidat_cv",
          "idk_kandidat_kontakt_info", "idk_kandidat_vjestine", "idk_kandidat_akademija", "idk_kandidat_financije",
          "idk_kandidati_contracts", "idk_kandidati_reject_reasons", "idk_validnosti_inputa", "users",
          "idk_nostrifikovane_diplome"]
# Code-Statistik außerhalb der Profil-Tabellen nur für filterrelevante Tabellen (Rest: klassifiziert, nicht gemessen)
CODE_TABLES = ["idk_task_force", "idk_tf_stats_reservations", "idk_tf_statusi", "idk_pp_documents", "idk_pp_cand_appts",
               "idk_log_statusi_prijave", "idk_nalozi", "idk_nd_kandidata", "idk_pp_visa_incomplete", "idk_projects",
               "idk_pp_cand_required_documents", "idk_kandidat_status_prijave", "idk_companies"]
MAX_LEN = 7000


def kind(typ):
    if re.match(r"(tiny|small|medium|big)?int|decimal|float|double", typ):
        return "num"
    if re.match(r"date|datetime|timestamp", typ):
        return "date"
    if typ == "time":
        return "time"
    return "text"


def main(outdir):
    rows = list(csv.DictReader(open(os.path.join(HERE, "verweis_kandidaten.tsv"), encoding="utf-8"), delimiter="\t"))
    by_t = {}
    for r in rows:
        if r["klasse"] == "SENSIBEL":
            continue
        if r["tabelle"] in PROFIL or (r["klasse"] == "CODE" and r["tabelle"] in CODE_TABLES):
            by_t.setdefault(r["tabelle"], []).append(r)
    keys, stats = [], []
    for t, cols in sorted(by_t.items(), key=lambda x: (x[0] not in PROFIL, x[0])):
        exprs = ["COUNT(*)"]
        for r in cols:
            c, k = r["spalte"], kind(r["typ"])
            keys.append((len(keys), t, c, r["typ"], r["klasse"]))
            if k == "num":
                exprs.append(f"CONCAT_WS(':',COUNT({c}),COUNT(DISTINCT {c}),MIN({c}),MAX({c}))")
            elif k == "date":
                exprs.append(f"CONCAT_WS(':',SUM({c}>'1900-01-01'),COUNT(DISTINCT {c}),"
                             f"DATE(MIN(IF({c}>'1900-01-01',{c},NULL))),DATE(MAX({c})))")
            elif k == "time":
                exprs.append(f"CONCAT_WS(':',COUNT({c}),COUNT(DISTINCT {c}))")
            else:
                exprs.append(f"CONCAT_WS(':',SUM(NULLIF(TRIM({c}),'') IS NOT NULL),COUNT(DISTINCT {c}))")
        stats.append(f"SELECT '{t}' t,CONCAT_WS('|',{','.join(exprs)}) s FROM {t}")
    tops = []
    for i, t, c, typ, klass in keys:
        if klass == "CODE":
            txt = kind(typ) == "text"
            v = f"CONVERT(TRIM({c}) USING utf8mb4) COLLATE utf8mb4_general_ci" if txt else f"CAST({c} AS CHAR)"
            hv = " HAVING COUNT(*)>=5" if txt else ""
            tops.append(f"SELECT {i} k,(SELECT JSON_ARRAYAGG(CONCAT(IFNULL(v,'NULL'),'=',n)) FROM(SELECT {v} v,COUNT(*) n "
                        f"FROM {t} GROUP BY v{hv} ORDER BY n DESC LIMIT 12)x) j")
    os.makedirs(outdir, exist_ok=True)

    def write(prefix, parts, head, tail):
        files, cur = [], []
        for p in parts:
            if cur and sum(len(x) for x in cur) + len(p) > MAX_LEN:
                files.append(cur)
                cur = []
            cur.append(p)
        if cur:
            files.append(cur)
        for i, f_ in enumerate(files):
            with open(os.path.join(outdir, f"{prefix}_{i:02d}.sql"), "w", encoding="utf-8") as f:
                f.write(head + "\nUNION ALL ".join(f_) + tail)
        return len(files)

    big = [s for s in stats if len(s) > MAX_LEN]
    n1 = write("stat", stats, "SELECT JSON_ARRAYAGG(JSON_ARRAY(t,s)) r FROM(\n", "\n)z")
    n2 = write("top", tops, "SELECT JSON_OBJECTAGG(k,j) r FROM(\n", "\n)z")
    with open(os.path.join(HERE, "profil_keys.tsv"), "w", encoding="utf-8") as f:
        f.write("i\ttabelle\tspalte\ttyp\tklasse\n" + "".join("\t".join(map(str, k)) + "\n" for k in keys))
    print(n1, "stat-Dateien (", len(big), "überlang),", n2, "top-Dateien,", len(keys), "Spalten,", len(tops), "Top-Listen")


if __name__ == "__main__":
    main(sys.argv[1])
