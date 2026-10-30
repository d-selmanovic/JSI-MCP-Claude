# BUILD_LOG – JSI-MCP-Claude Server v1

## 2026-10-30

- **Schritt 0 – Sicherheitscheck: FEHLGESCHLAGEN.** GitHub-API (`search_repositories repo:d-selmanovic/JSI-MCP-Claude`) meldet `"private": false`, `"visibility": "public"`. → **Kein Push, kein PR, kein Manufact-Deploy**, bis der Nutzer das Repo auf privat stellt. Lokale Arbeit läuft weiter.
- Schritt 1: Arbeitsstand aus `dsactivi-2/jsi-mcp-claude` (depth 1) übernommen: `HANDOVER.md`, `CLAUDE.md`, `README.md`, `.gitignore`, `.env.example`, `plugin/`, `docs/`.
- Schritt 2: Branch `feature/server-v1` lokal angelegt; `server/` mit `pyproject.toml` (Python 3.12, uv). MCP-SDK auf PyPI ist **`mcp` 2.3.0**: `FastMCP` heißt dort `mcp.server.mcpserver.MCPServer` (Modul `mcp.server.fastmcp` existiert nur noch als Fehlermeldung). Server nutzt daher `MCPServer` (Nachfolger von FastMCP im offiziellen SDK).
- BlazeSQL-Referenz „Elektriker + Führerschein C“ (SQL unverändert aus `build_query.py`): **2.672** (2026-10-30) vs. 2.676 (2026-10-29) → Abweichung 4, wahrscheinlich Datenänderung seit gestern (nicht belegt).
- BlazeSQL: `COLUMN_DEFAULT`/`EXTRA` der Schreib-Tabellen gelesen → `docs/rohdaten/column_defaults.json` (nötig für lokales DDL und Pflichtfeld-Prüfung bei `create`).
- BlazeSQL: `idk_notes.note_group` gemessen: Gruppe 2 = 182.850 Notizen, davon 182.808 mit gültiger `kandidat_id` → **Annahme: Gruppe 2 = Kandidat** (Schlussfolgerung, nicht dokumentiert). Andere Gruppen (1, 3–8) nicht eindeutig → Schreib-Tool legt nur Kandidaten-Notizen an (Gruppe 2).
- BlazeSQL: Code-Verteilungen gelesen (keine Personendaten): `company_status` 0–5, `contact_status` 0/1, `kj_*`-Niveaus (A1–C2, „Bez znanja“, Altwerte), `ke_vrsta_obrazovanja` srednje/visoko/ostalo, `nalog_status` 1,3–8,10–12, `project_status` 0/1.
- Docker-Daemon in der Session gestartet (`dockerd`), Image `mysql:8.4` für Integrationstests.
- BlazeSQL: `lsp_broj_dana` gemessen (Log seit 2025, 46.185 Zeilen): = Tage im Status, beim nächsten Wechsel in die **vorherige** Zeile geschrieben (27.300/27.313 ±1 Tag; 20.949 exakt `DATEDIFF`); letzte Zeile je Kandidat immer NULL. → so in `set_application_status` umgesetzt.
- BlazeSQL: `kj_naziv`-Werte gelesen (Njemački 69.999, Engleski 11.879, Talijanski, Španjolski, Francuski, Ruski, Arapski …) → Enum im Register.
- Server gebaut (`server/`): 11 Tools (`whoami`, `search_candidates`, `filter_options`, `candidate_profile`, `kpis`, `orders_overview`, `pipeline_history`, `change_log`, `record_preview`, `record_write`, `set_application_status`), WorkOS-JWT-Prüfung, Schreib-Register (12 Entitäten), GRANT-Generator, DDL-Generator, Dockerfile.
- **Tests: 127 passed** (91 Unit inkl. 15 Filter-Tests, Schemas, Permission-Matrix, JWT, Register; 36 Integration gegen lokale MySQL 8.4.13 mit `ONLY_FULL_GROUP_BY`+Strict, Schema aller 190 Tabellen aus `columns.json`, synthetische Daten, Server läuft dabei als DB-Benutzer mit den generierten GRANTs).
- Lese-SQL gegen echte DB (BlazeSQL, Literal-SQL aus `scripts/render_sql.py`): Vermittlungen 299/536/71/24/1 ✅, Bestand 854 ✅, Umsatz 2023 430.050 / 1.819.207,36 / 239.716,92 ✅, DIPL 2021–2024 = Referenz ✅, Casting 3.828 Reservierungen ✅, Auftrag 254 = 300/900/165 ✅, Profil-SQL (mit nicht existierender ID) fehlerfrei ✅, Elektriker+C 2.672 (Ref. 2.676 vom Vortag).
- Smoke-Test: uvicorn-Prozess + MCP-Client über HTTP (11 Tools gelistet, Suche ok); Docker-Image gebaut (nur in der Session mit Proxy-Build-Args) und gestartet: ohne Konfiguration `degraded` + 503 mit Klartext, mit WorkOS-Konfig 401 + `resource_metadata`, `JSI_AUTH_DISABLED` mit https-URL → Start verweigert.
- **Nicht gemacht (wegen Schritt 0):** Push, Draft-PR, Manufact `create_server`, Variablen auf Manufact, Build-/Runtime-Logs. Commit liegt nur lokal auf `feature/server-v1`.
