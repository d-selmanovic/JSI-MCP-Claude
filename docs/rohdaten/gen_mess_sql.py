#!/usr/bin/env python3
"""Erzeugt die Mess-SQL (BlazeSQL, read-only) für alle FK/LOOKUP/TEXTREF-Hypothesen aus verweis_kandidaten.tsv.

Je Hypothese eine Zeile: k, n, leer, treffer, dist, maxv
  leer    = NULL / '' / 0 (0 nur, wenn 0 kein gültiger Zielschlüssel ist)
  treffer = Wert existiert in der Zieltabelle
  ins Leere = n - leer - treffer
Batches: Hypothesen einer Quelltabelle zusammen, max. BATCH je Abfrage; große Tabellen einzeln.
Aufruf: python3 -I gen_mess_sql.py <ausgabeordner>   -> batch_XX.sql
"""
import csv
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BATCH = 20
BIG = {"idk_logs", "idk_nd_kandidata_biljeske", "idk_task_force", "idk_nd_termini", "idk_nd_kandidata_status_log",
       "idk_log_statusi_prijave", "idk_nd_menadzeri_statistike", "idk_messenger_obavijesti", "idk_log_kandidat_statusi",
       "idk_project_kandidati"}


def coltypes():
    rows = json.load(open(os.path.join(HERE, "columns.json"), encoding="utf-8"))["rows"]
    return {(r["t"], r["col"]): r["typ"] for r in rows}


def expr(t, c, typ):
    if re.match(r"(var)?char|text|mediumtext", typ):
        return f"CAST(NULLIF(TRIM({c}),'') AS SIGNED)"
    return c


KEYS = []
MAX_ROWS = 1_500_000  # Quellzeilen je Abfrage (60-s-Limit)


def counts():
    out = {}
    with open(os.path.join(HERE, "counts.tsv"), encoding="utf-8") as f:
        for line in f:
            t, n = line.rstrip("\n").split("\t")
            out[t] = int(n)
    return out


def main(outdir):
    """Eine Abfrage je Zieltabelle: Quellwerte mit laufender Nummer k per UNION ALL, ein Join, GROUP BY k."""
    types, cnt = coltypes(), counts()
    by_target = {}
    with open(os.path.join(HERE, "verweis_kandidaten.tsv"), encoding="utf-8") as f:
        for r in csv.DictReader(f, delimiter="\t"):
            if r["klasse"] not in ("FK", "LOOKUP", "TEXTREF") or not r["ziele"] or r["tabelle"].startswith("rb_"):
                continue  # rb_*: char(36)-IDs, Fremdprojekt, eigene Messung
            for tg in r["ziele"].split(","):
                KEYS.append(f"{r['tabelle']}.{r['spalte']}>{tg}")
                typ = types[(r["tabelle"], r["spalte"])]
                v = r["spalte"] if r["klasse"] == "TEXTREF" else expr(r["tabelle"], r["spalte"], typ)
                if r["klasse"] == "TEXTREF":
                    v = f"NULLIF(CONVERT(TRIM({r['spalte']}) USING utf8mb4) COLLATE utf8mb4_general_ci,'')"
                by_target.setdefault((tg, r["klasse"] == "TEXTREF"), []).append(
                    (len(KEYS) - 1, f"SELECT {len(KEYS) - 1} k,{v} v FROM {r['tabelle']}", cnt.get(r["tabelle"], 0)))
    queries = []
    for (tg, textref), parts in sorted(by_target.items()):
        tt, tc = tg.split(".")
        chunk, rows = [], 0
        for k, sel, n in sorted(parts, key=lambda x: x[2]):
            if chunk and rows + n > MAX_ROWS:
                queries.append((tg, textref, chunk, rows))
                chunk, rows = [], 0
            chunk.append(sel)
            rows += n
        queries.append((tg, textref, chunk, rows))
    os.makedirs(outdir, exist_ok=True)
    stmts = []
    for tg, textref, chunk, rows in queries:
        tt, tc = tg.split(".")
        zero = "v IS NULL" if textref else "v IS NULL OR(v=0 AND p IS NULL)"
        dist = "COUNT(DISTINCT v)" if textref else "COUNT(DISTINCT NULLIF(v,0))"
        maxv = "NULL" if textref else "MAX(v)"
        stmts.append((f"SELECT k,COUNT(*) n,SUM({zero}) l,SUM(p IS NOT NULL) t,{dist} d,{maxv} m "
                      f"FROM({' UNION ALL '.join(chunk)})s LEFT JOIN(SELECT DISTINCT "
                      + (f"CONVERT({tc} USING utf8mb4) COLLATE utf8mb4_general_ci" if textref else tc)
                      + f" p FROM {tt})y ON p=v GROUP BY k", rows))
    files, cur, rows = [], [], 0
    for st, n in stmts:  # kleine Abfragen bündeln
        if cur and (rows + n > MAX_ROWS or sum(len(x) for x in cur) + len(st) > 6000):
            files.append(cur)
            cur, rows = [], 0
        cur.append(st)
        rows += n
    files.append(cur)
    for i, f_ in enumerate(files):
        with open(os.path.join(outdir, f"q_{i:02d}.sql"), "w", encoding="utf-8") as f:
            f.write("\nUNION ALL ".join(f_))
    print(len(files), "Dateien")
    with open(os.path.join(HERE, "mess_keys.tsv"), "w", encoding="utf-8") as f:
        f.write("k\thypothese\n" + "".join(f"{i}\t{k}\n" for i, k in enumerate(KEYS)))
    print(len(queries), "Abfragen,", len(KEYS), "Hypothesen")


if __name__ == "__main__":
    main(sys.argv[1])
