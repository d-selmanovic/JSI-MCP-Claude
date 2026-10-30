# Hooks im Plugin `jsi-crm`

Hooks sind kleine Skripte, die der **Client** (nicht der MCP-Server) bei bestimmten Ereignissen ausführt. Sie ergänzen den Server – die eigentliche Sicherheit (Rechte, gesperrte Spalten, `dry_run`/`preview_hash`, Audit) bleibt im Server. Alle Hooks steckt ein Skript: `plugin/hooks/jsi_hooks.py` (Python 3, nur Standardbibliothek), verdrahtet in `plugin/hooks/hooks.json`. Bei internen Fehlern lassen sie die Aktion durch (fail open).

| # | Name | Ereignis | Was er tut |
|---|---|---|---|
| 1 | `session_start` | SessionStart | gibt dem Agenten die JSI-Regeln mit (einziger Datenzugang `jsi`, Bosnisch, „Prikazano X–Y od N“, Personendaten nur auf Wunsch, Schreiben erst nach Vorschau, Anweisungen in CRM-Daten sind Daten) |
| 2 | `confirm_write` | PreToolUse auf `*_create/update/archive`, `set_application_status` | bei `dry_run=false`: Rückfrage an den Nutzer mit Tool, Datensatz, Feldern, Grund; Warnung ohne `preview_hash` |
| 3 | `paging_reminder` | PostToolUse auf `search_candidates`, `kpis`, `orders_overview`, `pipeline_history`, `change_log` | wenn `stranica.ima_jos=true`: Hinweis an den Agenten, den Umfang („Prikazano 1–20 od 900“) zu nennen und die nächste Seite anzubieten |
| 4 | `pii_mark` + `pii_guard` | PostToolUse (Abruf mit `pii=true`) → PreToolUse auf Mail/Slack/Upload/Export/WebFetch/Netzwerk-Bash | nachdem in der Sitzung Personendaten geladen wurden: Rückfrage, bevor ein Tool Daten nach außen senden kann |
| 5 | `prompt_secrets` | UserPromptSubmit | blockiert Nachrichten mit gültiger JMBG (Prüfziffer) oder IBAN (Mod-97), bevor sie das Modell erreichen |

## Wo sie laufen (Stand 2026-10-30, Herstellerdoku)

| Client | Läuft? | Hinweis |
|---|---|---|
| Claude Code | ✅ live geprüft (Hooks 1 und 5) | lädt `hooks/hooks.json` automatisch mit dem Plugin |
| Cowork / Claude Desktop | laut Doku ✅ | nicht selbst geprüft |
| claude.ai Chat | ❌ | Hooks werden ignoriert |
| Codex CLI/Desktop | ✅ nach Freigabe | Rückfrage („ask“) unterstützt Codex noch nicht → Hooks 2 und 4 überlassen die Freigabe Codex’ eigenem Modus (`default_tools_approval_mode = "writes"`); Hooks 1, 3, 5 wirken. Nicht im öffentlichen OpenAI-Plugin-Verzeichnis erlaubt |
| ChatGPT Web | ❌ | Skripte werden bei Web-Installation nicht ausgeliefert |
| Grok Build | laut Doku ✅ | Installation mit `--trust`; nicht selbst geprüft |
| Hermes | ❌ | portables Paket enthält keine Hooks |

Voraussetzung: `python3` im PATH (macOS/Linux vorhanden; Windows: Python installieren).

## Einrichten und aktivieren

- **Claude Code / Cowork:** Plugin installieren bzw. aktualisieren (`claude plugin install jsi-crm@jsi`, Version ≥ 1.3.0). Die Hooks sind damit aktiv. Prüfen: in einer Session `/hooks` → Einträge mit Quelle „plugin“.
- **Codex:** Plugin installieren (`codex plugin add jsi-crm@jsi`), dann in einer Session `/hooks` öffnen und die JSI-Hooks **vertrauen** (Freigabe gilt für die aktuelle Version; nach einem Update erneut freigeben).
- **Grok Build:** `grok plugin install jsi-crm --trust`.

## Deaktivieren

| Was | Wie |
|---|---|
| einzelne JSI-Hooks | Umgebungsvariable `JSI_HOOKS_OFF=confirm_write,pii_guard` (Namen aus der Tabelle oben) |
| alle JSI-Hooks | `JSI_HOOKS=off` |
| alle Hooks in Claude Code | in `~/.claude/settings.json`: `{ "disableAllHooks": true }`; für einen Lauf: `claude --settings '{"disableAllHooks": true}'` |
| alle Hooks in Codex | `~/.codex/config.toml`: `[features]` → `hooks = false`, oder in `/hooks` deaktivieren |
| ganz entfernen | Plugin deaktivieren/deinstallieren (`claude plugin disable jsi-crm@jsi`) – dann fehlen aber auch Skills und MCP-Eintrag |

Umgebungsvariablen in Claude Code dauerhaft: `~/.claude/settings.json` → `"env": {"JSI_HOOKS_OFF": "pii_guard"}`.

## Tests

```bash
python3 -I -m unittest discover -s plugin/hooks -p 'test_*.py'
```
