# Task Force (call center, castings, follow-ups)

## Quick Reference
The task force (TF) is the agent team that calls candidates through each process step. Every call/action is a row in `idk_task_force`. Task types (`idk_tf_vrste`) are grouped into 3 categories: **1 Casting**, **2 Posredovanje** (contract follow-up, language-course steps, Western Balkans application), **3 Obrada** (diploma recognition / document collection). Data runs 2023-03 → 2026-02.

## Key Tables

### idk_task_force
**PK**: `tf_id` · **Rows**: 452,568

| Column | Description | Notes |
|---|---|---|
| tf_doe | Task timestamp | filter on this first |
| tf_agent_id | Agent (employee id) | NULL = created by cron/system |
| tf_candidate_id | → idk_kandidati.kandidat_id | |
| tf_vrsta_id | Task type → idk_tf_vrste.id | |
| tf_status_id | Outcome → idk_tf_statusi.tfs_id | |
| tf_last_active_task | 1 = candidate's current open task | 468 rows |
| tf_nalog_id, tf_project_id, tf_casting_id | Context | tf_casting_id = appointment group |
| tf_brojac_neuspjela_komunikacija | Failed-contact counter | |
| tf_call_appointment | Scheduled call-back | |

### idk_tf_statusi
Per task type; `tfs_is_positive` (1 continues / 0 exits), `tfs_has_interview`, `tfs_status_prijave` (pipeline status the candidate moves to). Status names repeat across types ("Ne javlja se", "Odustao") — always group by `tfs_id` or `(tfs_vrsta_id, tfs_name)`.

### Related
| Table | Use |
|---|---|
| idk_tf_reservations | Candidate reserved for agent/project/nalog |
| idk_tf_stats_reservations | Casting attendance (tsr_status 1 Došao / 2 Nije došao / 3 Odustao; 4 (279 rows) and 5 (2 rows) undocumented) |
| idk_tf_agent_nalog | Which agent works which nalog per task type |
| idk_tf_transfered_candidates_logs | Bulk transfers to projects |
| idk_agenti_activity | Agent status switches (activity_status 0 idle,1 pauza,2 live,3 viber,4 obuka,5 inbound). **Durations are not usable**: `activity_kraj` = `activity_pocetak` and `activity_ukupno` = 0 in 99.6 % of rows — count events only |
| idk_pp_appointments / idk_pp_appointment_groups | Casting dates & locations |
| idk_pp_cand_appts | Interview results (avg rating, recommendation 1 Hire / 2 Reject / 3 Not sure) |

## Sample Queries

Outcome distribution per task category (2025):
```sql
SELECT v.category, s.tfs_name, COUNT(*) AS taskova
FROM idk_task_force t
JOIN idk_tf_vrste v ON v.id = t.tf_vrsta_id
LEFT JOIN idk_tf_statusi s ON s.tfs_id = t.tf_status_id
WHERE t.tf_doe >= '2025-01-01' AND t.tf_doe < '2026-01-01'
GROUP BY v.category, s.tfs_id, s.tfs_name
ORDER BY v.category, taskova DESC;
```

Casting attendance per month:
```sql
SELECT DATE_FORMAT(g.ppaq_start_date, '%Y-%m') AS mjesec,
       COUNT(*) AS rezervacija,
       SUM(r.tsr_status = 1) AS dosao,
       ROUND(100 * SUM(r.tsr_status = 1) / NULLIF(COUNT(*), 0), 1) AS pct_dosao
FROM idk_tf_stats_reservations r
JOIN idk_pp_appointment_groups g ON g.ppaq_id = r.tsr_interview_id
GROUP BY mjesec
ORDER BY mjesec;
```

Agent status switches by type (counts, not time):
```sql
SELECT employee_id, activity_status, COUNT(*) AS promjena
FROM idk_agenti_activity
WHERE activity_pocetak >= '2025-01-01'
GROUP BY employee_id, activity_status
ORDER BY employee_id, activity_status;
```
