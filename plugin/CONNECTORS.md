# Connectors

## How tool references work

Plugin files refer to tool categories (e.g. data warehouse). At JSI these map to the tools below.

Plugins are **tool-agnostic** — they describe workflows in terms of categories (data warehouse, notebook, product analytics, etc.) rather than specific products. The `.mcp.json` pre-configures specific MCP servers, but any MCP server in that category works.

## Connectors for this plugin

| Category | Tool at JSI | Connection |
|----------|-------------|------------|
| JSI CRM (only data access) | JSI MCP server – tools `search_candidates`, `kpis`, `orders_overview`, … (OAuth via WorkOS) | `jsi` in `.mcp.json` / `mcp.json` |
| Data warehouse / free SQL | — (BlazeSQL disconnected 2026-10-30; no direct SQL access) | — |
| Notebook | — (not used) | — |

Default language for reports, dashboards and stakeholder summaries: **Bosnian** (keep SQL, table and column names in their original form).
