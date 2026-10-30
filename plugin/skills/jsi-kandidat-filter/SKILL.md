---
name: jsi-kandidat-filter
description: "Filter-based candidate search for the JSI recruiting CRM (MySQL 'Mysql JSI' via BlazeSQL), like the filter panel of a UI. Use whenever the user wants to FIND, COUNT or LIST candidates by criteria, e.g. 'alle Elektriker mit Führerschein C', 'električari sa C kategorijom i njemačkim B1', 'automehaničari iz BiH 20-45 godina, slobodni', 'how many CE drivers with German A2'. Converts the request into a JSON filter spec, builds a tested SQL query with scripts/build_query.py and runs it with BlazeSQL execute_sql – no manual search through the 190 tables."
---

# JSI Kandidat-Filter

Turns a natural-language candidate search into a deterministic, tested SQL query. The heavy lifting (which tables, which columns, synonyms, licence rules, data-quality workarounds, performance) lives in `scripts/build_query.py` and `scripts/occupations.json` – do not hand-write candidate search SQL.

## Workflow

1. **Parse the request into a filter spec** (JSON, keys below). Ask only if a criterion is genuinely ambiguous (e.g. "Elektriker" strict vs. broad incl. Elektrotechniker/Hilfselektriker – default strict).
2. **Build the SQL**:
   ```bash
   python3 -I <skill-dir>/scripts/build_query.py --notes --spec '<json>'
   ```
   `--notes` prints the interpretation (stderr) – show it to the user in Bosnian so they see exactly how the filter was applied.
3. **Run** the printed SQL with BlazeSQL `execute_sql` (single read-only statement). Typical runtime 5–20 s.
4. **Answer in Bosnian** (unless asked otherwise): count first, then breakdown/list, then the applied filter notes and data-coverage caveats (see `references/filteri.md`).
5. Default output is a **count**. Produce a list only when asked (`"izlaz": "lista"`). Names/phones/emails only with `"pii": true` **and** an explicit user request.

Recommended first answer for a search: run `"izlaz": "izvori"` (count per occupation source) – it shows how strong the evidence is (only applied as X vs. confirmed by qualification + work experience).

## Filter spec (all keys optional, combined with AND)

| Key | Example | Meaning |
|---|---|---|
| `zanimanje` | `"Elektriker"` · `["elektriker","elektrotehnicar"]` · `{"name":"elektriker","broad":true,"sources":["iskustvo","kvalifikacija"]}` · `{"keywords":["dimnjačar"]}` · `{"berufsgruppen":["schweisser"]}` | Occupation, matched across 6 sources: `prijava` (application text/PP position), `grupa` (application group), `iskustvo` (work experience), `kvalifikacija` (qualification text), `smjer` (school programme), `de_profil`. Synonyms bs/de/en resolve via `occupations.json`; unknown words fall back to keyword search. `broad` adds neighbouring occupations. |
| `vozacka` | `"C"` · `["C","CE"]` · `{"kategorije":["C"],"strict":true}` · `{"kategorije":["B","C1"],"mode":"all"}` · `true` | Driving licence. Default EU logic: a higher category satisfies the lower (C ⇐ C, CE; B ⇐ B…DE; C1 ⇐ C1, C1E, C, CE). `strict` = exact category only. `true` = any licence. |
| `jezik` / `jezici` | `{"jezik":"njemacki","min_nivo":"B1"}` · `{"jezik":"de","min_nivo":"A2","certifikat":true}` · `{"jezik":"engleski","min_nivo":"B2","vjestina":"bilo_koja"}` | Language min. CEFR level (self-assessment, skill `govorna_interakcija` by default). `certifikat: true` = uploaded certificate exists, `"vazeci"` = not expired. `jezici` = list for several languages. |
| `obrazovanje` | `{"vrsta":"srednje"}` · `{"smjer":"elektro"}` · `{"vrsta":"visoko","smjer":"mašin"}` | Education type (`srednje`/`visoko`/`ostalo`) and/or programme/qualification keyword. |
| `iskustvo_u_struci` | `true` · `{"min_godina":2}` | Self-declared work experience in profession (field filled for only 18 %). |
| `drzava` | `"BIH"` · `["BIH","SRB"]` | Country of residence (normalised free text): BIH, SRB, HRV, DEU, MNE, SVN, MKD, XKX, AUT. |
| `drzavljanstvo` | `"NON-EU"` · `"EU"` | Citizenship type. |
| `spol` | `"m"` · `"z"` | Gender (filled for only 13 %). |
| `starost` | `{"od":20,"do":45}` | Age in years (birth date filled for 60 %). |
| `registriran` | `{"od":"2024-01-01","do":"2025-01-01"}` | Registration date range (`kandidat_datetime`). |
| `slobodni` | `true` | Not reserved for an order (pipeline status NULL/0/1/2/5). |
| `status_prijave` | `[3,7,8,9]` | Exact pipeline status codes. |
| `kandidat_status` | `[1,2]` | Processing status codes. |
| `ukljuci_arhivu` | `true` | Include archived candidates (excluded by default). |
| `kontaktabilni` | `true` | Exclude wrong number / unavailable / no mobile. |
| `nacin_odlaska` | `[2]` | 0 skilled/EU, 2 Western Balkans regulation. |
| `nalog_id` / `projekt_id` | `[254]` | Assigned order / member of project. |
| `nostrifikacija` | `true` | Diploma fully recognised (`idk_nostrifikovane_diplome.full_recognition = 1`). |
| `izlaz` | `"broj"` (default) · `"izvori"` · `"lista"` · `"id"` | Output: count · count per occupation source · candidate list · IDs only. |
| `limit` | `200` | Rows for `lista`/`id` (max 5000). |
| `pii` | `true` | Add name, mobile, email to `lista` (only on explicit request). |
| `sortiraj` | `"relevantnost"` (default with occupation) · `"novi"` | List order. |

Status codes and occupation catalog: `references/filteri.md`. Full database documentation: `../jsi-data-analyst/references/schema/README.md`, wiring: `../jsi-data-analyst/references/veze.md`.

## Examples

| User says | Spec |
|---|---|
| „Alle Elektriker mit Führerschein C“ | `{"zanimanje":"Elektriker","vozacka":"C","izlaz":"izvori"}` → 2,676 (2026-10-29) |
| „Električari sa C, njemački min. A2, kontaktabilni – lista“ | `{"zanimanje":"električar","vozacka":"C","jezik":{"jezik":"njemacki","min_nivo":"A2"},"kontaktabilni":true,"izlaz":"lista","limit":50}` |
| „Automehaničari iz BiH ili Srbije, 20–45, slobodni, srednja škola“ | `{"zanimanje":"automehaničar","drzava":["BIH","SRB"],"starost":{"od":20,"do":45},"slobodni":true,"obrazovanje":{"vrsta":"srednje"}}` |
| „Wie viele CE-Fahrer mit Deutsch-Zertifikat?“ | `{"vozacka":{"kategorije":["CE"],"strict":true},"jezik":{"jezik":"de","min_nivo":"A1","certifikat":true}}` |
| „Svi iz elektro struke, široko“ | `{"zanimanje":{"name":"elektriker","broad":true},"izlaz":"izvori"}` |

## Rules

- Never hand-edit the generated SQL to add personal or credential columns. If a filter is missing, extend `build_query.py` (+ a test in `scripts/test_build_query.py`) instead of ad-hoc SQL.
- Always state the data end date: candidate activity largely ends Feb 2026 (see `jsi-data-analyst`).
- State coverage caveats when a filter uses a sparsely filled field (gender, experience flag, country, certificate).
- Language levels are self-assessed unless `certifikat` is set.
- After changing the scripts: `python3 -I -m unittest discover -s scripts -p 'test_*.py'`.
