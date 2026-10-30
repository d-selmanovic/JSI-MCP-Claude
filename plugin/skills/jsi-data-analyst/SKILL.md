---
name: jsi-data-analyst
description: "JSI data analysis skill for the recruiting CRM (MySQL database \"Mysql JSI\", schema jsicrm, queried via BlazeSQL). Provides entity definitions, status code meanings, metric formulas, standard filters and tested query patterns. Use when analyzing JSI data for: (1) new candidate registrations and acquisition channels, (2) task force / call-center agent performance, (3) document and visa processing, (4) placements (signed contracts), or any question about kandidati, nalozi, partneri, projekti, castings or racuni."
---

# JSI Data Analysis

JSI (JobStep group — invoicing entities Jobstep GmbH (DE) and Jobstep Int GmbH (CH); teams in `idk_timovi`: JobStep Main, GoCloud, WE Connect, SSC d.o.o., Team JSI, NTH Beograd; branches in `idk_poslovnice`) runs a recruiting/placement business: candidates from the Western Balkans (BiH, Serbia, …) are recruited, qualified (German language courses, diploma recognition / nostrifikacija), matched to German employers (partners / nalozi), and taken through contract, visa and start of work. The CRM schema is `jsicrm` (190 tables). A second business line is **DIPL** — diploma recognition (nostrifikacija) sold to candidates (`idk_nd_*`, `idk_predracuni`).

**How to query – first choice: JSI MCP server** (`jsi`, `https://calm-steel-onjlq.run.mcp-use.com/mcp`) if its tools are available: `kpis` (vermittlungen, neue_kandidaten, pipeline_bestand, umsatz, task_force, casting, dipl_funnel), `orders_overview`, `pipeline_history`, `search_candidates`, `candidate_profile`, `filter_options`, `change_log`, `whoami`. They apply the metric definitions below, permissions and the [TAJNO] rules server-side. Write tools (`record_preview`, `record_write`, `set_application_status`) only on explicit request, always `dry_run` first.

**Fallback / free analysis**: BlazeSQL tools — `list_tables` / `describe_tables` for schema, `execute_sql` for read-only SQL, `graph_sql_result` for charts. Full column comments are available via `describe_tables` (many are in Bosnian and contain the code meanings).

**Report language**: Bosnian, unless the user asks otherwise. Keep table/column names as-is.

---

## SQL Dialect: MySQL

- Server runs with `ONLY_FULL_GROUP_BY` → every non-aggregated SELECT column must be in `GROUP BY` (grouping by a SELECT alias works).
- Table references: plain names (`idk_kandidati`) or backticks; reserved column names need backticks (e.g. `` `date` `` in `idk_clients_stats`).
- Safe division: `a / NULLIF(b, 0)`.
- Dates: `DATE_FORMAT(col, '%Y-%m')` for monthly grain, `DATE_SUB(col, INTERVAL 1 DAY)`, `DATEDIFF(end, start)`, `TIMESTAMPDIFF(DAY, a, b)`.
- No `EXCEPT` / `QUALIFY`; CTEs (`WITH`) and window functions are supported.
- Boolean expressions return 0/1 → `SUM(cond)` counts matches.
- JSON columns (`rb_*`, `idk_chat_question`): `col->>'$.field'`.

---

## Entity Disambiguation

**"Kandidat" / candidate** — a person in the CRM (`idk_kandidati.kandidat_id`). ~122k rows, most are old/inactive leads. Always clarify: all registered, active, or in a specific pipeline stage?

**"Nalog"** — an employer job order / service contract (`idk_nalozi`, 239 rows): `nalog_naziv`, `kompanija_id → idk_companies`, `nalog_potrebno_kandidata`, commission terms (`nalog_provizija`, `nalog_provizija_po_plati`, `nalog_provizija_nostrifikacija`, `nalog_provizija_akademija`), installment plan (`idk_nalozi_rate`), `nalog_firma_fakturisanja` (1 Jobstep GmbH DE, 2 Jobstep Int GmbH CH). `nalog_status` codes (1,3–8,10–12) are **undocumented** — history in `idk_nalozi_log`.

**"Partner" / "poslodavac"** — German employer using the Partner Portal (PP). Two levels:
- `idk_pp_partners` (`ppa_id`): partner participation per nalog (company + nalog + required candidate count).
- `idk_companies` (`company_id`): the company master record. `ppa_company_id → company_id`.
- Partner-portal logins: `idk_pp_users` (`pu_id`), access per partner/nalog: `idk_pp_user_access`.

**"Klijent"** — sales CRM record (`idk_clients`, 387 rows) with FC/sales pipeline status. Not the same as a company in `idk_companies`.

**"Projekt"** — internal recruiting project (`idk_projects`), candidates linked via `idk_project_kandidati` (pk_kandidatid, pk_projectid).

**"Agent" / "zaposlenik" / "employee"** — CRM staff in `idk_employees` (370 rows, PK `employee_id`). Join any `*_employee_id` / `tf_agent_id` / `*_zaposlenik*` column to get `employee_firstname`, `employee_lastname`, `employee_team` (→ `idk_timovi.id_t`), `employee_poslovnica` (→ `idk_poslovnice.branch_id`), `employee_position`. **Select only these columns** — the table also holds credentials (see Standard Filters). `employee_status` is a comma list with undocumented codes (360 × "0").

**"Partner" (JobStep partner / makler)** — not the same as an employer partner! `idk_jobstep_partners` (34k app users: brokers/recommenders who bring candidates, `jp_position` 1 junior, 2 partner, 3 senior, 4 agency, 5 lilium super; `jp_user_permission` 1 makler, 2 supervizor). Their payouts: `idk_partner_uplate`. Always clarify: employer partner (`idk_pp_partners`) or JobStep partner (`idk_jobstep_partners`)?

**"DIPL kandidat"** — record in the diploma-recognition funnel `idk_nd_kandidata` (~81k), linked via `idk_kandidati.kandidat_dipl_id = idk_nd_kandidata.id_broj_nd_kandidata`.

**"Status"** — candidates have *two* independent status fields:
- `kandidat_status` → processing/profile status (`idk_kandidat_status`): 0 Na provjeri, 1 U obradi, 2 Obrađen, **3 Arhiviran**, 4 Kontrola, 5 Dopuna, 6 Odbio Messenger, 7 U obradi > 3 dana, 8 Na dopuni > 3 dana.
- `kandidat_status_prijave` → placement pipeline status (`idk_kandidat_status_prijave`, ordered by `redoslijed_statusa`). See `references/entities.md`.

---

## Standard Filters

```sql
-- Default for all candidate analyses: exclude archived candidates
WHERE k.kandidat_status <> 3
```

**When to override**: if the user explicitly asks for "all candidates incl. archived" or for historical totals.

Other hygiene (apply where relevant, mention in caveats):
- 3 candidates have `kandidat_datetime` = 1970-01-01 → exclude with `kandidat_datetime >= '2000-01-01'` in time series.
- `idk_task_force.tf_agent_id IS NULL` = task created by cron/system (5.5k rows) → exclude from agent performance.
- Never output personal data (names, JMBG, passport, phone, email, address, IBAN) unless explicitly required. Employee first/last names are OK for performance reports.
- **Never select credential or banking columns** — not even in `SELECT *`. Always list columns explicitly on these tables:
  - `idk_employees`: `employee_password`, `employee_vicipass`, `employee_viciuser`, `employee_reset_token`, `employee_key`, `employee_rfid`, `employee_jmbg`
  - `idk_jobstep_partners`: `jp_password`, `jp_password_reset_code`, `jp_social_token`, `jp_fcmtoken`, `jp_mailconfirmation_token`, `jp_iban`, `jp_swift`
  - `idk_kandidati.kandidat_password`, `idk_pp_users.pu_password` / `pu_key`, `users.password` / `users.token`, `idk_api_clients.client_token`, `idk_nd_ugovori.ug_token`

---

## Key Metrics (summary — details in `references/metrics.md`)

| Metric | Definition |
|---|---|
| **Novi kandidati** | Candidates by `kandidat_datetime` per period, split by `kandidat_porijeklo` (channel) |
| **Vermittelt / placed (stock)** | Current `kandidat_status_prijave` at or beyond **Potpisan ugovor** (`redoslijed_statusa >= 7`) |
| **Vermittelt per period (flow)** | First time a candidate reached status 9 in `idk_log_statusi_prijave` (2022: 299 · 2023: 536 · 2024: 71 · 2025: 24) |
| **Prihodi (revenue)** | Paid employer invoices (`idk_kandidat_financije`, `idk_nalog_financije`, `*_placeno = 3`) + paid DIPL proformas (`idk_predracuni.pr_status = 2`) |
| **TF produktivnost** | Task-force tasks per agent per period; share with positive status (`tfs_is_positive = 1`) |
| **Casting odziv** | `idk_tf_stats_reservations.tsr_status`: 1 Došao / 2 Nije došao / 3 Odustao |
| **Dokumenti — vrijeme obrade** | `idk_pp_documents_status_logs.dsl_days_count` per status (non-terminal statuses only) |
| **Vize — dopune/odbijenice** | `idk_pp_visa_incomplete` by `vi_type` (1 Dopuna, 2 Odbijenica) |

---

## Data Freshness (checked 2026-10-29)

| Table | Rows | Latest record |
|---|---|---|
| idk_kandidati | 122,006 | 2026-10-24 (but only ~20/month since 2025-12; before ~100–135/month) |
| idk_task_force | 452,568 | 2026-02-25 |
| idk_agenti_activity | 7,848 | 2026-02-23 |
| idk_pp_documents_status_logs | 14,602 | 2025-11-20 |
| idk_candidate_verified_languages | 3,897 | 2025-11-07 |
| idk_log_statusi_prijave | 361,201 | 2026-02-25 |
| idk_nd_kandidata_status_log | 407,806 | 2026-02-16 |
| idk_racuni | 4,509 | 2024-10-24 |
| idk_predracuni | 10,701 | 2024-11-13 |
| idk_kandidat_financije / idk_nalog_financije | 1,067 / 126 | 2025-02 / 2024-07 |
| idk_obracuni (commissions) | 168,233 | 2024-08-16 |
| idk_pp_visa_incomplete | 49 | 2024-08-06 |
| idk_clients_stats | 858 | 2024-08-14 |

Activity largely stops in early 2026. **Always state the data's end date** in reports and don't present "last 30 days" as current activity without checking `MAX(date)` first:

```sql
SELECT MAX(tf_doe) FROM idk_task_force;
```

---

## Knowledge Base Navigation

| Domain | Reference File | Use For |
|---|---|---|
| Entities & status codes | `references/entities.md` | All lookup values, pipeline order, code meanings |
| Metrics | `references/metrics.md` | Exact formulas and caveats |
| Candidates | `references/tables/kandidati.md` | idk_kandidati + profile sub-tables, channels |
| Task force | `references/tables/task_force.md` | Calls, castings, agents, reservations |
| Documents & visa | `references/tables/dokumenti_vize.md` | Required docs, document status flow, visa dopune, languages, nostrifikacija |
| **All 190 tables + 1,809 columns** | `references/schema/README.md` (+ one file per domain, `osjetljive_kolone.md`) | Complete data dictionary with row counts, periods, PKs, column comments, [TAJNO]/[PII] flags |
| **Wiring** | `references/veze.md` | 76 measured relationships, two candidate ID spaces, polymorphic links, indexes |
| **Candidate search** | skill `jsi-kandidat-filter` | Filter-based search (occupation, licence, language, …) – use it instead of hand-written candidate SQL |
| Finance & sales | `references/tables/finansije_klijenti.md` | Revenue (employer invoices, DIPL proformas), commissions, clients, companies, partners |
| Orders, staff, DIPL | `references/tables/nalozi_zaposlenici_dipl.md` | idk_nalozi, idk_employees, JobStep partners, diploma-recognition funnel, pipeline history |

---

## Common Query Patterns

### New candidates per month and channel
```sql
SELECT DATE_FORMAT(kandidat_datetime, '%Y-%m') AS mjesec,
       kandidat_porijeklo,
       COUNT(*) AS novih
FROM idk_kandidati
WHERE kandidat_datetime >= '2025-01-01'
  AND kandidat_status <> 3
GROUP BY mjesec, kandidat_porijeklo
ORDER BY mjesec, novih DESC;
```

### Task force performance per agent
```sql
SELECT t.tf_agent_id,
       COUNT(*) AS taskova,
       SUM(s.tfs_is_positive = 1) AS pozitivnih,
       ROUND(100 * SUM(s.tfs_is_positive = 1) / NULLIF(COUNT(*), 0), 1) AS pct_pozitivnih
FROM idk_task_force t
LEFT JOIN idk_tf_statusi s ON s.tfs_id = t.tf_status_id
WHERE t.tf_doe >= '2025-01-01' AND t.tf_doe < '2026-01-01'
  AND t.tf_agent_id IS NOT NULL
GROUP BY t.tf_agent_id
ORDER BY taskova DESC;
```

### Placements per year (from pipeline history)
```sql
WITH prvi_potpis AS (
  SELECT lsp_kandidat_id, MIN(lsp_datetime) AS datum_potpisa
  FROM idk_log_statusi_prijave
  WHERE lsp_status_prijave_id = 9
  GROUP BY lsp_kandidat_id
)
SELECT YEAR(datum_potpisa) AS godina, COUNT(*) AS potpisanih_ugovora
FROM prvi_potpis
GROUP BY godina
ORDER BY godina;
```

### Placed candidates (signed contract or later)
```sql
SELECT sp.status_naziv, COUNT(*) AS kandidata
FROM idk_kandidati k
JOIN idk_kandidat_status_prijave sp ON sp.status_id = k.kandidat_status_prijave
WHERE sp.redoslijed_statusa >= 7
  AND k.kandidat_status <> 3
GROUP BY sp.status_id, sp.status_naziv, sp.redoslijed_statusa
ORDER BY sp.redoslijed_statusa;
```

---

## Troubleshooting

### Common Mistakes
- **Mixing the two candidate status fields** → `kandidat_status` = profile processing, `kandidat_status_prijave` = placement pipeline.
- **Summing invoice currencies** → `racun_vrijednost_EUR/BAM/RSD` are the *same* invoice in three currencies (BAM ≈ EUR × 1.95583). Pick one currency.
- **Using `racun_uplaceno` / `racun_datum_uplate` as payment data** → always 0 / NULL; payment status is not tracked here.
- **Measuring agent working time** → `idk_agenti_activity` has no usable durations (start = end); only count events.
- **Treating `kandidat_status = 6` (Odbio Messenger, ~61 %) as "rejected by employer"** → it means the candidate never installed the JobStep messenger; they are mostly dormant leads.
- **Using the current status for time trends** → `kandidat_status_prijave` is current state only. For "when" questions use the history logs: `idk_log_statusi_prijave` (pipeline, with `lsp_broj_dana` = days in status), `idk_log_kandidat_statusi` (processing status), `idk_nd_kandidata_status_log` (DIPL), `idk_pp_documents_status_logs`, `idk_candidate_language_logs`, `idk_nalozi_log`.
- **Confusing `idk_racuni` with `idk_predracuni`** → predračuni are DIPL proformas (with real payment status `pr_status = 2` / `pr_uplaceno`); računi are the final invoices issued afterwards. Don't add both — that double counts.
- **`datum_aplikacije`** is NULL for 97 % of candidates → use `kandidat_datetime` as registration date.
- **Undocumented codes**: `kandidat_porijeklo` 6/7/8 and `kandidat_nacin_odlaska` 3 exist in data but have no documented meaning → report them as "nepoznato (kod X)" and ask the user.

### Access
- Since 2026-10-29 all 190 tables are visible in BlazeSQL (previously 99). `kandidat_group → idk_kandidati_grupe.kg_id` (kg_title = occupation group, e.g. 68 Monter solarnih panela, 22 Automehaničar; 7 "Ostalo" = 75k).

### Performance Tips
- `idk_task_force` (450k rows) and `idk_kandidati` (122k): always filter by date (`tf_doe`, `kandidat_datetime`) first.
- Use `LIMIT` while exploring.
