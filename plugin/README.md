# JSI CRM Plugin (`jsi-crm`)

Connects the agent to the **JSI MCP server** (`jsi`, `https://calm-steel-onjlq.run.mcp-use.com/mcp`, OAuth via WorkOS). Slim package: connection, hooks and the pointer skill `jsi-mcp`. Logic and know-how live on the server.

## Installation

```
/plugin install jsi-crm --marketplace d-selmanovic/JSI-MCP-Claude
```
or `claude plugin marketplace add d-selmanovic/JSI-MCP-Claude` + `claude plugin install jsi-crm@jsi`. Then `/mcp` → `jsi` → Authenticate. Codex, ChatGPT, Hermes, Grok, claude.ai: see `../docs/INSTALLATION.md`.

## Contents

| Part | What it does |
|------|--------------|
| `.mcp.json` / `mcp.json` | Configures the MCP server `jsi` |
| `hooks/` | Context at session start, confirmation before writes, paging hint, personal-data guard, JMBG/IBAN block – see `../docs/HOOKS.md` |
| `skills/jsi-mcp` | Which tool answers which question, data-protection rules, sign-in help, `AGENTS.md` snippet |
| `skills/sql-queries`, `skills/write-query`, `skills/data-context-extractor` | Generic SQL skills (based on Anthropic's data plugin, Apache-2.0, see `LICENSE`). At JSI there is no SQL access – SQL written with them is for review only |

## Skills on the server

The JSI know-how skills are served by the MCP server itself (`server/src/jsi_mcp/skills/`), so every connected client gets the current version without a plugin update:

| Skill | Content |
|-------|---------|
| `jsi-data-analyst` | Entities, status codes, metric definitions, standard filters, schema of all 190 tables, wiring |
| `jsi-kandidat-filter` | Filter keys for `search_candidates` (occupation across 6 sources, driving licence EU rules, language/certificate, …) |
| `analyze`, `explore-data`, `build-dashboard`, `create-viz`, `data-visualization`, `statistical-analysis`, `validate-data` | Analysis and visualisation methods (based on Anthropic's data plugin, Apache-2.0) |

Access: tool `skill_lesen` (all clients; no argument = catalogue) and the MCP skills extension `io.modelcontextprotocol/skills` (`skills/list`, `skills/get`, `skill://<name>/…` via `resources/read`) for hosts that support it.
