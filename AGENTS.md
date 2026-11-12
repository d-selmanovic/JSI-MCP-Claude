# AGENTS.md – JSI-MCP-Claude

Regeln für alle Coding-Agents (Codex, Hermes, Grok, Claude Code) in diesem Repo. Claude Code liest zusätzlich `CLAUDE.md` (importiert diese Datei).

## Repo-Regeln

- Zuerst `HANDOVER.md` lesen (v. a. §0, §6, §13). Mit dem Nutzer Deutsch sprechen; Berichte für JSI auf Bosnisch.
- Niemals Spalten aus `server/src/jsi_mcp/skills/jsi-data-analyst/references/schema/osjetljive_kolone.md` selektieren, loggen oder dokumentieren (Passwörter, Tokens, JMBG, Pass, IBAN …).
- Personendaten (Name, Telefon, E-Mail) nur auf ausdrücklichen Wunsch; nie Beispielwerte aus der DB in Dateien übernehmen.
- Zugangsdaten nur aus Umgebungsvariablen (`JSI_MIRROR_DB_*`, später `JSI_DB_*`); nie ausgeben, nie committen.
- Schreibzugriffe nur gegen die Mirror-DB und nur über die definierten Schreib-Tools (mit `dry_run` + Audit). Nie gegen Produktion.
- Datenzugriff nur über den JSI-MCP-Server `jsi` (BlazeSQL ist seit 2026-10-30 von der MySQL getrennt). Freies SQL gegen die CRM-Datenbank nur über das Tool `sql_query`: nur lesend, nur mit `jsi:sql:read` (Rolle `jsi-admin-test`), jede Ausführung bestätigt der Mensch im Dialog des Servers. Für Fachfragen zuerst die festen Tools.
- Neue Abfragen im Server (`build_query.py`, `tools_read.py`): Kindtabellen in CTEs voraggregieren, kein korreliertes EXISTS über `idk_kandidati` (Timeout 30 s).
- Tests: Server `cd server && uv run pytest -q --ignore=tests/integration` (Such-Logik `build_query.py` liegt nur im Server). Hooks: `python3 -I -m unittest discover -s plugin/hooks -p 'test_*.py'` (Doku `docs/HOOKS.md`).

## Struktur

- `server/` – Python-MCP-Server (Streamable HTTP `/mcp`, WorkOS AuthKit). Tests: `cd server && uv run pytest -q --ignore=tests/integration`.
- `plugin/` – schlankes Plugin `jsi-crm` (MCP-Verbindung, Hooks, Skill `jsi-mcp`) für Claude, Codex/ChatGPT, Hermes, Grok. Fach-Skills liegen im Server (`server/src/jsi_mcp/skills/`, ausgeliefert über `skill_lesen` und die MCP-Skills-Extension). Installation: `docs/INSTALLATION.md`.
- `.claude-plugin/marketplace.json`, `.agents/plugins/marketplace.json` – Marketplaces für `owner/repo`-Installation.

<!-- JSI-MCP:BEGIN (managed by jsi-crm plugin – do not edit inside the markers) -->
## JSI CRM (MCP server `jsi`)

This agent has the **JSI MCP server** `jsi` (`https://calm-steel-onjlq.run.mcp-use.com/mcp`, OAuth via WorkOS) for the JSI recruiting CRM.

- Use its tools for every question about JSI candidates, orders, pipeline/application status, placements, task force, castings, DIPL and KPIs: `search_candidates`, `filter_options`, `candidate_profile`, `kpis`, `orders_overview`, `pipeline_history`, `change_log`, `whoami`, and for all other CRM tables `table_describe` + `table_read` (per-area permissions). Free SQL only via `sql_query` (read-only, permission `jsi:sql:read` for admins/developers, every run confirmed by the human in the server's dialog; clients without that dialog are refused) – otherwise never write SQL against the CRM yourself.
- Write tools – one per entity and action, e.g. `candidate_update`, `candidate_note_create`, `company_create`, `candidate_archive`, plus `set_application_status` only on explicit request; always preview / `dry_run=true` first and write only after the user confirms.
- Answer JSI users in Bosnian unless asked otherwise. Personal data (name, phone, e-mail) only on explicit request and with permission `jsi:kandidati:pii`; never select or log [TAJNO] columns (passwords, tokens, JMBG, passport, IBAN).
- If the tools are missing, the user must sign in once (Claude Code `/mcp`, Codex `codex mcp add jsi --url <URL>` + `codex mcp login jsi`, Hermes `hermes mcp login jsi`, claude.ai/ChatGPT: Connect in the connector settings).
- Know-how (status codes, metric definitions, filters, schema, analysis methods) comes from the server as skills: tool `skill_lesen` (catalogue; e.g. `skill_lesen(skill='jsi-data-analyst')` before analyses, `jsi-kandidat-filter` for candidate filters). Hosts with the MCP skills extension load them automatically (`skills/list`). Client skill: `jsi-mcp`.
<!-- JSI-MCP:END -->

<!-- graphify-rules-start (managed by `graphify init`) -->
## Use Graphify before grep

This repository is indexed by Graphify: a code graph over its call, dependency, and test structure, exposed through a connected Graphify MCP server. Before reaching for grep or reading files, use the Graphify tools your MCP client lists (their exact names and descriptions are in the server's tool list) for what the graph knows and a text search does not:

- find where a symbol, function, or class is defined (instead of grepping for it)
- understand how something works, or where a behavior is handled
- find who calls a function, or what it calls
- see what a change affects (its blast radius) and which tests cover it
- map a file's dependencies and dependents

Fall back to grep or file reads only for what the graph does not model: literal string or comment matches, non-indexed files, or reading a file you have already located. If no Graphify tools are listed, check the MCP server connection.
<!-- graphify-rules-end -->
