# Komunikacija s kandidatima (SMS, Viber, Messenger, bot, notifikacije)

Tabele: 11. Redovi i periodi stanje 2026-10-29.

## `idk_bot_obavijesti`

- **Opis**: Stores records of automated bot notifications, including the associated candidate, work order, dispatch status, and received response.
- **Redova**: 2 · **Period**: – · **PK**: `bo_id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `bo_id` | int | PRI |  |  |
| `bo_kandidat_id` | int |  |  |  |
| `bo_nalog_id` | int |  |  |  |
| `bo_poslana` | int |  |  |  |
| `bo_odgovor` | int |  | 0 - nije pogledana jos, 1 - pogledana obavijest, 2 - zainteresiran, 3- nezainteresiran za oglas, 4 - zavrsio sa unosom |  |

## `idk_chat_question`

- **Opis**: Stores predefined chat questions, answers, and their hierarchical ordering for interactive chat flows.
- **Redova**: 56 · **Period**: 2024-02-19 → 2024-02-21 (`deletedAt`) · **PK**: `id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `id` | int | PRI |  |  |
| `type` | text |  | type id from idk_chat_type |  |
| `question_order` | int |  | order of question |  |
| `question` | text |  | json for all languages |  |
| `answer` | text |  | json for all languages |  |
| `parentQuestion` | int |  | id of previous question |  |
| `deletedAt` | datetime |  |  |  |

## `idk_chat_type`

- **Opis**: Stores lookup categories and names defining different types of chats within the CRM system.
- **Redova**: 1 · **Period**: – · **PK**: `id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `id` | int | PRI |  |  |
| `name` | varchar(150) |  |  |  |

## `idk_email_text`

- **Opis**: Stores predefined email templates and notification messages, including their identifiers, subjects, and text content.
- **Redova**: 3 · **Period**: – · **PK**: `email_id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `email_id` | int | PRI |  | [PII] |
| `email_value` | varchar(100) |  |  | [PII] |
| `email_title` | varchar(255) |  |  | [PII] |
| `email_txt` | text |  |  | [PII] |

## `idk_glossa_log`

- **Opis**: Logs API requests, responses, status codes, and associated candidate identifiers for interactions with the Glossa API.
- **Redova**: 13 · **Period**: 2023-09-19 → 2024-05-16 (`doe`) · **PK**: `id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `id` | int | PRI |  |  |
| `request` | text |  |  |  |
| `response` | text |  |  |  |
| `code` | int |  |  |  |
| `candidate` | text |  | FK iz tabele idk_kandidati (check) - nekad se salje jedan, nekad array |  |
| `request_endpoint` | varchar(255) |  |  |  |
| `doe` | datetime |  |  |  |

## `idk_messenger_obavijesti`

- **Opis**: Records messenger notification events sent to candidates, including the candidate ID, dispatch timestamp, and notification type.
- **Redova**: 260,423 · **Period**: 2020-02-18 → 2025-07-08 (`mo_datum_slanja`) · **PK**: `mo_id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `mo_id` | int | PRI |  |  |
| `mo_kandidat_id` | int |  |  |  |
| `mo_tip` | int |  | 1-sms za instalaciju |  |
| `mo_datum_slanja` | datetime |  |  |  |

## `idk_notification`

- **Opis**: Stores user and candidate notifications, including message content, status, type, timestamp, and target redirect URLs.
- **Redova**: 75,248 · **Period**: 2017-09-07 → 2026-02-21 (`not_date`) · **PK**: `not_id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `not_id` | int | PRI |  |  |
| `not_kandidatid` | int |  |  |  |
| `not_text` | text |  |  |  |
| `not_url` | varchar(255) |  |  |  |
| `not_date` | datetime |  |  |  |
| `not_type` | int |  | 2-ponovna prijava |  |
| `not_status` | int |  |  |  |

## `idk_provider_for_sending_messages`

- **Opis**: Stores configuration details and active status for messaging provider groups used to send messages.
- **Redova**: 9 · **Period**: – · **PK**: `psm_id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `psm_id` | int | PRI |  |  |
| `psm_group_type` | int |  | Tip grupe |  |
| `psm_group_name` | varchar(500) |  | Naziv grupe |  |
| `psm_active_provider` | int |  | Aktivni provider. Za sad imamo: 1 - Infobip; 2 - NTH; |  |

## `idk_sms_messages`

- **Opis**: Records sent SMS messages, including recipient phone numbers, message content, delivery statuses, response codes, and tracking timestamps.
- **Redova**: 3,512 · **Period**: 2020-02-17 → 2020-03-23 (`sms_created_at`) · **PK**: `sms_id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `sms_id` | int | PRI |  |  |
| `sms_origin` | varchar(50) |  |  |  |
| `sms_number` | varchar(100) |  |  | [PII] |
| `sms_content` | text |  |  |  |
| `sms_status` | int |  | 0-pocetni status, 1-poslan sms |  |
| `sms_created_at` | datetime |  |  |  |
| `sms_response_nthsmsid` | text |  |  |  |
| `sms_response_statuscode` | varchar(10) |  |  |  |
| `sms_count` | int |  |  |  |
| `sms_updated_at` | datetime |  |  |  |
| `sms_notification_statuscode` | int |  |  |  |
| `sms_notification_datetime` | datetime |  |  | [PII] |
| `sms_type` | int |  | 1-jobstep messenger; 2 - sms za stare kandidate sa linkom prijave |  |

## `idk_triggerurl`

- **Opis**: Records trigger URLs, associated email task tags, and timestamps used for tracking or initiating automated actions.
- **Redova**: 10 · **Period**: 2019-06-18 → 2023-05-01 (`url_datetime`) · **PK**: `url_id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `url_id` | int | PRI |  |  |
| `url_link` | varchar(250) |  |  |  |
| `url_datetime` | datetime |  |  | [PII] |
| `url_tag` | varchar(50) |  |  |  |

## `idk_viber_obavijesti`

- **Opis**: Stores records of Viber notifications sent to candidates, including timestamps, related order IDs, and notification purposes.
- **Redova**: 3,905 · **Period**: 2020-06-18 → 2020-06-18 (`vo_datetime`) · **PK**: `vo_id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `vo_id` | int | PRI |  |  |
| `vo_nalogid` | int |  |  |  |
| `vo_kandidati_id` | int |  |  |  |
| `vo_obavijest_za` | varchar(255) |  |  |  |
| `vo_datetime` | datetime |  |  | [PII] |

