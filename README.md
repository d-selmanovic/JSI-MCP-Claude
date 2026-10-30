# jsi-mcp-claude

Eigener MCP-Server für das JSI-Recruiting-CRM (MySQL, Schema `jsicrm`) mit festen, getesteten Tools statt freiem SQL – plus das angepasste Claude-Plugin „data“ als Wissensschicht.

| Pfad | Inhalt |
|---|---|
| `HANDOVER.md` | **Zuerst lesen.** Ziel, Entscheidungen (§0, §13), Erkenntnisse, Fallen, offene Fragen |
| `plugin/` | Angepasstes Plugin inkl. Skills `jsi-data-analyst` (Schema-/Verknüpfungsdoku) und `jsi-kandidat-filter` (`build_query.py`) |
| `docs/rohdaten/` | Schema-Metadaten (`information_schema`), Zeilenzahlen, Zeiträume, gemessene Verknüpfungen – keine Personendaten |
| `server/` | MCP-Server (folgt) |

Sicherheit: keine Zugangsdaten im Repo; Secrets nur als Umgebungsvariablen. Spalten aus `plugin/skills/jsi-data-analyst/references/schema/osjetljive_kolone.md` werden nie gelesen oder ausgegeben.
