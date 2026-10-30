#!/usr/bin/env python3
"""Baut veze_komplett.tsv aus verweis_kandidaten.tsv + mess_keys.tsv + mess_results.tsv + poly_results.tsv + rel_results.tsv.

Je verweisartiger Spalte (FK, LOOKUP, TEXTREF, POLY, LISTE) eine Zeile mit der besten gemessenen Hypothese:
n, leer/0, treffer, ins_leere, quote (= treffer / (n - leer)), alle Hypothesen, Bewertung, Vergleich mit rel_results (alt).
Bewertung: belegt (>= 98 %), wahrscheinlich (>= 90 %), schwach (>= 50 %), falsch/unklar (< 50 %), leer (nur NULL/0),
           Tabelle leer, nicht gemessen. Zufallstreffer-Hinweis, wenn das Ziel einen kleineren ID-Raum hat als die Quelle.
Aufruf: python3 -I build_veze.py   -> gibt Abdeckung aus
"""
import csv
import os

HERE = os.path.dirname(os.path.abspath(__file__))


def rd(name):
    with open(os.path.join(HERE, name), encoding="utf-8") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def main():
    kand = rd("verweis_kandidaten.tsv")
    keys = {r["k"]: r["hypothese"] for r in rd("mess_keys.tsv")}
    res = {r["k"]: r for r in rd("mess_results.tsv")}
    poly = {}
    for r in rd("poly_results.tsv"):
        poly.setdefault(r["quelle"], []).append(r)
    old = {}
    with open(os.path.join(HERE, "rel_results.tsv"), encoding="utf-8") as f:
        for line in f:
            p = line.rstrip("\n").split("\t")
            if len(p) >= 3:
                old[p[0]] = (p[1], p[2])
    counts = {}
    with open(os.path.join(HERE, "counts.tsv"), encoding="utf-8") as f:
        for line in f:
            t, n = line.rstrip("\n").split("\t")
            counts[t] = int(n)

    hyp = {}
    for k, h in keys.items():
        src, tgt = h.split(">")
        r = res.get(k)
        if r:
            n, leer, t = int(r["n"]), int(r["leer"] or 0), int(r["treffer"] or 0)
            basis = n - leer
            q = t / basis if basis else None
            hyp.setdefault(src, []).append(dict(ziel=tgt, n=n, leer=leer, treffer=t, ins_leere=basis - t, quote=q,
                                                dist=r["dist"], maxv=r["maxv"]))
        else:
            hyp.setdefault(src, []).append(dict(ziel=tgt, n=0, leer=0, treffer=0, ins_leere=0, quote=None, dist="", maxv=""))

    out = ["tabelle\tspalte\tklasse\tziel\tn\tleer_0\ttreffer\tins_leere\tquote\tdistinct\tmax\tbewertung\thypothesen\talt_rel_results\thinweis"]
    stat = {"verweisartig": 0, "gemessen": 0}
    bew_count = {}
    for r in kand:
        if r["klasse"] not in ("FK", "LOOKUP", "TEXTREF", "POLY", "LISTE"):
            continue
        stat["verweisartig"] += 1
        col = f"{r['tabelle']}.{r['spalte']}"
        hinweis = r["grund"]
        alt = "; ".join(f"{k.split('>')[1]} n={v[0]} ok={v[1]}" for k, v in old.items() if k.startswith(col + ">"))
        if r["klasse"] == "POLY":
            rows = poly.get(col)
            if rows:
                stat["gemessen"] += 1
                bew = "je Gruppe (poly_results.tsv)"
                out.append("\t".join([r["tabelle"], r["spalte"], "POLY", r["ziele"], str(sum(int(x["n"]) for x in rows if x["n"].isdigit())),
                                      "", "", "", "", "", "", bew,
                                      " | ".join(f"g={x['gruppe']}: n={x['n']} {x['treffer_je_ziel']}" for x in rows), alt, hinweis]))
            else:
                bew = "Tabelle leer" if counts.get(r["tabelle"], 0) == 0 else "nicht gemessen"
                if counts.get(r["tabelle"], 0) <= 2:
                    bew = f"nicht gemessen (Tabelle {counts.get(r['tabelle'], 0)} Zeilen)"
                out.append("\t".join([r["tabelle"], r["spalte"], "POLY", r["ziele"], str(counts.get(r["tabelle"], 0)),
                                      "", "", "", "", "", "", bew, "", alt, hinweis]))
            bew_count[bew.split(" (")[0]] = bew_count.get(bew.split(" (")[0], 0) + 1
            continue
        hs = hyp.get(col, [])
        if r["klasse"] == "LISTE" or not hs:
            bew = "nicht gemessen (ID-Liste)" if r["klasse"] == "LISTE" else "nicht gemessen"
            if r["tabelle"].startswith("rb_"):
                bew = f"nicht gemessen (Fremdprojekt rb_*, {counts.get(r['tabelle'], 0)} Zeilen)"
            out.append("\t".join([r["tabelle"], r["spalte"], r["klasse"], r["ziele"], str(counts.get(r["tabelle"], "")),
                                  "", "", "", "", "", "", bew, "", alt, hinweis]))
            bew_count["nicht gemessen"] = bew_count.get("nicht gemessen", 0) + 1
            continue
        stat["gemessen"] += 1
        best = max(hs, key=lambda h: (h["quote"] or -1, h["treffer"]))
        if best["n"] == 0:
            bew = "Tabelle leer"
        elif best["n"] == best["leer"]:
            bew = "leer (nur NULL/0)"
        elif best["quote"] >= 0.98:
            bew = "belegt"
        elif best["quote"] >= 0.90:
            bew = "wahrscheinlich"
        elif best["quote"] >= 0.50:
            bew = "schwach"
        else:
            bew = "falsch/unklar"
        if len([h for h in hs if h["quote"] and h["quote"] >= 0.9]) > 1:
            hinweis += "; mehrere Ziele >= 90 % (ID-Räume überlappen, Zuordnung nach Name/Kommentar)"
        bew_count[bew] = bew_count.get(bew, 0) + 1
        fmt = lambda h: f"{h['ziel']}: {h['treffer']}/{h['n'] - h['leer']}" + (f" ({h['quote']:.1%})" if h["quote"] is not None else "")
        out.append("\t".join([r["tabelle"], r["spalte"], r["klasse"], best["ziel"], str(best["n"]), str(best["leer"]),
                              str(best["treffer"]), str(best["ins_leere"]),
                              f"{best['quote']:.4f}" if best["quote"] is not None else "", str(best["dist"]), str(best["maxv"]),
                              bew, " | ".join(fmt(h) for h in hs), alt, hinweis]))
    with open(os.path.join(HERE, "veze_komplett.tsv"), "w", encoding="utf-8") as f:
        f.write("\n".join(out) + "\n")
    print(stat, bew_count)


if __name__ == "__main__":
    main()
