# JSI-MCP-Claude – MCP-Server für das JSI-CRM

Python 3.12 · offizielles MCP-Python-SDK (`mcp` 2.3, `MCPServer` = Nachfolger von FastMCP) · Transport **Streamable HTTP** auf `/mcp` · Health `/health` · OAuth-Resource-Server für **WorkOS AuthKit** · MySQL über PyMySQL (TLS).

Kein freies SQL. Alle Abfragen sind fest oder werden von `build_query.py` (unverändert aus `plugin/skills/jsi-kandidat-filter/scripts/`) erzeugt. [TAJNO]-Spalten (`osjetljive_kolone.md`) werden vor jeder Ausführung blockiert (`sensitive.assert_clean_sql`) **und** sollen per DB-GRANT gesperrt sein (`sql/`).

## Tools

| Tool | Permission (WorkOS) | Zweck |
|---|---|---|
| `whoami` | – (nur gültiges Token) | eigene `sub`/Permissions, Serverstatus, Konfigurationsfehler |
| `search_candidates` | `jsi:kandidati:read` (+ `jsi:kandidati:pii` für `pii=true`) | alle Filter aus `jsi-kandidat-filter/SKILL.md`; `izlaz` broj/izvori/lista/id |
| `filter_options` | `jsi:kandidati:read` | Codes, Berufskatalog, Länder, Status, Schreib-Register |
| `candidate_profile` | `jsi:kandidati:read` (+ `pii`, + `jsi:dipl:read` für DIPL-Block) | ein Kandidat ohne PII; nie [TAJNO] |
| `kpis` | `jsi:kennzahlen:read`; `umsatz` + `jsi:finansije:read`; `dipl_funnel` + `jsi:dipl:read` | vermittlungen, neue_kandidaten, pipeline_bestand, umsatz, task_force, casting, dipl_funnel |
| `orders_overview` | `jsi:kennzahlen:read` | Auftrag: Bedarf / Kandidaten / unterschrieben |
| `pipeline_history` | `jsi:kennzahlen:read` | Verlauf eines Kandidaten oder Statuswechsel je Periode |
| `change_log` | `jsi:audit:read` (+ `pii` für vorher/nachher) | `mcp_aenderung` lesen |
| `record_preview` | `jsi:write:<entität>:<aktion>` | Vorschau vorher/nachher, Prüfungen, `preview_hash` – schreibt nie |
| `record_write` | `jsi:write:<entität>:<aktion>` | create/update/archive laut Register; **Standard `dry_run=true`** |
| `set_application_status` | `jsi:write:application_status:update` | Pipeline-Status + `idk_log_statusi_prijave`; Standard `dry_run=true` |

Wildcards in WorkOS möglich: `jsi:write:*`, `jsi:write:candidate:*`, `*` (nur Admin-Testrolle).
Limits: 200 Zeilen Standard, 5.000 max, 30 s (`MAX_EXECUTION_TIME` + Socket-Timeout).

### Schreib-Register (`src/jsi_mcp/write_registry.yaml`)
Entitäten: `candidate` (create/update/archive → `kandidat_status=3`), `candidate_driving_licence`, `candidate_language`, `candidate_education`, `candidate_experience`, `candidate_note` (`idk_notes`, Gruppe 2), `candidate_order` (`kandidat_nalog_id`), `project_member` (`idk_project_kandidati`), `candidate_dipl_link` (`kandidat_dipl_id` eindeutig), `company`, `contact`, `application_status` (nur über `set_application_status`).
Erzwungen beim Laden + in Tests: keine [TAJNO]-Spalten, keine PKs, keine Log-/Audit-/Event-/Technik-Tabellen, Spalten/Typen/Längen passen zu `docs/rohdaten/columns.json`, `create` deckt alle NOT-NULL-Spalten ohne Default ab. Kein Löschen.

Ablauf Schreiben: `record_preview` → Nutzer bestätigt → `record_write(dry_run=false, preview_hash=…)`. In einer Transaktion: `SELECT … FOR UPDATE`, Hash-Vergleich (Abbruch bei paralleler Änderung), Referenz-/Eindeutigkeitsprüfungen, Schreiben, Audit-Zeile in `mcp_aenderung` (`a_zustand='ausgefuehrt'`, `a_freigabe_code`=Hash, `a_notiz` mit `sub`), COMMIT. Fehler → ROLLBACK + Zeile in `mcp_fehler`.
Schreiben nur wenn `JSI_WRITES_ENABLED=true` **und** `JSI_DB_TARGET=mirror`.

`set_application_status`: setzt `kandidat_status_prijave` (bei `rezervisanje=1` auch `kandidat_latest_reserved_time`), schreibt `lsp_broj_dana = DATEDIFF(NOW(), lsp_datetime)` in die bisher letzte Log-Zeile und fügt eine neue Log-Zeile ein (`lsp_izvor = JSI_LSP_IZVOR`, Standard 1 = CRM). Die `lsp_broj_dana`-Logik ist aus den Daten abgeleitet (2026-10-30: 27.300 von 27.313 Zeilen seit 2025 stimmen ±1 Tag), nicht dokumentiert.

## Umgebungsvariablen

| Variable | geheim | Bedeutung |
|---|---|---|
| `PORT` | nein | Standard 3000 |
| `JSI_DB_TARGET` | nein | `mirror` (Standard) oder `prod` |
| `JSI_MIRROR_DB_HOST/PORT/NAME/USER` | nein* | Mirror-DB (*Host/User nach Wunsch als Secret) |
| `JSI_MIRROR_DB_PASSWORD` | **ja** | |
| `JSI_DB_HOST/PORT/NAME/USER/PASSWORD` | Passwort **ja** | Produktion (später, Read-only-Benutzer) |
| `JSI_DB_CA_CERT` | nein (öffentliches CA) | PEM-Inhalt des Aiven-CA (Zeilenumbrüche echt oder als `\n`) |
| `JSI_DB_CA_FILE` | nein | alternativ Pfad; Standard `certs/aiven-ca.pem` (`*.pem` ist in `.gitignore`) |
| `JSI_DB_SSL_REQUIRED` | nein | Standard `true`; `false` nur lokal |
| `JSI_WRITES_ENABLED` | nein | Standard `false` |
| `WORKOS_AUTHKIT_DOMAIN` | nein | z. B. `xyz.authkit.app` (ohne https) |
| `WORKOS_CLIENT_ID` | nein | derzeit nur informativ |
| `JSI_MCP_PUBLIC_URL` | nein | öffentliche MCP-URL inkl. `/mcp` = Resource Indicator = Token-`aud` |
| `JSI_WRITE_EMPLOYEE_ID` | nein | `idk_employees.employee_id`, der als Autor von Notizen/Log-Einträgen gilt (Standard 0 → Log: NULL) |
| `JSI_LSP_IZVOR` | nein | `lsp_izvor` für Pipeline-Log (Standard 1 = CRM; es gibt keinen Code „MCP“) |
| `JSI_AUTH_DISABLED` | nein | **nur lokal**; Start wird verweigert, wenn `JSI_MCP_PUBLIC_URL` nicht `http://localhost…`/`http://127.0.0.1…` ist; bindet dann nur an 127.0.0.1 |
| `JSI_DEV_PERMISSIONS` | nein | nur mit `JSI_AUTH_DISABLED`: kommagetrennte Permissions (Standard `*`) |

Ohne DB- oder WorkOS-Konfiguration startet der Server trotzdem: `/health` meldet `degraded` + Liste der Fehler; ohne WorkOS antwortet `/mcp` mit 503 und Klartext-Grund, ohne DB liefern die Tools klare Fehlermeldungen.

## Lokal

```bash
cd server
uv sync
uv run pytest -q                                   # Unit-Tests (Integration wird übersprungen)
docker run -d --name jsi-mysql -e MYSQL_ROOT_PASSWORD=rootpw -p 13306:3306 mysql:8.4 \
  --sql-mode="ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION"
JSI_IT_MYSQL=127.0.0.1:13306 JSI_IT_ROOT_PASSWORD=rootpw uv run pytest -q   # + Integration (Schema aus columns.json, synthetische Daten, generierte GRANTs)
JSI_AUTH_DISABLED=true JSI_MCP_PUBLIC_URL=http://localhost:3000/mcp JSI_DB_SSL_REQUIRED=false \
  JSI_MIRROR_DB_HOST=127.0.0.1 JSI_MIRROR_DB_PORT=13306 JSI_MIRROR_DB_NAME=jsicrm_it \
  JSI_MIRROR_DB_USER=jsi_it_ro JSI_MIRROR_DB_PASSWORD=it-only-password-1 uv run jsi-mcp-server
```
Hilfsskripte: `scripts/schema_ddl.py` (DDL aus `columns.json`), `scripts/gen_grants.py` (GRANTs), `scripts/render_sql.py` (Lese-SQL mit Literalen zum Gegenprüfen über BlazeSQL).

## Deploy auf Manufact

`create_server`: Org „Job Step“, GitHub-Verbindung des Kontos `d-selmanovic`, Repo `d-selmanovic/JSI-MCP-Claude`, Branch `feature/server-v1`, `rootDir server`, Name `JSI-MCP-Claude`, Port 3000, Region `AUTO` (EU/US/APAC erst ab Plan „Startup“). Build: `Dockerfile` in `server/` (alternativ Python-Erkennung über `pyproject.toml`; Start `jsi-mcp-server`).
Danach `JSI_MCP_PUBLIC_URL` auf die von Manufact vergebene URL + `/mcp` setzen.

## WorkOS AuthKit einrichten

1. AuthKit aktivieren; **Domain** notieren → `WORKOS_AUTHKIT_DOMAIN`.
2. In der AuthKit-/MCP-Konfiguration (Menübezeichnung im WorkOS-Dashboard nicht verifiziert) die MCP-URL (`JSI_MCP_PUBLIC_URL`, exakt inkl. `/mcp`) als **Resource Indicator** eintragen; Tokens müssen `aud` = diese URL tragen (der Server prüft `iss`, `aud`, `exp`, Signatur über `https://<domain>/oauth2/jwks`).
3. **Client ID Metadata Documents (CIMD)** aktivieren, ggf. zusätzlich Dynamic Client Registration (welches Verfahren der claude.ai-Connector nutzt, beim Einbinden prüfen).
4. Permissions anlegen: `jsi:kandidati:read`, `jsi:kandidati:pii`, `jsi:kennzahlen:read`, `jsi:finansije:read`, `jsi:dipl:read`, `jsi:audit:read`, `jsi:write:application_status:update` und je Entität/Aktion `jsi:write:<entität>:<create|update|archive>` (vollständige Liste: `filter_options` → `schreib_register.*.permissions`). Wildcards (`jsi:write:*`) funktionieren serverseitig.
5. Rollen anlegen (Vorschlag): `jsi-reader` (kandidati:read, kennzahlen:read), `jsi-analyst` (+ finansije, dipl), `jsi-recruiter` (+ pii + Schreiben Kandidat/Notiz/Status), `jsi-admin-test` (`*` bzw. alle Slugs, nur für die Abnahme).
6. ⚠️ **Zu testen:** ob WorkOS den `permissions`-Claim auch in MCP-OAuth-Tokens ausstellt (belegt ist er für AuthKit-Session-Tokens). Prüfung: Connector verbinden → `whoami`. Sind `permissions` leer, JWT-Template in WorkOS um `permissions` ergänzen.

## Minimale DB-Benutzer (Aiven)

```bash
python3 -I scripts/gen_grants.py readonly jsicrm jsi_mcp_ro  > sql/grants_readonly.sql
python3 -I scripts/gen_grants.py write    jsicrm jsi_mcp_mirror > sql/grants_mirror_write.sql
```
- `jsi_mcp_ro` (Produktion): `SELECT` auf alle 190 Tabellen; bei den 10 Tabellen mit [TAJNO]-Spalten nur spaltenweise (`SELECT (col, …)`), d. h. `SELECT *` auf diese Tabellen schlägt fehl – gewollt.
- `jsi_mcp_mirror` (Mirror): zusätzlich `INSERT`/`UPDATE` nur auf die Register-Spalten, `INSERT` auf `mcp_aenderung`/`mcp_fehler`, `INSERT` + `UPDATE(lsp_broj_dana)` auf `idk_log_statusi_prijave`. Kein `DELETE`/`DROP`/`ALTER`.
- Benutzer vorher anlegen: `CREATE USER 'jsi_mcp_ro'@'%' IDENTIFIED BY '…' REQUIRE SSL;` (Passwort nur in der Aiven-Konsole / Manufact-Secrets).
- Beide Skripte sind in den Integrationstests gegen MySQL 8.4 ausgeführt (inkl. Negativtests: `kandidat_jmbg`, `SELECT *`, `DELETE`, `DROP` werden abgelehnt).

## Abnahmeliste (nach Deploy über den Connector)

1. `/health` → `status: ok`, `db_konfiguriert: true`, keine Konfigurationsfehler.
2. Ohne Token: `POST /mcp` → 401 mit `WWW-Authenticate … resource_metadata=…`; `/.well-known/oauth-protected-resource/mcp` nennt AuthKit.
3. Connector in claude.ai einbinden, über WorkOS anmelden → `whoami`: `sub` + erwartete Permissions (siehe WorkOS Punkt 6).
4. `search_candidates {"zanimanje":"Elektriker","vozacka":"C"}` → BlazeSQL-Referenz **2.672** (2026-10-30; 2.676 am 2026-10-29).
5. `kpis vermittlungen` → 2022 299 · 2023 536 · 2024 71 · 2025 24 · 2026 1; `stanje.plasirani_trenutno` 854.
6. `kpis umsatz od=2023-01-01 do=2024-01-01` → 430.050 / 1.819.207,36 / 239.716,92.
7. `kpis dipl_funnel` → 2021 41.619/1.895/840 … (Rolle ohne `jsi:dipl:read` → Ablehnung).
8. `orders_overview` → Auftrag 254: 300 / 900 / 165.
9. `candidate_profile` ohne `pii` enthält keine Namen/Telefon/E-Mail; mit `pii` (Permission) schon.
10. Rolle ohne `jsi:kandidati:pii`: `search_candidates … pii=true` → Ablehnung.
11. Schreiben (Mirror, `JSI_WRITES_ENABLED=true`): `record_preview` → `record_write dry_run=false preview_hash=…` (z. B. `candidate_note` an einem Testkandidaten) → `change_log` zeigt Eintrag → Rücknahme per `record_write update` (Notizen: keine Löschung; Testnotiz kennzeichnen).
12. `set_application_status` dry_run → ausführen → `pipeline_history kandidat_id=…` zeigt neue Zeile; vorherige Zeile hat `broj_dana`; zurücksetzen auf alten Status.
13. Mit `JSI_WRITES_ENABLED=false` → `record_write dry_run=false` wird abgelehnt.
