# jsi-mcp-claude

Eigener MCP-Server für das JSI-Recruiting-CRM (MySQL, Schema `jsicrm`) mit festen, getesteten Tools statt freiem SQL – plus das angepasste Claude-Plugin „data“ als Wissensschicht.

| Pfad | Inhalt |
|---|---|
| `HANDOVER.md` | **Zuerst lesen.** Ziel, Entscheidungen (§0, §13), Erkenntnisse, Fallen, offene Fragen |
| `plugin/` | Schlankes Plugin `jsi-crm`: MCP-Verbindung, Hooks, Skill `jsi-mcp` (+ SQL-Skills `sql-queries`, `write-query`, `data-context-extractor`) |
| `server/src/jsi_mcp/skills/` | Fach-Skills (`jsi-data-analyst` mit Schema-/Verknüpfungsdoku, `jsi-kandidat-filter`, Analyse-Skills) – vom Server ausgeliefert (`skill_lesen`, MCP-Skills-Extension `skills/list`, `skill://`) |
| `docs/rohdaten/` | Schema-Metadaten (`information_schema`), Zeilenzahlen, Zeiträume, gemessene Verknüpfungen – keine Personendaten |
| `server/` | MCP-Server (folgt) |

Sicherheit: keine Zugangsdaten im Repo; Secrets nur als Umgebungsvariablen. Spalten aus `server/src/jsi_mcp/skills/jsi-data-analyst/references/schema/osjetljive_kolone.md` werden nie gelesen oder ausgegeben.
