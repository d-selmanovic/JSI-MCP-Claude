# Installation: JSI-MCP-Server + Skills (Plugin `jsi-crm`)

Ein Repo, ein Plugin (`plugin/`), alle Plattformen. Wer das Plugin installiert, bekommt den MCP-Server `jsi` (`https://calm-steel-onjlq.run.mcp-use.com/mcp`) **automatisch konfiguriert** und dazu die Skills `jsi-mcp`, `jsi-kandidat-filter`, `jsi-data-analyst` (+ allgemeine Analyse-Skills).

**Einmaliger Schritt je Nutzer auf jeder Plattform: OAuth-Anmeldung** (WorkOS AuthKit, Konto mit JSI-Rolle). Keine Plattform dokumentiert eine automatische Anmeldung beim Installieren. Danach kennt der Agent die Tools über die Server-Instructions und den Skill `jsi-mcp`; den Projekt-Hinweis in `AGENTS.md` schreibt `plugin/skills/jsi-mcp/scripts/add_to_agents_md.py` (idempotent).

Stand der Formate: Primärquellen abgerufen 2026-10-30 (Links je Abschnitt). Nicht selbst auf der jeweiligen Plattform ausgeführt sind die mit ⚠️ markierten Schritte.

| Plattform | Paket-Dateien im Repo | Installation | Anmeldung |
|---|---|---|---|
| Claude Code ✅ | `.claude-plugin/marketplace.json`, `plugin/.claude-plugin/plugin.json`, `plugin/.mcp.json` | `claude plugin marketplace add d-selmanovic/JSI-MCP-Claude` → `claude plugin install jsi-crm@jsi` | `/mcp` → `jsi` → Authenticate |
| claude.ai / Cowork / Desktop | wie Claude Code | Customize → Plugins → Add → Add marketplace `d-selmanovic/JSI-MCP-Claude` | Plugin → Connectors → **Connect** |
| Codex (CLI/Desktop) | `.agents/plugins/marketplace.json`, `plugin/plugin.json`, `plugin/mcp.json`, `skills/*/agents/openai.yaml` | `codex plugin marketplace add d-selmanovic/JSI-MCP-Claude` → `codex plugin add jsi-crm@jsi` | in der Session über `/plugins` (⚠️); sicher: `codex mcp add jsi --url …` + `codex mcp login jsi` |
| ChatGPT (Web/Desktop) ⚠️ | wie Codex (Plugin-Verzeichnis ist gemeinsam) | chatgpt.com/plugins → „+“ → „Add custom MCP server“ → URL oben → OAuth → „Create as a plugin“ | im Dialog |
| Hermes Agent ⚠️ | `plugin/plugin.json`, `plugin/mcp.json`, `plugin/skills/` | `hermes plugins install d-selmanovic/JSI-MCP-Claude --no-enable` → `hermes plugins enable jsi-crm` | `hermes mcp login jsi` → `/reload-mcp` |
| Grok Build ⚠️ | `.claude-plugin/marketplace.json` (wird gelesen), `plugin/.mcp.json`, `plugin/skills/` | `grok plugin marketplace add d-selmanovic/JSI-MCP-Claude` → `grok plugin install jsi-crm --trust` | automatisch beim ersten Aufruf |

## Claude Code

```bash
claude plugin marketplace add d-selmanovic/JSI-MCP-Claude
claude plugin install jsi-crm@jsi
# in einer Session:
/mcp            # jsi → Authenticate (Browser, WorkOS-Login)
```
Live geprüft am 2026-10-30 mit Claude Code 2.1.314: `claude plugin validate` ✅, Marketplace + Install ✅, `claude mcp list` zeigt `plugin:jsi-crm:jsi … (HTTP) – Needs authentication` ✅ (Server automatisch eingetragen, Anmeldung offen). Claude Code startet die MCP-Server eines aktivierten Plugins automatisch; Tools heißen `mcp__plugin_jsi-crm_jsi__<tool>`. CIMD/DCR erkennt Claude Code selbst. Projekt-Hinweis: `AGENTS.md` mit dem JSI-Block und in `CLAUDE.md` die Zeile `@AGENTS.md` (Claude Code liest `AGENTS.md` nur, wenn es keine `CLAUDE.md` gibt).
Quellen: https://code.claude.com/docs/en/plugins-reference · https://code.claude.com/docs/en/plugin-marketplaces · https://code.claude.com/docs/en/mcp

## claude.ai / Cowork / Claude Desktop

- **Plugin:** Customize → Plugins → Add → „Add marketplace“ → `d-selmanovic/JSI-MCP-Claude` → `jsi-crm` installieren. Der Server erscheint im Connectors-Tab des Plugins; **Connect** klicken (Installation verbindet nicht automatisch).
- **Ohne Plugin:** Customize → Connectors → „+ Add“ → „Add custom connector“ → URL oben → „Use Claude's published identity“ oder „Register automatically“. Skills dann einzeln als ZIP: Customize → Skills → „Upload a skill“ (Ordner `plugin/skills/<name>` zippen; Code-Ausführung muss aktiv sein).
Quellen: https://claude.com/docs/plugins/build · https://claude.com/docs/cowork/guide/plugins

## Codex (CLI / Desktop)

Live geprüft am 2026-10-30 mit `codex-cli 0.166.0`:
```bash
codex plugin marketplace add d-selmanovic/JSI-MCP-Claude   # liest .agents/plugins/marketplace.json  ✅
codex plugin add jsi-crm@jsi                               # Status: installed, enabled            ✅
```
Der MCP-Server aus `plugin/mcp.json` ist danach **nicht** unter `codex mcp list` sichtbar (`codex mcp login jsi` → „No MCP server named 'jsi' found“). Ob Codex ihn in der Session lädt und über `/plugins` anmeldet, ist ⚠️ nicht geprüft (braucht ein OpenAI-Konto). Sicherer Weg, live geprüft bis zum WorkOS-Login-Link mit korrekter `resource`:
```bash
codex mcp add jsi --url https://calm-steel-onjlq.run.mcp-use.com/mcp     ✅
codex mcp login jsi        # öffnet https://balanced-lantern-65-staging.authkit.app/oauth2/authorize?…  ✅
```
Entspricht in `~/.codex/config.toml` (oder projektweit `.codex/config.toml`):
```toml
[mcp_servers.jsi]
url = "https://calm-steel-onjlq.run.mcp-use.com/mcp"
```
Skills ohne Plugin: Ordner nach `.agents/skills/` (Projekt) oder `~/.agents/skills/` kopieren. Codex liest `AGENTS.md` nativ. Plugins laufen laut Doku nicht in der IDE-Extension.
Quellen: https://developers.openai.com/plugins/build/plugins · https://learn.chatgpt.com/docs/extend/mcp.md · https://learn.chatgpt.com/docs/agent-configuration/agents-md.md

## ChatGPT ⚠️

chatgpt.com/plugins → „+“ → „Add custom MCP server“ → Server-URL oben → Authentifizierung OAuth → „Create as a plugin“. Veröffentlichen im Workspace nur durch Admins (Personal → ⋯ → Publish). Die Plugin-Installation verbindet das Konto nicht; jeder Nutzer meldet sich einmal an. Eigenständige Skill-ZIPs für ChatGPT: Format nicht verifiziert.
Quelle: https://developers.openai.com/api/docs/guides/custom-mcp-server.md

## Hermes Agent (Nous Research) ⚠️

```bash
hermes plugins install d-selmanovic/JSI-MCP-Claude --no-enable
hermes plugins enable jsi-crm
```
OAuth aus dem Paket-`mcp.json` ist nicht verifiziert – sicherer zusätzlich in `~/.hermes/config.yaml` (Eintrag dort gewinnt):
```yaml
mcp_servers:
  jsi:
    url: "https://calm-steel-onjlq.run.mcp-use.com/mcp"
    auth: oauth
```
Dann `hermes mcp login jsi` und `/reload-mcp`. Skills ohne Plugin: `~/.hermes/skills/` oder `<projekt>/.agents/skills/`. Hermes lädt pro Session eine Kontextdatei (`.hermes.md` → `AGENTS.override.md` → `AGENTS.md` → `CLAUDE.md`).
Quelle: github.com/NousResearch/hermes-agent `website/docs/reference/mcp-config-reference.md`, `user-guide/features/{mcp,skills,context-files}.md`

## Grok Build (xAI) ⚠️

```bash
grok plugin marketplace add d-selmanovic/JSI-MCP-Claude     # liest .claude-plugin/marketplace.json
grok plugin install jsi-crm --trust                         # MCP bleibt ohne --trust inaktiv
```
Nur MCP: `grok mcp add --transport http jsi https://calm-steel-onjlq.run.mcp-use.com/mcp`. Grok liest `AGENTS.md` und `CLAUDE.md`. Über die xAI-API (`tools: [{"type":"mcp","server_url":…}]`) gibt es kein interaktives OAuth – dort müsste ein Bearer-Token übergeben werden.
Quellen: https://docs.x.ai/docs/guides/tools/remote-mcp-tools · github.com/xai-org/grok-build `docs/user-guide/{07-mcp-servers,08-skills,09-plugins,12-project-rules}.md`

## Voraussetzungen auf Server-Seite (Stand 2026-10-30, live geprüft)

- WorkOS (Staging-Umgebung, AuthKit `balanced-lantern-65-staging.authkit.app`): DCR + CIMD aktiv, Resource `https://calm-steel-onjlq.run.mcp-use.com/mcp` eingetragen, Rollen `jsi-reader`, `jsi-analyst`, `jsi-admin-test`.
- Nutzer brauchen eine Mitgliedschaft mit JSI-Rolle; ohne Rolle liefern die Tools `forbidden`.
- Eine neue Server-URL (z. B. Preview-Branch) muss zusätzlich als WorkOS-Resource eingetragen werden, sonst scheitert die Token-Audience.
