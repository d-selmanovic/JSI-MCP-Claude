# Connectors

## How tool references work

Plugin files refer to tool categories (data warehouse, product analytics, project tracker). At JSI these map to the tools below.

Plugins are **tool-agnostic** — they describe workflows in terms of categories (data warehouse, notebook, product analytics, etc.) rather than specific products. The `.mcp.json` pre-configures specific MCP servers, but any MCP server in that category works.

## Connectors for this plugin

| Category | Tool at JSI | Connection |
|----------|-------------|------------|
| Data warehouse | BlazeSQL → MySQL database "Mysql JSI" (schema `jsicrm`, recruiting CRM) | claude.ai connector "Blaze SQL" (tools `list_schemas`, `list_tables`, `describe_tables`, `execute_sql`, `graph_sql_result`) |
| Product analytics | Amplitude (project `default`, appId `100063413`) | `amplitude` in `.mcp.json` |
| Project tracker | Notion | `notion` in `.mcp.json` |
| Notebook | — (not used; analyses run directly via SQL/BlazeSQL) | — |

Default language for reports, dashboards and stakeholder summaries: **Bosnian** (keep SQL, table and column names in their original form).
