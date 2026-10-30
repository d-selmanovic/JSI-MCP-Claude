# Documents, Visa, Languages, Diploma Recognition

## Quick Reference
For each nalog, employers define required documents (`idk_pp_nalog_required_documents`), instantiated per candidate (`idk_pp_cand_required_documents`). Uploaded files live in `idk_pp_documents`, every status change is logged in `idk_pp_documents_status_logs` (the only real status history in the CRM). Visa supplements/rejections are in `idk_pp_visa_incomplete`.

Document flow: 3 Uploadan → 6 Provjeren → 9 Čekamo original → 12 Poslan → 15 Imamo original → 18 Spreman (exceptions: 21 Nije prošao provjeru, 24 Odbijen; end: 27 Arhiviran).

## Key Tables
| Table | PK | Notes |
|---|---|---|
| idk_pp_nalog_required_documents | nrd_id | per nalog; flags by route: nrd_west_balkan, nrd_skilled_candidates, nrd_work_experience; nrd_done_by 1 poslodavac / 2 kandidat / 3 JSI; nrd_status 1 active / 2 inactive |
| idk_pp_cand_required_documents | crd_id | per candidate; crd_vi_id links to a visa supplement |
| idk_pp_document_types | doc_type_id | names BS/DE |
| idk_pp_documents | doc_id | doc_status → idk_pp_documents_statuses; doc_visibility_status 0 arhiva / 1 nevidljiv / 2 vidljiv |
| idk_pp_documents_status_logs | — | dsl_date, dsl_doc_status, dsl_days_count (days spent in status), dsl_user_id (CRM) or dsl_pp_user_id (partner); 14.6k rows, 2022-05 → 2025-11 |
| idk_pp_visa_incomplete | vi_id | vi_type 1 Dopuna / 2 Odbijenica; deadlines and receipt dates for candidate & employer; 49 rows |
| idk_pp_contract_sent | id_cs | contract mailing: cs_status 1 poslano / 2 zaprimljeno / 3 arhivirano; sent/received dates |
| idk_pp_reminders (+ _settings, _types, _documents) | pr_id | reminder escalation: pr_status 1 poslan, 2 prihvaćen, 3 izvršen, 4 neizvršen, 5 izvršen odustankom; pr_level = escalation level |
| idk_candidate_verified_languages | cvl_id | language level status 1–14 (see entities.md), exam & certificate dates |
| idk_candidate_language_logs | cll_id | language status history, cll_days_count |
| idk_nostrifikovane_diplome | id_nd | recognized diplomas; full_recognition 0/1 |

## Sample Queries

Average days per document status (non-terminal only):
```sql
SELECT ds.ds_name, COUNT(*) AS promjena, ROUND(AVG(l.dsl_days_count), 1) AS prosjek_dana
FROM idk_pp_documents_status_logs l
JOIN idk_pp_documents_statuses ds ON ds.ds_id = l.dsl_doc_status
WHERE l.dsl_doc_status IN (3, 6, 9, 12, 15, 21)
GROUP BY ds.ds_id, ds.ds_name
ORDER BY ds.ds_id;
```

Open required documents per nalog by responsible party:
```sql
SELECT crd.crd_nalog_id, crd.crd_done_by, COUNT(*) AS otvorenih
FROM idk_pp_cand_required_documents crd
LEFT JOIN idk_pp_documents d ON d.doc_crd_id = crd.crd_id AND d.doc_status = 18
WHERE crd.crd_status = 1 AND d.doc_id IS NULL
GROUP BY crd.crd_nalog_id, crd.crd_done_by
ORDER BY otvorenih DESC;
```

Visa supplements: deadline met?
```sql
SELECT vi_type,
       COUNT(*) AS ukupno,
       SUM(vi_date_received_candidate <= vi_deadline_date_candidate) AS kandidat_u_roku,
       SUM(vi_date_received_employer <= vi_deadline_date_employer) AS poslodavac_u_roku
FROM idk_pp_visa_incomplete
GROUP BY vi_type;
```

Active language level distribution:
```sql
SELECT cvl_status, COUNT(*) AS kandidata
FROM idk_candidate_verified_languages
WHERE cvl_active = 1
GROUP BY cvl_status
ORDER BY cvl_status;
```
