# Pipeline historija i logovi

Tabele: 4. Redovi i periodi stanje 2026-10-29.

## `idk_duration_per_status`

- **Opis**: Records the duration, description, and group associations for various operational or CRM process statuses.
- **Redova**: 19 · **Period**: – · **PK**: `dpr_id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `dpr_id` | int | PRI |  |  |
| `dpr_group` | int |  | 1 - Status prijave prije potpisa ugovora; 2 - Status nostrifikacije; 3 - Status jezika; 4 - Status prijave nakon potpisa ugovora |  |
| `dpr_status` | varchar(10) |  | Ukoliko je vrijednost 0 onda su to dani koji se odnose na ostale statuse te grupe. |  |
| `dpr_duration` | int |  |  |  |
| `dpr_description` | varchar(400) |  |  |  |
| `dpr_status_name` | varchar(100) |  |  |  |

## `idk_log_kandidat_statusi`

- **Opis**: Logs historical changes and timestamped status updates for candidates, including processing and messenger statuses recorded by employees.
- **Redova**: 242,032 · **Period**: 2020-02-26 → 2026-10-24 (`lks_datetime`) · **PK**: `lks_id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `lks_id` | int | PRI |  |  |
| `lks_kandidat_id` | int | MUL |  |  |
| `lks_status_obrade` | int |  |  |  |
| `lks_status_messenger` | int |  |  |  |
| `lks_datetime` | datetime |  |  | [PII] |
| `lks_employee_id` | int |  |  |  |
| `lks_broj_dana` | int |  |  |  |
| `lks_link_id` | int | MUL | ID linka na kojeg se kandidat prijavio. Unosi se samo kod statusa 1 i 9 |  |

## `idk_log_statusi_prijave`

- **Opis**: Logs historical status changes and timeline details for candidate job applications across different projects and employees.
- **Redova**: 361,201 · **Period**: 2021-12-07 → 2026-02-25 (`lsp_datetime`) · **PK**: `lsp_id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `lsp_id` | int | PRI |  |  |
| `lsp_kandidat_id` | int | MUL |  |  |
| `lsp_projekt_id` | int | MUL |  |  |
| `lsp_status_prijave_id` | int | MUL |  |  |
| `lsp_employee_id` | int |  |  |  |
| `lsp_izvor` | int |  | 1-CRM, 2-PP, 3-bot, 4-queue, 5-automatski cronom, 6-Transfer kandidata |  |
| `lsp_datetime` | datetime |  |  | [PII] |
| `lsp_broj_dana` | int |  |  |  |

## `idk_logs`

- **Opis**: Stores system event and activity logs, capturing the date, type, detailed description, and the associated employee for each entry.
- **Redova**: 3,006,939 · **Period**: 2018-04-11 → 2026-09-30 (`log_date`) · **PK**: `log_id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `log_id` | int | PRI |  |  |
| `log_employeeid` | int |  |  |  |
| `log_desc` | text |  |  |  |
| `log_date` | datetime |  |  |  |
| `log_type` | int |  | Log za skladiste - $log_type = 1, Log za pozicije - $log_type = 2, Log za biljeske - $log_type = 3, Log za financije - $log_type = 4, Log za IP-ove 5 i 6(bot),  7- dak, 8 klijentin, 10-PP, 11-nivoi jezika, 12-log za remindere na CRM-u, 13-log za bridge sistem API |  |

