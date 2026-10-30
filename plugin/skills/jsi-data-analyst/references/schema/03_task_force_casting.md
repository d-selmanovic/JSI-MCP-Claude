# Task force, casting, intervjui

Tabele: 19. Redovi i periodi stanje 2026-10-29.

## `idk_agenti_activity`

- **Opis**: Records the start, end, duration, and status of activities or work sessions performed by agents or employees.
- **Redova**: 7,848 · **Period**: 2021-12-02 → 2026-02-23 (`activity_pocetak`) · **PK**: `id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `id` | int | PRI |  |  |
| `employee_id` | int |  | agentov id |  |
| `activity_status` | int |  | 0 - idle / 1 - pauza / 2 - live / 3 - viber / 4 - obuka / 5. inbound |  |
| `activity_pocetak` | datetime |  |  |  |
| `activity_kraj` | datetime |  |  |  |
| `activity_ukupno` | time |  |  |  |
| `activity_aktivan` | int |  |  |  |

## `idk_appointment_invite_links`

- **Opis**: Stores invitation links sent to candidates for appointment or interview scheduling, along with tracking metrics such as sent dates, open status, confirmation status, and link state.
- **Redova**: 4,570 · **Period**: 2023-03-31 → 2024-09-18 (`date_sent`) · **PK**: `id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `id` | int | PRI |  |  |
| `candidate_id` | int |  |  |  |
| `interview_id` | int | MUL | pca_id iz idk_cand_appts |  |
| `link_status` | int |  | 1 - poslano, 2 - otvoreno, 3 - potvrđeno, 0 - arhivirano |  |
| `date_sent` | datetime |  | Datum slanja / DOE |  |
| `date_open` | datetime |  | Datum otvaranja linka od strane kandidata |  |
| `date_confirmed` | datetime |  | Datum prihvatanja |  |
| `date_archived` | datetime |  | Datum arhiviranja |  |
| `send_key` | varchar(50) |  | Generisan ključ (md5(id+date_sent)) | **[TAJNO]** |
| `sent_days_before` | int |  | Vrijeme termina - Trenutno vrijeme = sent_days_before |  |
| `counter_sent` | int |  | 1 - prvo slanje; 2 - drugo slanje; n - n slanje |  |

## `idk_nedostupan_log`

- **Opis**: Logs instances and counts of unavailable contact attempts made by agents to candidates for specific orders, along with the resulting status and timestamp.
- **Redova**: 10,122 · **Period**: 2024-02-19 → 2026-01-06 (`doe`) · **PK**: `id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `id` | int | PRI |  |  |
| `kandidat` | int |  |  |  |
| `nalog` | int |  |  |  |
| `agent` | int |  |  |  |
| `brojac` | int |  |  |  |
| `status` | int |  | 1-aktivan, 0-neaktivan |  |
| `doe` | timestamp |  |  |  |

## `idk_pp_appointment_groups`

- **Opis**: Stores appointment group definitions, including their names, associated date ranges, order identifiers, and automation status flags for casting and interviews.
- **Redova**: 92 · **Period**: 2022-03-11 → 2026-07-01 (`ppaq_start_date`) · **PK**: `ppaq_id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `ppaq_id` | int | PRI |  |  |
| `ppaq_start_date` | date |  |  |  |
| `ppaq_end_date` | date |  |  |  |
| `ppaq_casting_cron_executed` | tinyint(1) |  | 0 - Nije izvršen cron za casting 1 - izvršen cron za casting |  |
| `ppaq_interview_cron_executed` | tinyint(1) |  | 0 - Nije izvršen cron za interview 1 - izvršen cron za inteview |  |
| `papq_name` | varchar(200) |  |  |  |
| `papq_name_de` | varchar(200) |  |  |  |
| `papq_nalog_id` | varchar(7) |  |  |  |

## `idk_pp_appointment_hours`

- **Opis**: Stores scheduled appointment times and associated employee details within the CRM system.
- **Redova**: 199 · **Period**: 2023-05-22 → 2026-01-06 (`pah_doe`) · **PK**: `pah_id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `pah_id` | int | PRI |  |  |
| `pah_time` | time |  | Vrijeme satnice | [PII] |
| `pah_employee_id` | int |  | Zaposlenik koji je dodao |  |
| `pah_doe` | timestamp |  | Trenutak dodavanja |  |
| `pap_id` | int |  | FK na tabelu idk_pp_appointments |  |

## `idk_pp_appointments`

- **Opis**: Stores scheduled appointment details, including dates, locations, associated groups, and notification dispatch settings.
- **Redova**: 172 · **Period**: 2022-03-11 → 2026-07-01 (`pap_date`) · **PK**: `pap_id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `pap_id` | int | PRI |  |  |
| `pap_date` | date |  |  |  |
| `pap_nalog_id` | int | MUL |  |  |
| `pap_city` | varchar(100) |  | Grad u kojem se održava casting |  |
| `pap_location_name` | text |  | Naziv lokacije (NPR: hotel Opal) |  |
| `pap_google_maps_location` | text |  | Google maps link za lokaciju održavanja castinga |  |
| `pap_first_sending_number_days` | int |  | Broj dana prije za prvo slanje |  |
| `pap_second_sending_number_days` | int |  | Broj dana prije za drugo slanje |  |
| `pap_first_send_enabled` | int |  | Omogućeno prvo slanje: 0 - NE; 1 - DA; |  |
| `pap_second_send_enabled` | int |  | Omogućeno drugo slanje: 0 - NE; 1 - DA; |  |
| `pap_group_id` | varchar(7) |  |  |  |

## `idk_pp_appointments_questions`

- **Opis**: This table links appointments to specific questions, defining the display or processing order of questions associated with each appointment.
- **Redova**: 1,230 · **Period**: – · **PK**: `papq_id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `papq_id` | int | PRI |  |  |
| `papq_question_id` | int | MUL |  |  |
| `papq_appointment_id` | int | MUL |  |  |
| `papq_order` | int |  | Redoslijed |  |

## `idk_pp_cand_appts`

- **Opis**: Stores candidate appointment and interview records, including ratings, interviewer comments, recommendations, and status updates.
- **Redova**: 6,808 · **Period**: – · **PK**: `pca_id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `pca_id` | int | PRI |  |  |
| `pca_appointment_id` | int |  |  |  |
| `pca_kandidat_id` | int | MUL |  |  |
| `pca_time` | time |  |  | [PII] |
| `pca_avg_rating` | double |  |  |  |
| `pca_comment` | text |  |  |  |
| `pca_interviewer` | text |  | User koji je ocjenio kandidata |  |
| `pca_recommendation` | int |  | Preporuka: 1 - Hire, 2 - Reject, 3 - Not sure |  |
| `pca_reason_recommendation` | text |  |  |  |
| `pca_status` | int | MUL | 0 - neaktivan(kandidat je zavrsio sa intervjuem, ili je prihvacen ili odbijen ili nije dosao na intervju); 1 - aktivan intervju |  |
| `pca_pah_id` | int |  |  |  |

## `idk_pp_question_categories`

- **Opis**: Stores question categories with their identifiers and names in English and German.
- **Redova**: 15 · **Period**: – · **PK**: `pqc_id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `pqc_id` | int | PRI |  |  |
| `pqc_name` | text |  |  |  |
| `pqc_name_de` | text |  |  |  |

## `idk_pp_question_options`

- **Opis**: Stores answer choices and their multilingual text and subtext for specific survey or assessment questions.
- **Redova**: 17 · **Period**: – · **PK**: `pqo_id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `pqo_id` | int | PRI |  |  |
| `pqo_question_id` | int |  | pqu_id iz tabele idk_pp_questions |  |
| `pqo_value` | int |  | value koji se pojavi u select |  |
| `pqo_value_text` | text |  |  |  |
| `pqo_value_text_de` | text |  |  |  |
| `pqo_value_subtext` | text |  |  |  |
| `pqo_value_subtext_de` | text |  |  |  |

## `idk_pp_questions`

- **Opis**: Stores survey or evaluation questions along with their categories, display order, associated users, and supported response formats such as text, dropdowns, or ratings.
- **Redova**: 282 · **Period**: – · **PK**: `pqu_id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `pqu_id` | int | PRI |  |  |
| `pqu_question` | text |  |  |  |
| `pqu_nalog_id` | int |  |  |  |
| `pqu_user_id` | int |  |  |  |
| `pqu_category_id` | int |  | NULL - nema kategorije X - (x>0) pqc_id iz tabele idk_pp_question_categories |  |
| `pqu_has_text` | int |  | Kolona koja oznacava da li ce pitanje na frontendu imati polje za unos teksta |  |
| `pqu_has_rating` | int |  | Kolona koja oznacava da li ce pitanje na frontendu imati polje za unos ocjene |  |
| `pqu_has_dropdown` | int |  | Kolona koja oznacava da li ce pitanje na frontendu imati polje sa padajucim izbornikom |  |
| `pqu_export_order` | int |  | Redoslijed samo za export pitanja |  |

## `idk_pp_ratings`

- **Opis**: Stores candidate ratings, selected option values, and feedback comments linked to specific appointment questions.
- **Redova**: 27,221 · **Period**: – · **PK**: `pra_id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `pra_id` | int | PRI |  |  |
| `pra_rating` | int |  |  |  |
| `pra_comment` | text |  |  |  |
| `pra_options_value` | int |  |  |  |
| `pra_appointment_question_id` | int |  |  |  |
| `pra_kandidat_id` | int |  |  |  |

## `idk_task_force`

- **Opis**: Records task force assignments and communications tracking candidate engagement across projects, castings, and work orders, including status, appointments, and interaction notes.
- **Redova**: 452,568 · **Period**: 2023-03-08 → 2026-02-25 (`tf_doe`) · **PK**: `tf_id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `tf_id` | int | PRI |  |  |
| `tf_candidate_id` | int | MUL |  |  |
| `tf_agent_id` | int | MUL | Nekad task moze kreirati cron ili sistem automatski, a to pratimo sa NULL u ovoj koloni |  |
| `tf_nalog_id` | int | MUL |  |  |
| `tf_project_id` | int | MUL |  |  |
| `tf_casting_id` | int | MUL | ID iz grupe termina |  |
| `tf_status_id` | int | MUL |  |  |
| `tf_call_appointment` | datetime |  |  |  |
| `tf_note` | text |  |  |  |
| `tf_important_note` | int |  | 0 - ne, 1 - da |  |
| `tf_last_active_task` | int | MUL | 0 - nije, 1 - jeste |  |
| `tf_brojac_neuspjela_komunikacija` | int |  |  |  |
| `tf_files` | text |  | Sprema se naziv priloga dodanog na biljesku. Fileovi se nalaze na putanji: files/prilozi_kandidati |  |
| `tf_doe` | datetime |  |  |  |
| `tf_vrsta_id` | int | MUL | FK iz tabele idk_tf_vrste |  |

## `idk_tf_agent_nalog`

- **Opis**: Stores associations linking agents to specific orders or tasks, categorized by order type.
- **Redova**: 23 · **Period**: – · **PK**: `tfan_id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `tfan_id` | int | PRI |  |  |
| `tfan_nalog` | int | MUL |  |  |
| `tfan_agent` | int | MUL |  |  |
| `tfan_vrsta_id` | int | MUL | FK iz tabele idk_tf_vrste |  |

## `idk_tf_reservations`

- **Opis**: Stores reservation records linking candidates and agents to projects, categories, order assignments, and qualifications.
- **Redova**: 0 · **Period**: – · **PK**: `tf_kandidat_id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `tf_kandidat_id` | int | PRI |  |  |
| `tf_agent_id` | int |  |  |  |
| `tf_projekt_id` | int |  |  |  |
| `tf_nalog_id` | int |  |  |  |
| `tf_vrsta_id` | int |  | FK iz tabele idk_tf_vrste |  |
| `tf_dipl_id` | int |  |  |  |
| `tf_category_id` | int |  |  |  |

## `idk_tf_stats_reservations`

- **Opis**: Stores tracking statistics and reservation records for candidate interviews, linking candidates, agents, assignments, and statuses.
- **Redova**: 3,852 · **Period**: – · **PK**: `tsr_id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `tsr_id` | int | PRI |  |  |
| `tsr_candidate_id` | int | MUL |  |  |
| `tsr_agent_id` | int | MUL |  |  |
| `tsr_interview_id` | int | MUL | ID grupe castinga |  |
| `tsr_nalog_id` | int | MUL |  |  |
| `tsr_link_id` | int | MUL | Id linka sa kojeg se kandidat zadnji put prijavio prije ulaska u ovu tabelu |  |
| `tsr_status` | int | MUL | Došao=1, Nije došao=2, Odustao=3 |  |

## `idk_tf_statusi`

- **Opis**: Stores lookup definitions and attributes for tracking and filtering statuses, including interview requirements, display order, and positive outcome flags.
- **Redova**: 136 · **Period**: – · **PK**: `tfs_id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `tfs_id` | int | PRI |  |  |
| `tfs_name` | varchar(255) |  |  |  |
| `tfs_is_positive` | int |  | 0 - oznacava da je status negativan, tj da kandidat ispada iz taskova;  1 - status pozitivan, kandidat nastavlja proces kroz taskove |  |
| `tfs_has_interview` | int |  | 0-nema intervju, 1-ima intervju |  |
| `tfs_appointment` | int |  | 1 - Oznacava da je potrebno unijeti termin za zvanje;  0 - ne treba unositi termin |  |
| `tfs_order` | int |  |  |  |
| `tfs_status_prijave` | int |  | Oznacava na koji status prijave vodimo kandidata nakon odabira taska.  Default je NULL sto znaci da mu se ne mijenja status prijave. |  |
| `tfs_vrsta_id` | int | MUL | FK iz tabele idk_tf_vrste |  |

## `idk_tf_transfered_candidates_logs`

- **Opis**: Logs details of candidate transfers to destination projects, including the employee who performed the transfer and the transfer timestamp.
- **Redova**: 725 · **Period**: 2023-03-24 → 2026-02-16 (`tcl_doe`) · **PK**: `tcl_id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `tcl_id` | int | PRI |  |  |
| `tcl_transfered_candidates` | mediumtext |  |  |  |
| `tcl_destination_project_id` | int |  |  |  |
| `tcl_doe` | datetime |  |  |  |
| `tcl_employee_id` | int |  |  |  |

## `idk_tf_vrste`

- **Opis**: Stores categories or types of items, including their names, associated category identifiers, and status flags.
- **Redova**: 28 · **Period**: – · **PK**: `id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `id` | int | PRI |  |  |
| `name` | varchar(255) |  |  |  |
| `status` | int |  | 1-aktivan |  |
| `category` | int |  | 1-casting, 2-posredovanje, 3-obrada |  |

