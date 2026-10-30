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
LANG_LIKE = {"njemacki": "Njema%", "engleski": "Engl%", "talijanski": "Talij%", "spanjolski": "%panjol%",
             "francuski": "Franc%", "ruski": "Rusk%", "arapski": "Arap%", "turski": "Tursk%"}
LANG_ALIASES = {
    "njemacki": "njemacki", "njemački": "njemacki", "deutsch": "njemacki", "german": "njemacki", "de": "njemacki",
    "engleski": "engleski", "englisch": "engleski", "english": "engleski", "en": "engleski",
    "talijanski": "talijanski", "italienisch": "talijanski", "italian": "talijanski", "it": "talijanski",
    "spanjolski": "spanjolski", "španjolski": "spanjolski", "spanisch": "spanjolski", "spanish": "spanjolski", "es": "spanjolski",
    "francuski": "francuski", "französisch": "francuski", "franzosisch": "francuski", "french": "francuski", "fr": "francuski",
    "ruski": "ruski", "russisch": "ruski", "russian": "ruski", "ru": "ruski",
    "arapski": "arapski", "arabisch": "arapski", "arabic": "arapski", "ar": "arapski",
    "turski": "turski", "türkisch": "turski", "turkisch": "turski", "turkish": "turski", "tr": "turski",
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

# citizenship (kandidat_drzavljanstvo, free text, ~14 % filled; values like 'Bosanskohercegovačko', 'Srpsko')
CITIZENSHIP_REGEX = {
    "BIH": r"^(BOSAN|BIH|B ?I ?H|BOSN)",
    "SRB": r"^(SRP|SRB|SERB)",
    "HRV": r"^(HRV|CROA|KROAT)",
    "MNE": r"^(CRNOGOR|MONTEN)",
    "MKD": r"^(MAKED|MACED)",
    "SVN": r"^(SLOVEN)",
    "BGR": r"^(BUGAR|BULGAR)",
    "HUN": r"^(MA[DĐ]JAR|MA[DĐ]AR|HUNGAR)",
    "DEU": r"^(NJEMA|NEMA|DEUT|GERM)",
    "ITA": r"^(ITAL|TALIJ)",
    "AUT": r"^(AUSTR|ÖSTERR)",
    "XKX": r"^(KOSOV)",
    "ALB": r"^(ALBAN)",
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

# documented codes (column comments / lookup tables, read 2026-10-30); undocumented values are allowed but flagged
PORIJEKLO = {0: "stari put (CRM/prijava)", 1: "došao sa DIPL-a", 2: "došao sa DAK-a", 3: "preporuka partnera",
             4: "svezavize web (SZV->DIPL->KAN)", 5: "JobStep web (JS->DIPL->KAN)", 6: "nedokumentovano", 7: "nedokumentovano",
             8: "nedokumentovano"}
MESSENGER_STATUS = {0: "ništa rađeno", 1: "poslan SMS za instalaciju", 2: "logirao se", 3: "odbio instalirati",
                    4: "italijanske prijave", 5: "u toku popunjavanje profila", 6: "u toku dopunjavanje profila"}
BRACNO_STANJE = {0: "nepoznato", 1: "neoženjen/neudana", 2: "oženjen/udana", 3: "udovac/udovica", 4: "razveden/a"}
CASTING_STATUS = {1: "Došao", 2: "Nije došao", 3: "Odustao", 4: "nedokumentovano", 5: "nedokumentovano"}
INTERVJU_PREPORUKA = {"hire": 1, "reject": 2, "not_sure": 3}
ODBIO = {"kandidat": 1, "poslodavac": 2}
NOSTR_PRIZNANJE = {"potpuno": [1], "djelimicno": [0], "status_2": [2], "bilo_koje": None}
GLOSSA = {0: "nije glossa lead", 1: "glossa lead", 2: "prihvaćen glossa lead", 3: "potencijalni glossa lead"}


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


def load_berufsgruppen():
    with open(os.path.join(HERE, "berufsgruppen.json"), encoding="utf-8") as f:
        return json.load(f)["gruppen"]


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
        bg = norm(n).replace(" ", "_")
        if not key and bg in load_berufsgruppen():
            notes.append(f"Zanimanje '{n}' -> berufsgruppe '{bg}' (beruf_mapping; bez sinonima/grupa prijave)")
            groups.add(bg)
            continue
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
    bad = [g for g in occ_spec.get("berufsgruppen", []) if g not in load_berufsgruppen()]
    if bad:
        raise SpecError(f"unknown berufsgruppen {bad}; see filter_options berufsgruppen")
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


def _date_range(r, col, name):
    conds = []
    if not isinstance(r, dict):
        raise SpecError(f"{name} must be an object with od/do")
    for key, op in (("od", ">="), ("do", "<")):
        if r.get(key):
            if not isinstance(r[key], str) or not re.match(r"^\d{4}-\d{2}-\d{2}$", r[key]):
                raise SpecError(f"{name}.{key} must be YYYY-MM-DD")
            conds.append(f"{col} {op} '{r[key]}'")
    return conds


def _codes(v, allowed, name):
    vals = v if isinstance(v, list) else [v]
    for x in vals:
        if isinstance(x, bool) or not isinstance(x, int) or (allowed is not None and x not in allowed):
            raise SpecError(f"{name}: allowed codes {sorted(allowed) if allowed else 'integers'}")
    return int_list(vals)


def _cte(ctes, joins, name, sql):
    ctes.append(f"{name} AS ({sql})")
    joins.append(f"JOIN {name} ON {name}.kid = k.kandidat_id")


def extra_filters(spec, catalog, ctes, joins, where, notes):
    """Filters added 2026-10-30 from the measured link/profile catalogue (docs/rohdaten/veze_komplett.tsv,
    kandidat_profil.tsv). Child tables are pre-aggregated in CTEs (DISTINCT kid), never correlated."""
    if spec.get("porijeklo") is not None:
        where.append(f"k.kandidat_porijeklo IN ({_codes(spec['porijeklo'], PORIJEKLO, 'porijeklo')})")
        notes.append("Porijeklo/kanal: kodovi 6–8 nisu dokumentovani u bazi.")
    if spec.get("messenger_status") is not None:
        where.append(f"k.kandidat_status_messenger IN ({_codes(spec['messenger_status'], MESSENGER_STATUS, 'messenger_status')})")
    if spec.get("bracno_stanje") is not None:
        where.append(f"k.kandidat_bracno_stanje IN ({_codes(spec['bracno_stanje'], BRACNO_STANJE, 'bracno_stanje')})")
        notes.append("Bračno stanje: 0 = nepoznato kod ~97 % kandidata.")
    if spec.get("viza") is not None:
        v = spec["viza"]
        if v not in ("ima", "nema", "dobio", "odbijena", "dopuna"):
            raise SpecError("viza must be ima|nema|dobio|odbijena|dopuna")
        if v in ("ima", "nema"):
            where.append(f"k.kandidat_viza = {1 if v == 'ima' else 0}")
            notes.append("Viza iz kandidat_viza (popunjeno ~40 %, 1 = ima vizu kod 1.231).")
        elif v == "dobio":
            _cte(ctes, joins, "viz", "SELECT DISTINCT lsp_kandidat_id AS kid FROM idk_log_statusi_prijave WHERE lsp_status_prijave_id = 27")
            notes.append("Viza: kandidat je bar jednom bio u statusu 27 'Dobio vizu' (log od 2021-12).")
        else:
            _cte(ctes, joins, "viz", f"SELECT DISTINCT vi_cand_id AS kid FROM idk_pp_visa_incomplete WHERE vi_type = {2 if v == 'odbijena' else 1}")
            notes.append("Viza: " + ("odbijenica" if v == "odbijena" else "dopuna") + " iz idk_pp_visa_incomplete (samo 49 zapisa, partner portal).")
    if spec.get("termin_za_vizu") is not None:
        where.append(f"k.kandidat_termin_za_vizu = {1 if spec['termin_za_vizu'] else 2}")
        notes.append("Termin za vizu popunjen samo kod ~2 % kandidata.")
    if spec.get("casting"):
        c = spec["casting"] if isinstance(spec["casting"], dict) else {}
        conds = []
        if c.get("status") is not None:
            conds.append(f"r.tsr_status IN ({_codes(c['status'], CASTING_STATUS, 'casting.status')})")
        if c.get("nalog_id"):
            conds.append(f"r.tsr_nalog_id IN ({int_list(c['nalog_id'])})")
        conds += _date_range({k: c[k] for k in ("od", "do") if k in c}, "g.ppaq_start_date", "casting")
        _cte(ctes, joins, "cst", "SELECT DISTINCT r.tsr_candidate_id AS kid FROM idk_tf_stats_reservations r "
             "LEFT JOIN idk_pp_appointment_groups g ON g.ppaq_id = r.tsr_interview_id" + (" WHERE " + " AND ".join(conds) if conds else ""))
        notes.append("Casting: rezervacije iz idk_tf_stats_reservations (1 Došao, 2 Nije došao, 3 Odustao; 4/5 nedokumentovano).")
    if spec.get("intervju"):
        c = spec["intervju"] if isinstance(spec["intervju"], dict) else {}
        conds = []
        if c.get("preporuka"):
            pr = c["preporuka"] if isinstance(c["preporuka"], list) else [c["preporuka"]]
            if any(x not in INTERVJU_PREPORUKA for x in pr):
                raise SpecError(f"intervju.preporuka must be in {list(INTERVJU_PREPORUKA)}")
            conds.append("a.pca_recommendation IN (" + ", ".join(str(INTERVJU_PREPORUKA[x]) for x in pr) + ")")
        if c.get("nalog_id"):
            conds.append(f"ap.pap_nalog_id IN ({int_list(c['nalog_id'])})")
        if c.get("aktivan") is not None:
            conds.append(f"a.pca_status = {1 if c['aktivan'] else 0}")
        _cte(ctes, joins, "itv", "SELECT DISTINCT a.pca_kandidat_id AS kid FROM idk_pp_cand_appts a "
             "LEFT JOIN idk_pp_appointments ap ON ap.pap_id = a.pca_appointment_id" + (" WHERE " + " AND ".join(conds) if conds else ""))
        notes.append("Intervju (partner portal): preporuka poslodavca popunjena samo kod 567 od 6.808 termina.")
    if spec.get("odbijen"):
        c = spec["odbijen"] if isinstance(spec["odbijen"], dict) else {}
        conds = []
        if c.get("razlog_id"):
            conds.append(f"x.krr_reason_id IN ({int_list(c['razlog_id'] if isinstance(c['razlog_id'], list) else [c['razlog_id']])})")
        if c.get("odbio"):
            if c["odbio"] not in ODBIO:
                raise SpecError("odbijen.odbio must be kandidat|poslodavac")
            conds.append(f"rr.rr_rejected_by = {ODBIO[c['odbio']]}")
        if c.get("nalog_id"):
            conds.append(f"x.krr_nalog_id IN ({int_list(c['nalog_id'])})")
        _cte(ctes, joins, "odb", "SELECT DISTINCT x.krr_candidate_id AS kid FROM idk_kandidati_reject_reasons x "
             "LEFT JOIN idk_reject_reasons rr ON rr.rr_id = x.krr_reason_id" + (" WHERE " + " AND ".join(conds) if conds else ""))
        notes.append("Razlozi odbijanja: idk_kandidati_reject_reasons (1.832 zapisa, od 2022-04).")
    if spec.get("dokument_status") is not None:
        _cte(ctes, joins, "dok", "SELECT DISTINCT doc_candidate_id AS kid FROM idk_pp_documents WHERE doc_status IN ("
             + _codes(spec["dokument_status"], None, "dokument_status") + ")")
        notes.append("Dokumenti partner portala (idk_pp_documents, 2.418 dokumenata / 574 kandidata).")
    if spec.get("makler") is not None:
        m = spec["makler"]
        if m is True:
            where.append("IFNULL(k.kandidat_partnerid, 0) > 0")
        else:
            where.append(f"k.kandidat_partnerid IN ({_codes(m, None, 'makler')})")
        notes.append("Makler/partner (idk_jobstep_partners) preko kandidat_partnerid – popunjeno kod 2.009 kandidata.")
    if spec.get("pp_partner_id"):
        where.append(f"k.kandidat_ppa_partner_id IN ({_codes(spec['pp_partner_id'], None, 'pp_partner_id')})")
    if spec.get("tf_agent_id"):
        where.append(f"k.tf_reserved_agent IN ({_codes(spec['tf_agent_id'], None, 'tf_agent_id')})")
    if spec.get("tf_status") is not None:
        t = spec["tf_status"]
        where.append("k.kandidat_tf_status IS NOT NULL" if t is True else f"k.kandidat_tf_status IN ({_codes(t, None, 'tf_status')})")
        notes.append("Task-force status: samo aktivni taskovi (kandidat_tf_status, 1.704 kandidata).")
    if spec.get("vjestina"):
        kws = spec["vjestina"] if isinstance(spec["vjestina"], list) else [spec["vjestina"]]
        kw = " OR ".join(f"v.kv_naziv LIKE '%{esc_like(x)}%' OR v.kv_naziv_de LIKE '%{esc_like(x)}%'" for x in kws)
        _cte(ctes, joins, "vje", f"SELECT DISTINCT v.kv_kandidat_id AS kid FROM idk_kandidat_vjestine v WHERE {kw}")
        notes.append("Vještine: slobodan tekst (idk_kandidat_vjestine, 5.267 kandidata).")
    if spec.get("grad"):
        g = esc_like(spec["grad"])
        if len(g) < 3:
            raise SpecError("grad: min. 3 characters")
        where.append(f"k.kandidat_grad LIKE '%{g}%'")
        notes.append("Grad: slobodan tekst (popunjeno ~35 %).")
    if spec.get("aktivan"):
        conds = _date_range(spec["aktivan"], "lsp_datetime", "aktivan")
        if not conds:
            raise SpecError("aktivan needs od and/or do")
        _cte(ctes, joins, "akt", "SELECT DISTINCT lsp_kandidat_id AS kid FROM idk_log_statusi_prijave WHERE " + " AND ".join(conds))
        notes.append("Aktivnost = promjena statusa prijave u periodu (log od 2021-12).")
    if spec.get("status_historija"):
        c = spec["status_historija"]
        if not isinstance(c, dict) or not c.get("status"):
            raise SpecError("status_historija needs status: [codes]")
        conds = [f"l.lsp_status_prijave_id IN ({_codes(c['status'], STATUS_PRIJAVE, 'status_historija.status')})"]
        conds += _date_range({k: c[k] for k in ("od", "do") if k in c}, "l.lsp_datetime", "status_historija")
        if c.get("projekt_id"):
            conds.append(f"l.lsp_projekt_id IN ({int_list(c['projekt_id'])})")
        if c.get("nalog_id"):
            conds.append(f"l.lsp_projekt_id IN (SELECT project_id FROM idk_projects WHERE CAST(NULLIF(TRIM(project_nalogid),'') AS UNSIGNED) "
                         f"IN ({int_list(c['nalog_id'])}))")
        _cte(ctes, joins, "hist", "SELECT DISTINCT l.lsp_kandidat_id AS kid FROM idk_log_statusi_prijave l WHERE " + " AND ".join(conds))
        notes.append("Historija statusa: kandidat je bar jednom bio u statusu (idk_log_statusi_prijave, od 2021-12).")
    if spec.get("faza_min") is not None:
        f = spec["faza_min"]
        if isinstance(f, bool) or not isinstance(f, int) or not 1 <= f <= 15:
            raise SpecError("faza_min must be 1..15 (redoslijed_statusa)")
        joins.append("JOIN idk_kandidat_status_prijave spf ON spf.status_id = k.kandidat_status_prijave")
        where.append(f"spf.redoslijed_statusa >= {f}")
        notes.append(f"Faza: trenutni status s redoslijedom >= {f} (7 = Potpisan ugovor ili dalje).")
    if spec.get("ima_biljeske"):
        _cte(ctes, joins, "bil", "SELECT DISTINCT note_dataid AS kid FROM idk_notes WHERE note_group = 2")
        notes.append("Bilješke: idk_notes grupa 2 = kandidat (99,98 % pogodaka, izvedeno iz podataka).")
    if spec.get("ima_dokumente"):
        _cte(ctes, joins, "dkm", "SELECT document_dataid AS kid FROM idk_documents WHERE document_group = 2 "
             "UNION SELECT doc_candidate_id FROM idk_pp_documents")
        notes.append("Dokumenti: idk_documents grupa 2 (= kandidat, 99,97 %) ili partner portal.")
    if spec.get("firma_id"):
        ids = int_list(spec["firma_id"])
        _cte(ctes, joins, "frm", f"SELECT kandidat_id AS kid FROM idk_kandidati WHERE kandidat_zaposlen_kod IN ({ids}) "
             f"UNION SELECT pk.pk_kandidatid FROM idk_project_kandidati pk JOIN idk_projects p ON p.project_id = pk.pk_projectid "
             f"WHERE p.project_companyid IN ({ids})")
        notes.append("Firma: zaposlen kod firme (kandidat_zaposlen_kod) ili član projekta firme.")
    if spec.get("dipl"):
        d = spec["dipl"] if isinstance(spec["dipl"], dict) else {"povezan": True}
        if d.get("povezan") is not None:
            where.append("k.kandidat_dipl_id IS NOT NULL AND k.kandidat_dipl_id > 0" if d["povezan"]
                         else "IFNULL(k.kandidat_dipl_id, 0) = 0")
        if d.get("status") is not None:
            joins.append("JOIN idk_nd_kandidata nd ON nd.id_broj_nd_kandidata = k.kandidat_dipl_id")
            where.append(f"nd.status_nd_kandidata IN ({_codes(d['status'], None, 'dipl.status')})")
        notes.append("DIPL veza preko kandidat_dipl_id (ne kandidat_id – drugi ID prostor).")
    if spec.get("cv_de"):
        where.append("k.cv_de = 1")
    if spec.get("profil_de"):
        where.append("k.profile_de = 1")
    if spec.get("ugovor"):
        u = spec["ugovor"]
        if u not in ("potpisan", "postoji"):
            raise SpecError("ugovor must be potpisan|postoji")
        _cte(ctes, joins, "ugv", "SELECT DISTINCT kc_candidate_id AS kid FROM idk_kandidati_contracts WHERE kc_visibility_status <> 0"
             + (" AND kc_signed = 1" if u == "potpisan" else ""))
        notes.append("Ugovor: uploadovan ugovor (idk_kandidati_contracts, bez arhive)" + ("; kc_signed = 1." if u == "potpisan" else "."))
    if spec.get("pocetak_rada_potvrden"):
        where.append("k.kandidat_potvrden_pocetak_rada = 1")
    if spec.get("grupa_id"):
        where.append(f"k.kandidat_group IN ({_codes(spec['grupa_id'], None, 'grupa_id')})")
    if spec.get("glossa") is not None:
        where.append(f"k.kandidat_glossa IN ({_codes(spec['glossa'], GLOSSA, 'glossa')})")
    if spec.get("radno_iskustvo"):
        c = spec["radno_iskustvo"]
        if not isinstance(c, dict):
            raise SpecError("radno_iskustvo must be an object")
        mg = c.get("min_godina", 0)
        if isinstance(mg, bool) or not isinstance(mg, (int, float)) or not 0 <= mg <= 50:
            raise SpecError("radno_iskustvo.min_godina must be 0..50")
        conds, join_bm = ["r.kri_darum_od > '1900-01-01'"], ""
        occ = c.get("zanimanje")
        if occ:
            names = occ if isinstance(occ, list) else [occ]
            groups = set()
            for n in names:
                key = resolve_occupation(n, catalog)
                if not key:
                    raise SpecError(f"radno_iskustvo.zanimanje '{n}' not in catalogue; use filter_options zanimanje")
                groups.update(catalog[key]["berufsgruppen"])
            join_bm = " JOIN beruf_mapping bm ON bm.freitext_wert = r.kri_pozicija"
            conds.append(f"bm.berufsgruppe_id IN ({ident_list(sorted(groups))})")
        months = ("TIMESTAMPDIFF(MONTH, r.kri_darum_od, CASE WHEN r.kri_datum_do > '1900-01-01' THEN r.kri_datum_do "
                  "WHEN r.kri_aktuelno = 1 THEN CURDATE() END)")
        _cte(ctes, joins, "isk", f"SELECT r.kri_kandidat_id AS kid, SUM(GREATEST(IFNULL({months}, 0), 0)) AS mjeseci "
             f"FROM idk_kandidat_radno_iskustvo r{join_bm} WHERE {' AND '.join(conds)} GROUP BY r.kri_kandidat_id "
             f"HAVING mjeseci >= {int(round(mg * 12))}")
        notes.append(f"Radno iskustvo >= {mg} god. (zbir perioda iz CV-a; preklapanja se zbrajaju, bez kraja = 0 osim 'aktuelno')"
                     + (f", zanimanje {names}" if occ else "") + ".")


def build(spec):
    if not isinstance(spec, dict):
        raise SpecError("spec must be a JSON object")
    allowed = {"zanimanje", "vozacka", "jezici", "jezik", "obrazovanje", "iskustvo_u_struci", "drzava",
               "drzavljanstvo", "spol", "starost", "registriran", "status_prijave", "slobodni",
               "kandidat_status", "ukljuci_arhivu", "kontaktabilni", "nacin_odlaska", "nalog_id", "projekt_id",
               "nostrifikacija", "izlaz", "limit", "offset", "pii", "sortiraj",
               # added 2026-10-30 (filter catalogue, see references/filteri.md)
               "porijeklo", "messenger_status", "bracno_stanje", "viza", "termin_za_vizu", "casting", "intervju",
               "odbijen", "dokument_status", "makler", "pp_partner_id", "tf_agent_id", "tf_status", "vjestina", "grad",
               "aktivan", "status_historija", "faza_min", "ima_biljeske", "ima_dokumente", "firma_id", "dipl",
               "cv_de", "profil_de", "ugovor", "pocetak_rada_potvrden", "grupa_id", "radno_iskustvo", "glossa",
               "nalog_izvor"}
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
        if edu.get("skola_id"):
            conds.append(f"e.ke_skola_id IN ({int_list(edu['skola_id'])})")
        if edu.get("smjer_id"):
            conds.append(f"e.ke_smjer_id IN ({int_list(edu['smjer_id'])})")
        if not conds and not edu.get("smjer"):
            raise SpecError("obrazovanje needs vrsta, smjer, skola_id or smjer_id")
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
        dvs = spec["drzavljanstvo"] if isinstance(spec["drzavljanstvo"], list) else [spec["drzavljanstvo"]]
        ors = []
        for dv in dvs:
            dv = str(dv).upper()
            if dv in ("EU", "NON-EU"):
                ors.append("REPLACE(REPLACE(UPPER(TRIM(k.kandidat_drzavljanstvo_vrsta)),'-',''),' ','') "
                           + ("LIKE 'EUDR%'" if dv == "EU" else "LIKE 'NONEU%'"))
            elif dv in CITIZENSHIP_REGEX:
                ors.append(f"UPPER(TRIM(k.kandidat_drzavljanstvo)) REGEXP '{CITIZENSHIP_REGEX[dv]}'")
            else:
                raise SpecError(f"drzavljanstvo must be EU, NON-EU or one of {list(CITIZENSHIP_REGEX)}")
        where.append("(" + " OR ".join(ors) + ")")
        notes.append(f"Državljanstvo: {dvs} (EU/NON-EU iz kandidat_drzavljanstvo_vrsta ~44 %, država iz kandidat_drzavljanstvo ~14 %).")

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
        ids = int_list(spec["nalog_id"])
        izvor = spec.get("nalog_izvor", "kandidat")
        if izvor not in ("kandidat", "projekt", "oba"):
            raise SpecError("nalog_izvor must be kandidat|projekt|oba")
        if izvor == "kandidat":
            where.append(f"k.kandidat_nalog_id IN ({ids})")
        else:
            parts = [f"SELECT pk.pk_kandidatid AS kid FROM idk_project_kandidati pk JOIN idk_projects p ON p.project_id = pk.pk_projectid "
                     f"WHERE CAST(NULLIF(TRIM(p.project_nalogid),'') AS UNSIGNED) IN ({ids})"]
            if izvor == "oba":
                parts.append(f"SELECT kandidat_id FROM idk_kandidati WHERE kandidat_nalog_id IN ({ids})")
            ctes.append("nal AS (SELECT DISTINCT kid FROM (" + " UNION ".join(parts) + ") x)")
            joins.append("JOIN nal ON nal.kid = k.kandidat_id")
        notes.append("Nalog: " + {"kandidat": "trenutno dodijeljen (kandidat_nalog_id)",
                                  "projekt": "član projekta tog naloga (idk_projects.project_nalogid)",
                                  "oba": "dodijeljen ili član projekta naloga"}[izvor] + ".")
    if spec.get("projekt_id"):
        ctes.append(f"prj AS (SELECT DISTINCT pk_kandidatid AS kid FROM idk_project_kandidati WHERE pk_projectid IN ({int_list(spec['projekt_id'])}))")
        joins.append("JOIN prj ON prj.kid = k.kandidat_id")
    if spec.get("nostrifikacija"):
        nv = spec["nostrifikacija"]
        pr = "potpuno" if nv is True else (nv.get("priznanje", "potpuno") if isinstance(nv, dict) else nv)
        if pr not in NOSTR_PRIZNANJE:
            raise SpecError(f"nostrifikacija must be true or one of {list(NOSTR_PRIZNANJE)}")
        cond = f" WHERE full_recognition IN ({int_list(NOSTR_PRIZNANJE[pr])})" if NOSTR_PRIZNANJE[pr] else ""
        ctes.append(f"nostr AS (SELECT DISTINCT id_cand_job AS kid FROM idk_nostrifikovane_diplome{cond})")
        joins.append("JOIN nostr ON nostr.kid = k.kandidat_id")
        notes.append({"potpuno": "Diploma potpuno priznata (full_recognition = 1).",
                      "djelimicno": "Diploma djelimično priznata (full_recognition = 0).",
                      "status_2": "full_recognition = 2 (vrijednost nije dokumentovana; 388 zapisa).",
                      "bilo_koje": "Postoji uploadovano rješenje o nostrifikaciji (bilo koji ishod)."}[pr])

    extra_filters(spec, catalog, ctes, joins, where, notes)

    izlaz = spec.get("izlaz", "broj")
    if izlaz not in ("broj", "lista", "izvori", "id"):
        raise SpecError("izlaz must be broj|lista|izvori|id")
    limit = spec.get("limit", 200)
    if not isinstance(limit, int) or not 1 <= limit <= 5000:
        raise SpecError("limit must be 1..5000")
    offset = spec.get("offset", 0)
    if isinstance(offset, bool) or not isinstance(offset, int) or not 0 <= offset <= 1_000_000:
        raise SpecError("offset must be 0..1000000")
    page = f"LIMIT {limit}" + (f" OFFSET {offset}" if offset else "") + "\n"

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
        tail = "ORDER BY k.kandidat_id\n" + page
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
            tail = "ORDER BY occ.broj_izvora DESC, k.kandidat_datetime DESC, k.kandidat_id DESC\n" + page
        else:
            tail = "ORDER BY k.kandidat_datetime DESC, k.kandidat_id DESC\n" + page

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
