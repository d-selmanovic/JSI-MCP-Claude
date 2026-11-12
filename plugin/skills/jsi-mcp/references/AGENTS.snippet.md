<!-- JSI-MCP:BEGIN (managed by jsi-crm plugin – do not edit inside the markers) -->
## JSI CRM (MCP server `jsi`)

This agent has the **JSI MCP server** `jsi` (`https://calm-steel-onjlq.run.mcp-use.com/mcp`, OAuth via WorkOS) for the JSI recruiting CRM.

- Use its tools for every question about JSI candidates, orders, pipeline/application status, placements, task force, castings, DIPL and KPIs: `search_candidates`, `filter_options`, `candidate_profile`, `kpis`, `orders_overview`, `pipeline_history`, `change_log`, `whoami`, and for all other CRM tables `table_describe` + `table_read` (per-area permissions). Free SQL only via `sql_query` (read-only, permission `jsi:sql:read` for admins/developers, every run confirmed by the human in the server's dialog; clients without that dialog are refused) – otherwise never write SQL against the CRM yourself.
- Write tools – one per entity and action, e.g. `candidate_update`, `candidate_note_create`, `company_create`, `candidate_archive`, plus `set_application_status` only on explicit request; always preview / `dry_run=true` first and write only after the user confirms.
- Answer JSI users in Bosnian unless asked otherwise. Personal data (name, phone, e-mail) only on explicit request and with permission `jsi:kandidati:pii`; never select or log [TAJNO] columns (passwords, tokens, JMBG, passport, IBAN).
- If the tools are missing, the user must sign in once (Claude Code `/mcp`, Codex `codex mcp add jsi --url <URL>` + `codex mcp login jsi`, Hermes `hermes mcp login jsi`, claude.ai/ChatGPT: Connect in the connector settings).
- Know-how (status codes, metric definitions, filters, schema, analysis methods) comes from the server as skills: tool `skill_lesen` (catalogue; e.g. `skill_lesen(skill='jsi-data-analyst')` before analyses, `jsi-kandidat-filter` for candidate filters). Hosts with the MCP skills extension load them automatically (`skills/list`). Client skill: `jsi-mcp`.
<!-- JSI-MCP:END -->
