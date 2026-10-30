# Interno: zaposlenici, timovi, tiketi, skladište, postavke

Tabele: 27. Redovi i periodi stanje 2026-10-29.

## `idk_analitika`

- **Opis**: Stores analytical tracking records including timestamps, ratings, and unique analytics identifiers.
- **Redova**: 1,418 · **Period**: 2020-03-09 → 2024-01-22 (`analitika_datum`) · **PK**: `analizika_id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `analizika_id` | int | PRI |  |  |
| `analitika_rating` | int |  |  |  |
| `analitika_datum` | datetime |  |  |  |

## `idk_api_clients`

- **Opis**: Stores registered API clients and their authentication tokens for system access.
- **Redova**: 3 · **Period**: – · **PK**: `client_id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `client_id` | int | PRI |  |  |
| `client_name` | varchar(525) |  |  |  |
| `client_token` | varchar(525) |  |  | **[TAJNO]** |

## `idk_employees`

- **Opis**: Stores employee personal profiles, system and telephony credentials, organizational assignments, and commission factors for the CRM system.
- **Redova**: 370 · **Period**: 2014-08-01 → 2025-06-23 (`employee_doe`) · **PK**: `employee_id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `employee_id` | int | PRI |  |  |
| `employee_firstname` | varchar(150) |  |  | [PII] |
| `employee_lastname` | varchar(150) |  |  | [PII] |
| `employee_email` | varchar(250) |  |  | [PII] |
| `employee_password` | varchar(250) |  |  | **[TAJNO]** |
| `employee_key` | varchar(150) |  |  | **[TAJNO]** |
| `employee_color` | varchar(10) |  |  |  |
| `employee_jmbg` | bigint |  |  | **[TAJNO]** |
| `employee_rfid` | varchar(50) |  |  | **[TAJNO]** |
| `employee_position` | varchar(150) |  |  |  |
| `employee_dob` | date |  |  | [PII] |
| `employee_doe` | date |  |  |  |
| `employee_address` | text |  |  | [PII] |
| `employee_city` | varchar(150) |  |  |  |
| `employee_country` | varchar(150) |  |  |  |
| `employee_info` | text |  |  |  |
| `employee_inote` | text |  |  |  |
| `employee_image` | varchar(150) |  |  |  |
| `employee_status` | varchar(255) |  |  |  |
| `employee_supervizor` | varchar(255) |  |  |  |
| `employee_dlanguage` | varchar(50) |  |  |  |
| `employee_phone` | varchar(250) |  |  | [PII] |
| `employee_warehouse` | int |  |  |  |
| `employee_odjel` | int |  |  |  |
| `employee_poslovnica` | int |  |  |  |
| `employee_nostrifikacija_diploma` | int |  |  |  |
| `employee_nostrifikacija_zadnji_menadzer` | int |  |  |  |
| `employee_nostrifikacija_zadnji_menadzer_app` | int |  |  |  |
| `employee_faktor_provizije_bih` | double |  |  |  |
| `employee_faktor_provizije_srb` | double |  |  |  |
| `employee_faktor_za_timove` | double |  |  |  |
| `employee_team` | int |  | id_t iz tabele idk_timovi |  |
| `employee_viciuser` | varchar(150) |  |  | **[TAJNO]** |
| `employee_vicipass` | varchar(150) |  |  | **[TAJNO]** |
| `employee_reset_password` | int |  | 1-needs reset |  |
| `employee_last_password_change` | datetime |  |  |  |
| `employee_reset_token` | varchar(255) |  |  | **[TAJNO]** |
| `employee_reset_token_doe` | datetime |  |  |  |
| `employee_dvag` | int |  | 1 - employee can call DVAG candidates |  |
| `employee_makler_representative_status` | int |  | 0 - User ne može biti representative za maklera; 1 - Employee može biti representative za nekog maklera; 2 - Employee je defaultni representative za nekog maklera; |  |

## `idk_employees_info`

- **Opis**: Stores supplementary employee details, attributes, and grouped profile data categorized by title.
- **Redova**: 93 · **Period**: – · **PK**: `ei_id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `ei_id` | int | PRI |  |  |
| `ei_group` | int |  |  |  |
| `ei_title` | varchar(150) |  |  |  |
| `ei_data` | varchar(250) |  |  |  |
| `ei_primary` | int |  |  |  |
| `ei_employeeid` | int |  |  |  |

## `idk_employees_reports`

- **Opis**: Records individual work reports and time logs submitted by employees, detailing the date, time spent, project, and status of tasks performed.
- **Redova**: 1,296 · **Period**: 2019-08-15 → 2023-01-09 (`er_date`) · **PK**: `er_id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `er_id` | int | PRI |  |  |
| `er_date` | date |  |  |  |
| `er_title` | varchar(250) |  |  |  |
| `er_timefrom` | time |  |  | [PII] |
| `er_timeto` | time |  |  | [PII] |
| `er_projectid` | int |  |  |  |
| `er_nalogid` | int |  |  |  |
| `er_employeeid` | int |  |  |  |
| `er_status` | int |  |  |  |

## `idk_ipwhitelist`

- **Opis**: Stores whitelisted IP addresses along with associated user details, justification reasons, status, timestamps, and who added them.
- **Redova**: 10 · **Period**: 2019-02-07 → 2020-05-14 (`ipwl_datetime`) · **PK**: `ipwl_id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `ipwl_id` | int | PRI |  |  |
| `ipwl_user` | varchar(255) |  |  |  |
| `ipwl_ip` | varchar(100) |  |  | [PII] |
| `ipwl_added_by` | varchar(100) |  |  |  |
| `ipwl_reason` | varchar(250) |  |  |  |
| `ipwl_status` | int |  |  |  |
| `ipwl_datetime` | datetime |  |  | [PII] |

## `idk_kategorije`

- **Opis**: Stores category names and their corresponding identifiers for organizing various CRM processes, documents, or tickets.
- **Redova**: 5 · **Period**: – · **PK**: `kategorija_id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `kategorija_id` | int | PRI |  |  |
| `kategorija_naziv` | text |  |  |  |

## `idk_korisni_dokumenti`

- **Opis**: Stores useful reference documents and files uploaded by employees, including file paths, descriptions, document types, and upload timestamps.
- **Redova**: 14 · **Period**: 2019-09-06 → 2020-10-08 (`kd_datetime`) · **PK**: `kd_id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `kd_id` | int | PRI |  |  |
| `kd_naziv` | varchar(150) |  |  |  |
| `kd_detaljni_opis` | text |  |  |  |
| `kd_file` | varchar(150) |  |  |  |
| `kd_icon` | varchar(5) |  |  |  |
| `kd_datetime` | datetime |  |  | [PII] |
| `kd_employee_id` | int |  |  |  |
| `kd_status` | int |  |  |  |

## `idk_korisni_linkovi`

- **Opis**: Stores a curated list of useful external web links, including their URLs, descriptions, publication status, and the employees who added them.
- **Redova**: 5 · **Period**: 2019-09-06 → 2020-04-07 (`kl_datetime`) · **PK**: `kl_id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `kl_id` | int | PRI |  |  |
| `kl_naziv` | text |  |  |  |
| `kl_detaljni_opis` | text |  |  |  |
| `kl_link` | text |  |  |  |
| `kl_datetime` | datetime |  |  | [PII] |
| `kl_employee_id` | int |  |  |  |
| `kl_status` | int |  |  |  |

## `idk_messages`

- **Opis**: Stores records of sent messages, including their subject, text content, delivery status, timestamp, and associated identifiers.
- **Redova**: 41 · **Period**: 2018-04-17 → 2023-02-22 (`message_datetime`) · **PK**: `message_id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `message_id` | int | PRI |  |  |
| `message_subject` | varchar(150) |  |  |  |
| `message_text` | text |  |  |  |
| `message_sentid` | int |  |  |  |
| `message_status` | int |  |  |  |
| `message_datetime` | datetime |  |  | [PII] |

## `idk_messages_users`

- **Opis**: Tracks the delivery and read status of messages associated with specific employees.
- **Redova**: 41 · **Period**: – · **PK**: `mu_id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `mu_id` | int | PRI |  |  |
| `mu_messageid` | int |  |  |  |
| `mu_employeeid` | int |  |  |  |
| `mu_status` | int |  |  |  |

## `idk_module_permissions`

- **Opis**: Stores access permissions for system modules by mapping module names to comma-separated lists of authorized employee IDs.
- **Redova**: 8 · **Period**: – · **PK**: `mp_id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `mp_id` | int | PRI |  |  |
| `mp_name` | varchar(255) |  |  |  |
| `mp_employees` | varchar(255) |  |  |  |

## `idk_modules`

- **Opis**: Stores information about application CRM modules, including their names, descriptions, and active status.
- **Redova**: 2 · **Period**: – · **PK**: `module_id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `module_id` | int | PRI |  |  |
| `module_name` | varchar(150) |  |  |  |
| `module_status` | int |  |  |  |
| `module_desc` | text |  |  |  |

## `idk_notifications`

- **Opis**: Stores user notifications and alerts for employees, including notification status, titles, timestamps, and associated links.
- **Redova**: 1,759 · **Period**: 2018-04-13 → 2023-04-28 (`notification_datetime`) · **PK**: `notification_id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `notification_id` | int | PRI |  |  |
| `notification_datetime` | datetime |  |  | [PII] |
| `notification_title` | varchar(250) |  |  |  |
| `notification_icon` | varchar(150) |  |  |  |
| `notification_link` | varchar(250) |  |  |  |
| `notification_employeeid` | int |  |  |  |
| `notification_status` | int |  |  |  |

## `idk_otherdata`

- **Opis**: Stores miscellaneous grouped string data entries identified by group and entry IDs.
- **Redova**: 22 · **Period**: – · **PK**: `otherdata_id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `otherdata_id` | int | PRI |  |  |
| `otherdata_data` | varchar(150) |  |  |  |
| `otherdata_group` | int |  |  |  |

## `idk_poslovnice`

- **Opis**: Stores information about company branch offices, including their unique identifiers, names, cities, and countries.
- **Redova**: 14 · **Period**: – · **PK**: `branch_id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `branch_id` | int | PRI |  |  |
| `branch_name` | varchar(150) |  |  |  |
| `branch_state` | varchar(150) |  |  |  |
| `branch_city` | varchar(150) |  |  |  |

## `idk_pushnotifications`

- **Opis**: Records push notifications sent to employees regarding specific orders or tasks, including timestamps and notification identifiers.
- **Redova**: 22 · **Period**: 2020-05-13 → 2021-07-27 (`pushnot_datetime`) · **PK**: `pushnot_id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `pushnot_id` | int | PRI |  |  |
| `pushnot_datetime` | datetime |  |  | [PII] |
| `pushnot_nalogid` | int |  |  |  |
| `pushnot_employeeid` | int |  |  |  |

## `idk_settings`

- **Opis**: Stores system-wide CRM configuration settings and parameters, including application URLs, names, storage limits, and security options.
- **Redova**: 5 · **Period**: – · **PK**: `settings_id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `settings_id` | int | PRI |  |  |
| `settings_name` | varchar(50) |  |  |  |
| `settings_title` | varchar(100) |  |  |  |
| `settings_value` | text |  |  |  |
| `settings_group` | int |  |  |  |

## `idk_skladiste`

- **Opis**: Stores warehouse and inventory item records, including category, availability, purchase date, branch location, and descriptions.
- **Redova**: 305 · **Period**: 2019-12-02 → 2023-03-23 (`skl_datum_nabavke`) · **PK**: `skl_id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `skl_id` | int | PRI |  |  |
| `skl_branch` | int |  |  |  |
| `skl_title` | varchar(250) |  |  |  |
| `skl_desc` | text |  |  |  |
| `skl_image` | varchar(250) |  |  |  |
| `skl_available` | int |  |  |  |
| `skl_archive` | int |  |  |  |
| `skl_kategorija` | int |  |  |  |
| `skl_datum_nabavke` | date |  |  |  |

## `idk_skladiste_kategorije`

- **Opis**: Stores warehouse or inventory category identifiers and their corresponding category names.
- **Redova**: 19 · **Period**: – · **PK**: `isk_id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `isk_id` | int | PRI |  |  |
| `isk_naziv_kategorije` | varchar(50) |  |  |  |

## `idk_skladiste_product`

- **Opis**: Stores warehouse inventory records for individual products, tracking serial numbers, inventory status, and reasons for product discharge or rejection.
- **Redova**: 471 · **Period**: – · **PK**: `isp_id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `isp_id` | int | PRI |  |  |
| `isp_skl_id` | int |  |  |  |
| `isp_serijski_broj` | varchar(150) |  |  |  |
| `isp_dodatni_info` | text |  |  |  |
| `isp_razlozi_odbijanja` | text |  |  |  |
| `isp_razlozi_razduzivanja` | text |  |  |  |
| `isp_archive` | int |  |  |  |
| `isp_inventar` | int |  | 0 - neinventarno, 1 - inventarno |  |

## `idk_skladiste_zaposlenici`

- **Opis**: Records warehouse inventory items and equipment assigned to or used by specific employees, including product details, quantities, locations, and assignment descriptions.
- **Redova**: 296 · **Period**: – · **PK**: `isz_id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `isz_id` | int | PRI |  |  |
| `isz_sklid` | int |  |  |  |
| `sz_employeeid` | int |  |  |  |
| `sz_quantity` | int |  |  |  |
| `sz_branch` | int |  |  |  |
| `sz_opis` | varchar(250) |  |  |  |
| `isz_status` | int |  |  |  |
| `isz_product_id` | int |  |  |  |

## `idk_tasks`

- **Opis**: Stores CRM task records, including task descriptions, due dates, statuses, assigned employees, and notification settings.
- **Redova**: 873 · **Period**: 2018-04-25 → 2023-04-28 (`task_datetime`) · **PK**: `task_id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `task_id` | int | PRI |  |  |
| `task_txt` | text |  |  |  |
| `task_replytxt` | text |  |  |  |
| `task_duedatetime` | datetime |  |  | [PII] |
| `task_assignedid` | int |  |  |  |
| `task_emailnotifi` | int |  |  | [PII] |
| `task_repeatnotifi` | int |  |  |  |
| `task_group` | int |  |  |  |
| `task_dataid` | int |  |  |  |
| `task_employeeid` | int |  |  |  |
| `task_datetime` | datetime |  |  | [PII] |
| `task_status` | int |  |  |  |

## `idk_ticketi`

- **Opis**: Stores support or internal service tickets, including sender and recipient details, priority, status, subject, description, timestamps, and attached documents.
- **Redova**: 252 · **Period**: 2019-10-30 → 2023-12-15 (`ticket_vrijeme_kreiranja`) · **PK**: `ticket_id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `ticket_id` | int | PRI |  |  |
| `ticket_status` | int |  |  |  |
| `ticket_predmet` | varchar(255) |  |  |  |
| `ticket_opis` | text |  |  |  |
| `ticket_hitnost` | int |  |  |  |
| `ticket_posiljaoc` | int |  |  |  |
| `ticket_primatelj` | int |  |  |  |
| `ticket_primatelj_odjel` | int |  |  |  |
| `ticket_vrijeme_kreiranja` | datetime |  |  |  |
| `ticket_vrijeme_prihvatanja` | datetime |  |  |  |
| `ticket_vrijeme_zavrsetka` | datetime |  |  |  |
| `ticket_dokument` | varchar(255) |  |  |  |

## `idk_ticketi_komentari`

- **Opis**: Stores user comments and responses associated with support tickets, including message content, sender information, timestamps, and attached documents.
- **Redova**: 213 · **Period**: 2019-10-30 → 2023-12-14 (`ticket_k_vrijeme_kreiranja`) · **PK**: `ticket_k_id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `ticket_k_id` | int | PRI |  |  |
| `ticket_k_id_tiketa` | int |  |  |  |
| `ticket_k_posiljaoc` | int |  |  |  |
| `ticket_k_sadrzaj` | text |  |  |  |
| `ticket_k_dokument` | varchar(50) |  |  |  |
| `ticket_k_vrijeme_kreiranja` | datetime |  |  |  |

## `idk_timovi`

- **Opis**: This table stores information about organizational teams, including their full and abbreviated names, assigned display colors, status, and registration dates.
- **Redova**: 6 · **Period**: 2021-01-07 → 2022-05-10 (`datum_reg_t`) · **PK**: `id_t`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `id_t` | int | PRI | id tima |  |
| `naziv_t` | varchar(200) |  | naziv tima |  |
| `skraceni_naziv_t` | varchar(20) |  |  |  |
| `boja_t` | varchar(20) |  |  |  |
| `datum_reg_t` | datetime |  | datum registracije |  |
| `status_t` | int |  | 0 - nije aktivan 1 - aktivan |  |

## `idk_tutorijali`

- **Opis**: Stores tutorial records, including their descriptions, category associations, document attachments, and YouTube video URLs.
- **Redova**: 13 · **Period**: – · **PK**: `tutorijal_id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `tutorijal_id` | int | PRI |  |  |
| `tutorijal_kategorija_id` | int | MUL |  |  |
| `tutorijal_yt_url` | text |  |  |  |
| `tutorijal_doc` | text |  |  |  |
| `tutorijal_opis` | text |  |  |  |

