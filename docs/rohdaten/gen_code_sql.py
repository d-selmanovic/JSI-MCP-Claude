#!/usr/bin/env python3
"""Mess-SQL für alle CODE-Spalten aus verweis_kandidaten.tsv (Werteverteilung, read-only).

Je Spalte: n, NULL/leer, Anzahl verschiedener Werte, Top-12-Werte mit Häufigkeit.
Datenschutz: Text-Codes nur mit Häufigkeit >= 5 (seltene Freitexte könnten Personen identifizieren);
die Zahl verschiedener Werte wird trotzdem vollständig gezählt.
Ausgabe je Zeile: "k|wert|anzahl|distinct|n|leer"; Zuordnung k -> Spalte in code_keys.tsv.
Aufruf: python3 -I gen_code_sql.py <ausgabeordner>
"""
import csv
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
MAX_LEN = 6000


def main(outdir):
    cols = []
    with open(os.path.join(HERE, "verweis_kandidaten.tsv"), encoding="utf-8") as f:
        for r in csv.DictReader(f, delimiter="\t"):
            if r["klasse"] == "CODE":
                cols.append((r["tabelle"], r["spalte"], r["typ"]))
    parts = []
    for i, (t, c, typ) in enumerate(cols):
        is_text = typ.startswith(("varchar", "char", "text"))
        v = f"CONVERT(TRIM({c}) USING utf8mb4) COLLATE utf8mb4_general_ci" if is_text else f"CAST({c} AS CHAR)"
        having = " HAVING COUNT(*)>=5 OR v IS NULL" if is_text else ""
        parts.append(
            f"SELECT {i} k,v,c,d,nn,ll FROM(SELECT v,c,ROW_NUMBER()OVER(ORDER BY c DESC) rn,"
            f"(SELECT COUNT(DISTINCT {c}) FROM {t}) d,(SELECT COUNT(*) FROM {t}) nn,"
            f"(SELECT COUNT(*) FROM {t} WHERE {c} IS NULL" + (f" OR TRIM({c})=''" if is_text else "") + ") ll "
            f"FROM(SELECT {v} v,COUNT(*) c FROM {t} GROUP BY v{having})g)x WHERE rn<=12")
    files, cur = [], []
    for p in parts:
        if cur and sum(len(x) for x in cur) + len(p) > MAX_LEN:
            files.append(cur)
            cur = []
        cur.append(p)
    files.append(cur)
    os.makedirs(outdir, exist_ok=True)
    for i, f_ in enumerate(files):
        with open(os.path.join(outdir, f"c_{i:02d}.sql"), "w", encoding="utf-8") as f:
            f.write("SELECT JSON_ARRAYAGG(CONCAT_WS('|',k,IFNULL(v,'NULL'),c,d,nn,ll)) r FROM(\n" + "\nUNION ALL ".join(f_) + "\n)z")
    with open(os.path.join(HERE, "code_keys.tsv"), "w", encoding="utf-8") as f:
        f.write("k\ttabelle\tspalte\ttyp\n" + "".join(f"{i}\t{t}\t{c}\t{typ}\n" for i, (t, c, typ) in enumerate(cols)))
    print(len(files), "Dateien,", len(cols), "Spalten")


if __name__ == "__main__":
    main(sys.argv[1])
