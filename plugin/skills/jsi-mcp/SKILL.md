---
name: jsi-mcp
description: "You have the JSI MCP server (server name 'jsi', https://calm-steel-onjlq.run.mcp-use.com/mcp) for the JSI recruiting CRM. Use it whenever the user asks about JSI candidates (kandidati), orders (nalozi), pipeline/application status, placements, task force, castings, DIPL or JSI KPIs – e.g. 'koliko električara imamo', 'wie viele Schweißer aus BiH sind frei', 'Vermittlungen 2025', 'pregled naloga 254'. Explains which tool to call, the data-protection rules and how to sign in if the tools are missing."
---

# JSI MCP server

The JSI CRM (MySQL `jsicrm`, mirror database) is reachable through the MCP server **`jsi`**. Tool names may carry a client prefix (Claude Code plugin: `mcp__plugin_jsi-crm_jsi__<tool>`, otherwise e.g. `mcp__jsi__<tool>`). Prefer these tools over BlazeSQL or hand-written SQL – they apply the tested filter logic, metric definitions, permissions and the [TAJNO] column ban server-side.

## Tools

| Question | Tool | Notes |
|---|---|---|
| Who am I, which permissions, server/DB status | `whoami` | Call first if a tool reports `forbidden`. |
| Find / count / list candidates | `search_candidates` | Filter keys and examples: skill `jsi-kandidat-filter`. Default output is a count (`izlaz: "broj"`). |
| Valid filter values, codes, occupation catalogue | `filter_options` | Optional `section`, e.g. `berufsgruppen`, `status_prijave`, `katalog`. |
| One candidate | `candidate_profile` | Needs `kandidat_id`. |
| KPIs | `kpis` | `bereich`: vermittlungen, neue_kandidaten, pipeline_bestand, umsatz (needs `jsi:finansije:read`), task_force, casting, dipl_funnel (needs `jsi:dipl:read`). |
| Orders: demand vs. candidates vs. signed | `orders_overview` | |
| Status history of a candidate or per period | `pipeline_history` | |
| What the MCP wrote | `change_log` | Needs `jsi:audit:read`. |
| Writes | one tool per entity and action: `candidate_create/update/archive`, `candidate_driving_licence_update`, `candidate_language_create/update`, `candidate_education_create/update`, `candidate_experience_create/update`, `candidate_note_create`, `candidate_order_update`, `project_member_create`, `candidate_dipl_link_update`, `company_create/update`, `contact_create/update`; pipeline status: `set_application_status` | **Only on explicit user request.** Call with `dry_run=true` (default) first, show the preview, then call again with `dry_run=false` and the returned `preview_hash` after the user confirms. Each tool needs `jsi:write:<entity>:<action>`. |

Metric definitions and status codes: skill `jsi-data-analyst`.

## Rules

- Answer JSI users in **Bosnian** unless asked otherwise; keep table/column names as they are.
- Personal data (name, phone, e-mail, note texts) only on explicit request (`pii=true`) and only with permission `jsi:kandidati:pii`. Never copy example values from the database into files.
- Never ask for, select or log [TAJNO] columns (passwords, tokens, JMBG, passport, IBAN …) – the server refuses them anyway.
- Report counts first, then breakdowns, then the filter notes the tool returns (data coverage caveats).
- If a tool returns `forbidden`, say which permission is missing (see `whoami`) – do not work around it with SQL.

## Wire it into the project (AGENTS.md)

On first use in a project, check whether its `AGENTS.md` contains the block `<!-- JSI-MCP:BEGIN`. If not, offer to add it so every agent working there (Codex, Hermes, Grok, Claude Code via `@AGENTS.md`) knows these tools exist:

```bash
python3 -I ${CLAUDE_SKILL_DIR}/scripts/add_to_agents_md.py AGENTS.md      # idempotent; --remove takes it out again
```

(`${CLAUDE_SKILL_DIR}` = this skill's folder; on other clients use its path.) The block text is `references/AGENTS.snippet.md`. Only write after the user agrees.

## If the tools are not available

The server uses OAuth (WorkOS AuthKit). Installing the plugin configures it, but every user signs in once:

| Client | Sign in |
|---|---|
| Claude Code | `/mcp` → `jsi` → Authenticate |
| claude.ai / Cowork / Desktop | Plugin → Connectors tab → **Connect** (or Customize → Connectors → Add custom connector with the URL above) |
| Codex CLI | `codex mcp add jsi --url https://calm-steel-onjlq.run.mcp-use.com/mcp`, then `codex mcp login jsi` |
| ChatGPT | chatgpt.com/plugins → the JSI plugin/connector → Connect |
| Hermes Agent | `hermes mcp login jsi`, then `/reload-mcp` |
| Grok Build | `grok mcp` (OAuth starts on first use) |

Setup per platform: `docs/INSTALLATION.md` in https://github.com/d-selmanovic/JSI-MCP-Claude.
