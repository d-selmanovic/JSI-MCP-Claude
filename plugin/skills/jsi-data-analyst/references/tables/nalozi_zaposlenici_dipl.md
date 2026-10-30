# Orders, staff, JobStep partners, DIPL, pipeline history

Code meanings: `../entities.md`. All columns: `../schema/05_nalozi_projekti_firme.md`, `../schema/08_dipl_nostrifikacija.md`, `../schema/10_interno_admin.md`, `../schema/07_jobstep_partneri_makleri.md`. Wiring: `../veze.md`.

## Orders (`idk_nalozi`, 239) – demand vs. placement (tested 2026-10-29)
```sql
SELECT n.nalog_id, n.nalog_naziv, c.company_name, n.nalog_status, n.nalog_potrebno_kandidata,
       COUNT(DISTINCT k.kandidat_id) AS kandidata_na_nalogu,
       SUM(sp.redoslijed_statusa >= 7) AS potpisano_ili_dalje
FROM idk_nalozi n
JOIN idk_companies c ON c.company_id = n.kompanija_id
LEFT JOIN idk_kandidati k ON k.kandidat_nalog_id = n.nalog_id AND k.kandidat_status <> 3
LEFT JOIN idk_kandidat_status_prijave sp ON sp.status_id = k.kandidat_status_prijave
GROUP BY n.nalog_id, n.nalog_naziv, c.company_name, n.nalog_status, n.nalog_potrebno_kandidata
ORDER BY potpisano_ili_dalje DESC;
```
Largest orders: 254 Enpal „Photovoltaik Monteur“ (300 needed, 900 candidates, 165 signed+), 272 CARGLASS (100 / 94 / 93), 222 NKG Fiberservice, 211 & 262 Solutions 30. Most large orders have `nalog_status = 10` (meaning undocumented – ask).

## Staff (`idk_employees`) – names for reports (tested)
```sql
SELECT CONCAT(e.employee_firstname, ' ', LEFT(e.employee_lastname, 1), '.') AS agent,
       t.skraceni_naziv_t AS tim, COUNT(*) AS taskova
FROM idk_task_force tf
JOIN idk_employees e ON e.employee_id = tf.tf_agent_id
LEFT JOIN idk_timovi t ON t.id_t = e.employee_team
WHERE tf.tf_doe >= '2025-01-01' AND tf.tf_doe < '2026-01-01'
GROUP BY e.employee_id, e.employee_firstname, e.employee_lastname, t.skraceni_naziv_t
ORDER BY taskova DESC;
```
Only ever select name/team/branch/position columns from `idk_employees` (see `../schema/osjetljive_kolone.md`).

## DIPL funnel per year (tested)
```sql
SELECT YEAR(d.vrijeme_kreiranja_nd_kandidata) AS godina,
       COUNT(*) AS novih_dipl,
       SUM(d.status_nd_kandidata = 6) AS zavrseno,
       SUM(d.status_nd_kandidata = 7) AS arhivirano,
       COUNT(DISTINCT p.pr_kandidat_id) AS sa_uplacenim_predracunom
FROM idk_nd_kandidata d
LEFT JOIN idk_predracuni p ON p.pr_kandidat_id = d.id_broj_nd_kandidata
     AND p.pr_status = 2 AND IFNULL(p.pr_stornirano, 0) = 0
GROUP BY godina ORDER BY godina;
```
Reference: 2021 41.6k new DIPL leads / 1,895 finished / 840 paying; 2022 23.4k / 1,779 / 847; 2023 10.5k / 1,234 / 627; 2024 830 / 108 / 81; 2025 65 / 0 / 0. The DIPL business effectively stopped in 2024.

Call/appointment activity: `idk_nd_termini` (451k), notes `idk_nd_kandidata_biljeske` (929k), status history `idk_nd_kandidata_status_log` (408k), manager assignment history `idk_nd_menadzeri_statistike` (261k), re-applications `idk_ponovne_prijave` (12.8k).

## Placements per year (pipeline history, tested)
```sql
WITH prvi_potpis AS (
  SELECT lsp_kandidat_id, MIN(lsp_datetime) AS datum_potpisa
  FROM idk_log_statusi_prijave WHERE lsp_status_prijave_id = 9
  GROUP BY lsp_kandidat_id)
SELECT YEAR(datum_potpisa) AS godina, COUNT(*) AS potpisanih_ugovora
FROM prvi_potpis GROUP BY godina ORDER BY godina;
```
2022 299 · 2023 536 · 2024 71 · 2025 24 · 2026 1.

## JobStep partners (makleri) – `idk_jobstep_partners` (34k)
Recommenders/brokers using the partner app. Candidates linked via `idk_kandidati.kandidat_partnerid` (2,009) / `zaduzeni_makler_id` (6); orders via `nalog_js_partner_id` (3); companies via `js_partner_id` (41). Payouts in `idk_partner_uplate` (147). **Never** select `jp_password`, `jp_*token*`, `jp_iban`, `jp_swift`, `jp_socialid`.
