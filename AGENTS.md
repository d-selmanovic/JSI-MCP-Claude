# AGENTS.md – JSI-MCP-Claude

Regeln für alle Coding-Agents (Codex, Hermes, Grok, Claude Code) in diesem Repo. Claude Code liest zusätzlich `CLAUDE.md` (importiert diese Datei).

## Repo-Regeln

- Zuerst `HANDOVER.md` lesen (v. a. §0, §6, §13). Mit dem Nutzer Deutsch sprechen; Berichte für JSI auf Bosnisch.
- Niemals Spalten aus `plugin/skills/jsi-data-analyst/references/schema/osjetljive_kolone.md` selektieren, loggen oder dokumentieren (Passwörter, Tokens, JMBG, Pass, IBAN …).
- Personendaten (Name, Telefon, E-Mail) nur auf ausdrücklichen Wunsch; nie Beispielwerte aus der DB in Dateien übernehmen.
- Zugangsdaten nur aus Umgebungsvariablen (`JSI_MIRROR_DB_*`, später `JSI_DB_*`); nie ausgeben, nie committen.
- Schreibzugriffe nur gegen die Mirror-DB und nur über die definierten Schreib-Tools (mit `dry_run` + Audit). Nie gegen Produktion.
- BlazeSQL-Tools können je Session anders heißen (`mcp__<id>__execute_sql`); per ToolSearch „blaze sql execute“ finden. Timeout 60 s → Kindtabellen in CTEs voraggregieren, kein korreliertes EXISTS über `idk_kandidati`.
- Tests: `python3 -I -m unittest discover -s plugin/skills/jsi-kandidat-filter/scripts -p 'test_*.py'`.

## Struktur

- `server/` – Python-MCP-Server (Streamable HTTP `/mcp`, WorkOS AuthKit). Tests: `cd server && uv run pytest -q --ignore=tests/integration`.
- `plugin/` – Plugin `jsi-crm` (Skills + MCP-Konfiguration) für Claude, Codex/ChatGPT, Hermes, Grok. Installation: `docs/INSTALLATION.md`.
- `.claude-plugin/marketplace.json`, `.agents/plugins/marketplace.json` – Marketplaces für `owner/repo`-Installation.

<!-- JSI-MCP:BEGIN (managed by jsi-crm plugin – do not edit inside the markers) -->
## JSI CRM (MCP server `jsi`)

This agent has the **JSI MCP server** `jsi` (`https://calm-steel-onjlq.run.mcp-use.com/mcp`, OAuth via WorkOS) for the JSI recruiting CRM.

- Use its tools for every question about JSI candidates, orders, pipeline/application status, placements, task force, castings, DIPL and KPIs: `search_candidates`, `filter_options`, `candidate_profile`, `kpis`, `orders_overview`, `pipeline_history`, `change_log`, `whoami`. Prefer them over BlazeSQL or hand-written SQL.
- Write tools (`record_preview`, `record_write`, `set_application_status`) only on explicit request; always preview / `dry_run=true` first and write only after the user confirms.
- Answer JSI users in Bosnian unless asked otherwise. Personal data (name, phone, e-mail) only on explicit request and with permission `jsi:kandidati:pii`; never select or log [TAJNO] columns (passwords, tokens, JMBG, passport, IBAN).
- If the tools are missing, the user must sign in once (Claude Code `/mcp`, Codex `codex mcp add jsi --url <URL>` + `codex mcp login jsi`, Hermes `hermes mcp login jsi`, claude.ai/ChatGPT: Connect in the connector settings).
- Details: skills `jsi-mcp`, `jsi-kandidat-filter`, `jsi-data-analyst`.
<!-- JSI-MCP:END -->
