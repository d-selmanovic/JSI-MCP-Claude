# JSI-MCP-Claude – MCP-Server für das JSI-CRM

Python 3.12 · offizielles MCP-Python-SDK (`mcp` 2.3, `MCPServer` = Nachfolger von FastMCP) · Transport **Streamable HTTP** auf `/mcp` · Health `/health` · OAuth-Resource-Server für **WorkOS AuthKit** · MySQL über PyMySQL (TLS).

Kein freies SQL – außer `sql_query` (nur lesend, nur `jsi:sql:read`, jede Ausführung vom Menschen bestätigt, siehe unten). Alle übrigen Abfragen sind fest oder werden von `build_query.py` erzeugt (einzige Kopie; Filterkatalog: `scripts/filter_catalog.py`). [TAJNO]-Spalten (`osjetljive_kolone.md`) werden vor jeder Ausführung blockiert (`sensitive.assert_clean_sql`) **und** sollen per DB-GRANT gesperrt sein (`sql/`).

## Tools

| Tool | Permission (WorkOS) | Zweck |
|---|---|---|
| `whoami` | – (nur gültiges Token) | eigene `sub`/Permissions, Serverstatus, Konfigurationsfehler |
| `search_candidates` | `jsi:kandidati:read` (+ `jsi:kandidati:pii` für `pii=true`) | alle Filter aus `src/jsi_mcp/skills/jsi-kandidat-filter/SKILL.md`; `izlaz` broj/izvori/lista/id |
| `filter_options` | `jsi:kandidati:read` | Codes, Berufskatalog, Länder, Status, Schreib-Register |
| `candidate_profile` | `jsi:kandidati:read` (+ `pii`, + `jsi:dipl:read` für DIPL-Block) | ein Kandidat ohne PII; nie [TAJNO] |
| `kpis` | `jsi:kennzahlen:read`; `umsatz` + `jsi:finansije:read`; `dipl_funnel` + `jsi:dipl:read` | vermittlungen, neue_kandidaten, pipeline_bestand, umsatz, task_force, casting, dipl_funnel |
| `orders_overview` | `jsi:kennzahlen:read` | Auftrag: Bedarf / Kandidaten / unterschrieben |
| `pipeline_history` | `jsi:kennzahlen:read` | Verlauf eines Kandidaten oder Statuswechsel je Periode |
| `change_log` | `jsi:audit:read` (+ `pii` für vorher/nachher) | `mcp_aenderung` lesen |
| `table_describe` | – (Details: Bereichs-Permission) | Bereiche, Tabellen, Spalten, Typen, Beschreibungen, `pii`-Kennzeichen |
| `table_read` | `jsi:tabele:<bereich>` (+ `jsi:finansije:read` für Finanztabellen, + `jsi:kandidati:pii` für pii-Spalten) | eine Tabelle lesen/auswerten: Spalten, Filter (`eq ne lt le gt ge in not_in like between is_null not_null`), Sortierung, Gruppieren mit `count/count_distinct/sum/avg/min/max`, Seiten. Kein freies SQL: Bezeichner nur aus `tabele_katalog.json`, Werte als Parameter. |
| `skill_lesen` | – | Fach-Skills des Servers (Katalog, SKILL.md, Hilfsdateien); dieselben Inhalte über die MCP-Skills-Extension (`skills/list`, `skill://…`) |
| `sql_query` | `jsi:sql:read` (nur Rolle `jsi-admin-test`; + `jsi:kandidati:pii` für Personendaten-Spalten) | freies, **nur lesendes** SQL (eine SELECT/WITH/EXPLAIN-Anweisung, kein `SELECT *`, [TAJNO] gesperrt, max. 1000 Zeilen, 30 s). Jede Ausführung bestätigt der Mensch im Dialog des Servers (Form-Elicitation; bei uns zustandslos nur ab Protokoll 2026-07-28) – Clients ohne Dialog werden abgelehnt. Log enthält nur einen SHA-256 der Anweisung. |

**Tabellen-Katalog:** `src/jsi_mcp/tabele_katalog.json` – 7 Bereiche, 135 Tabellen; erzeugt mit `python3 -I scripts/gen_tabele.py` aus `docs/rohdaten/columns.json` + Schema-Doku; [TAJNO]-Spalten fehlen, Personendaten-Spalten (`pii`) nach Namensregeln + Freitext-Spalten. Rollen: `jsi-reader` → kandidati, pipeline, taskforce, firme, partner_portal; `jsi-analyst` → zusätzlich komunikacija, dipl. Nach einem neuen Schema-Scan `columns.json`/`counts.tsv` ersetzen und das Skript erneut laufen lassen.
| `<entität>_<aktion>` (z. B. `candidate_update`, `candidate_note_create`, `company_create`, `candidate_archive`; 18 Tools aus `write_registry.yaml`) | `jsi:write:<entität>:<aktion>` | je Tool eigenes Schema mit den Register-Spalten; **Standard `dry_run=true`** = Vorschau vorher/nachher + `preview_hash`, `dry_run=false` + `preview_hash` = ausführen. Ersetzt die früheren generischen `record_preview`/`record_write` (OpenAI-Plugin-Richtlinie „tool independence“). |
| `set_application_status` | `jsi:write:application_status:update` | Pipeline-Status + `idk_log_statusi_prijave`; Standard `dry_run=true` |

Wildcards in WorkOS möglich: `jsi:write:*`, `jsi:write:candidate:*`, `*` (nur Admin-Testrolle).
Limits: 200 Zeilen Standard, 5.000 max, 30 s (`MAX_EXECUTION_TIME` + Socket-Timeout).

### Schreib-Register (`src/jsi_mcp/write_registry.yaml`)
Entitäten: `candidate` (create/update/archive → `kandidat_status=3`), `candidate_driving_licence`, `candidate_language`, `candidate_education`, `candidate_experience`, `candidate_note` (`idk_notes`, Gruppe 2), `candidate_order` (`kandidat_nalog_id`), `project_member` (`idk_project_kandidati`), `candidate_dipl_link` (`kandidat_dipl_id` eindeutig), `company`, `contact`, `application_status` (nur über `set_application_status`).
Erzwungen beim Laden + in Tests: keine [TAJNO]-Spalten, keine PKs, keine Log-/Audit-/Event-/Technik-Tabellen, Spalten/Typen/Längen passen zu `docs/rohdaten/columns.json`, `create` deckt alle NOT-NULL-Spalten ohne Default ab. Kein Löschen.

Ablauf Schreiben: `<entität>_<aktion>(dry_run=true)` → Nutzer bestätigt → dasselbe Tool mit `dry_run=false, preview_hash=…`. In einer Transaktion: `SELECT … FOR UPDATE`, Hash-Vergleich (Abbruch bei paralleler Änderung), Referenz-/Eindeutigkeitsprüfungen, Schreiben, Audit-Zeile in `mcp_aenderung` (`a_zustand='ausgefuehrt'`, `a_freigabe_code`=Hash, `a_notiz` mit `sub`), COMMIT. Fehler → ROLLBACK + Zeile in `mcp_fehler`.
Schreiben nur wenn `JSI_WRITES_ENABLED=true` **und** `JSI_DB_TARGET=mirror`.

`set_application_status`: setzt `kandidat_status_prijave` (bei `rezervisanje=1` auch `kandidat_latest_reserved_time`), schreibt `lsp_broj_dana = DATEDIFF(NOW(), lsp_datetime)` in die bisher letzte Log-Zeile und fügt eine neue Log-Zeile ein (`lsp_izvor = JSI_LSP_IZVOR`, Standard 1 = CRM). Die `lsp_broj_dana`-Logik ist aus den Daten abgeleitet (2026-10-30: 27.300 von 27.313 Zeilen seit 2025 stimmen ±1 Tag), nicht dokumentiert.

> ⚠️ **Schreiben bleibt in v1 ausgeschaltet.** Direkte DB-Schreibzugriffe lösen die Automationen des CRM nicht aus (Benachrichtigungen, Task-Force-Aufgaben, weitere Logs – die DB hat keine Trigger, die Logik liegt im CRM-Code). Pflichtpunkt direkt nach Go-live: CRM-Code/API klären, Automationen nachbauen oder über die API schreiben, Mirror-Abnahme, erst dann `JSI_WRITES_ENABLED=true`.

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

Ohne DB- oder WorkOS-Konfiguration startet der Server trotzdem: `/health` meldet `degraded` + Liste der Fehler; ohne WorkOS antwortet `/mcp` mit 401 (`WWW-Authenticate` mit Klartext-Grund; 503 würde den MCP-Health-Check von Manufact scheitern lassen), ohne DB liefern die Tools klare Fehlermeldungen.

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
Hilfsskripte: `scripts/schema_ddl.py` (DDL aus `columns.json`), `scripts/gen_grants.py` (GRANTs), `scripts/render_sql.py` (Lese-SQL mit Literalen zum Gegenprüfen direkt an der DB, z. B. mit dem mysql-Client).

## Deploy auf Manufact

Server `JSI-MCP-Claude`, Org „Job Step“, Repo `d-selmanovic/JSI-MCP-Claude`, Branch `feature/server-v1`, `rootDir server`, Port 3000, Region `AUTO` (EU/US/APAC erst ab Plan „Startup“). Produktion: `https://calm-steel-onjlq.run.mcp-use.com/mcp`.

Beide Build-Varianten sind getestet und laufen:
- **Dockerfile:** `dockerfilePath` **relativ zu `rootDir`** angeben (`Dockerfile`, nicht `server/Dockerfile` – sonst stille Rückfallebene auf Auto-Erkennung). Liegt ein `Dockerfile` im `rootDir`, nutzt Manufact es auch ohne Einstellung.
- **Automatisch (pyproject.toml):** Manufact installiert mit `uv sync --frozen --no-dev` und startet `python app.py` → `server/app.py` startet den Server (lenkt auf `.venv` um). Wirkt nur, wenn kein `Dockerfile` im `rootDir` liegt.

Manufact prüft nach dem Deploy per MCP-`initialize` auf `/mcp`: 401 (Auth verlangt) gilt als gesund, 503 als Fehler. Öffentliches `/health` liefert eine Plattform-Antwort, nicht die der App (App-Health nur in den Runtime-Logs/intern).

## WorkOS AuthKit einrichten

**Stand 2026-10-30:** eingerichtet in WorkOS **Staging** (`balanced-lantern-65-staging.authkit.app`) – Ressourcen, 25 `jsi:*`-Permissions, Rollen `jsi-reader` / `jsi-analyst` / `jsi-admin-test`, Organisation „Activi“. Production muss im Dashboard manuell nachgezogen werden (der WorkOS-Connector darf dort nicht schreiben); dafür die folgenden Schritte nutzen und danach `WORKOS_AUTHKIT_DOMAIN`/`WORKOS_CLIENT_ID` auf Manufact umstellen.


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
11. Schreiben (Mirror, `JSI_WRITES_ENABLED=true`): `candidate_note_create` (dry_run=true) → dasselbe mit `dry_run=false preview_hash=…` an einem Testkandidaten → `change_log` zeigt Eintrag → Rücknahme per Update-Tool (Notizen: keine Löschung; Testnotiz kennzeichnen).
12. `set_application_status` dry_run → ausführen → `pipeline_history kandidat_id=…` zeigt neue Zeile; vorherige Zeile hat `broj_dana`; zurücksetzen auf alten Status.
13. Mit `JSI_WRITES_ENABLED=false` → jedes Schreib-Tool mit `dry_run=false` wird abgelehnt.

## Admin-Status-Seite (`/admin`)

Nur lesen. Aus, solange `JSI_ADMIN_PASSWORD` (≥ 16 Zeichen) nicht gesetzt ist; dann Login per Browser-Dialog mit Benutzer `admin` und diesem Passwort. Zeigt: Version, Laufzeit, DB-Ziel, DB erreichbar (mit Antwortzeit), CA-Zertifikat vorhanden, Schreibschalter, Auth-Modus, Konfigurationsfehler (ohne Werte), Aufrufe je Tool und letzte Aufrufe dieser Instanz (ohne Argumente/Ergebnisse), letzte 20 Schreibaktionen aus `mcp_aenderung` (ohne vorher/nachher). JSON: `/admin/status.json`. Ändern lässt sich dort nichts – Einstellungen und Secrets bleiben in Manufact (Server → Environment variables, danach Redeploy). Das Admin-Passwort öffnet **nicht** den MCP-Endpunkt (`/mcp` braucht weiter ein WorkOS-Token).
