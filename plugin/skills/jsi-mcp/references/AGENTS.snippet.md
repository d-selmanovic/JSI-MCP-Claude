<!-- JSI-MCP:BEGIN (managed by jsi-crm plugin – do not edit inside the markers) -->
## JSI CRM (MCP server `jsi`)

This agent has the **JSI MCP server** `jsi` (`https://calm-steel-onjlq.run.mcp-use.com/mcp`, OAuth via WorkOS) for the JSI recruiting CRM.

- Use its tools for every question about JSI candidates, orders, pipeline/application status, placements, task force, castings, DIPL and KPIs: `search_candidates`, `filter_options`, `candidate_profile`, `kpis`, `orders_overview`, `pipeline_history`, `change_log`, `whoami`. Prefer them over BlazeSQL or hand-written SQL.
- Write tools (`record_preview`, `record_write`, `set_application_status`) only on explicit request; always preview / `dry_run=true` first and write only after the user confirms.
- Answer JSI users in Bosnian unless asked otherwise. Personal data (name, phone, e-mail) only on explicit request and with permission `jsi:kandidati:pii`; never select or log [TAJNO] columns (passwords, tokens, JMBG, passport, IBAN).
- If the tools are missing, the user must sign in once (Claude Code `/mcp`, Codex `codex mcp add jsi --url <URL>` + `codex mcp login jsi`, Hermes `hermes mcp login jsi`, claude.ai/ChatGPT: Connect in the connector settings).
- Details: skills `jsi-mcp`, `jsi-kandidat-filter`, `jsi-data-analyst`.
<!-- JSI-MCP:END -->
