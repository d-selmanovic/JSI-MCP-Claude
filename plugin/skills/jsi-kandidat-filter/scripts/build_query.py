#!/usr/bin/env python3
"""Build a read-only MySQL candidate search query for the JSI CRM (schema jsicrm).

Input: a JSON filter spec (argument --spec '<json>' or --spec-file path, or stdin).
Output: one SQL statement on stdout, ready for BlazeSQL execute_sql.

Design rules (verified against the live database on 2026-10-29):
- Child tables are pre-aggregated in CTEs and joined once. Correlated EXISTS over
  idk_kandidati (122k rows) exceeds BlazeSQL's 60 s timeout.
- Occupation is matched across several sources (application text, application group,
  work experience, qualification, education programme, DE profile) via beruf_mapping,
  which normalises free text into berufsgruppe_id.
- Every value is whitelisted or escaped; free text is only used inside LIKE '%...%'.
- No credential columns are ever selected. Personal data only with "pii": true.
"""
import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

# --- driving licence (EU directive 2006/126/EC): category X is satisfied by these held tokens
LICENCE_IMPLIED = {
    "AM": ["AM", "A1", "A2", "A", "B", "BE", "C1", "C1E", "C", "CE", "D1", "D1E", "D", "DE"],
    "A1": ["A1", "A2", "A"],
    "A2": ["A2", "A"],
    "A": ["A"],
    "B1": ["B1", "B", "BE", "C1", "C1E", "C", "CE", "D1", "D1E", "D", "DE"],
    "B": ["B", "BE", "C1", "C1E", "C", "CE", "D1", "D1E", "D", "DE"],
    "BE": ["BE", "C1E", "CE", "D1E", "DE"],
    "C1": ["C1", "C1E", "C", "CE"],
    "C1E": ["C1E", "CE"],
    "C": ["C", "CE"],
    "CE": ["CE"],
    "D1": ["D1", "D1E", "D", "DE"],
    "D1E": ["D1E", "DE"],
    "D": ["D", "DE"],
    "DE": ["DE"],
    "E": ["E", "BE", "CE", "C1E", "DE", "D1E"],
    "F": ["F"], "G": ["G"], "M": ["M"],
}

LEVELS = ["A1", "A2", "B1", "B2", "C1", "C2"]
LANG_LIKE = {"njemacki": "Njema%", "engleski": "Engl%", "talijanski": "Talij%"}
LANG_ALIASES = {
    "njemacki": "njemacki", "njemački": "njemacki", "deutsch": "njemacki", "german": "njemacki", "de": "njemacki",
    "engleski": "engleski", "englisch": "engleski", "english": "engleski", "en": "engleski",
    "talijanski": "talijanski", "italienisch": "talijanski", "italian": "talijanski", "it": "talijanski",
}
LANG_SKILLS = {
    "govorna_interakcija": "kj_govorna_interakcija",
    "govorna_produkcija": "kj_govorna_produkcija",
    "citanje": "kj_citanje",
    "slusanje": "kj_slusanje",
    "pisanje": "kj_pisanje",
}

COUNTRY_REGEX = {
    "BIH": r"^(B ?I ?H|R ?BIH|BOS|BIS|BOSNIA|REPUBLIKA SRPSKA|RS ?/? ?BIH|BIH)",
    "SRB": r"^(SRB|SERB|R[.]? ?SRBIJA|REPUBLIKA SRBIJA|СРБ|Срб)",
    "HRV": r"^(HRV|CROA|KROAT|REPUBLIKA HRVATSKA)",
    "DEU": r"^(NJEM|NEM|DEUT|GERM)",
    "MNE": r"^(CRNA|MONTEN|CG$)",
    "SVN": r"^(SLOVEN)",
    "MKD": r"^(MAKED|SJEVERNA MAKED|NORTH MACED)",
    "XKX": r"^(KOSOV)",
    "AUT": r"^(AUSTR|ÖSTERR|OESTERR)",
}

KANDIDAT_STATUS = {0: "Na provjeri", 1: "U obradi", 2: "Obrađen", 3: "Arhiviran", 4: "Kontrola",
                   5: "Dopuna", 6: "Odbio Messenger", 7: "U obradi više od 3 dana", 8: "Na dopuni više od 3 dana"}
STATUS_PRIJAVE = {1: "Slobodan", 2: "U projektu NR", 3: "Casting", 4: "Završen", 5: "Odbijen", 6: "U projektu RZ",
                  7: "Čeka ugovor", 8: "Poslan ugovor", 9: "Potpisan ugovor", 10: "Početak rada",
                  12: "Prikupljanje dokumentacije", 15: "Čeka termin", 18: "Čeka vizu", 21: "Dopuna dokumenata",
                  24: "Odbijena viza", 27: "Dobio vizu"}
# statuses in which a candidate is NOT reserved for an order (rezervisanje = 0) plus "no status"
FREE_STATUSES = [0, 1, 2, 5]

OCC_SOURCES = ["prijava", "grupa", "iskustvo", "kvalifikacija", "smjer", "de_profil"]


class SpecError(ValueError):
    pass


def esc_like(text):
    """Escape a user fragment for use inside LIKE '%...%'."""
    if not isinstance(text, str) or not text.strip():
        raise SpecError(f"invalid keyword: {text!r}")
    t = text.strip()
    if len(t) > 60:
        raise SpecError("keyword too long (max 60 chars)")
    t = t.replace("\\", "\\\\").replace("'", "''").replace("%", "\\%").replace("_", "\\_")
    return t


def ident_list(values, allowed_re=r"^[a-z0-9_]+$"):
    out = []
    for v in values:
        if not isinstance(v, str) or not re.match(allowed_re, v):
            raise SpecError(f"invalid identifier value: {v!r}")
        out.append(f"'{v}'")
    return ", ".join(out)


def int_list(values):
    out = []
    for v in values:
        if isinstance(v, bool) or not isinstance(v, int):
            raise SpecError(f"expected integer, got {v!r}")
        out.append(str(v))
    return ", ".join(out)


def load_occupations():
    with open(os.path.join(HERE, "occupations.json"), encoding="utf-8") as f:
        data = json.load(f)
    return {k: v for k, v in data.items() if not k.startswith("_")}


def norm(s):
    s = s.lower().strip()
    for a, b in (("č", "c"), ("ć", "c"), ("š", "s"), ("ž", "z"), ("đ", "dj"), ("ä", "a"), ("ö", "o"), ("ü", "u"), ("ß", "ss")):
        s = s.replace(a, b)
    return re.sub(r"[\s\-_/]+", " ", s)


def resolve_occupation(term, catalog):
    n = norm(term)
    if n.replace(" ", "_") in catalog:
        return n.replace(" ", "_")
    for key, cfg in catalog.items():
        if n == norm(key) or any(n == norm(s) for s in cfg.get("synonyms", [])):
            return key
    for key, cfg in catalog.items():
        if any(n in norm(s) or norm(s) in n for s in cfg.get("synonyms", []) if len(norm(s)) >= 4):
            return key
    return None


def occupation_ctes(occ_spec, catalog):
    """Return (cte_sql, notes). occ_spec: {"name": str | [str], "broad": bool, "sources": [...],
    "berufsgruppen": [...], "keywords": [...]}"""
    names = occ_spec.get("name") or []
    if isinstance(names, str):
        names = [names]
    broad = bool(occ_spec.get("broad", False))
    sources = occ_spec.get("sources") or OCC_SOURCES
    for s in sources:
        if s not in OCC_SOURCES:
            raise SpecError(f"unknown occupation source {s!r}; allowed: {OCC_SOURCES}")
    groups, kg_ids, keywords, smjer_kw, notes = set(), set(), set(), set(), []
    for n in names:
        key = resolve_occupation(n, catalog)
        if not key:
            notes.append(f"Zanimanje '{n}' nije u katalogu - koristi se samo pretraga po ključnoj riječi.")
            keywords.add(n)
            smjer_kw.add(n)
            continue
        cfg = catalog[key]
        notes.append(f"Zanimanje '{n}' -> katalog '{key}'" + (" (široko)" if broad else ""))
        groups.update(cfg["berufsgruppen"])
        kg_ids.update(cfg["kg_ids"])
        keywords.update(cfg["keywords"])
        smjer_kw.update(cfg["smjer_keywords"])
        if broad:
            groups.update(cfg.get("broad", []))
            kg_ids.update(cfg.get("broad_kg_ids", []))
    groups.update(occ_spec.get("berufsgruppen", []))
    keywords.update(occ_spec.get("keywords", []))
    if not (groups or kg_ids or keywords or smjer_kw):
        raise SpecError("occupation filter is empty")

    g = ident_list(sorted(groups)) if groups else None
    kw = lambda col: " OR ".join(f"{col} LIKE '%{esc_like(k)}%'" for k in sorted(keywords))
    parts = []
    if "prijava" in sources:
        if g:
            parts.append(f"SELECT k.kandidat_id AS kid, 'prijava' AS izvor FROM idk_kandidati k "
                         f"JOIN beruf_mapping bm ON bm.freitext_wert = k.kandidat_prijava_na WHERE bm.berufsgruppe_id IN ({g})")
        if keywords:
            parts.append(f"SELECT k.kandidat_id, 'prijava' FROM idk_kandidati k WHERE {kw('k.kandidat_prijava_na')} OR {kw('k.kandidat_pp_pozicija')}")
    if "grupa" in sources and kg_ids:
        parts.append(f"SELECT k.kandidat_id, 'grupa' FROM idk_kandidati k WHERE k.kandidat_group IN ({int_list(sorted(kg_ids))})")
    if "iskustvo" in sources:
        if g:
            parts.append(f"SELECT r.kri_kandidat_id, 'iskustvo' FROM idk_kandidat_radno_iskustvo r "
                         f"JOIN beruf_mapping bm ON bm.freitext_wert = r.kri_pozicija WHERE bm.berufsgruppe_id IN ({g})")
        if keywords:
            parts.append(f"SELECT r.kri_kandidat_id, 'iskustvo' FROM idk_kandidat_radno_iskustvo r WHERE {kw('r.kri_pozicija')} OR {kw('r.kri_pozicija_de')}")
    if "kvalifikacija" in sources:
        if g:
            parts.append(f"SELECT e.ke_kandidat_id, 'kvalifikacija' FROM idk_kandidat_edukacija e "
                         f"JOIN beruf_mapping bm ON bm.freitext_wert = e.ke_naziv_kvalifikacije WHERE bm.berufsgruppe_id IN ({g})")
        if keywords:
            parts.append(f"SELECT e.ke_kandidat_id, 'kvalifikacija' FROM idk_kandidat_edukacija e WHERE {kw('e.ke_naziv_kvalifikacije')}")
    if "smjer" in sources and smjer_kw:
        skw = " OR ".join(f"s.ss_naziv LIKE '%{esc_like(k)}%' OR s.ss_naziv_de LIKE '%{esc_like(k)}%'" for k in sorted(smjer_kw))
        parts.append(f"SELECT e.ke_kandidat_id, 'smjer' FROM idk_kandidat_edukacija e "
                     f"JOIN idk_skole_smjerovi s ON s.ss_id = e.ke_smjer_id WHERE {skw}")
    if "de_profil" in sources and keywords:
        parts.append(f"SELECT d.kde_kandidat_id, 'de_profil' FROM idk_kandidat_de d WHERE {kw('d.kde_prijava_na')}")
    if not parts:
        raise SpecError("no occupation source produced a condition")
    cte = ("occ_raw AS (\n  " + "\n  UNION\n  ".join(parts) + "\n),\n"
           "occ AS (SELECT kid, GROUP_CONCAT(DISTINCT izvor ORDER BY izvor SEPARATOR ',') AS izvori, "
           "COUNT(DISTINCT izvor) AS broj_izvora FROM occ_raw WHERE kid IS NOT NULL AND kid <> 0 GROUP BY kid)")
    return cte, notes


def licence_condition(spec, notes):
    cats = spec.get("kategorije") or []
    if isinstance(cats, str):
        cats = [c.strip() for c in cats.split(",")]
    mode = spec.get("mode", "any")
    strict = bool(spec.get("strict", False))
    if mode not in ("any", "all"):
        raise SpecError("vozacka.mode must be 'any' or 'all'")
    norm_cat = "REPLACE(REPLACE(UPPER(k.kandidat_vozacka_kategorija), ' ', ''), ';', ',')"
    legacy = "UPPER(TRIM(k.kandidat_vozacka_dozvola))"
    if not cats:  # "has any licence"
        notes.append("Vozačka: bilo koja kategorija.")
        return (f"(k.kandidat_vozacka_dozvola IN ('Da','B','C','CE','C1','BE','C1E') "
                f"OR (NULLIF(TRIM(k.kandidat_vozacka_kategorija),'') IS NOT NULL AND UPPER(TRIM(k.kandidat_vozacka_kategorija)) NOT IN ('NE','0')))")
    conds = []
    for c in cats:
        c = c.upper().strip()
        if c not in LICENCE_IMPLIED:
            raise SpecError(f"unknown licence category {c!r}")
        held = [c] if strict else LICENCE_IMPLIED[c]
        ors = [f"FIND_IN_SET('{h}', {norm_cat}) > 0" for h in held]
        ors.append(f"{legacy} IN ({', '.join(repr(h) for h in held)})")
        conds.append("(" + " OR ".join(ors) + ")")
        notes.append(f"Vozačka {c}: " + ("tačno ta kategorija" if strict else f"prihvata {', '.join(held)} (EU pravilo: viša kategorija uključuje nižu)"))
    return "(" + (" OR " if mode == "any" else " AND ").join(conds) + ")"


def language_cte(spec, idx, notes):
    lang = LANG_ALIASES.get(norm(spec.get("jezik", "njemacki")))
    if not lang:
        raise SpecError(f"unknown language {spec.get('jezik')!r}")
    min_level = (spec.get("min_nivo") or "A1").upper()
    if min_level not in LEVELS:
        raise SpecError(f"min_nivo must be one of {LEVELS}")
    skill = spec.get("vjestina", "govorna_interakcija")
    lvl_list = ", ".join(f"'{l}'" for l in LEVELS)
    if skill == "bilo_koja":
        level_expr = "GREATEST(" + ", ".join(f"FIELD(TRIM(j.{c}), {lvl_list})" for c in LANG_SKILLS.values()) + ")"
    elif skill in LANG_SKILLS:
        level_expr = f"FIELD(TRIM(j.{LANG_SKILLS[skill]}), {lvl_list})"
    else:
        raise SpecError(f"vjestina must be one of {list(LANG_SKILLS)} or 'bilo_koja'")
    need = LEVELS.index(min_level) + 1
    # Certificates are recorded by file upload (cvl_certificate_path, 367 rows), not by cvl_status = 8 (2 rows);
    # most uploaded certificates later moved to status 9 "certifikat istekao".
    cert = spec.get("certifikat", False)
    if cert not in (False, True, "postoji", "vazeci"):
        raise SpecError("certifikat must be true/'postoji' or 'vazeci'")
    name = f"lang{idx}"
    if cert:
        valid = (" AND (v.cvl_certificate_expiration_date IS NULL OR v.cvl_certificate_expiration_date >= CURDATE())"
                 if cert == "vazeci" else "")
        sql = (f"{name} AS (SELECT j.kj_kandidatid AS kid, MAX({level_expr}) AS nivo FROM idk_kandidat_jezici j "
               f"JOIN idk_candidate_verified_languages v ON v.cvl_id = j.kj_id "
               f"AND NULLIF(TRIM(v.cvl_certificate_path), '') IS NOT NULL{valid} "
               f"WHERE j.kj_naziv LIKE '{LANG_LIKE[lang]}' AND {level_expr} >= {need} GROUP BY j.kj_kandidatid)")
    else:
        sql = (f"{name} AS (SELECT j.kj_kandidatid AS kid, MAX({level_expr}) AS nivo FROM idk_kandidat_jezici j "
               f"WHERE j.kj_naziv LIKE '{LANG_LIKE[lang]}' AND {level_expr} >= {need} GROUP BY j.kj_kandidatid)")
    notes.append(f"Jezik {lang} >= {min_level} ({skill})" + ((", sa certifikatom (" + ("važeći danas" if cert == "vazeci" else "postoji") + ")") if cert else ", samoprocjena kandidata"))
    return name, sql


def build(spec):
    if not isinstance(spec, dict):
        raise SpecError("spec must be a JSON object")
    allowed = {"zanimanje", "vozacka", "jezici", "jezik", "obrazovanje", "iskustvo_u_struci", "drzava",
               "drzavljanstvo", "spol", "starost", "registriran", "status_prijave", "slobodni",
               "kandidat_status", "ukljuci_arhivu", "kontaktabilni", "nacin_odlaska", "nalog_id", "projekt_id",
               "nostrifikacija", "izlaz", "limit", "pii", "sortiraj"}
    unknown = set(spec) - allowed
    if unknown:
        raise SpecError(f"unknown filter keys: {sorted(unknown)}; allowed: {sorted(allowed)}")

    catalog = load_occupations()
    ctes, joins, where, notes = [], [], [], []

    # default: exclude archived candidates
    if not spec.get("ukljuci_arhivu", False):
        where.append("k.kandidat_status <> 3")
        notes.append("Arhivirani kandidati (kandidat_status = 3) isključeni.")

    occ = spec.get("zanimanje")
    if occ:
        if isinstance(occ, (str, list)):
            occ = {"name": occ}
        cte, n = occupation_ctes(occ, catalog)
        ctes.append(cte)
        joins.append("JOIN occ ON occ.kid = k.kandidat_id")
        notes += n

    if spec.get("vozacka") is not None:
        v = spec["vozacka"]
        if isinstance(v, (str, list)):
            v = {"kategorije": v}
        if v is True:
            v = {}
        where.append(licence_condition(v, notes))

    langs = spec.get("jezici") or ([spec["jezik"]] if spec.get("jezik") else [])
    for i, lspec in enumerate(langs):
        name, sql = language_cte(lspec, i, notes)
        ctes.append(sql)
        joins.append(f"JOIN {name} ON {name}.kid = k.kandidat_id")

    edu = spec.get("obrazovanje")
    if edu:
        vrsta = edu.get("vrsta")
        if vrsta and vrsta not in ("srednje", "visoko", "ostalo"):
            raise SpecError("obrazovanje.vrsta must be srednje|visoko|ostalo")
        conds = []
        if vrsta:
            conds.append(f"e.ke_vrsta_obrazovanja = '{vrsta}'")
        if edu.get("smjer"):
            s = esc_like(edu["smjer"])
            ctes.append(f"edu AS (SELECT DISTINCT e.ke_kandidat_id AS kid FROM idk_kandidat_edukacija e "
                        f"LEFT JOIN idk_skole_smjerovi s ON s.ss_id = e.ke_smjer_id "
                        f"WHERE (s.ss_naziv LIKE '%{s}%' OR e.ke_naziv_kvalifikacije LIKE '%{s}%')"
                        + (" AND " + " AND ".join(conds) if conds else "") + ")")
        else:
            ctes.append("edu AS (SELECT DISTINCT e.ke_kandidat_id AS kid FROM idk_kandidat_edukacija e WHERE " + " AND ".join(conds) + ")")
        joins.append("JOIN edu ON edu.kid = k.kandidat_id")
        notes.append(f"Obrazovanje: {edu}")

    isk = spec.get("iskustvo_u_struci")
    if isk:
        where.append("k.kandidat_iskustvo_u_struci = 1")
        if isinstance(isk, dict) and isk.get("min_godina") is not None:
            mg = isk["min_godina"]
            if not isinstance(mg, int) or not 1 <= mg <= 6:
                raise SpecError("iskustvo_u_struci.min_godina must be 1..6")
            where.append(f"k.kandidat_iskustvo_u_struci_trajanje >= {mg + 1}")  # 1 = <1 god, 2 = 1 god, ...
        notes.append("Radno iskustvo u struci = da (samo ~18% kandidata ima popunjeno ovo polje).")

    if spec.get("drzava"):
        codes = spec["drzava"] if isinstance(spec["drzava"], list) else [spec["drzava"]]
        ors = []
        for c in codes:
            c = c.upper()
            if c not in COUNTRY_REGEX:
                raise SpecError(f"drzava must be one of {list(COUNTRY_REGEX)}")
            ors.append(f"TRIM(k.kandidat_drzava) REGEXP '{COUNTRY_REGEX[c]}'")
        where.append("(" + " OR ".join(ors) + ")")
        notes.append(f"Država prebivališta: {codes} (normalizirano iz slobodnog teksta; popunjeno ~35%).")

    if spec.get("drzavljanstvo"):
        dv = spec["drzavljanstvo"].upper()
        if dv not in ("EU", "NON-EU"):
            raise SpecError("drzavljanstvo must be EU or NON-EU")
        where.append("REPLACE(REPLACE(UPPER(TRIM(k.kandidat_drzavljanstvo_vrsta)),'-',''),' ','') "
                     + ("LIKE 'EUDR%'" if dv == "EU" else "LIKE 'NONEU%'"))

    if spec.get("spol"):
        sp = spec["spol"].lower()
        if sp not in ("m", "z", "ž", "muško", "žensko"):
            raise SpecError("spol must be m or z")
        where.append("k.kandidat_spol = " + ("'Muško'" if sp in ("m", "muško") else "'Žensko'"))
        notes.append("Spol popunjen samo kod ~13% kandidata.")

    if spec.get("starost"):
        st = spec["starost"]
        if st.get("od") is not None:
            where.append(f"k.kandidat_datumrodjenja <= DATE_SUB(CURDATE(), INTERVAL {int(st['od'])} YEAR)")
        if st.get("do") is not None:
            where.append(f"k.kandidat_datumrodjenja > DATE_SUB(CURDATE(), INTERVAL {int(st['do']) + 1} YEAR)")
        where.append("k.kandidat_datumrodjenja > '1940-01-01'")

    if spec.get("registriran"):
        r = spec["registriran"]
        for key, op in (("od", ">="), ("do", "<")):
            if r.get(key):
                if not re.match(r"^\d{4}-\d{2}-\d{2}$", r[key]):
                    raise SpecError("registriran.od/do must be YYYY-MM-DD")
                where.append(f"k.kandidat_datetime {op} '{r[key]}'")

    if spec.get("status_prijave"):
        where.append(f"k.kandidat_status_prijave IN ({int_list(spec['status_prijave'])})")
    if spec.get("slobodni"):
        where.append(f"(k.kandidat_status_prijave IS NULL OR k.kandidat_status_prijave IN ({int_list(FREE_STATUSES)}))")
        notes.append("Samo kandidati koji nisu rezervisani za nalog (status prijave NULL/0/1/2/5).")
    if spec.get("kandidat_status"):
        where.append(f"k.kandidat_status IN ({int_list(spec['kandidat_status'])})")
    if spec.get("kontaktabilni"):
        where.append("IFNULL(k.kandidat_pogresan_broj,0) = 0 AND IFNULL(k.kandidat_nedostupan,0) = 0 AND NULLIF(TRIM(k.kandidat_mobitel),'') IS NOT NULL")
        notes.append("Isključeni: pogrešan broj, nedostupni, bez mobitela.")
    if spec.get("nacin_odlaska") is not None:
        where.append(f"k.kandidat_nacin_odlaska IN ({int_list(spec['nacin_odlaska'])})")
    if spec.get("nalog_id"):
        where.append(f"k.kandidat_nalog_id IN ({int_list(spec['nalog_id'])})")
    if spec.get("projekt_id"):
        ctes.append(f"prj AS (SELECT DISTINCT pk_kandidatid AS kid FROM idk_project_kandidati WHERE pk_projectid IN ({int_list(spec['projekt_id'])}))")
        joins.append("JOIN prj ON prj.kid = k.kandidat_id")
    if spec.get("nostrifikacija"):
        ctes.append("nostr AS (SELECT DISTINCT id_cand_job AS kid FROM idk_nostrifikovane_diplome WHERE full_recognition = 1)")
        joins.append("JOIN nostr ON nostr.kid = k.kandidat_id")
        notes.append("Samo kandidati sa potpuno priznatom (nostrificiranom) diplomom.")

    izlaz = spec.get("izlaz", "broj")
    if izlaz not in ("broj", "lista", "izvori", "id"):
        raise SpecError("izlaz must be broj|lista|izvori|id")
    limit = spec.get("limit", 200)
    if not isinstance(limit, int) or not 1 <= limit <= 5000:
        raise SpecError("limit must be 1..5000")

    with_sql = ("WITH\n" + ",\n".join(ctes) + "\n") if ctes else ""
    from_sql = "FROM idk_kandidati k\n" + ("\n".join(joins) + "\n" if joins else "")
    where_sql = ("WHERE " + "\n  AND ".join(where) + "\n") if where else ""
    has_occ = bool(occ)

    if izlaz == "broj":
        select = "SELECT COUNT(*) AS broj_kandidata\n"
        tail = ""
    elif izlaz == "izvori":
        if not has_occ:
            raise SpecError("izlaz 'izvori' needs a zanimanje filter")
        select = "SELECT occ.izvori, COUNT(*) AS broj_kandidata\n"
        tail = "GROUP BY occ.izvori\nORDER BY broj_kandidata DESC\n"
    elif izlaz == "id":
        select = "SELECT k.kandidat_id\n"
        tail = f"ORDER BY k.kandidat_id\nLIMIT {limit}\n"
    else:
        cols = ["k.kandidat_id"]
        if spec.get("pii"):
            cols += ["k.kandidat_ime", "k.kandidat_prezime", "k.kandidat_mobitel", "k.kandidat_email"]
        cols += [
            "TRIM(g.kg_title) AS grupa",
            "TRIM(k.kandidat_prijava_na) AS prijava_na",
            "k.kandidat_vozacka_kategorija AS vozacka",
            "TRIM(k.kandidat_drzava) AS drzava",
            "IF(k.kandidat_datumrodjenja > '1940-01-01', TIMESTAMPDIFF(YEAR, k.kandidat_datumrodjenja, CURDATE()), NULL) AS starost",
            "sp.status_naziv AS status_prijave",
            "ks.status_naziv AS kandidat_status",
            "DATE(k.kandidat_datetime) AS registriran",
        ]
        if has_occ:
            cols += ["occ.izvori AS izvori_zanimanja"]
        for i, _ in enumerate(langs):
            cols.append(f"ELT(lang{i}.nivo, 'A1','A2','B1','B2','C1','C2') AS jezik{i + 1}_nivo")
        from_sql += ("LEFT JOIN idk_kandidati_grupe g ON g.kg_id = k.kandidat_group\n"
                     "LEFT JOIN idk_kandidat_status_prijave sp ON sp.status_id = k.kandidat_status_prijave\n"
                     "LEFT JOIN idk_kandidat_status ks ON ks.status_id = k.kandidat_status\n")
        select = "SELECT " + ",\n       ".join(cols) + "\n"
        order = spec.get("sortiraj", "relevantnost")
        if order == "relevantnost" and has_occ:
            tail = f"ORDER BY occ.broj_izvora DESC, k.kandidat_datetime DESC\nLIMIT {limit}\n"
        else:
            tail = f"ORDER BY k.kandidat_datetime DESC\nLIMIT {limit}\n"

    sql = with_sql + select + from_sql + where_sql + tail
    return sql.strip(), notes


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--spec", help="filter spec as JSON string")
    ap.add_argument("--spec-file", help="path to JSON spec")
    ap.add_argument("--notes", action="store_true", help="print interpretation notes to stderr")
    args = ap.parse_args()
    raw = args.spec if args.spec else (open(args.spec_file, encoding="utf-8").read() if args.spec_file else sys.stdin.read())
    try:
        sql, notes = build(json.loads(raw))
    except (SpecError, json.JSONDecodeError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(2)
    if args.notes:
        for n in notes:
            print(f"-- {n}", file=sys.stderr)
    print(sql)


if __name__ == "__main__":
    main()
