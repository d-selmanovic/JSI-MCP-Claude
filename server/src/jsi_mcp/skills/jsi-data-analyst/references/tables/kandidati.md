# Candidates (Kandidati)

## Quick Reference
Candidate master data and profile sub-tables. ~122k candidates, most of them dormant leads (61 % "Odbio Messenger"). Default filter: `kandidat_status <> 3`.

## Key Tables

### idk_kandidati
**Location**: `jsicrm.idk_kandidati` · **PK**: `kandidat_id` · **Rows**: 122,006

| Column | Description | Notes |
|---|---|---|
| kandidat_datetime | Registration timestamp | Use as "created at"; 3 rows = 1970 |
| kandidat_status | Profile processing status | see entities.md; 3 = Arhiviran |
| kandidat_status_prijave | Placement pipeline status | current state only |
| kandidat_porijeklo | Acquisition channel | 4 = SveZaVize (52 %), 0 = legacy (44 %) |
| kandidat_nacin_odlaska | Migration route | 0 skilled/EU, 2 Western Balkans |
| kandidat_nalog_id | Assigned job order | only ~3k filled |
| kandidat_ppa_partner_id | Partner (idk_pp_partners.ppa_id) | |
| kandidat_datum_ugovora | Contract date | 32 % filled among placed |
| kandidat_dogovoreni_pocetak_rada | Agreed start date ("proces odlaska") | preferred over legacy `kandidat_datum_pocetakrada` |
| kandidat_potvrden_pocetak_rada | Start confirmed (1) / not started (0) | |
| kandidat_viza, kandidat_viza_vrijedi_od/do, kandidat_termin_za_vizu | Visa info | termin: 1 has appointment, 2 none |
| kandidat_ima_nostrifikaciju | Diploma recognized (1/0) | |
| kandidat_tf_status | Current task-force status | NULL = no active task |
| tf_reserved_agent | Agent the candidate is reserved for | |
| kandidat_drzavljanstvo, kandidat_grad, kandidat_drzava | Citizenship / location | free text, inconsistent spelling |
| kandidat_zeljena_regija / kandidat_zeljeni_grad | Desired region/city in DE | FK idk_pp_regions / idk_pp_city; NULL undefined, 0/1 no preference |
| PII | ime, prezime, jmbg, broj_pasosa, mobitel, email, adresa, password | **do not output** |

Deprecated columns (keep out of new analyses): `kandidat_datum_pocetakrada`, `kandidat_datum_pocetakrada_mjesec`, `kandidat_potencijalni_pocetak_rada`, `datum_aplikacije` (97 % NULL).

### Profile sub-tables (1:n per candidate)
| Table | FK | Content |
|---|---|---|
| idk_kandidat_jezici | kj_kandidatid | Self-reported language levels |
| idk_candidate_verified_languages | via kj_id (cvl_id) | Verified level, course & exam dates, certificate |
| idk_kandidat_edukacija | ke_kandidat_id | Education (school, major → idk_skole / idk_skole_smjerovi) |
| idk_kandidat_radno_iskustvo | kri_kandidat_id | Work experience |
| idk_kandidat_vjestine | kv_kandidat_id | Skills |
| idk_kandidat_cv | kcv_kandidatid | CV files (BA/DE) |
| idk_kandidat_kontakt_info | kki_kandidat_id | Extra contacts (PII) |
| idk_kandidat_projekcije | kandidat_id | Projected start date |
| idk_project_kandidati | pk_kandidatid | Candidate ↔ project |
| idk_project_candidate_queue | queue_candidate_id (varchar!) | Waiting for project assignment; cast when joining |

## Sample Queries

Pipeline snapshot:
```sql
SELECT sp.redoslijed_statusa, sp.status_naziv, COUNT(*) AS kandidata
FROM idk_kandidati k
LEFT JOIN idk_kandidat_status_prijave sp ON sp.status_id = k.kandidat_status_prijave
WHERE k.kandidat_status <> 3
GROUP BY sp.redoslijed_statusa, sp.status_naziv
ORDER BY sp.redoslijed_statusa;
```

Channel mix of new candidates per year:
```sql
SELECT YEAR(kandidat_datetime) AS godina, kandidat_porijeklo, COUNT(*) AS novih
FROM idk_kandidati
WHERE kandidat_datetime >= '2000-01-01' AND kandidat_status <> 3
GROUP BY godina, kandidat_porijeklo
ORDER BY godina, novih DESC;
```
