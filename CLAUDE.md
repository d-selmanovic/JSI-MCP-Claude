# Regeln für Claude-Sessions in diesem Repo

- Zuerst `HANDOVER.md` lesen (v. a. §0, §6, §13). Mit dem Nutzer Deutsch sprechen; Berichte für JSI auf Bosnisch.
- Niemals Spalten aus `server/src/jsi_mcp/skills/jsi-data-analyst/references/schema/osjetljive_kolone.md` selektieren, loggen oder dokumentieren (Passwörter, Tokens, JMBG, Pass, IBAN …).
- Personendaten (Name, Telefon, E-Mail) nur auf ausdrücklichen Wunsch; nie Beispielwerte aus der DB in Dateien übernehmen.
- Zugangsdaten nur aus Umgebungsvariablen (`JSI_MIRROR_DB_*`, später `JSI_DB_*`); nie ausgeben, nie committen.
- Schreibzugriffe nur gegen die Mirror-DB und nur über die definierten Schreib-Tools (mit `dry_run` + Audit). Nie gegen Produktion.
- Datenzugriff nur über den JSI-MCP-Server `jsi` (BlazeSQL ist seit 2026-10-30 von der MySQL getrennt). Freies SQL gegen die CRM-Datenbank nur über das Tool `sql_query`: nur lesend, nur mit `jsi:sql:read` (Rolle `jsi-admin-test`), jede Ausführung bestätigt der Mensch im Dialog des Servers. Für Fachfragen zuerst die festen Tools.
- Neue Abfragen im Server (`build_query.py`, `tools_read.py`): Kindtabellen in CTEs voraggregieren, kein korreliertes EXISTS über `idk_kandidati` (Timeout 30 s).
- Tests: Server `cd server && uv run pytest -q --ignore=tests/integration` (Such-Logik `build_query.py` liegt nur im Server). Hooks: `python3 -I -m unittest discover -s plugin/hooks -p 'test_*.py'` (Doku `docs/HOOKS.md`).

@AGENTS.md
