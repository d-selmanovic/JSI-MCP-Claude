# Entities & Status Codes (JSI)

All values below were read from the lookup tables on 2026-10-29. Re-check with a `SELECT * FROM <lookup>` if a code is missing.

## Candidate (`idk_kandidati`, PK `kandidat_id`)

### `kandidat_status` → `idk_kandidat_status` (profile processing)
| Code | Name | Count (2026-10) |
|---|---|---|
| 0 | Na provjeri | 3,999 |
| 1 | U obradi | 8,433 |
| 2 | Obrađen | 3,804 |
| 3 | **Arhiviran** (excluded by default) | 4,447 |
| 4 | Kontrola | 24,545 |
| 5 | Dopuna | 461 |
| 6 | Odbio Messenger | 74,164 |
| 7 | U obradi više od 3 dana | 1,960 |
| 8 | Na dopuni više od 3 dana | 193 |

### `kandidat_status_prijave` → `idk_kandidat_status_prijave` (placement pipeline)
Ordered by `redoslijed_statusa`. `rezervisanje = 1` means the candidate is reserved for a nalog.

| Order | Code | Name | Reserved | Count |
|---|---|---|---|---|
| 1 | 1 | Slobodan | 0 | 54,276 |
| 2 | 2 | U projektu NR | 0 | 22,817 |
| 3 | 6 | U projektu RZ | 1 | 2,175 |
| 4 | 3 | Casting | 1 | 170 |
| 5 | 7 | Čeka ugovor | 1 | 6 |
| 6 | 8 | Poslan ugovor | 1 | 0 |
| **7** | **9** | **Potpisan ugovor** ← placement threshold | 1 | 43 |
| 8 | 12 | Prikupljanje dokumentacije | 1 | 17 |
| 9 | 15 | Čeka termin | 1 | 1 |
| 10 | 18 | Čeka vizu | 1 | 18 |
| 11 | 21 | Dopuna dokumenata | 1 | 0 |
| 12 | 24 | Odbijena viza | 1 | 0 |
| 13 | 27 | Dobio vizu | 1 | 16 |
| 14 | 10 | Početak rada | 1 | 104 |
| 15 | 4 | Završen | 1 | 660 |
| — | 5 | Odbijen | (no order / inactive) | 298 |
| — | 0 / NULL | not set | — | 106 / 41,299 |

Note: `Odbijena viza` (24) has order 12 and therefore counts as "placed" under the agreed definition (≥ order 7). Mention this if it is non-zero.

### `kandidat_porijeklo` (acquisition channel)
| Code | Meaning | Count |
|---|---|---|
| 0 | Old path (direct / legacy) | 53,894 |
| 1 | Came from DIPL | 1,887 |
| 2 | Came from DAK | 58 |
| 3 | Partner recommendation (Partner → Dipl → Kandidati) | 0 |
| 4 | SveZaVize web (SZV → DIPL → KAN) | 63,208 |
| 5 | JobStep web (JS → DIPL → KAN) | 964 |
| 6, 7, 8 | **undocumented** | 1,245 / 726 / 24 |

### `kandidat_nacin_odlaska` (migration route)
0 = Stručni kadar (skilled worker, default; also EU fallback) · 1 = EU (reserved for display) · 2 = Zapadno-balkanski sistem (Western Balkans regulation) · 3 = undocumented (13 rows).

### Other candidate flags
- `kandidat_potvrden_pocetak_rada`: 1 confirmed start, 0 did not start on agreed date, NULL unknown (515 × 1).
- `kandidat_nivo_obrazovanja`: 1 fakultet, 2 srednja škola, NULL unknown.
- `kandidat_iskustvo_u_struci`: 0/1/NULL; `_trajanje`: 0 none in last 5 yrs, 1 <1 yr, 2…6 years.
- `kandidat_glossa`: 0 no, 1 Glossa lead, 2 accepted Glossa lead, 3 potential (language school partner Glossa).
- `kandidat_partner_lead_status`: 1 Lead, 2 Klijent, 3 Nije zainteresiran.
- `kandidat_tf_status`: current task force status; NULL = no active tasks.
- `kandidat_group` → `idk_kandidati_grupe.kg_id` (application/occupation group, 77 groups): 7 Ostalo 75k, 68 Monter solarnih panela 15.7k, 22 Automehaničar 4.2k, 25 Montažer kablovske opreme 3.9k, 64 Internet monter 3.2k, 46 Servisni tehničar 2.4k, 2 Medicinski tehničar 1.6k, 51 Administrativni radnik 1.5k, 71 Autostaklar 1.5k, 39 Električar 1.5k.

## Task force
- `idk_tf_vrste.category`: 1 Casting, 2 Posredovanje (placement follow-up incl. language-course steps), 3 Obrada (diploma recognition / document processing).
- `idk_tf_statusi`: per task type (`tfs_vrsta_id`), `tfs_is_positive` 1 = candidate continues, 0 = drops out of tasks / task closed; `tfs_status_prijave` = pipeline status the candidate is moved to (e.g. 16 Pristao → 3 Casting; 6/10 → 1 Slobodan).
- Casting statuses (vrsta 1): 2 Neuspješna komunikacija, 4 Ne ispunjava uslove, 6 Nije zainteresiran, 8 Ispunjava uslove – ne javlja se, 10 Ne odgovara termin, 12 Dopuna, 14 Zainteresiran, 16 Pristao, 18 Dolazi, 20 Došao, 22 Nije došao, 24 Inbound poziv, 147 Pogrešan broj, 148 Nedostupan.
- `idk_tf_stats_reservations.tsr_status`: 1 Došao (1,351), 2 Nije došao (1,131), 3 Odustao (1,089), 4 / 5 undocumented (279 / 2).
- `idk_agenti_activity.activity_status`: 0 idle, 1 pauza, 2 live, 3 viber, 4 obuka, 5 inbound (durations not recorded — see task_force.md).

## Documents & visa
- `idk_pp_documents_statuses` (flow order): 3 Uploadan → 6 Provjeren → 9 Čekamo original → 12 Poslan → 15 Imamo original → 18 Spreman; exceptions 21 Nije prošao provjeru, 24 Odbijen; end 27 Arhiviran.
- `doc_visibility_status`: 0 arhiva, 1 nevidljiv, 2 vidljiv.
- `*_done_by` (required docs): 1 poslodavac, 2 kandidat, 3 JSI.
- `idk_pp_visa_incomplete.vi_type`: 1 Dopuna, 2 Odbijenica; `vi_complaint` 1 = appeal possible.
- `idk_candidate_verified_languages.cvl_status`: 1 samoprocjena, 2 samostalno uči, 3 kurs podnivo 1, 4 kurs podnivo 2, 5 čeka datum polaganja, 6 čeka polaganje (ima termin), 7 čeka rezultat, 8 ima certifikat, 9 certifikat istekao, 10 napreduje na veći nivo, 11 nije položen, 12 odustao, 13 arhiva, 14 motive. Only one row per candidate with `cvl_active = 1`. **Certificates** are recorded by upload (`cvl_certificate_path`, 367 rows); status 8 is almost unused (2 rows) and most certificates moved to 9 'istekao'.
- `idk_nostrifikovane_diplome.full_recognition`: NULL default, 0 partial, 1 full.

## Sales / companies
- `idk_clients.client_sales_status`: 0 lead, 1 in progress, 2 čeka ugovor, 3 aktivan, 4 arhiviran. `client_fc_status`: 0 lead, 1 in progress, 2 aktivan, 3 arhiviran. `client_fc_or_sales`: 0 FC, 1 sales. `client_origin`: 0 ručno, 1 dipl, 2 dak.
- `idk_companies.company_origin`: 0 normal, 1 dipl, 2 dak, 5 partner app.
- `idk_ro_usluge.tip_ro`: 1 DIPL, 2 DAK, 3 RO ugovora, 4 Inkaso DIPL; `status_ro`: 0 na čekanju, 1 aktivan, 2 odbijen, 3 deaktiviran.

## Pipeline history (`idk_log_statusi_prijave`)
One row per status change: `lsp_kandidat_id`, `lsp_status_prijave_id`, `lsp_datetime`, `lsp_projekt_id`, `lsp_employee_id`, `lsp_broj_dana`, `lsp_izvor` 1 CRM / 2 PP / 3 bot / 4 queue / 5 cron / 6 transfer. 361k rows, 2021-12 → 2026-02.
Processing-status history: `idk_log_kandidat_statusi` (`lks_status_obrade`, `lks_status_messenger`, `lks_broj_dana`, `lks_link_id` → `idk_link_generator`).

## Orders (`idk_nalozi`, 239)
`nalog_firma_fakturisanja` 1 Jobstep GmbH (DE), 2 Jobstep Int GmbH (CH); `nalog_ugovor` nalog / okvirni; `nalog_placena_prva_rata` 0 neplaćeno, 1 plaćeno, 2 NDF; `nalog_nacin_nostrifikacije` 1 standard (pošta), 2 mjesečne rate; `nalog_akademija`/`nalog_placa_nostrifikaciju` 0/1. `nalog_status` values 1,3–8,10–12 are **undocumented** (largest: 8 = 83, 12 = 82, 10 = 33, 1 = 23) – ask the user. Application blocks/criteria: `idk_nalozi_blokovi_prijave`, profiles: `idk_nalog_profil` + `idk_profil_kriterij`.

## DIPL (diploma recognition, own ID space `id_broj_nd_kandidata`)
- `idk_nd_kandidata.status_nd_kandidata`: 1 Novi (17.4k), 2 Prikupljanje dokumentacije, 3 Poslana pošta, 4 U obradi, 5 Dopuna dokumentacije, 6 Završen (2.2k), 7 Arhiviran (61.2k).
- `pstatus_nd_kandidata`: documented 1 Lead, 2 Neuspješan, 3 Zainteresiran, 4 Nezainteresiran, 5 U obradi; values 6–12 (≈42k rows) **undocumented**.
- `povijest_nd_kandidata` (source): 0 CRM, 1 Kandidati, 2 DAK, 3 Partner, 4 JS web, 5 Kampanje (72k → `kampanja_id` → `idk_kampanje_dipl`).
- `vrsta_obrade`: 1 Ausbildung, 2 srednja škola, 3 fakultet. `nivo_poznavanja_jezika`: 0 n/a, 1 none, 2 A1 … 7 C2. `vrsta_ugovora_nd_kandidata`: 1 bez popusta, 2 sa popustom.
- `idk_nd_ugovori.ug_status`: 0 arhiviran, 1 poslan, 2 prihvaćen, 3 odbijen, 4 otvoren link.
- `idk_predracuni.pr_status`: 0 arhiviran, 1 aktivan, 2 uplaćen, 3/4/5 inkaso 1/2/3.
- `idk_nd_kandidata_biljeske.tip_biljeska_nd`: 1 Ostalo, 2 Neuspješna komunikacija, 3 Nije zainteresiran, 4 Poslana infolista, 5 Poslan ugovor i predračun.
- `idk_dak_kandidati.status_dak_kandidat` (DAK = health-insurance partner line, 670 rows): 0 novi … 7 arhiviran.

## Staff & partners
- `idk_employees` (370): `employee_team` → `idk_timovi` (JobStep Main, GoCloud, WE Connect, SSC d.o.o., Team JSI, NTH Beograd), `employee_poslovnica` → `idk_poslovnice` (Bihać, Sarajevo, Mostar, Jelah, Doboj, Banja Luka, Beograd, Esslingen, Bern). `employee_status` is a comma list of undocumented codes.
- `idk_jobstep_partners` (34k app users = makleri/recommenders): `jp_position` 1 junior partner, 2 partner, 3 senior, 4 agency, 5 lilium super; `jp_user_permission` 1 makler, 2 supervizor; `jp_confirmedaccount` 0/1/2 deactivated; `jp_partner_company` → `idk_partner_companies` (DVAG, Internal, Dysordian, DAK, BARMER). Payouts: `idk_partner_uplate` (vrsta 1 NALOG / 2 DIPL; status 1 uplaćeno, 2 neuplaćeno, 3 odgođeno).

## Key relationships

Full measured wiring (76 relationships with coverage %): `references/veze.md`.

- `idk_kandidati.kandidat_ppa_partner_id → idk_pp_partners.ppa_id → idk_companies.company_id`
- `idk_kandidati.kandidat_nalog_id` = nalog the candidate is assigned to (only ~3k candidates have one)
- `idk_task_force.tf_candidate_id → idk_kandidati.kandidat_id`; `tf_status_id → idk_tf_statusi.tfs_id`; `tf_vrsta_id → idk_tf_vrste.id`
- `idk_pp_documents.doc_candidate_id → kandidat_id`; `doc_status → idk_pp_documents_statuses.ds_id`; `doc_crd_id → idk_pp_cand_required_documents.crd_id`; `doc_nrd_id → idk_pp_nalog_required_documents.nrd_id`
- `idk_pp_cand_appts.pca_appointment_id → idk_pp_appointments.pap_id` (interviews; `pca_recommendation` 1 Hire, 2 Reject, 3 Not sure)
- `idk_project_kandidati (pk_kandidatid, pk_projectid)` links candidates ↔ projects
