# JobStep partner app – makleri/preporučitelji

Tabele: 12. Redovi i periodi stanje 2026-10-29.

## `idk_jobstep_partners`

- **Opis**: Stores user profiles, contact details, authentication credentials, and banking information for Jobstep partners and brokers.
- **Redova**: 34,396 · **Period**: 2020-01-31 → 2024-09-10 (`jp_register_date`) · **PK**: `jp_id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `jp_id` | int | PRI |  |  |
| `jp_imeprezime` | varchar(255) |  |  | [PII] |
| `jp_ime` | varchar(255) |  |  | [PII] |
| `jp_prezime` | varchar(255) |  |  | [PII] |
| `jp_email` | varchar(255) |  |  | [PII] |
| `jp_password` | varchar(255) |  |  | **[TAJNO]** |
| `jp_lang` | varchar(255) |  |  |  |
| `jp_posta` | int |  |  |  |
| `jp_racun` | int |  |  |  |
| `jp_iban` | varchar(255) |  |  | **[TAJNO]** |
| `jp_swift` | varchar(255) |  |  | **[TAJNO]** |
| `jp_placanjeimeprezime` | varchar(255) |  |  | [PII] |
| `jp_brtelefona` | varchar(255) |  |  | [PII] |
| `jp_drzava` | varchar(255) |  |  |  |
| `jp_grad` | varchar(255) |  |  |  |
| `jp_postanskibroj` | int |  |  |  |
| `jp_ulica` | varchar(255) |  |  | [PII] |
| `jp_provider` | varchar(255) |  |  |  |
| `jp_register_date` | datetime |  |  |  |
| `jp_fcmtoken` | varchar(550) |  |  | **[TAJNO]** |
| `jp_mailconfirmation_token` | varchar(255) |  |  | **[TAJNO]** |
| `jp_confirmedaccount` | int |  | 0 - nije , 1 - prihvacen, 2 - deactivated |  |
| `jp_position` | int |  | 1 - junior partner , 2 - partner , 3 - senior partner, 4- agency, 5 - lilium super |  |
| `jp_socialid` | text |  | social network id | **[TAJNO]** |
| `jp_social_token` | text |  |  | **[TAJNO]** |
| `jp_social_imgurl` | text |  |  |  |
| `jp_preporuka_id` | int |  |  |  |
| `jp_source` | int |  | 0 - klijent self-register / 1 - system register |  |
| `jp_user_type` | int |  | 0 - stari useri partner app-a, 1 - novi useri partner app-a |  |
| `jp_user_permission` | int |  | 1 - makler, 2 - supervizor |  |
| `jp_partner_company` | int |  | id iz tabele idk_partner_companies |  |
| `jp_makler_id` | varchar(255) |  |  |  |
| `jp_direction_number` | varchar(255) |  |  |  |
| `jp_region_de` | varchar(255) |  | Region partnera za njemacku, opcije su Bayern Nordrhein-Westfalen Baden-Württemberg Niedersachsen Hessen Sachsen Rheinland-Pfalz Brandenburg Schleswig-Holstein Thüringen Sachsen-Anhalt Mecklenburg-Vorpommern Saarland Hamburg Berlin Bremen |  |
| `jp_spoken_languages` | text |  |  |  |
| `jp_received_last_lead` | int |  |  |  |
| `jp_last_password_reset` | timestamp |  |  |  |
| `jp_makler_broj_direkcije` | varchar(10) |  |  |  |
| `jp_representative_employee_id` | int |  |  |  |
| `jp_latest_login` | datetime |  |  |  |
| `jp_first_login` | datetime |  |  |  |
| `jp_datum_deaktivacije` | datetime |  |  |  |
| `jp_latest_activity` | datetime |  |  |  |
| `jp_tutorial_sent` | varchar(200) |  |  |  |
| `jp_password_reset_code` | varchar(255) |  |  | **[TAJNO]** |
| `jp_password_reset_datetime` | timestamp |  |  | [PII] |
| `jp_password_reset_tries` | int |  |  |  |
| `jp_device` | varchar(255) |  |  |  |
| `jp_app_version` | varchar(255) |  |  |  |

## `idk_jobstep_partners_pregledi`

- **Opis**: Records the count of examinations or reviews associated with specific partners and orders within the JobStep workflow.
- **Redova**: 1,022 · **Period**: – · **PK**: `jpp_id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `jpp_id` | int | PRI |  |  |
| `jpp_partnerid` | varchar(255) |  |  |  |
| `jpp_nalogid` | int |  |  |  |
| `jpp_pregledi_count` | int |  |  |  |

## `idk_partner_companies`

- **Opis**: Stores information about partner companies, including their names, branding logos, and primary color schemes.
- **Redova**: 5 · **Period**: – · **PK**: `pc_id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `pc_id` | int | PRI |  |  |
| `pc_name` | varchar(255) |  |  |  |
| `pc_primary_color` | json |  |  |  |
| `pc_logo` | varchar(255) |  |  |  |

## `idk_partner_notification`

- **Opis**: Stores records of notifications sent to partners, including their content, payload, target audience, delivery timestamps, and associated navigation actions.
- **Redova**: 37 · **Period**: 2024-03-19 → 2024-10-14 (`notification_created_at`) · **PK**: `notification_id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `notification_id` | int | PRI |  |  |
| `notification_type_id` | int |  |  |  |
| `notification_audience` | varchar(255) |  | PERSONAL, ALL, DVAG |  |
| `notification_payload` | text |  |  |  |
| `notification_sent_at` | datetime |  |  |  |
| `notification_created_at` | datetime |  |  |  |
| `notification_title` | text |  |  |  |
| `notification_content` | text |  |  |  |
| `notification_partner_id` | int |  |  |  |
| `notification_action` | varchar(255) |  | NAVIGATE_TO_JOB, NAVIGATE_TO_CANDIDATE,NAVIGATE_TO_COMPANY |  |

## `idk_partner_notification_logs`

- **Opis**: Logs partner notifications sent to employees, recording the creation timestamp along with the message title and content in English and German.
- **Redova**: 9 · **Period**: 2024-03-19 → 2024-06-19 (`created_at`) · **PK**: `id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `id` | int | PRI |  |  |
| `employee_id` | int |  |  |  |
| `title_de` | varchar(255) |  |  |  |
| `content_de` | varchar(255) |  |  |  |
| `title_en` | varchar(255) |  |  |  |
| `content_en` | varchar(255) |  |  |  |
| `created_at` | timestamp |  |  |  |

## `idk_partner_notification_status`

- **Opis**: Tracks the delivery, read, and deletion status of notifications sent to partners.
- **Redova**: 11 · **Period**: 2024-03-19 → 2024-10-15 (`read_at`) · **PK**: `status_id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `status_id` | int | PRI |  |  |
| `partner_id` | int |  |  |  |
| `notification_id` | int |  |  |  |
| `read_at` | datetime |  |  |  |
| `deleted_at` | datetime |  |  |  |

## `idk_partner_personal_notification_types`

- **Opis**: Defines the distinct categories of personal notifications available for partners, such as candidates, orders, companies, and global alerts.
- **Redova**: 4 · **Period**: – · **PK**: `type_id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `type_id` | int | PRI |  |  |
| `type_name` | varchar(255) |  |  |  |

## `idk_partner_personal_notifications_preferences`

- **Opis**: Stores personal notification settings for partners, including global muting options and lists of blocked notification types.
- **Redova**: 108 · **Period**: – · **PK**: `preference_id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `preference_id` | int | PRI |  |  |
| `mute_all_notifications` | tinyint(1) |  |  |  |
| `blocked_notification_types` | text |  |  |  |
| `partner_id` | int |  |  |  |

## `idk_partner_pushnot`

- **Opis**: Stores partner contact details, registration dates, and identifiers used for managing partner push notifications.
- **Redova**: 1,212 · **Period**: – · **PK**: `idk_ppid`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `idk_ppid` | int | PRI |  |  |
| `idk_partnerid` | int |  |  |  |
| `idk_partner_imeprezime` | varchar(555) |  |  | [PII] |
| `idk_partner_telefon` | varchar(555) |  |  | [PII] |
| `idk_partner_email` | varchar(555) |  |  | [PII] |
| `idk_datum_registracije` | varchar(555) |  |  |  |

## `idk_partner_tutorials`

- **Opis**: Stores partner tutorial documents and guides, including their file names, default status, and the uploading employee.
- **Redova**: 4 · **Period**: 2024-01-18 → 2024-02-12 (`doe`) · **PK**: `id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `id` | int | PRI |  |  |
| `name` | varchar(100) |  |  |  |
| `file_name` | varchar(50) |  |  |  |
| `is_default` | tinyint(1) |  |  |  |
| `doe` | datetime |  |  |  |
| `employee_id` | int |  |  |  |

## `idk_partner_uplate`

- **Opis**: Records partner payment transactions, including payment dates, commission amounts, payment types, statuses, and associated partners, employees, and candidates.
- **Redova**: 147 · **Period**: 2020-11-30 → 2024-09-03 (`jp_uplate_datum`) · **PK**: `jp_uplateid`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `jp_uplateid` | int | PRI |  |  |
| `jp_uplate_partnerid` | int |  |  |  |
| `jp_uplate_kandidatid` | int | UNI |  |  |
| `jp_uplate_status` | int |  | 1-uplaceno / 2 - neuplaceno / 3 - odgodjeno |  |
| `jp_uplate_zaposlenikid` | int |  | ZADUZEN ZAPOSLENIK ILI ADMINISTRATOR UPLATE |  |
| `jp_uplate_datum` | datetime |  |  |  |
| `jp_uplate_provizija` | varchar(255) |  |  |  |
| `jp_uplate_vrsta` | int |  | 1 - NALOG / 2 - DIPL |  |

## `idk_partner_user_log`

- **Opis**: Records activity logs and descriptions of actions taken by partner users along with the corresponding timestamps.
- **Redova**: 1,319 · **Period**: 2024-05-21 → 2025-01-26 (`created_at`) · **PK**: `log_id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `log_id` | int | PRI |  |  |
| `user_id` | int |  |  |  |
| `created_at` | timestamp |  |  |  |
| `log_desc` | varchar(255) |  |  |  |

