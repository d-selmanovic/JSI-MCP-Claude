# Partner portal (PP) – poslodavci, dokumenti, vize, reminderi

Tabele: 20. Redovi i periodi stanje 2026-10-29.

## `idk_pp_cand_required_documents`

- **Opis**: Tracks the status, lifecycle, and fulfillment details of required documents associated with candidates and specific orders.
- **Redova**: 70 · **Period**: 2023-03-17 → 2024-08-06 (`crd_date_activated`) · **PK**: `crd_id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `crd_id` | int | PRI |  |  |
| `crd_cand_id` | int |  |  |  |
| `crd_nalog_id` | int |  |  |  |
| `crd_type_id` | int |  | foreign key iz tabele pp_document_types |  |
| `crd_done_by` | int |  | ko je zaduzen za kreiranje dokumenta: 1-poslodavac, 2-kandidat, 3-mi |  |
| `crd_status` | int |  | 1-aktivan, 2-neaktivan |  |
| `crd_date_activated` | datetime |  |  |  |
| `crd_user_activated` | int |  |  |  |
| `crd_date_archived` | datetime |  |  |  |
| `crd_user_archived` | int |  |  |  |
| `crd_comment` | text |  |  |  |
| `crd_vi_id` | int |  | foreign key iz tabele pp_visa_incomplete |  |

## `idk_pp_city`

- **Opis**: Stores information about cities, including their names, associated regions, and active status.
- **Redova**: 55 · **Period**: – · **PK**: `pc_id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `pc_id` | int | PRI |  |  |
| `pc_region` | int |  | FK iz idk_pp_regions |  |
| `pc_name` | varchar(255) |  |  |  |
| `pc_status` | int |  | 1-aktivan |  |

## `idk_pp_contract_sent`

- **Opis**: Tracks the dispatch, delivery status, and archiving details of candidate and partner contracts, including associated employees and shipment tracking codes.
- **Redova**: 3 · **Period**: 2024-08-08 → 2024-10-24 (`cs_entry_date`) · **PK**: `id_cs`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `id_cs` | int | PRI |  |  |
| `cs_kandidat_id` | int | MUL | Id kandidata iz tabele  idk_kandidati |  |
| `cs_nalog_id` | int | MUL | Id naloga iz tabele idk_kandidati u trenutku inserta |  |
| `cs_partner_id` | int | MUL | Id partnera iz tabele idk_kandidati u trenutku inserta |  |
| `cs_tracking_code` | text |  | Tracking code koji unosi poslodavac |  |
| `cs_tracking_link` | text |  | Link stranice od pošte gdje se može provjeriti  pošiljka za unešeni tracking code |  |
| `cs_sent_date` | date |  | Datum kada je pošiljka poslana |  |
| `cs_status` | int |  | 1 - poslano, 2 - zaprimljeno, 3 - arhivirano |  |
| `cs_entry_date` | datetime |  | Datum unosa/inserta |  |
| `cs_entry_pua_id` | int | MUL | Pua_id je različito od null ako je poslodavac preko  PPa označio da je poslano. Pua_id je jednako null  ako je employee_id različito od null. |  |
| `cs_entry_employee_id` | int |  | Analogno prethodnoj koloni. |  |
| `cs_received_date` | date |  | Datum prijema koji unosi employee preko CRMa. |  |
| `cs_received_employee_id` | int |  | Zapolsenik koji je označio prijem pošte. |  |
| `cs_archived_date` | datetime |  | Datum arhiviranja reda. |  |
| `cs_archived_employee_id` | int |  | Employee koji je pokrenuo određenu akciju u kojoj je   arhiviran ovaj red.  idk_kandidati  PK kandidat_id  FK1 kandidat_nalog_id  FK2 kandidat_ppa_partner_id |  |

## `idk_pp_document_types`

- **Opis**: A lookup table that stores definitions of document types, including their names in Bosnian/Croatian/Serbian and German, creation dates, and the users who entered them.
- **Redova**: 10 · **Period**: 2022-10-27 → 2024-05-31 (`doc_type_date`) · **PK**: `doc_type_id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `doc_type_id` | int | PRI | Tip dokumenta |  |
| `doc_type_name` | varchar(400) |  | Naziv dokumenta na Bosanskom jeziku |  |
| `doc_type_name_de` | varchar(400) |  | Naziv dokumenta na Njemačkom jeziku |  |
| `doc_type_date` | datetime |  | Datum unosa tipa dokumenta |  |
| `doc_type_entered_user` | int |  | Zaposlenik koji je unio tip dokumenta |  |

## `idk_pp_documents`

- **Opis**: Stores metadata, file names, status, and associated entity identifiers for documents linked to candidates, partners, and related records.
- **Redova**: 2,418 · **Period**: – · **PK**: `doc_id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `doc_id` | int | PRI |  |  |
| `doc_file_name` | varchar(512) |  | Naziv filea kako je spremljen na serveru |  |
| `doc_candidate_id` | int |  |  |  |
| `doc_nalog_id` | int |  | Dokument vrijedi za nalog_id |  |
| `doc_partner_id` | int |  | Dokument vrijedi za partner_id |  |
| `doc_visibility_status` | int |  | 0 - arhiva; 1 - nevidljiv; 2 - vidljiv |  |
| `doc_nrd_id` | int |  | foreign key iz tabele pp_nalog_required_documents |  |
| `doc_crd_id` | int |  | foreign key iz tabele pp_cand_required_documents |  |
| `doc_status` | int |  | foreign key iz tabele documents_statuses |  |

## `idk_pp_documents_status_logs`

- **Opis**: Stores audit logs tracking changes to document statuses, including the user who made the change, timestamps, and associated comments.
- **Redova**: 14,602 · **Period**: 2022-05-10 → 2025-11-20 (`dsl_date`) · **PK**: `dsl_doc_id,dsl_doc_status`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `dsl_doc_id` | int | PRI | foreign key iz tabele pp_documents |  |
| `dsl_doc_status` | int | PRI | foreign key iz tabele documents_statuses |  |
| `dsl_date` | datetime |  | vrijeme mijenjanja statusa |  |
| `dsl_user_id` | int |  | zaposlenik koji je promijenio status, FK iz tabele employees |  |
| `dsl_pp_user_id` | int |  | korisnik PP-a koji je promijenio status, FK iz tabele pp_users |  |
| `dsl_days_count` | int |  | broj dana proveden na tom statusu |  |
| `dsl_comment` | text |  | dodatni komentar (mozda nece trebati) |  |

## `idk_pp_documents_statuses`

- **Opis**: Lookup table storing document processing status definitions and their display sequence, with multilingual name labels in Bosnian/Croatian/Serbian and German.
- **Redova**: 9 · **Period**: – · **PK**: `ds_id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `ds_id` | int | PRI |  |  |
| `ds_name` | varchar(50) |  |  |  |
| `ds_name_de` | varchar(250) |  |  |  |
| `ds_name_pp` | varchar(250) |  |  |  |
| `ds_name_de_pp` | varchar(250) |  |  |  |
| `ds_order` | int |  | redoslijed statusa (ako bude potrebno) |  |

## `idk_pp_informacije_profil`

- **Opis**: Lookup table defining profile information fields and attributes, such as contact details, citizenship, and work experience, available in both Bosnian/Croatian/Serbian and German.
- **Redova**: 9 · **Period**: – · **PK**: `pip_id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `pip_id` | int | PRI |  |  |
| `pip_name` | varchar(255) |  |  |  |
| `pip_name_de` | varchar(255) |  | Naziv labela u pp-u na ispisu |  |
| `pip_status` | int |  | 1-aktivan |  |

## `idk_pp_nalog_profil`

- **Opis**: This table links orders or accounts to specific profile information records within the CRM system.
- **Redova**: 13 · **Period**: – · **PK**: `pnp_id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `pnp_id` | int | PRI |  |  |
| `pnp_nalog_id` | int | MUL | FK iz tabele nalozi |  |
| `pnp_info_id` | int | MUL | FK iz tabele idk_pp_informacije_profil |  |

## `idk_pp_nalog_required_documents`

- **Opis**: Stores records of required documents for orders or permits, tracking candidate criteria, activation and archival statuses, and processing details.
- **Redova**: 142 · **Period**: 2022-10-18 → 2025-04-23 (`nrd_date_activated`) · **PK**: `nrd_id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `nrd_id` | int | PRI | U tabeli se nalaze samo REQUIRED dokumenti |  |
| `nrd_nalog_id` | int |  | Required za nalog |  |
| `nrd_type_id` | int |  | foreign key iz tabele pp_document_types |  |
| `nrd_done_by` | int |  | ko je zaduzen za kreiranje dokumenta: 1-poslodavac, 2-kandidat, 3-mi |  |
| `nrd_status` | int |  | 1-aktivan, 2-neaktivan |  |
| `nrd_date_activated` | datetime |  | Datum aktiviranja dokumenta za nalog |  |
| `nrd_user_activated` | int |  | Korisnik koji je aktivirao dokument |  |
| `nrd_date_archived` | datetime |  | Datum arhiviranja dokumenta za nalog |  |
| `nrd_user_archived` | int |  | Korisnik koji je arhivirao dokument |  |
| `nrd_comment` | text |  | komentar koji je vezan uz dokument |  |
| `nrd_skilled_candidates` | int |  | Označava da li je dokument potreban za odlazak po sistemu stručni kadar: 0 - nije; 1 - jeste. |  |
| `nrd_west_balkan` | int |  | Označava da li je dokument potreban za odlazak po zapadno-balkansom sistemu: 0 - nije; 1 - jeste. |  |
| `nrd_work_experience` | int |  | Označava da li je dokument potreban za odlazak po sistemu radno iskustvo: 0 - nije; 1 - jeste. |  |

## `idk_pp_partners`

- **Opis**: Stores partner program participant records, including associated company and tax identifiers, candidate counts, and status information.
- **Redova**: 58 · **Period**: – · **PK**: `ppa_id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `ppa_id` | int | PRI |  |  |
| `ppa_nalog_id` | int |  | nalog_id iz tabele idk_nalozi |  |
| `ppa_company_id` | int |  | company_id iz tabele idk_companies |  |
| `ppa_status` | int |  | 0 - deaktiviran, 1 - aktivan |  |
| `ppa_number_of_candidates` | int |  | Broj potrebnih kandidata za navedenog partnera. |  |

## `idk_pp_permissions`

- **Opis**: Stores user permissions, including titles, permission types, and associated accessible menu items.
- **Redova**: 2 · **Period**: – · **PK**: `ppe_id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `ppe_id` | int | PRI |  |  |
| `ppe_type` | int |  | 1 - superadmin 2 - admin |  |
| `ppe_menu` | text |  | Za "ppe_type" = 1 (superAdmin) imamo slučajeve: 1 - obradjen, 2 - casting; Za "ppe_type" = 2 (Admin) imamo slučajeve: 1 - ceka ugovor, 2 - poslan ugovor kandidatu, 3 - potpisan ugovor, 4 - pocetak rada, 5 - zavrsen; |  |
| `ppe_title` | text |  | Ako je npr. u ppe type vrijednost 1 i u ppe_menu niz sa vrijednostima "1,2" u ovom nizu treba da se nalazi "Obrađeni,Casting" |  |

## `idk_pp_regions`

- **Opis**: Stores definitions of geographic or operational regions along with their names and status codes.
- **Redova**: 16 · **Period**: – · **PK**: `pr_id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `pr_id` | int | PRI |  |  |
| `pr_name` | varchar(255) |  |  |  |
| `pr_status` | int |  | 1-aktivan |  |

## `idk_pp_reminder_documents`

- **Opis**: Stores configuration and schedule settings for reminder documents, including frequency, creation delays, and active status.
- **Redova**: 382 · **Period**: – · **PK**: `prd_id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `prd_id` | int | PRI |  |  |
| `prd_prs_id` | int | MUL |  |  |
| `prd_nrd_id` | int | MUL |  |  |
| `prd_crd_id` | int | MUL |  |  |
| `prd_day_freq` | int |  |  |  |
| `prd_create_after` | int |  | create first reminder after x days from certain event |  |
| `prd_active` | int |  | 0-neaktivan, 1-aktivan(default) |  |

## `idk_pp_reminder_settings`

- **Opis**: Stores configuration settings for automated partner or tax reminder notifications, including triggering rules, schedule dates, and assigned recipient and controlling employee IDs.
- **Redova**: 460 · **Period**: 2022-05-03 → 2022-05-19 (`prs_first_trigger_date`) · **PK**: `prs_id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `prs_id` | int | PRI |  |  |
| `prs_nalog_id` | int |  |  |  |
| `prs_partner_id` | int |  |  |  |
| `prs_reminder_type_id` | int |  |  |  |
| `prs_pua_ids` | varchar(500) |  |  |  |
| `prs_controlling_pua_ids` | varchar(500) |  | id-evi usera koji rade kontroling |  |
| `prs_employee_ids` | varchar(50) |  |  |  |
| `prs_controlling_employee_ids` | varchar(50) |  | id-evi CRM zaposlenika zaduzenih za controlling remindera |  |
| `prs_active` | int |  | 0-neaktivan, 1-aktivan |  |
| `prs_first_trigger_date` | date |  |  |  |
| `prs_create_after` | int |  | Create first reminder after X days from certain event |  |

## `idk_pp_reminder_types`

- **Opis**: Defines configuration settings and localized notification templates for different automated reminder types, including email subjects, notification texts, and frequency intervals.
- **Redova**: 25 · **Period**: – · **PK**: `prt_id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `prt_id` | int | PRI |  |  |
| `prt_name` | varchar(100) |  |  |  |
| `prt_user_type` | int |  | 1-superadmin, 2-admin, 3-PM |  |
| `prt_day_freq` | int |  |  |  |
| `prt_controling` | int |  | 0-nema kontroling, 1-ima kontroling |  |
| `prt_mail_subject_de` | varchar(100) |  |  | [PII] |
| `prt_mail_text_de` | text |  |  | [PII] |
| `prt_notification_text_de` | text |  | Text notifikacije koji se pojavljuje userima na PP |  |
| `prt_has_documents` | int |  | 0-default nema dokumenta, 1-ima dokumente |  |

## `idk_pp_reminders`

- **Opis**: Stores records of document-related reminders sent to candidates and assigned to CRM users, tracking their assignment, completion, and status.
- **Redova**: 22,348 · **Period**: 2023-07-13 → 2026-02-26 (`pr_date_sent`) · **PK**: `pr_id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `pr_id` | int | PRI |  |  |
| `pr_reminder_setting_id` | int | MUL |  |  |
| `pr_reminder_document_id` | int | MUL |  |  |
| `pr_candidate_id` | int |  |  |  |
| `pr_level` | int |  | Kolona koja govori o kojem levelu remindera se radi za jednog kandidata i jedan tip remindera. Default: 1 - level 1; Dalje: 2 - level 2, 3 - level 3, n - level n; |  |
| `pr_date_sent` | datetime |  |  |  |
| `pr_users_sent` | varchar(500) |  |  |  |
| `pr_user_assigned` | int |  |  |  |
| `pr_done_by_crm_employee` | int |  | kolona koja sluzi za remindere namijenjene poslodavcima a izvrsi ih CRM zaposlenik |  |
| `pr_date_assigned` | datetime |  |  |  |
| `pr_date_completed` | datetime |  |  |  |
| `pr_status` | int |  | 1-poslan reminder, 2-prihvacen(dodijeljen), 3-izvrsen, 4-neizvrsen, 5-izvrsen odustankom kandidata |  |

## `idk_pp_user_access`

- **Opis**: Stores user access permissions, associating users with specific partners, access types, and permission statuses.
- **Redova**: 1,416 · **Period**: – · **PK**: `pua_id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `pua_id` | int | PRI |  |  |
| `pua_type` | int |  | 1 - superadmin 2 - admin |  |
| `pua_partner_id` | int |  | ppa_id iz tabele idk_pp_partners |  |
| `pua_nalog_id` | int |  | nalog_id iz tabele idk_nalozi |  |
| `pua_user_id` | int |  | pu_id iz tabele idk_pp_users |  |
| `pua_permission_id` | int |  | ppe_id iz tabele idk_pp_permissions |  |
| `pua_status` | int |  | 0 - deaktiviran, 1 - aktiviran |  |

## `idk_pp_users`

- **Opis**: Stores user account details, including names, login credentials, contact information, language preferences, and company affiliations for the CRM portal.
- **Redova**: 175 · **Period**: – · **PK**: `pu_id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `pu_id` | int | PRI |  |  |
| `pu_status` | int |  | 0 - deaktiviran, 1 - aktivan |  |
| `pu_fname` | varchar(100) |  |  | [PII] |
| `pu_lname` | varchar(150) |  |  | [PII] |
| `pu_email` | varchar(200) |  |  | [PII] |
| `pu_password` | varchar(250) |  |  | **[TAJNO]** |
| `pu_key` | varchar(250) |  |  | **[TAJNO]** |
| `pu_language` | int |  | 0 - BiH, 1 - DE, 2 - EN .... |  |
| `pu_gender` | varchar(7) |  | spol korisnika |  |
| `pu_company_id` | int |  | company_id iz tabele idk_companies |  |

## `idk_pp_visa_incomplete`

- **Opis**: Tracks incomplete partner visa applications, including candidate and employer receipt dates, deadlines, status, and related complaints.
- **Redova**: 49 · **Period**: 2023-01-01 → 2024-08-06 (`vi_date_we_received_employer`) · **PK**: `vi_id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `vi_id` | int | PRI |  |  |
| `vi_cand_id` | int |  |  |  |
| `vi_type` | int |  | 1 - Dopuna, 2 - Odbijenica |  |
| `vi_complaint` | int |  | 0 - default/nema uslova za zalbu ako je vi_type = 2 , 1 - ima uslova za zalbu ako je vi_type = 2 |  |
| `vi_status` | int |  | status dopune/zalbe: 0 - nije aktivna, 1 - aktivna |  |
| `vi_date_received_candidate` | datetime |  | datum prijema dopune/zalbe kandidata |  |
| `vi_date_we_received_candidate` | datetime |  | datum naseg prijema ove informacije |  |
| `vi_deadline_date_candidate` | date |  | datum roka do kad se moze poslati |  |
| `vi_date_received_employer` | datetime |  | datum prijema dopune/zalbe poslodavca |  |
| `vi_date_we_received_employer` | datetime |  | datum naseg prijema ove informacije |  |
| `vi_deadline_date_employer` | date |  | datum roka do kad se moze poslati |  |
| `vi_nalog_id` | int |  |  |  |
| `vi_pp_partner_id` | int |  |  |  |

