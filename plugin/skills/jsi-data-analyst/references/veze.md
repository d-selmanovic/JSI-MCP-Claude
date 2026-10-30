# Veze između tabela (Verdrahtung) – izmjereno 2026-10-29

Za svaku vezu: koliko redova ima popunjen ključ (`n`, bez NULL/0) i koliko njih stvarno pronalazi red u ciljnoj tabeli (`ok`). MySQL 8.4.11, InnoDB. Baza ima samo **3 deklarisana foreign key-a** (`idk_tutorijali.tutorijal_kategorija_id → idk_kategorije`, `rb_field_state → rb_entity_state`, `rb_outbox.event_id → rb_events`). Sve poslovne veze su konvencija aplikacije – zato su ovdje izmjerene.

## Dva odvojena ID prostora kandidata (najvažnije pravilo)

| ID | Tabela | Koristi se u |
|---|---|---|
| `kandidat_id` | `idk_kandidati` (vermittlung/posao) | task force, pipeline logovi, jezici, obrazovanje, iskustvo, PP dokumenti, projekti, `users`, `idk_kandidat_financije`, `idk_pp_reminders` |
| `id_broj_nd_kandidata` | `idk_nd_kandidata` (DIPL/nostrifikacija) | `idk_predracuni`, `idk_racuni`, `idk_obracuni`(via predračun), `idk_nd_*`, `idk_ponovne_prijave`, `idk_reminders`, `idk_nostrifikovane_diplome.id_cand_dipl` |

**Most**: `idk_kandidati.kandidat_dipl_id = idk_nd_kandidata.id_broj_nd_kandidata` (77.616 kandidata, 100 % pogodaka). `idk_nostrifikovane_diplome` ima oba ključa (`id_cand_job` → kandidati, `id_cand_dipl` → DIPL).

### Jesu li svi DIPL kandidati i u `idk_kandidati`? – NE (izmjereno 2026-10-29)

| | Broj |
|---|---:|
| DIPL kandidata (`idk_nd_kandidata`) | 81.330 |
| povezano preko `idk_kandidati.kandidat_dipl_id` | 77.583 (95,4 %) |
| **nije povezano** | **3.747 (4,6 %)** |
| – od toga nađeno u `idk_kandidati` po telefonu (zadnjih 8 cifara) ili e-mailu | 2.572 (vjerovatno ista osoba, link nedostaje) |
| – ima telefon/e-mail, ali nema pogotka | 575 (najvjerovatnije stvarno nisu u Kandidatima) |
| – bez telefona i e-maila (ne može se provjeriti) | 600 |

Nepovezani su uglavnom iz kampanja (`povijest_nd_kandidata = 5`: 3.274), iz 2021–2022, i arhivirani (`status_nd_kandidata = 7`: 3.150).

- **`idk_nd_kandidata.kandidat_idd` NIJE pouzdan link**: od 5.756 popunjenih, 3.189 se slaže s `kandidat_dipl_id`, **1.539 pokazuje na drugog kandidata**, 1.028 kandidata nema `kandidat_dipl_id`. Koristiti samo `kandidat_dipl_id`.
- **33 DIPL ID-a su vezana za 2 kandidata** (duplikati u `idk_kandidati`) – kod brojanja osoba koristiti `COUNT(DISTINCT kandidat_dipl_id)`.
- Telefonsko poklapanje je heuristika (moguće lažne pozitivne kod dijeljenih brojeva); e-mail je pouzdaniji (945 pogodaka).

⚠️ Pogrešan join `idk_predracuni.pr_kandidat_id = idk_kandidati.kandidat_id` daje 8.323 *slučajnih* pogodaka (78 %) – izgleda ispravno, ali je pogrešno. Isto za `idk_racuni` (70 %) i `idk_reminders` (61 %).

## Sve izmjerene veze

| Veza (dijete.kolona → roditelj.kolona) | n | ok | pokrivenost | ocjena |
|---|---:|---:|---:|---|
| `idk_kandidati.kandidat_group` → `idk_kandidati_grupe.kg_id` | 122,006 | 122,006 | 100.00 % | ✅ potpuna |
| `idk_kandidati.kandidat_status` → `idk_kandidat_status.status_id` | 118,007 | 118,007 | 100.00 % | ✅ potpuna |
| `idk_kandidati.kandidat_status_prijave` → `idk_kandidat_status_prijave.status_id` | 80,601 | 80,601 | 100.00 % | ✅ potpuna |
| `idk_kandidati.kandidat_nalog_id` → `idk_nalozi.nalog_id` | 2,961 | 2,961 | 100.00 % | ✅ potpuna |
| `idk_kandidati.kandidat_ppa_partner_id` → `idk_pp_partners.ppa_id` | 585 | 584 | 99.83 % | ✅ (1 siročadi) |
| `idk_kandidati.kandidat_dipl_id` → `idk_nd_kandidata.id_broj_nd_kandidata` | 77,616 | 77,616 | 100.00 % | ✅ potpuna |
| `idk_kandidati.tf_reserved_agent` → `idk_employees.employee_id` | 320 | 320 | 100.00 % | ✅ potpuna |
| `idk_kandidati.zaduzeni_makler_id` → `idk_jobstep_partners.jp_id` | 6 | 6 | 100.00 % | ✅ potpuna |
| `idk_kandidati.kandidat_partnerid` → `idk_jobstep_partners.jp_id` | 2,009 | 2,005 | 99.80 % | ✅ (4 siročadi) |
| `idk_kandidati.kandidat_zaposlen_kod` → `idk_companies.company_id` | 354 | 354 | 100.00 % | ✅ potpuna |
| `idk_kandidati.struka_sa_prijave` → `idk_struke.id_struke` | 943 | 943 | 100.00 % | ✅ potpuna |
| `idk_kandidati.kandidat_zeljeni_grad` → `idk_pp_city.pc_id` | 0 | 0 | – | neiskorištena kolona |
| `idk_kandidat_jezici.kj_kandidatid` → `idk_kandidati.kandidat_id` | 80,911 | 80,906 | 99.99 % | ✅ (5 siročadi) |
| `idk_kandidat_edukacija.ke_kandidat_id` → `idk_kandidati.kandidat_id` | 149,418 | 149,407 | 99.99 % | ✅ (11 siročadi) |
| `idk_kandidat_edukacija.ke_smjer_id` → `idk_skole_smjerovi.ss_id` | 119,234 | 119,234 | 100.00 % | ✅ potpuna |
| `idk_kandidat_edukacija.ke_skola_id` → `idk_skole.skola_id` | 120,803 | 120,802 | 100.00 % | ✅ (1 siročadi) |
| `idk_kandidat_radno_iskustvo.kri_kandidat_id` → `idk_kandidati.kandidat_id` | 87,844 | 87,842 | 100.00 % | ✅ (2 siročadi) |
| `idk_kandidat_de.kde_kandidat_id` → `idk_kandidati.kandidat_id` | 3,332 | 3,329 | 99.91 % | ✅ (3 siročadi) |
| `idk_candidate_verified_languages.cvl_id` → `idk_kandidat_jezici.kj_id` | 3,897 | 3,896 | 99.97 % | ✅ (1 siročadi) |
| `idk_task_force.tf_candidate_id` → `idk_kandidati.kandidat_id` | 452,568 | 452,565 | 100.00 % | ✅ (3 siročadi) |
| `idk_task_force.tf_agent_id` → `idk_employees.employee_id` | 447,025 | 447,025 | 100.00 % | ✅ potpuna |
| `idk_task_force.tf_status_id` → `idk_tf_statusi.tfs_id` | 452,568 | 452,568 | 100.00 % | ✅ potpuna |
| `idk_task_force.tf_vrsta_id` → `idk_tf_vrste.id` | 452,568 | 452,568 | 100.00 % | ✅ potpuna |
| `idk_task_force.tf_nalog_id` → `idk_nalozi.nalog_id` | 448,293 | 448,293 | 100.00 % | ✅ potpuna |
| `idk_task_force.tf_project_id` → `idk_projects.project_id` | 448,283 | 448,283 | 100.00 % | ✅ potpuna |
| `idk_log_statusi_prijave.lsp_kandidat_id` → `idk_kandidati.kandidat_id` | 360,225 | 360,224 | 100.00 % | ✅ (1 siročadi) |
| `idk_log_statusi_prijave.lsp_employee_id` → `idk_employees.employee_id` | 250,251 | 250,105 | 99.94 % | ✅ (146 siročadi) |
| `idk_log_statusi_prijave.lsp_projekt_id` → `idk_projects.project_id` | 358,317 | 357,019 | 99.64 % | ✅ (1298 siročadi) |
| `idk_log_kandidat_statusi.lks_kandidat_id` → `idk_kandidati.kandidat_id` | 240,869 | 240,822 | 99.98 % | ✅ (47 siročadi) |
| `idk_log_kandidat_statusi.lks_link_id` → `idk_link_generator.lg_id` | 128,369 | 128,369 | 100.00 % | ✅ potpuna |
| `idk_project_kandidati.pk_kandidatid` → `idk_kandidati.kandidat_id` | 205,170 | 205,111 | 99.97 % | ✅ (59 siročadi) |
| `idk_project_kandidati.pk_projectid` → `idk_projects.project_id` | 207,642 | 207,639 | 100.00 % | ✅ (3 siročadi) |
| `idk_projects.project_companyid` → `idk_companies.company_id` | 2,740 | 2,740 | 100.00 % | ✅ potpuna |
| `idk_nalozi.kompanija_id` → `idk_companies.company_id` | 239 | 239 | 100.00 % | ✅ potpuna |
| `idk_nalozi.nalog_js_partner_id` → `idk_jobstep_partners.jp_id` | 3 | 3 | 100.00 % | ✅ potpuna |
| `idk_pp_partners.ppa_company_id` → `idk_companies.company_id` | 58 | 58 | 100.00 % | ✅ potpuna |
| `idk_pp_partners.ppa_nalog_id` → `idk_nalozi.nalog_id` | 58 | 58 | 100.00 % | ✅ potpuna |
| `idk_predracuni.pr_kandidat_id` → `idk_nd_kandidata.id_broj_nd_kandidata` | 10,701 | 10,701 | 100.00 % | ✅ potpuna |
| `idk_predracuni.pr_kandidat_id` → `idk_kandidati.kandidat_id` | 10,701 | 8,323 | 77.78 % | ❌ POGREŠNA veza (slučajni pogoci) |
| `idk_racuni.racun_kandidat_id` → `idk_nd_kandidata.id_broj_nd_kandidata` | 4,509 | 4,509 | 100.00 % | ✅ potpuna |
| `idk_racuni.racun_kandidat_id` → `idk_kandidati.kandidat_id` | 4,509 | 3,172 | 70.35 % | ❌ POGREŠNA veza (slučajni pogoci) |
| `idk_racuni.predracun_id` → `idk_predracuni.pr_id` | 3,820 | 3,820 | 100.00 % | ✅ potpuna |
| `idk_obracuni.predracun_id` → `idk_predracuni.pr_id` | 168,233 | 167,920 | 99.81 % | ✅ (313 siročadi) |
| `idk_obracuni.employee_id` → `idk_employees.employee_id` | 168,233 | 168,233 | 100.00 % | ✅ potpuna |
| `idk_kandidat_financije.kandidat_id` → `idk_kandidati.kandidat_id` | 1,067 | 1,067 | 100.00 % | ✅ potpuna |
| `idk_kandidat_financije.nalog_id` → `idk_nalozi.nalog_id` | 1,067 | 1,067 | 100.00 % | ✅ potpuna |
| `idk_nalog_financije.nf_nalog_id` → `idk_nalozi.nalog_id` | 126 | 126 | 100.00 % | ✅ potpuna |
| `idk_nd_kandidata_biljeske.id_kandidata_biljeska_nd` → `idk_nd_kandidata.id_broj_nd_kandidata` | 928,806 | 928,802 | 100.00 % | ✅ (4 siročadi) |
| `idk_nd_kandidata_status_log.idd_broj_nd_kandidata` → `idk_nd_kandidata.id_broj_nd_kandidata` | 407,670 | 407,610 | 99.99 % | ✅ (60 siročadi) |
| `idk_nd_termini.termin_kandidat_id` → `idk_nd_kandidata.id_broj_nd_kandidata` | 450,943 | 450,943 | 100.00 % | ✅ potpuna |
| `idk_nd_ugovori.ug_kandidat_id` → `idk_nd_kandidata.id_broj_nd_kandidata` | 2,518 | 2,518 | 100.00 % | ✅ potpuna |
| `idk_nd_kandidata.kampanja_id` → `idk_kampanje_dipl.kd_id` | 73,689 | 73,687 | 100.00 % | ✅ (2 siročadi) |
| `idk_nd_kandidata.zaduzen_zaposlenik_nd_kandidata` → `idk_employees.employee_id` | 81,330 | 81,330 | 100.00 % | ✅ potpuna |
| `idk_nd_kandidata.idd_ustanova_nd` → `idk_nd_ustanove.id_ustanove_nd` | 2,799 | 2,799 | 100.00 % | ✅ potpuna |
| `idk_pp_documents.doc_candidate_id` → `idk_kandidati.kandidat_id` | 2,418 | 2,418 | 100.00 % | ✅ potpuna |
| `idk_pp_documents_status_logs.dsl_doc_id` → `idk_pp_documents.doc_id` | 14,602 | 14,555 | 99.68 % | ✅ (47 siročadi) |
| `idk_pp_cand_appts.pca_kandidat_id` → `idk_kandidati.kandidat_id` | 6,808 | 6,808 | 100.00 % | ✅ potpuna |
| `idk_pp_cand_appts.pca_appointment_id` → `idk_pp_appointments.pap_id` | 6,807 | 6,801 | 99.91 % | ✅ (6 siročadi) |
| `idk_tf_stats_reservations.tsr_interview_id` → `idk_pp_appointment_groups.ppaq_id` | 3,831 | 3,828 | 99.92 % | ✅ (3 siročadi) |
| `idk_kandidati_reject_reasons.krr_candidate_id` → `idk_kandidati.kandidat_id` | 1,832 | 1,832 | 100.00 % | ✅ potpuna |
| `idk_kandidati_reject_reasons.krr_reason_id` → `idk_reject_reasons.rr_id` | 1,832 | 1,832 | 100.00 % | ✅ potpuna |
| `idk_kandidati_contracts.kc_candidate_id` → `idk_kandidati.kandidat_id` | 2,103 | 2,103 | 100.00 % | ✅ potpuna |
| `users.kandidat_id` → `idk_kandidati.kandidat_id` | 111,120 | 111,111 | 99.99 % | ✅ (9 siročadi) |
| `idk_partner_uplate.jp_uplate_partnerid` → `idk_jobstep_partners.jp_id` | 147 | 147 | 100.00 % | ✅ potpuna |
| `idk_partner_uplate.jp_uplate_kandidatid` → `idk_kandidati.kandidat_id` | 147 | 144 | 97.96 % | ⚠️ djelimična |
| `idk_employees.employee_team` → `idk_timovi.id_t` | 369 | 369 | 100.00 % | ✅ potpuna |
| `idk_employees.employee_poslovnica` → `idk_poslovnice.branch_id` | 281 | 281 | 100.00 % | ✅ potpuna |
| `idk_validnosti_inputa.vi_kandidat_id` → `idk_kandidati.kandidat_id` | 82,277 | 82,264 | 99.98 % | ✅ (13 siročadi) |
| `idk_candidate_language_logs.cll_candidate_id` → `idk_kandidati.kandidat_id` | 5,796 | 5,796 | 100.00 % | ✅ potpuna |
| `idk_ponovne_prijave.id_kandidata` → `idk_nd_kandidata.id_broj_nd_kandidata` | 12,764 | 12,761 | 99.98 % | ✅ (3 siročadi) |
| `idk_nostrifikovane_diplome.id_cand_job` → `idk_kandidati.kandidat_id` | 2,109 | 2,109 | 100.00 % | ✅ potpuna |
| `idk_nostrifikovane_diplome.id_cand_dipl` → `idk_nd_kandidata.id_broj_nd_kandidata` | 2,155 | 2,155 | 100.00 % | ✅ potpuna |
| `idk_reminders.reminder_candidate_id` → `idk_kandidati.kandidat_id` | 16,009 | 9,800 | 61.22 % | ❌ POGREŠNA veza (slučajni pogoci) |
| `idk_reminders.reminder_candidate_id` → `idk_nd_kandidata.id_broj_nd_kandidata` | 16,009 | 16,008 | 99.99 % | ✅ (1 siročadi) |
| `idk_pp_reminders.pr_candidate_id` → `idk_kandidati.kandidat_id` | 22,348 | 22,348 | 100.00 % | ✅ potpuna |
| `idk_companies.js_partner_id` → `idk_jobstep_partners.jp_id` | 41 | 39 | 95.12 % | ⚠️ djelimična |

## Lookup veze (šifrarnici) bez posebnog mjerenja

| Kolona | Šifrarnik |
|---|---|
| `idk_kandidati.kandidat_status` | `idk_kandidat_status.status_id` |
| `idk_kandidati.kandidat_status_prijave`, `idk_log_statusi_prijave.lsp_status_prijave_id` | `idk_kandidat_status_prijave.status_id` |
| `idk_task_force.tf_status_id` / `tf_vrsta_id` | `idk_tf_statusi.tfs_id` / `idk_tf_vrste.id` |
| `idk_pp_documents.doc_status`, `idk_pp_documents_status_logs.dsl_doc_status` | `idk_pp_documents_statuses.ds_id` |
| `idk_pp_*_required_documents.*_type_id` | `idk_pp_document_types.doc_type_id` |
| `idk_kandidati_reject_reasons.krr_reason_id` | `idk_reject_reasons.rr_id` |
| `idk_nd_kandidata_biljeske.razlog_biljeska_nd` | `idk_ro_usluge.id_ro` |
| `idk_skole_smjerovi.ss_struka_id`, `idk_kandidati.struka_sa_prijave` | `idk_struke.id_struke` |
| `idk_pp_city.pc_region` | `idk_pp_regions.pr_id` |
| `idk_jobstep_partners.jp_partner_company` | `idk_partner_companies.pc_id` (DVAG, DAK, BARMER, Dysordian, Internal) |
| `idk_employees.employee_team` / `employee_poslovnica` | `idk_timovi.id_t` / `idk_poslovnice.branch_id` |
| Slobodni tekst zanimanja (`kandidat_prijava_na`, `kri_pozicija`, `ke_naziv_kvalifikacije`) | `beruf_mapping.freitext_wert` → `berufsgruppe_id` (pokrivenost 95 % / 100 % / 66 %) |

## Generičke (polimorfne) veze – oprez

- `idk_notes(note_group, note_dataid)`, `idk_documents(document_group, document_dataid)`, `idk_timeline(timeline_group, timeline_dataid)`, `idk_tasks(task_group, task_dataid)`, `idk_companies_info`, `idk_contacts_info`, `idk_employees_info`: `*_group` određuje na koji entitet `*_dataid` pokazuje (kandidat, firma, kontakt…). Značenje grupa nije dokumentovano u bazi – pitati korisnika prije join-a.
- `idk_project_candidate_queue.queue_candidate_id/queue_project_id` su **varchar(7)** – pri joinu koristiti `CAST(... AS UNSIGNED)`.
- `idk_pp_appointment_groups.papq_nalog_id` i `idk_pp_appointments.pap_group_id` su **varchar(7)**.
- `idk_projects.project_nalogid` je **varchar(25)**.
- `idk_module_permissions.mp_employees`, `idk_pp_reminder_settings.prs_*_ids`, `idk_companies.company_professions` su liste ID-eva u tekstu (comma-separated / array) – `FIND_IN_SET`.
- `idk_glossa_log.candidate` sadrži md5 hash (ponekad JSON niz), ne `kandidat_id`.

## Pregled (tekstualni dijagram)

```
idk_companies ─┬─< idk_nalozi ─┬─< idk_pp_partners ─< idk_kandidati.kandidat_ppa_partner_id
               │               ├─< idk_nalog_financije / idk_nalozi_rate / idk_nalozi_log / idk_nalozi_blokovi_prijave
               │               └─< idk_task_force.tf_nalog_id
               └─< idk_projects ─< idk_project_kandidati >─ idk_kandidati

idk_kandidati ─┬─< idk_kandidat_jezici ─< idk_candidate_verified_languages (cvl_id = kj_id) ─< idk_candidate_language_logs
               ├─< idk_kandidat_edukacija >─ idk_skole_smjerovi >─ idk_struke
               ├─< idk_kandidat_radno_iskustvo ··(tekst)·· beruf_mapping
               ├─< idk_task_force >─ idk_tf_statusi >─ idk_tf_vrste ; >─ idk_employees
               ├─< idk_log_statusi_prijave / idk_log_kandidat_statusi
               ├─< idk_pp_documents ─< idk_pp_documents_status_logs
               ├─< idk_pp_cand_appts >─ idk_pp_appointments >─ idk_pp_appointment_groups
               ├─< idk_kandidat_financije >─ idk_nalozi
               ├── users (1:1, app login)
               └── kandidat_dipl_id ══► idk_nd_kandidata (DIPL)

idk_nd_kandidata ─┬─< idk_nd_kandidata_biljeske / _status_log / _dokumenti / idk_nd_termini / idk_nd_ugovori / idk_nd_rate
                  ├─< idk_predracuni ─< idk_racuni ; ─< idk_obracuni >─ idk_employees
                  ├─< idk_ponovne_prijave / idk_reminders
                  └─> idk_kampanje_dipl / idk_nd_ustanove
```

## Indeksi (bitno za brzinu upita)

Indeksirane join kolone (brzo): `idk_kandidati(kandidat_dipl_id, kandidat_group, kandidat_nalog_id, kandidat_status, kandidat_status_prijave, kandidat_tf_status, tf_reserved_agent)`, `idk_kandidat_jezici(kj_kandidatid, kj_naziv)`, `idk_kandidat_edukacija(ke_kandidat_id)`, `idk_kandidat_radno_iskustvo(kri_kandidat_id)`, `idk_task_force(tf_agent_id, tf_candidate_id, tf_nalog_id, tf_project_id, tf_status_id, tf_vrsta_id, tf_casting_id)`, `idk_log_statusi_prijave(lsp_kandidat_id, lsp_projekt_id, lsp_status_prijave_id)`, `idk_log_kandidat_statusi(lks_kandidat_id)`, `idk_project_kandidati(pk_kandidatid, pk_projectid)`, `idk_nd_kandidata(status, pstatus, povijest, kampanja_id, vrijeme_kreiranja)`, `idk_nd_kandidata_biljeske(id_kandidata_biljeska_nd)`, `idk_nd_termini(termin_kandidat_id)`, `idk_predracuni(pr_kandidat_id)`, `idk_nostrifikovane_diplome(id_cand_job, id_cand_dipl)`, `beruf_mapping(freitext_wert UNIQUE, berufsgruppe_id)`, `users(kandidat_id UNIQUE, email UNIQUE)`.

**Bez indeksa** (izbjegavati korelirane upite nad njima): `idk_kandidat_de.kde_kandidat_id`, `idk_kandidat_edukacija.ke_smjer_id`, `idk_kandidati.kandidat_ppa_partner_id / kandidat_datetime / kandidat_prijava_na / kandidat_vozacka_*`, `idk_racuni.racun_kandidat_id`, `idk_obracuni.*`, `idk_kandidat_financije.*`.

**Pravilo**: korelirani `EXISTS` po `idk_kandidati` (122k) prelazi BlazeSQL timeout od 60 s. Uvijek prvo agregirati djecu u CTE (`SELECT DISTINCT kid ...`) pa joinati.
