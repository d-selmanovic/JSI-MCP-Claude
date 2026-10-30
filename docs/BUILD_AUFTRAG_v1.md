# Bauauftrag v1 – JSI-MCP-Claude (Python, Manufact)

Auftraggeber: Orchestrator-Session (Claude) im Auftrag des Nutzers. Sprache mit dem Nutzer: Deutsch. Stand: 2026-10-30.

## Entscheidungen (verbindlich, siehe HANDOVER.md §0, §13)
- Eigener JSI-MCP-Server, **Python 3.12**, offizielles MCP-Python-SDK (`mcp`, FastMCP, Transport *Streamable HTTP*), Hosting **Manufact Cloud**, Org „Job Step“ (`organizationId 43963a91-ff92-4f8b-837f-146f313992d8`, Slug `org-18c6f45f-zfi5v`), GitHub-Verbindung `08af150c-b22a-4920-afe5-b360b4a82287` (Konto `d-selmanovic`).
- Ziel-Repo: **`d-selmanovic/JSI-MCP-Claude`**. Servername auf Manufact: **`JSI-MCP-Claude`**.
- Authentifizierung **WorkOS AuthKit** (OAuth, Server = Resource Server), Berechtigungen pro Tool aus dem JWT-Claim `permissions` (Slugs siehe HANDOVER §13.1). Ohne gültiges Token → 401 + `WWW-Authenticate` mit `resource_metadata`.
- Lesen + **alle sinnvollen Schreibaktionen** über ein Schreib-Register (HANDOVER §13.2), jede mit `dry_run`, Transaktion, Audit in `mcp_aenderung` (Fehler in `mcp_fehler`), kein hartes Löschen. Schreiben nur, wenn `JSI_WRITES_ENABLED=true` **und** `JSI_DB_TARGET=mirror`.
- Kein freies SQL-Tool. Toolnamen Englisch, Beschreibungen Deutsch + Bosnisch. Limits: 200 Zeilen Standard, 5.000 max, 30 s Timeout.
- Personendaten (Name, Telefon, E-Mail) nur mit Permission `jsi:kandidati:pii`. Spalten aus `server/src/jsi_mcp/skills/jsi-data-analyst/references/schema/osjetljive_kolone.md` **niemals** lesen/ausgeben.
- Abnahme der echten DB-Verbindung und der Schreib-Tools erfolgt **nach dem Deploy über den MCP selbst** (Nutzer bindet Connector ein). Claude-Cloud-Sessions erreichen MySQL nicht direkt (nur Port 443).

## Schritte
0. **Sicherheitscheck:** `gh api repos/d-selmanovic/JSI-MCP-Claude --jq .private` muss `true` sein. Sonst NICHTS pushen, Nutzer bitten, das Repo auf privat zu stellen, und warten.
1. Arbeitsstand übernehmen: `git clone --depth 1 https://github.com/dsactivi-2/jsi-mcp-claude /home/user/arbeitsstand-src` (öffentlich, nur lesen). Ins Ziel-Repo kopieren: `HANDOVER.md`, `CLAUDE.md`, `README.md`, `.gitignore`, `.env.example`, `plugin/`, `docs/`. `HANDOVER.md` + `CLAUDE.md` lesen.
2. Branch `feature/server-v1`. Server unter `server/` (eigenes `pyproject.toml` mit `uv.lock`, Python 3.12; Manufact erkennt Python über `pyproject.toml`). Port aus `PORT` (Default 3000), Pfad `/mcp`, Health `/health`.
3. **Lese-Tools** (v1), Logik aus `plugin/skills/jsi-kandidat-filter/scripts/build_query.py` (heute `server/src/jsi_mcp/build_query.py`) (unverändert als Modul übernehmen, Tests mitnehmen):
   - `search_candidates` (alle Filter-Spec-Schlüssel aus `jsi-kandidat-filter/SKILL.md`; `izlaz` broj/izvori/lista/id; `pii` nur mit Permission)
   - `filter_options` (gültige Werte/Codes je Filter, Berufskatalog aus `occupations.json`, Länder, Status-Codes)
   - `candidate_profile` (ein Kandidat, ohne PII außer mit Permission; nie [TAJNO])
   - `kpis` (Vermittlungen, Umsatz, Task-Force, Casting, DIPL-Funnel – Abfragen aus `jsi-data-analyst/references/metrics.md` und `tables/*.md`, Permission je Bereich, Finanzen → `jsi:finansije:read`)
   - `orders_overview`, `pipeline_history`
4. **Schreib-Tools:** `write_registry.yaml` (aus Schema generieren, fachlich konservativ: zuerst Kandidat, Kandidat-Sprachen/-Ausbildung/-Erfahrung/-Führerschein, Bewerbung/Pipeline-Status, Notizen, Auftrag-Zuordnung, Firma, Kontakt, DIPL-Kandidat-Verknüpfung; [TAJNO], PKs, Log/Audit/Event-Tabellen nie). Tools `record_preview` (dry_run, vorher/nachher) und `record_write` (create/update/archive, Permission `jsi:write:<entitaet>:<aktion>`), plus Prozess-Tool `set_application_status` inkl. Pipeline-Log (Logtabellen siehe `schema/02_pipeline_logovi.md`).
5. **DB-Zugriff:** PyMySQL, TLS mit CA aus `JSI_DB_CA_CERT` (PEM-Inhalt) oder Datei `certs/aiven-ca.pem`; Verbindungsdaten aus `JSI_DB_TARGET` → `JSI_MIRROR_DB_*` bzw. `JSI_DB_*`. Lese-Abfragen in Read-only-Transaktion, `MAX_EXECUTION_TIME`.
6. **Auth:** JWKS `https://<WORKOS_AUTHKIT_DOMAIN>/oauth2/jwks`, `iss`, `aud = JSI_MCP_PUBLIC_URL`; `/.well-known/oauth-protected-resource`. `JSI_AUTH_DISABLED=true` nur für lokale Tests, beim Start auf Manufact verweigern (z. B. wenn `JSI_MCP_PUBLIC_URL` https ist). Jeder Aufruf wird mit `sub`, Tool, Dauer, Zeilenzahl geloggt (ohne Inhalte/PII).
7. **Tests:** bestehende 15 Filter-Tests; Tool-Schemas; Permission-Matrix; JWT (eigene Testschlüssel); Schreib-Register-Validierung; Integration gegen **lokale MySQL 8.4 in Docker** mit Schema aus `docs/rohdaten/columns.json` für die genutzten Tabellen + synthetischen Daten (keine echten Personendaten). Lese-SQL zusätzlich über BlazeSQL (`execute_sql`, Tool per ToolSearch „blaze sql execute“ finden) gegen echte DB prüfen, z. B. Elektriker + Führerschein C (Referenz 2.676 am 2026-10-29).
8. **Deploy:** Manufact-Connector `create_server` (Org, GitHub-Verbindung, Repo oben, `branch feature/server-v1`, `rootDir server`, Name `JSI-MCP-Claude`, Region AUTO – EU erst ab höherem Plan, im Bericht erwähnen). Nicht-geheime Variablen setzen (`JSI_DB_TARGET=mirror`, `JSI_WRITES_ENABLED=false`). **Geheime Werte (DB-Passwort, WorkOS) NICHT selbst setzen** – Nutzer trägt sie im Manufact-Dashboard ein; Liste der Variablennamen liefern. Build-/Runtime-Logs prüfen, bis der Server läuft (ohne DB darf er starten und klare Konfigurationsfehler melden).
9. Draft-PR `feature/server-v1` → `main`. `server/README.md`: Setup, Variablen, WorkOS-Einrichtung (Resource Indicator, CIMD, Permissions/Rollen), SQL für minimalen DB-Benutzer (GRANTs ohne [TAJNO]-Spalten), Abnahmeliste.

## Bericht an den Orchestrator (letzte Antwort, max. 30 Zeilen)
MCP-URL, Manufact-Dashboard-URL, PR-Link, Tool-Liste, Testergebnisse (Zahlen), was nicht getestet werden konnte, offene Punkte, Variablen, die der Nutzer setzen muss. Nichts erfinden; Fehlschläge wörtlich.
