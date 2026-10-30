# Finance, Clients, Companies, Partners

Revenue across all sources (employer installments `idk_kandidat_financije`, `idk_nalog_financije`, DIPL proformas `idk_predracuni`), receivables and commissions (`idk_obracuni`): see `../metrics.md` → *Prihodi* / *Provizije*. `idk_racuni`/`idk_predracuni` use the **DIPL id** (`idk_nd_kandidata.id_broj_nd_kandidata`).

## Key Tables

### idk_racuni (invoices to candidates)
**PK**: `racun_id` · **Rows**: 4,509 (2020-12 → 2024-10)

| Column | Notes |
|---|---|
| racun_datum_kreiranja | invoice date |
| racun_vrijednost_EUR / _BAM / _RSD | **same amount in 3 currencies — never add them up** |
| racun_domaca_valuta | candidate's home currency |
| racun_stornirano, racun_datum_storniranja, racun_razlog_storniranja | cancellations (4 rows) — exclude `racun_stornirano = 1` from revenue |
| racun_uplaceno, racun_datum_uplate | **not maintained** (always 0 / NULL) — no payment analysis possible |
| racun_vrsta_racuna | 0 (almost all), 1 DIPL (1 row) |

Yearly EUR totals: 2021 208.6k · 2022 274.2k · 2023 236.4k · 2024 46.5k (until Oct).

```sql
SELECT YEAR(racun_datum_kreiranja) AS godina,
       COUNT(*) AS racuna,
       ROUND(SUM(racun_vrijednost_EUR), 2) AS iznos_eur
FROM idk_racuni
WHERE IFNULL(racun_stornirano, 0) = 0
GROUP BY godina
ORDER BY godina;
```

### idk_clients (sales CRM) — 387 rows
`client_sales_status` 0 lead / 1 in progress / 2 čeka ugovor / 3 aktivan / 4 arhiviran; `client_fc_status` 0 lead / 1 in progress / 2 aktivan / 3 arhiviran; `client_fc_or_sales` 0 FC / 1 sales; `client_manager`, `client_sales_manager` = employee ids. History: `idk_clients_stats` (status changes, `fc_or_sales`), call planning: `idk_sales_reminders` (sr_status 1 active / 2 finished).

### idk_companies — 1,223 rows
Employer master data. `company_status` mostly 1; `company_origin` 0 normal / 1 dipl / 2 dak / 5 partner app; `company_total_workers_required`; `company_professions` = array of profession ids (→ idk_struke). Contacts: `idk_contacts` (contact_companyid), extra info: `idk_companies_info`.

### idk_pp_partners — 58 rows
Partner participation per nalog: `ppa_company_id`, `ppa_nalog_id`, `ppa_number_of_candidates` (needed), `ppa_status` 0/1.

Demand vs. placed per partner:
```sql
SELECT p.ppa_id, c.company_name, p.ppa_number_of_candidates AS potrebno,
       SUM(sp.redoslijed_statusa >= 7) AS plasirano
FROM idk_pp_partners p
JOIN idk_companies c ON c.company_id = p.ppa_company_id
LEFT JOIN idk_kandidati k ON k.kandidat_ppa_partner_id = p.ppa_id AND k.kandidat_status <> 3
LEFT JOIN idk_kandidat_status_prijave sp ON sp.status_id = k.kandidat_status_prijave
WHERE p.ppa_status = 1
GROUP BY p.ppa_id, c.company_name, p.ppa_number_of_candidates
ORDER BY potrebno DESC;
```

### idk_projects — 2,740 rows
Internal projects: `project_companyid`, `project_pmanagerid`, `project_status` (1 = 2,728 rows, 0 = 12), `project_datumtermina` (appointment date). Tasks: `idk_projects_tasks`.

## Technical / audit tables (normally not for business analysis)
`rb_*` (event sourcing / approvals for automated changes), `mcp_aenderung` (change log of automated tool edits with before/after), `mcp_fehler` (tool error log), `mcp_status_info` (DE/HR descriptions of document statuses), `idk_settings`, `idk_ipwhitelist`, `idk_api_clients` (contains tokens — never select `client_token`).
