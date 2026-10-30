#!/usr/bin/env python3
"""Baut kandidat_profil.tsv aus profil_keys.tsv + profil_stat_raw.tsv + profil_top_raw.json + profil_top2_raw.json.

Je Spalte der Profil-Tabellen: Klasse, befüllt, Füllgrad, distinct, min/max (nur Zahl/Datum), Top-Werte (nur Codes,
Text-Codes erst ab Häufigkeit 5), Plausibilität (automatische Hinweise), Filtertyp-Vorschlag.
[TAJNO]-Spalten: nicht gemessen. Aufruf: python3 -I build_profil.py
"""
import csv
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    keys = list(csv.DictReader(open(os.path.join(HERE, "profil_keys.tsv"), encoding="utf-8"), delimiter="\t"))
    klass = {(r["tabelle"], r["spalte"]): r for r in csv.DictReader(open(os.path.join(HERE, "verweis_kandidaten.tsv"),
                                                                           encoding="utf-8"), delimiter="\t")}
    raw = {}
    for line in open(os.path.join(HERE, "profil_stat_raw.tsv"), encoding="utf-8"):
        t, s = line.rstrip("\n").split("\t")
        raw[t] = s.split("|")
    top1 = json.load(open(os.path.join(HERE, "profil_top_raw.json"), encoding="utf-8"))
    top2 = json.load(open(os.path.join(HERE, "profil_top2_raw.json"), encoding="utf-8"))
    per_t = {}
    for k in keys:
        per_t.setdefault(k["tabelle"], []).append(k)
    out = ["tabelle\tspalte\ttyp\tklasse\tn_zeilen\tbefuellt\tfuellgrad\tdistinct\tmin\tmax\ttop_werte\tplausibilitaet\tfiltertyp"]
    n_cols = 0
    for (t, c), r in klass.items():
        if r["klasse"] == "SENSIBEL" and t in raw:
            out.append("\t".join([t, c, r["typ"], "SENSIBEL", "", "", "", "", "", "", "", "[TAJNO] – nicht gemessen", "nie"]))
    for t, ks in per_t.items():
        if t not in raw:
            continue
        vals = raw[t]
        n = int(vals[0])
        for i, k in enumerate(ks):
            n_cols += 1
            parts = vals[i + 1].split(":") if i + 1 < len(vals) else []
            fill = int(parts[0]) if parts and parts[0].isdigit() else 0
            dist = parts[1] if len(parts) > 1 else ""
            mn = parts[2] if len(parts) > 2 else ""
            mx = ":".join(parts[3:]) if len(parts) > 3 else ""
            cls = klass[(t, k["spalte"])]["klasse"]
            top = top1.get(k["i"]) or top2.get(k["spalte"]) if t == "idk_kandidati" or k["i"] in top1 else top1.get(k["i"])
            if t != "idk_kandidati" and not top and k["spalte"] in top2:
                top = top2[k["spalte"]]
            plaus = []
            if n and fill == 0:
                plaus.append("leer")
            elif n and fill / n < 0.05:
                plaus.append("fast leer (<5 %)")
            if re.match(r"date|datetime|timestamp", k["typ"]) and mx and mx[:4].isdigit() and int(mx[:4]) > 2027:
                plaus.append(f"Zukunftsdatum (max {mx})")
            if re.match(r"date|datetime", k["typ"]) and mn.startswith("1900"):
                plaus.append("Platzhalter 1900")
            if mn.startswith("1970-01-01"):
                plaus.append("Platzhalter 1970-01-01")
            if top and any(x.startswith("=") for x in top):
                plaus.append("leere Strings neben NULL")
            if cls == "PII":
                plaus.append("Personendaten – Werte nicht ausgegeben")
            if cls in ("TEXT", "PII") and dist and n and int(dist) > 0.5 * max(fill, 1) and fill > 1000:
                plaus.append("Freitext (hohe Kardinalität)")
            ftyp = {"FK": "ID/Verweis (Join)", "LOOKUP": "Code-Liste (Lookup)", "CODE": "Code-Liste/Flag", "DATUM": "Datumsbereich",
                    "ZAHL": "Zahlenbereich", "TEXTREF": "Beruf über beruf_mapping", "PII": "nie als Filter (nur PII-Rolle)",
                    "TEXT": "Stichwort (LIKE) oder keiner", "PK": "ID", "POLY": "Verweis je Gruppe", "TECH": "keiner"}.get(cls, "")
            out.append("\t".join([t, k["spalte"], k["typ"], cls, str(n), str(fill), f"{fill / n:.3f}" if n else "",
                                  dist, mn if cls not in ("TEXT", "PII") else "", mx if cls not in ("TEXT", "PII") else "",
                                  "; ".join(top or []) if cls in ("CODE", "LOOKUP") else "", "; ".join(plaus), ftyp]))
    with open(os.path.join(HERE, "kandidat_profil.tsv"), "w", encoding="utf-8") as f:
        f.write("\n".join(out) + "\n")
    print(n_cols, "Spalten profiliert in", len([t for t in per_t if t in raw]), "Tabellen")


if __name__ == "__main__":
    main()
