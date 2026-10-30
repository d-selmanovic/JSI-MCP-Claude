# Metrics (JSI)

All candidate metrics exclude archived candidates (`kandidat_status <> 3`) unless the user asks otherwise.

## Novi kandidati (new candidates)
- **Definition**: candidates registered in the period.
- **Formula**: `COUNT(*)` grouped by `DATE_FORMAT(kandidat_datetime, '%Y-%m')`, optionally by `kandidat_porijeklo`.
- **Source**: `idk_kandidati.kandidat_datetime`
- **Caveats**: `datum_aplikacije` is mostly NULL — don't use it. Exclude `kandidat_datetime < '2000-01-01'` (3 epoch rows). Volume drops sharply after 2025-11 (≈130/month → ≈20/month); confirm with the user whether this is real or a data-sync issue before interpreting it as a trend.

## Vermittelt / plasirani kandidati (placements) — agreed definition
- **Definition**: candidate whose current pipeline status is **Potpisan ugovor or any later stage**.
- **Formula**:
  ```sql
  COUNT(*) FROM idk_kandidati k
  JOIN idk_kandidat_status_prijave sp ON sp.status_id = k.kandidat_status_prijave
  WHERE sp.redoslijed_statusa >= 7 AND k.kandidat_status <> 3
  ```
  Current value (2026-10-29): **854** (incl. 660 Završen, 104 Početak rada).
- **Caveats**: current state only — no timestamp of when the contract was signed. For "placements per month" use `kandidat_datum_ugovora` (contract date) — filled for only 274 of 854 placed candidates (32 %), so always state the fill rate. Candidates who signed and later went to Odbijen (5) are not counted.

## Vermittelt pro Zeitraum (placements as flow) — preferred for trends
- **Definition**: candidates whose pipeline status changed to **Potpisan ugovor (9)** for the first time in the period.
- **Formula**: `MIN(lsp_datetime)` per `lsp_kandidat_id` where `lsp_status_prijave_id = 9`, from `idk_log_statusi_prijave`, then count per period.
- **Reference**: 2022 299 · 2023 536 · 2024 71 · 2025 24 · 2026 1 (931 candidates ever signed vs. 854 currently at ≥ order 7 → ~77 dropped out later).
- **Caveats**: log starts 2021-12-07; earlier placements are missing. If counts look low, also check first entry into any status with `redoslijed_statusa >= 7`. `lsp_izvor`: 1 CRM, 2 PP, 3 bot, 4 queue, 5 cron, 6 transfer.

## Prihodi (revenue)
Three paid-revenue sources (currency of `kf_iznos` / `nf_iznos` is not documented – assumed EUR, confirm with the user):
| Source | Table | Paid filter | Date | 2022 | 2023 | 2024 |
|---|---|---|---|---:|---:|---:|
| Employer per-candidate installments | `idk_kandidat_financije` | `kf_placeno = 3` | `kf_datum_placanja` | 140.8k | 430.1k | 272.2k |
| Employer per-order installments | `idk_nalog_financije` | `nf_placeno = 3` | `nf_datum_placanja` | 452.2k | 1,819.2k | 177.8k |
| DIPL proformas paid by candidates (EUR column) | `idk_predracuni` | `pr_status = 2 AND pr_stornirano = 0` | `pr_datum_uplate` | 287.7k | 239.7k | 55.4k |
- `kf_type`: 0 nostrifikacija, 1 ugovor, 2 dobio vizu, 3 početak rada, 4 mjeseci nakon, 5 akademija. `*_placeno`: 0 NDF, 1 treba fakturisati, 2 fakturisano, 3 plaćeno (nf: 4 arhivirano).
- `kf_status` 2/3 = installment for a replaced / surplus candidate.
- Open receivables: `*_placeno = 2`; DIPL inkaso: `pr_status` 3/4/5 = inkaso 1/2/3.
- `idk_racuni` are the final invoices for paid DIPL proformas (`racuni.predracun_id → predracuni.pr_id`, 100 %) – never add racuni + predracuni.
- `pr_kandidat_id` / `racun_kandidat_id` are **DIPL ids** (`idk_nd_kandidata.id_broj_nd_kandidata`), not `kandidat_id`.

## Provizije (commissions)
`idk_obracuni` (168k rows, 2021-01 → 2024-08): per employee, per proforma & installment. `tip_provizije` 1 normal, 2 ontop1, 3 tim, 4 ontop72h, 5 ontop48h, 99 inkaso agent, 98 normal minus inkaso; `status_obracuna` 0 neisplaćen, 1 isplaćen, 2 arhiviran; `valuta` + amounts in BAM/RSD/EUR columns. Remainders: `idk_ostatci_obracuna`. Definitions: `idk_kategorije_provizija`, `idk_tipovi_provizija`. Salary-related → aggregate only unless explicitly requested.

## TF produktivnost (task force performance)
- **Definition**: tasks handled per agent and the share that end in a positive status.
- **Formula**: `COUNT(*)` and `SUM(tfs_is_positive = 1) / COUNT(*)` from `idk_task_force` ⨝ `idk_tf_statusi` on `tf_status_id = tfs_id`, grouped by `tf_agent_id`, filtered on `tf_doe`.
- **Caveats**: exclude `tf_agent_id IS NULL` (system tasks). "Positive" means *the candidate continues in the process*, not "success" — e.g. "Ne javlja se" is positive (retry). For outcome quality use specific statuses (e.g. casting: 16 Pristao, 20 Došao). Segment by `tf_vrsta_id`/category (casting vs posredovanje vs obrada) — mixing them distorts rates. 2025 reference: top agents 9–14k tasks/year, 58–73 % positive.
- Agent names: join `tf_agent_id = idk_employees.employee_id` and select only `employee_firstname`, `employee_lastname`, `employee_team` (never credential columns).

## Casting odziv (casting attendance)
- **Formula**: `SUM(tsr_status = 1) / COUNT(*)` from `idk_tf_stats_reservations` (1 Došao, 2 Nije došao, 3 Odustao), per `tsr_nalog_id` or `tsr_agent_id`.
- **Caveat**: table has no date column; join `tsr_interview_id → idk_pp_appointment_groups.ppaq_id` (`ppaq_start_date`) for dates — matches 3,828 of 3,852 rows. Status 4 (279 rows) is undocumented — show it separately. Recent casting groups (2026) show 0 % Došao: verify with the user whether attendance was recorded before reporting it.

## Dokumenti — vrijeme obrade (document processing time)
- **Definition**: average days a document spends in each status.
- **Formula**: `AVG(dsl_days_count)` from `idk_pp_documents_status_logs` grouped by `dsl_doc_status`.
- **Caveats**: only meaningful for non-terminal statuses (3, 6, 9, 12, 15, 21). `Spreman` (18), `Odbijen` (24) and `Arhiviran` (27) are end states — `dsl_days_count` is mostly NULL or grows indefinitely there (Spreman avg 264 d). Reference: Uploadan 1.2 d, Provjeren 1.7 d, Čekamo original 1.7 d, Poslan 2.2 d.

## Vize — dopune i odbijenice
- **Formula**: `COUNT(*)` from `idk_pp_visa_incomplete` by `vi_type` (1 Dopuna, 2 Odbijenica); deadline adherence via `vi_date_received_candidate <= vi_deadline_date_candidate`.
- **Caveat**: only 49 rows (2023-01 → 2024-08); too small for trends.

## Jezici (language progress)
- **Formula**: active level per candidate from `idk_candidate_verified_languages` (`cvl_active = 1`) by `cvl_status`; time in status from `idk_candidate_language_logs.cll_days_count`.
