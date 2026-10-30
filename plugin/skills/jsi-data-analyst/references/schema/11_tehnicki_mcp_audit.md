# Tehnički: MCP/audit/event sourcing

Tabele: 10. Redovi i periodi stanje 2026-10-29.

## `mcp_aenderung`

- **Opis**: Logs change history, approvals, and execution details for candidate-related data records across system tables, capturing before-and-after states.
- **Redova**: 0 · **Period**: – · **PK**: `a_id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `a_id` | int | PRI |  |  |
| `a_zeit` | datetime | MUL |  |  |
| `a_werkzeug` | varchar(64) |  |  |  |
| `a_aktion` | varchar(10) |  |  |  |
| `a_tabelle` | varchar(64) |  |  |  |
| `a_datensatz_id` | int |  |  |  |
| `a_vorher` | text |  |  |  |
| `a_nachher` | text |  |  |  |
| `a_kandidat_id` | int | MUL |  |  |
| `a_art` | varchar(10) |  |  |  |
| `a_zustand` | varchar(16) | MUL |  |  |
| `a_freigabe_code` | varchar(64) |  |  |  |
| `a_freigabe_zeit` | datetime |  |  |  |
| `a_ausgefuehrt_zeit` | datetime |  |  |  |
| `a_notiz` | varchar(500) |  |  |  |

## `mcp_fehler`

- **Opis**: Logs application errors, including timestamps, error types, messages, context, associated tools, and export status.
- **Redova**: 0 · **Period**: – · **PK**: `f_id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `f_id` | int | PRI |  |  |
| `f_zeit` | datetime |  |  |  |
| `f_werkzeug` | varchar(64) |  |  |  |
| `f_art` | varchar(16) |  |  |  |
| `f_meldung` | text |  |  |  |
| `f_kontext` | text |  |  |  |
| `f_exportiert` | tinyint | MUL |  |  |

## `mcp_status_info`

- **Opis**: Defines document processing workflow statuses, including their multilingual names, meanings, permitted transitions, and update permissions.
- **Redova**: 9 · **Period**: – · **PK**: `s_id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `s_id` | int | PRI |  |  |
| `s_name_hr` | varchar(64) |  |  |  |
| `s_name_de` | varchar(64) |  |  |  |
| `s_bedeutung` | varchar(255) |  |  |  |
| `s_setzt` | varchar(40) |  |  |  |
| `s_naechste` | varchar(80) |  |  |  |
| `s_aktiv` | tinyint |  |  |  |

## `rb_approvals`

- **Opis**: Stores records of request approvals, including decision status, preview payloads, approver details, and expiration timestamps.
- **Redova**: 4 · **Period**: 2026-10-14 → 2026-10-14 (`decided_at`) · **PK**: `approval_id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `approval_id` | char(36) | PRI |  |  |
| `principal_hash` | char(64) |  |  |  |
| `preview_sha256` | char(64) |  |  |  |
| `preview_json` | json |  |  |  |
| `decision` | varchar(32) |  |  |  |
| `decision_by` | varchar(255) |  |  |  |
| `decided_at` | datetime(6) |  |  |  |
| `expires_at` | datetime(6) |  |  |  |
| `consumed_by_request_id` | char(36) |  |  |  |

## `rb_baselines`

- **Opis**: Stores point-in-time baseline snapshots of entity revisions and their typed values for tracking and auditing changes.
- **Redova**: 1 · **Period**: 2026-10-14 → 2026-10-14 (`captured_at`) · **PK**: `baseline_id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `baseline_id` | char(36) | PRI |  |  |
| `entity_type` | varchar(64) | MUL |  |  |
| `entity_id` | varchar(191) |  |  |  |
| `revision` | bigint unsigned |  |  |  |
| `captured_at` | datetime(6) |  |  |  |
| `typed_values` | json |  |  |  |

## `rb_entity_state`

- **Opis**: Tracks the current state, revision level, and baseline timestamp for various entities within the system.
- **Redova**: 1 · **Period**: 2026-10-14 → 2026-10-14 (`baseline_at`) · **PK**: `entity_type,entity_id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `entity_type` | varchar(64) | PRI |  |  |
| `entity_id` | varchar(191) | PRI |  |  |
| `revision` | bigint unsigned |  |  |  |
| `baseline_at` | datetime(6) |  |  |  |

## `rb_events`

- **Opis**: Stores audit log events tracking entity changes, revisions, and rollback or restore operations along with actor details and JSON-formatted change payloads.
- **Redova**: 2 · **Period**: 2026-10-14 → 2026-10-14 (`created_at`) · **PK**: `event_id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `event_id` | char(36) | PRI |  |  |
| `entity_type` | varchar(64) | MUL |  |  |
| `entity_id` | varchar(191) |  |  |  |
| `revision_before` | bigint unsigned |  |  |  |
| `revision_after` | bigint unsigned |  |  |  |
| `operation` | varchar(32) |  |  |  |
| `actor_issuer` | varchar(255) |  |  |  |
| `actor_subject` | varchar(255) |  |  |  |
| `request_id` | char(36) |  |  |  |
| `source_event_id` | char(36) |  |  |  |
| `created_at` | datetime(6) |  |  |  |
| `typed_changes` | json |  |  |  |
| `reason` | text |  |  |  |
| `event_sha256` | char(64) |  |  |  |

## `rb_field_state`

- **Opis**: Tracks revision and state information for specific fields associated with entities in the CRM.
- **Redova**: 1 · **Period**: – · **PK**: `entity_type,entity_id,field_name`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `entity_type` | varchar(64) | PRI |  |  |
| `entity_id` | varchar(191) | PRI |  |  |
| `field_name` | varchar(128) | PRI |  |  |
| `revision` | bigint unsigned |  |  |  |

## `rb_outbox`

- **Opis**: Stores outbox event messages and tracks their delivery status, retry attempts, and processing leases for asynchronous dispatch.
- **Redova**: 2 · **Period**: 2026-10-14 → 2026-10-14 (`next_attempt_at`) · **PK**: `event_id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `event_id` | char(36) | PRI |  |  |
| `status` | varchar(32) | MUL |  |  |
| `attempts` | int unsigned |  |  |  |
| `next_attempt_at` | datetime(6) |  |  |  |
| `lease_token` | char(36) |  |  |  |
| `lease_until` | datetime(6) |  |  |  |
| `archived_at` | datetime(6) |  |  |  |

## `rb_requests`

- **Opis**: Records API or operation requests including execution timestamps, payload hashes, idempotency keys, and JSON results for tracking and idempotency management.
- **Redova**: 2 · **Period**: 2026-10-14 → 2026-10-14 (`created_at`) · **PK**: `request_id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `request_id` | char(36) | PRI |  |  |
| `principal_hash` | char(64) | MUL |  |  |
| `idempotency_key` | varchar(128) |  |  |  |
| `payload_sha256` | char(64) |  |  |  |
| `result_json` | json |  |  |  |
| `created_at` | datetime(6) |  |  |  |
| `completed_at` | datetime(6) |  |  |  |

