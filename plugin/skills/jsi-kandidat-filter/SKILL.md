---
name: jsi-kandidat-filter
description: "Filter-based candidate search for the JSI recruiting CRM (via the JSI MCP server), like the filter panel of a UI. Use whenever the user wants to FIND, COUNT or LIST candidates by criteria, e.g. 'alle Elektriker mit Führerschein C', 'električari sa C kategorijom i njemačkim B1', 'automehaničari iz BiH 20-45 godina, slobodni', 'how many CE drivers with German A2'. Converts the request into a JSON filter spec and calls the JSI MCP tool search_candidates (server 'jsi'); without the MCP tools there is no data access (ask the user to sign in) – no manual search through the 190 tables."
---

# JSI Kandidat-Filter

Turns a natural-language candidate search into a filter spec for the MCP tool `search_candidates` (server `jsi`). The search logic (tables, synonyms, licence rules, data-quality workarounds, performance) runs **only on the server** – there is no local script and no SQL access.

## Workflow

1. **Parse the request into a filter spec** (keys below). Ask only if a criterion is genuinely ambiguous (e.g. "Elektriker" strict vs. broad incl. Elektrotehniker/Hilfselektriker – default strict). Valid codes and the occupation catalogue: `filter_options` (`section='katalog'` for the full catalogue).
2. **Call `search_candidates`** with the keys as arguments. First answer for a search: `"izlaz": "izvori"` (count per occupation source) – it shows how strong the evidence is. To show the generated SQL for review: `include_sql=true`.
3. **Answer in Bosnian** (unless asked otherwise): count first, then breakdown/list, then the filter notes and data-coverage caveats the tool returns (`napomene`; background in `references/filteri.md`).
4. Default output is a **count**. Lists only when asked (`"izlaz": "lista"`); they come in pages – state `stranica.pregled` ("Prikazano X–Y od N") and offer the next page via `offset`. Names/phones/emails only with `"pii": true` **and** an explicit user request (permission `jsi:kandidati:pii`).

If the `jsi` tools are missing, the user must sign in once (skill `jsi-mcp`). The free-text place-of-residence filter (`grad`) is not available over MCP; filter by country with `drzava`.

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

**Added 2026-10-30 (29 keys, full table with sources/fill rates/pitfalls in `references/filteri.md`, machine-readable via `filter_options(section='katalog')`):**
`porijeklo` (channel), `messenger_status`, `bracno_stanje`, `viza` (ima|nema|dobio|odbijena|dopuna), `termin_za_vizu`, `casting` {status,nalog_id,od,do}, `intervju` {preporuka hire|reject|not_sure}, `odbijen` {razlog_id, odbio kandidat|poslodavac}, `dokument_status`, `makler`, `pp_partner_id`, `tf_agent_id`, `tf_status`, `vjestina`, `grad`, `aktivan` {od,do}, `status_historija` {status,od,do,nalog_id,projekt_id}, `faza_min` (7 = contract signed or later), `ima_biljeske`, `ima_dokumente`, `firma_id`, `dipl` {povezan,status}, `cv_de`, `profil_de`, `ugovor` (postoji|potpisan), `pocetak_rada_potvrden`, `grupa_id`, `radno_iskustvo` {min_godina, zanimanje}, `glossa`, `nalog_izvor` (kandidat|projekt|oba). Extended: `drzavljanstvo` by country (BIH, SRB …), `nostrifikacija` (potpuno|djelimicno|status_2|bilo_koje), `obrazovanje.skola_id/smjer_id`, languages es/fr/ru/ar/tr, all 194 `berufsgruppe_id` as `zanimanje`.

Status codes and occupation catalog: `references/filteri.md`. Full database documentation: `../jsi-data-analyst/references/schema/README.md`, wiring: `../jsi-data-analyst/references/veze.md`.

## Examples

| User says | Spec |
|---|---|
| „Alle Elektriker mit Führerschein C“ | `{"zanimanje":"Elektriker","vozacka":"C","izlaz":"izvori"}` → 2,676 (2026-10-29) |
| „Električari sa C, njemački min. A2, kontaktabilni – lista“ | `{"zanimanje":"električar","vozacka":"C","jezik":{"jezik":"njemacki","min_nivo":"A2"},"kontaktabilni":true,"izlaz":"lista","limit":50}` |
| „Automehaničari iz BiH ili Srbije, 20–45, slobodni, srednja škola“ | `{"zanimanje":"automehaničar","drzava":["BIH","SRB"],"starost":{"od":20,"do":45},"slobodni":true,"obrazovanje":{"vrsta":"srednje"}}` |
| „Wie viele CE-Fahrer mit Deutsch-Zertifikat?“ | `{"vozacka":{"kategorije":["CE"],"strict":true},"jezik":{"jezik":"de","min_nivo":"A1","certifikat":true}}` |
| „Svi iz elektro struke, široko“ | `{"zanimanje":{"name":"elektriker","broad":true},"izlaz":"izvori"}` |
| „Elektriker, Deutsch A2, Führerschein B“ | `{"zanimanje":"Elektriker","jezik":{"jezik":"de","min_nivo":"A2"},"vozacka":"B"}` → 3,199 (2026-10-30) |
| „Schweißer aus BiH 25–45, frei, C/CE“ | `{"zanimanje":"Schweißer","drzava":"BIH","starost":{"od":25,"do":45},"slobodni":true,"vozacka":["C","CE"]}` → 45 |
| „Pflegekräfte mit DE-Zertifikat B1, Nostrifikation abgeschlossen“ | `{"zanimanje":["krankenpfleger","pflegehelfer"],"jezik":{"jezik":"de","min_nivo":"B1","certifikat":true},"nostrifikacija":true}` → 0 (no nurse has a certificate) |
| „Kandidaten im Auftrag 254 mit Status Vertrag unterschrieben“ | `{"nalog_id":[254],"status_prijave":[9]}` → 15 · or `"faza_min":7` → 165 · ever: `{"status_historija":{"status":[9],"nalog_id":[254]}}` → 276 |

## Rules

- If a filter is missing, it is added on the server (`server/src/jsi_mcp/build_query.py` + test in `server/tests/`, catalogue via `server/scripts/filter_catalog.py`) – never ad-hoc SQL.
- Always state the data end date: candidate activity largely ends Feb 2026 (see `jsi-data-analyst`).
- State coverage caveats when a filter uses a sparsely filled field (gender, experience flag, country, certificate).
- Language levels are self-assessed unless `certifikat` is set.
- After changing the scripts: `python3 -I -m unittest discover -s scripts -p 'test_*.py'`.
