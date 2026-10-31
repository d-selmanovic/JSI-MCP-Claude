# HANDOVER – JSI Data-Plugin / Tool-Calling (Stand 2026-10-29)

Lies diese Datei zuerst. Antworte dem Nutzer auf **Deutsch** (Berichte für JSI auf **Bosnisch**). Nutzerpräferenzen: präzise, kritisch, Fakten vs. Annahmen trennen, nichts erfinden.

## 0. ENTSCHEIDUNG 2026-10-29: Eigener JSI-MCP-Server (ersetzt den Plan „nur Plugin + BlazeSQL“)

**Beschluss (Nutzer):** Wir bauen einen **eigenen JSI-MCP-Server**, der sich **direkt an MySQL** anbindet und **feste Tools** anbietet (z. B. `kandidaten_suchen(beruf, fuehrerschein, sprache, …)`) statt beliebigem SQL. Intern nutzt er `build_query.py` (bzw. dessen Weiterentwicklung). Damit ist **Punkt 13 beantwortet**: Aufrufer ist der MCP-Server-Client (Claude und ggf. eigene App), nicht nur das Claude-Plugin.

**Warum:**
- Echtes Tool-Calling: feste, getestete Tools mit JSON-Schema statt frei generiertem SQL → reproduzierbar, prüfbar, keine Join-Fallen (z. B. DIPL-ID-Raum) zur Laufzeit.
- Sicherheit/Datenschutz: Zugriff über eigenen **Read-only-DB-Benutzer mit Spaltenrechten** (die 31 sensiblen Spalten technisch nicht lesbar) statt Drittanbieter BlazeSQL, dessen Metadaten Beispielwerte inkl. Klartext-Passwörter zeigten.
- Kein 60-s-Limit von BlazeSQL; Timeouts/Limits selbst steuerbar.
- Ein Server für mehrere Clients (Claude, eigene App).

**Was sich dadurch ändert:**
- Neues Hauptergebnis: **MCP-Server-Code (Python empfohlen, da `build_query.py` Python ist) + Tool-Schemas + Tests + Deployment-Anleitung**. Das Plugin bleibt als Wissens-/Doku-Schicht und Bedienanleitung für Claude, zeigt aber auf den JSI-MCP-Server.
- Punkt 21 (Tool-Schema): Format = **MCP-Tools mit JSON-Schema** (`inputSchema`), Toolnamen/Parameter stabil, Beschreibungen für das Modell.
- Punkt 26 (BlazeSQL nicht in `.mcp.json`): erledigt sich – `.mcp.json` bekommt den JSI-MCP-Server.
- Punkt 3 (sensible Spalten sperren): primär über **MySQL-GRANTs** des neuen Benutzers; BlazeSQL-Sperre nur, solange BlazeSQL verbunden bleibt.
- Punkt 5 (Datenschutz/AVV) wird **relevant** für das Projekt: Tool-Ergebnisse gehen an das Sprachmodell.
- Die Erhebung (17, 18) läuft bis zur Fertigstellung des Servers weiter über BlazeSQL.
- Punkt 14 (UI): bleibt offen; optional später als MCP-App-Oberfläche oder in eurer App.

**Offene Fragen zur Umsetzung → §11.**

## 1. Ziel
Das Anthropic-Plugin „data“ (ID `2529b2d1-9426-48a5-a8ad-2ebc77af2815`) für JSI anpassen und daraus eine **vollständige Wissens- und Tool-Schicht** über die CRM-Datenbank bauen, damit Kandidaten-/Geschäftsfragen per Tool-Calling (Filter statt Handsuche in 190 Tabellen) beantwortet werden.
Beispiel des Nutzers: „alle Elektriker mit Führerschein C“ → Filter → SQL → Ergebnis.

## 2. Umgebung
- Datenzugriff: **BlazeSQL-Connector** (claude.ai) → MySQL **8.4.11** „Mysql JSI“, Schema `jsicrm`, **190 Tabellen, 1.809 Spalten**, InnoDB, `ONLY_FULL_GROUP_BY` + Strict-Modus. Tools: `list_schemas`, `list_tables`, `describe_tables`, `execute_sql` (Timeout **60 s**).
- Seit 2026-10-29 sind **alle** Tabellen freigegeben (vorher 99).
- Amplitude und Notion: am 2026-10-30 aus dem Plugin entfernt (waren nie genutzt; nicht mit dem JSI-MCP-Server verbunden).
- Firma: JobStep-Gruppe (Jobstep GmbH DE / Jobstep Int GmbH CH), Teams JS, GC, WE, SSC, JSI, NTH; Filialen BiH/SRB/DE/CH. Zwei Geschäftsfelder: **Vermittlung** (Kandidaten → deutsche Arbeitgeber) und **DIPL** (Diplom-Nostrifikation, von Kandidaten bezahlt).

## 3. Inhalt dieses Pakets
| Pfad | Inhalt |
|---|---|
| `plugin/` | Komplettes angepasstes Plugin (= `jsi-data-plugin.zip`). Skills siehe §4. |
| `server/src/jsi_mcp/skills/jsi-data-analyst/` | Wissens-Skill (seit 2026-10-30 im Server, ausgeliefert über `skill_lesen` / `skills/list`): Entitäten, Codes, Kennzahlen, Fallen, getestete Abfragen; `references/schema/` (alle 190 Tabellen/1.809 Spalten, generiert), `references/veze.md` (Verknüpfungen), `osjetljive_kolone.md` |
| `server/src/jsi_mcp/skills/jsi-kandidat-filter/` | Filter-Skill (Doku zu `search_candidates`), `references/filteri.md` generiert von `server/scripts/filter_catalog.py`; Logik `build_query.py` im Server |
| `docs/rohdaten/columns.json` | `information_schema.COLUMNS` komplett (Tabelle, Pos., Spalte, Typ, Key, Kommentar) |
| `docs/rohdaten/counts.tsv` | Zeilenzahl jeder Tabelle |
| `docs/rohdaten/dates.tsv` | Zeitraum (MIN/MAX, Füllgrad) der Haupt-Datumsspalte, 107 Tabellen |
| `docs/rohdaten/rels.tsv` / `rel_results.tsv` | 76 gemessene Verknüpfungen (Definition / n, ok) |
| `docs/rohdaten/tables_meta.json` | BlazeSQL-Tabellenbeschreibungen |
| `docs/rohdaten/gen_schema.py` | Generator für `references/schema/` (aus columns/counts/dates) |

Neu generieren: `python3 -I rohdaten/gen_schema.py <ordner-mit-columns.json,counts.tsv,dates.tsv,gen/tables_meta.json> <ziel>` (Pfade im Skript ggf. anpassen).
Tests: seit 2026-10-30 nur im Server (`server/tests/`); `build_query.py` + Kataloge liegen nur noch in `server/src/jsi_mcp/`, Generator `server/scripts/filter_catalog.py`.

## 4. Was am Plugin geändert wurde
- `CONNECTORS.md`, `.mcp.json` (Snowflake/Databricks/BigQuery/Hex/Definite/Atlassian entfernt; seit 1.2.1 auch Amplitude + Notion – `.mcp.json` enthält nur noch `jsi`), `README.md`.
- Firmenkontext-Block in `analyze`, `write-query`, `explore-data`, `build-dashboard`, `create-viz` (MySQL, Bosnisch, PII-Regeln, Verweis auf beide JSI-Skills).
- `data-context-extractor`: Platzhalter `~~data warehouse` → BlazeSQL/MySQL.
- Neue Skills `jsi-data-analyst`, `jsi-kandidat-filter`. Plugin-Name/Struktur unverändert. Original im Sync-Ordner unverändert.

- **2026-10-30 (Plugin 1.6.0): Fach-Skills in den Server verlegt.** `jsi-data-analyst`, `jsi-kandidat-filter` und die Analyse-Skills (`analyze`, `explore-data`, `build-dashboard`, `create-viz`, `data-visualization`, `statistical-analysis`, `validate-data`) liegen in `server/src/jsi_mcp/skills/` und werden vom Server ausgeliefert: Tool `skill_lesen` (alle Clients) und MCP-Skills-Extension `io.modelcontextprotocol/skills` (SEP-2640: `skills/list`, `skills/get`, `skill://<name>/<pfad>` über `resources/read`, Manifest mit SHA-256). Das Plugin enthält nur noch Verbindung, Hooks, `jsi-mcp` und die SQL-Skills `sql-queries`, `write-query`, `data-context-extractor` (Löschen offen, Entscheidung Nutzer). Hosts unterstützen die Extension Stand 2026-10-30 kaum (MCP Inspector ja; Claude/claude.ai nein) – deshalb `skill_lesen`.

- **2026-10-31 (Plugin 1.7.0): SQL-Zugang `sql_query` für Admins/Entwickler** (Entscheidung Nutzer: nur Admins/Entwickler, der Agent muss jedes Mal fragen; ohne Bestätigungsdialog verweigern). Permission `jsi:sql:read`, vorerst nur Rolle `jsi-admin-test` (Rolle `jsi-developer` noch nicht angelegt). Bestätigung serverseitig per Form-Elicitation: Der Dialog zeigt die vollständige Anweisung, das SDK bindet die Antwort an genau diese Frage. Server läuft zustandslos (`stateless_http`, JSON) → kein Rückkanal für Protokoll 2025-11-25; gemessen lokal: 2025-11-25 „no back-channel“, 2026-07-28 mit elicitation → Dialog + Ausführung, ohne elicitation → Fehler. Deshalb Ablehnung unter 2026-07-28. Schutz: eine SELECT/WITH/EXPLAIN-Anweisung, kein `SELECT *`, Schreib-/Datei-/Sperr-Schlüsselwörter abgelehnt, [TAJNO] (Server-Prüfung + GRANT), Personendaten-Spaltennamen aller Tabellen (`sql_pii_kolone.json`, aus `gen_tabele.py`) nur mit `pii=true`, READ-ONLY-Transaktion, 30 s, max. 1000 Zeilen; Log nur SHA-256.

## 5. Gesicherte Erkenntnisse (gemessen)
- **Zwei Kandidaten-ID-Räume**: `idk_kandidati.kandidat_id` (Vermittlung) vs. `idk_nd_kandidata.id_broj_nd_kandidata` (DIPL). `idk_predracuni`, `idk_racuni`, `idk_reminders`, `idk_ponovne_prijave`, `idk_nd_*` hängen am DIPL-ID. Falscher Join auf `kandidat_id` = 61–78 % Zufallstreffer. Brücke: `kandidat_dipl_id` (77.583 DIPL-IDs).
- DIPL ⊄ Kandidaten: 81.330 DIPL, 3.747 unverknüpft (2.572 per Tel/E-Mail auffindbar, 575 nicht, 600 ohne Kontakt). `kandidat_idd` **unzuverlässig** (1.539 Widersprüche). 33 DIPL-IDs mit 2 Kandidaten (Dubletten).
- Nur **3 deklarierte FKs** (tutorijali, rb_*); alle Geschäftsverknüpfungen sind Konvention.
- Pipeline-Historie `idk_log_statusi_prijave` (361k, ab 2021-12). Vermittlungen (erstmals Status 9): 2022 299 · 2023 536 · 2024 71 · 2025 24 · 2026 1. Bestand „vermittelt“ (Status-Reihenfolge ≥ 7, ohne Archiv) = 854.
- Umsatz bezahlt: `idk_kandidat_financije` (2023: 430k), `idk_nalog_financije` (2023: 1,82 Mio), `idk_predracuni` DIPL (2023: 240k EUR). Währung kf/nf **unbestätigt (EUR angenommen)**. `racuni` = Endrechnungen zu Vorrechnungen → nie addieren. `racun_uplaceno` ungepflegt.
- DIPL faktisch 2024 eingestellt (Leads 2021 41,6k → 2025 65). Aktivität allgemein endet ~Feb 2026.
- `beruf_mapping` (Sept 2026, 35.701 Freitexte → 194 `berufsgruppe_id`, UNIQUE-Index) normalisiert Berufe: `kri_pozicija` 100 %, `kandidat_prijava_na` 95 %, `ke_naziv_kvalifikacije` 66 %.
- Führerschein: `kandidat_vozacka_kategorija` = Liste „B,C1,C,CE“ (51.511 befüllt) + Legacy `kandidat_vozacka_dozvola`.
- Sprachniveaus = Selbstauskunft; Zertifikate über `cvl_certificate_path` (367), nicht `cvl_status=8` (2).
- Füllgrade: Geschlecht 13 %, Land 35 %, Alter 60 %, Erfahrung-Flag 18 %, `kandidat_nivo_obrazovanja` fast leer.

## 6. Technische Fallen (beim Bauen beachten)
- Korrelierte `EXISTS` über `idk_kandidati` → **Timeout 60 s**. Immer Kind-Tabellen in CTE (`SELECT DISTINCT kid`) vorab aggregieren und joinen.
- Strict-Modus: kein `'0000-00-00'` in Vergleichen (`IF(d > '1940-01-01', …)` nutzen).
- `UNION` über Spalten mit verschiedener Collation → Fehler 1271.
- MySQL-Stringliterale: Backslash wird geschluckt → in REGEXP `[.]` statt `\.`.
- Text-IDs: `idk_project_candidate_queue.queue_*` varchar(7), `pap_group_id`/`papq_nalog_id` varchar(7), `project_nalogid` varchar(25) → CAST.
- Polymorphe Verknüpfungen `*_group`+`*_dataid` (notes, documents, timeline, tasks, *_info): Bedeutung der Gruppen unbekannt.
- **Sicherheit:** BlazeSQL-Metadaten zeigen Beispielwerte, inkl. Klartext-Passwörter. Niemals Spalten aus `osjetljive_kolone.md` selektieren oder in Doku übernehmen; Personendaten nur auf ausdrücklichen Wunsch.

## 7. Ehrlicher Vollständigkeitsstand (aktualisiert 2026-10-30, Branch `feature/filter-katalog`)
- Vollständig: Tabellen-/Spaltenliste, Zeilenzahlen, Zeiträume (107 Tabellen); **Klassifikation aller 1.809 Spalten** (`docs/rohdaten/verweis_kandidaten.tsv`).
- **Verknüpfungen: 368 von 381 verweisartigen Spalten gemessen (96,6 %)**, 395 Hypothesen; 312 belegt (≥ 98 %), 13 wahrscheinlich, 5 schwach, 3 falsch, 15 nur NULL/0, 9 leere Tabellen, 11 polymorph je Gruppe. Nicht gemessen: 5 ID-Listen, 8 `rb_*`/`mcp_aenderung` (≤ 4 Zeilen). → `docs/rohdaten/veze_komplett.tsv`, `plugin/.../veze.md`.
- **Spaltenprofil: 279 Spalten in 17 Kandidaten-Tabellen** (`kandidat_profil.tsv`, `docs/KANDIDAT_PROFIL.md`). Code-Werteverteilungen für 64 filterrelevante Code-Spalten; die übrigen ~355 CODE-Spalten nur klassifiziert.
- **Filter: 48** (vorher 19) + 4 Ausgabeoptionen, alle im JSON-Schema von `search_candidates`, Katalog `filter_catalog.json` + `references/filteri.md`. **Berufskatalog: 28 Berufe mit Synonymen + alle 194 Berufsgruppen** direkt nutzbar.
- **Automationen: 26 Regeln/Muster aus Daten abgeleitet (14 belegt, 8 wahrscheinlich, 4 vermutet)** (`docs/AUTOMATIONEN.md`), ohne Quellcode – vor Schreiben weiterhin CRM-Code/API nötig.
- Tests: Server 193 grün (127 + 66), Plugin 33 grün. Abnahme-Beispiele gegen BlazeSQL: 3.199 / 45 / 0 / 15.

## 8. Offene Punkte – Gruppe A (relevant für Plugin/Tool)
**A1 Entscheidungen (Nutzer):**
- 13 ✅ **Entschieden 2026-10-29:** eigener JSI-MCP-Server mit festen Tools, direkt an MySQL (siehe §0).
- 14 Sichtbare Filtermaske (UI) gewünscht?
- 15 Einheitliche Doku-Sprache (DE/BS/EN)? Aktuell gemischt.

**A2 Bauarbeiten (Claude):**
- 17 Alle ≈460 Verweisspalten messen + `*_group`-Felder.
- 18 Alle 288 Kandidatenspalten profilieren (Füllgrad, Distinct, Werte → Filtertyp).
- 19 Fehlende Filter: Fähigkeiten, Herkunftskanal, Visastatus, Dokumentstatus, Casting-Erscheinen, Interview-Bewertung, Absagegründe, Partner/Makler, Agent, Messenger-Status, Familienstand, Wunschgehalt, Stadt, DE-Profil-Führerschein.
- 20 Berufskatalog von 27 auf (bis zu) 194 Gruppen.
- 21 Vollständige MCP-Tool-Schemas (JSON-Schema) + Server-Code + Tests gegen DB.

**A3 Klärungen (Nutzer) für korrekte Ergebnisse:**
- 6 Aktivitätsende Feb 2026 echt oder veraltete Kopie?
- 7 Undokumentierte Codes: `nalog_status` 1,3–8,10–12 · `pstatus_nd_kandidata` 6–12 · `kandidat_porijeklo` 6–8 · `kandidat_nacin_odlaska` 3 · `tsr_status` 4/5 · `employee_status` · `*_group`-Werte.
- 8 Währung `kf_iznos`/`nf_iznos`.
- 9 Skala `kandidat_iskustvo_u_struci_trajanje` 2–6.
- 10 Castings 2026 mit 0 % „Došao“ – nicht nachgetragen?
- 11 Zählt „Odbijena viza“ (24) als vermittelt?
- 12 Bedeutung von `kandidat_idd`.

**A4 Technik/Plugin:**
- 3 31 sensible Spalten in BlazeSQL sperren.
- 22 Plugin sichern (Download erfolgt? Nutzer hatte Download-Probleme mit `.plugin`; ZIP-Kopie geliefert).
- 23 Plugin in Desktop-App installieren und testen (nie getestet).
- 24/25 erledigt: Notion und Amplitude aus dem Plugin entfernt (2026-10-30). 26 BlazeSQL nicht in `.mcp.json`.

## 9. Gruppe B – zurückgestellt (nicht Plugin-Bau)
- 1 ViciDial-Passwörter ändern ⚠️ dringend · 2 API-Tokens Bridge/Glossa/Lilium erneuern ⚠️ dringend · 4 MD5 → bcrypt/argon2 · 5 Datenschutz/AVV für BlazeSQL/KI
- 16b 2.572 DIPL im CRM nachverknüpfen (ID-Liste angeboten) · 16c 33 Dubletten · 16d 575 unverknüpfte DIPL gewollt?

## 10. Nächste Schritte
1. Nutzer beantwortet A1 (v. a. 13) und so viel wie möglich aus A3.
2. Claude erledigt A2 (17 → 18 → 19/20 → 21) in einem Durchgang; Ergebnisse in `plugin/` + `docs/rohdaten/`, Tests grün, gegen DB verifiziert.
3. Vorschlag: Plugin + Arbeitsstand in ein GitHub-Repo legen (sitzungsübergreifend verfügbar).

## 11. Offene Fragen zum JSI-MCP-Server (vom Nutzer zu beantworten)
Empfehlung jeweils in Klammern.

**Betrieb & Zugang**
- M1 **Wo läuft der Server?** Zentral auf eurem Server als Remote-MCP über HTTPS (empf.: nutzbar von claude.ai, Desktop, Claude Code und eigener App) oder lokal pro Arbeitsrechner (stdio, nur Desktop/Claude Code).
- M2 **Datenbankzugang:** Gibt es einen DB-Admin, der einen Read-only-Benutzer mit Spaltenrechten anlegt? Gibt es eine Lese-Kopie (Replica)? (empf.: Replica + eigener Benutzer ohne die 31 sensiblen Spalten)
- M3 **Netzwerkweg** Server ↔ DB: gleiches Netz, VPN, SSH-Tunnel, IP-Freigabe? Ist die BlazeSQL-DB die Live-Produktion (vgl. Punkt 6)?
- M4 **Hosting/Technik:** Docker auf eigenem Server? Wer betreibt und aktualisiert ihn? Code in einem GitHub-Repo? (empf.: Python + offizielles MCP-SDK, Docker, privates Repo)

**Clients & Sicherheit**
- M5 **Welche Clients** sollen den Server nutzen: claude.ai (Custom Connector), Claude Desktop/Code, eigene App (welche Technik?), weitere KI-Tools?
- M6 **Authentifizierung:** API-Schlüssel oder OAuth? Wer darf zugreifen? (empf.: OAuth bzw. pro Nutzer Schlüssel, Protokollierung jedes Aufrufs)
- M7 **Personendaten (PII):** Dürfen Tools Namen/Telefon/E-Mail liefern? Wenn ja, nur bestimmte Rollen? (empf.: standardmäßig nur IDs + nicht-personenbezogene Felder; PII nur per Rolle + Protokoll)
- M8 **Datenschutz:** AVV/Datenschutzprüfung für Weitergabe von Tool-Ergebnissen an das Sprachmodell (Anthropic) – wer klärt das?

**Funktionsumfang v1**
- M9 **Tool-Liste v1** (Vorschlag): `kandidaten_suchen` (alle Filter), `filter_optionen` (gültige Werte/Codes je Filter), `kandidat_profil` (ein Kandidat, ohne PII), `kennzahlen` (Vermittlungen, Umsatz, TF-Leistung, Casting, DIPL-Funnel), `nalozi_uebersicht`, `pipeline_verlauf`. Fehlt etwas / zu viel?
- M10 **Freies SQL-Tool** für Admins zusätzlich? (empf.: nein in v1; Ad-hoc-Analysen weiter über BlazeSQL oder später ein streng begrenztes Read-only-Tool)
- M11 **Nur lesen oder auch schreiben** (z. B. DIPL nachverknüpfen, Notizen, Status)? (empf.: v1 nur lesen)
- M12 **Benennung:** Toolnamen/Parameter auf Englisch, Deutsch oder Bosnisch? (empf.: Englisch für Namen, Beschreibungen zweisprachig DE/BS)
- M13 **Grenzen:** max. Zeilen pro Antwort, Timeout, Aufruflimit? (empf.: 200 Standard / 5.000 max, 30 s, Paging)

**Übergang**
- M14 **BlazeSQL:** parallel behalten (für Ad-hoc und für die Erhebung bis der Server läuft) oder danach kündigen? → **Entschieden 2026-10-30:** Verbindung BlazeSQL ↔ MySQL vom Nutzer getrennt; Skills/AGENTS.md verweisen nur noch auf den JSI-MCP-Server. Messwerte „über BlazeSQL“ in Doku/Rohdaten bleiben als Herkunftsangabe.
- M15 **UI (Punkt 14):** später Filtermaske als MCP-App oder in eurer App – jetzt schon einplanen?

## 12. Geänderte Reihenfolge der Arbeit
1. Nutzer: M1–M3, M7, M9 beantworten (blockierend), Rest A3 nach Möglichkeit.
2. Claude (parallel möglich, über BlazeSQL): 17 Verknüpfungen, 18 Spaltenprofil → vollständiger Filterkatalog.
3. Claude: Server-Gerüst (Python, MCP-SDK), Tools gemäß M9 auf Basis `build_query.py`, JSON-Schemas, Unit-Tests, Integrationstests gegen DB, Dockerfile, README (Deployment, Secrets als Umgebungsvariablen, SQL für den Read-only-Benutzer mit GRANTs).
4. DB-Admin: Benutzer/Replica/Netzwerk nach M2/M3.
5. Deployment + Anbindung in Claude (Custom Connector / `.mcp.json` im Plugin) + Abnahmetests (z. B. „Elektriker mit Führerschein C“ = 2.676 am 2026-10-29).

## 13. Entscheidungsprotokoll (Interview mit dem Nutzer, 2026-10-29)

| Nr. | Entscheidung | Stand |
|---|---|---|
| M1 | **Zentral/online bauen** (Remote-MCP über HTTPS, Streamable HTTP). Lokal nur als Entwicklungs-/Testschritt, kein späterer Umbau. | ✅ entschieden |
| M4 (Teil) | Code in **privatem Repo `dsactivi-2/jsi-mcp-claude`** (vom Nutzer angelegt; Claude kann aus Sessions keine Repos anlegen). Python + offizielles MCP-SDK + Docker. | ✅ entschieden |
| M6 | **WorkOS AuthKit** (OAuth), Permissions pro Tool in WorkOS gepflegt → §13.1 | ✅ entschieden |
| M2 | **Mirror-DB** = Backup-/Testserver („MiroServ“), freigegeben für Lese- und Schreibtests über die `JSI_MIRROR_DB_*`-Variablen. Zugangsdaten liegen als Umgebungsvariablen in der Cloud-Umgebung: `JSI_MIRROR_DB_HOST`, `JSI_MIRROR_DB_PORT`, `JSI_MIRROR_DB_NAME`, `JSI_MIRROR_DB_USER`, `JSI_MIRROR_DB_PASSWORD` (nur in **neuen** Sessions sichtbar; nie im Chat/Repo ausgeben). Read-only-Benutzer für Produktion: offen. | 🟡 teilweise |
| M11 | **Alle sinnvollen Schreibaktionen**, Einschränkung per WorkOS-Permission → §13.2. Ursprünglich: nicht nur lesen – **Schreib-Tools werden gebaut und auf der Mirror-DB getestet**. Nur eng definierte Aktionen (kein freies Schreiben), jede mit `dry_run`, Protokoll (Audit-Tabelle/Log) und Rollenprüfung. **Liste der Schreibaktionen: offen (Nutzer).** | 🟡 Umfang offen |
| M3 | DB läuft auf **Aiven** (Managed MySQL). Vorschlag: MCP-Server als Docker-Container **auf demselben Server/im selben privaten Netz wie die DB**, davor **Caddy** (automatisches HTTPS, Subdomain z. B. `mcp.<domain>`), MySQL nicht öffentlich. | 🟡 Anbieter offen |
| Orchestrierung | Kontext reicht (1 Mio.). Messarbeit 17/18 macht der Orchestrator selbst über BlazeSQL (keine Sub-Agenten nötig). Server-Code (21) in eigener **Cloud-Worker-Session** mit diesem Repo. | ✅ entschieden |

**Test einer Cloud-Worker-Session (2026-10-29):** BlazeSQL **verfügbar** (190 Tabellen), aber Tools heißen dort `mcp__<uuid>__*` statt `mcp__Blaze_SQL__*` → Aufträge nie mit festen Tool-Namen formulieren. Plugin-Skills `data-jsi:*` **nicht** verfügbar → Worker lesen Skills/Referenzen aus `plugin/` in diesem Repo.

**Netzwerk-Annahme (ungetestet):** Cloud-Container haben ausgehend nur HTTP(S) über Proxy; direkter MySQL-Zugriff (TCP 3306) auf die Mirror-DB ist wahrscheinlich nicht möglich. Plan: Entwicklung gegen **lokale MySQL 8.4 in Docker** mit vollständigem Schema (aus `docs/rohdaten/columns.json`) + synthetischen Testdaten; Abnahme gegen Mirror auf dem Zielserver per mitgelieferter Testliste. Falls der Mirror doch erreichbar ist: direkt testen.

**Mirror-Test 2026-10-29 23:26 UTC:** Neue Worker-Session (Umgebung `env_016eqsZ3vyoNkdxczi98CwVf`) sah **keine** `JSI_MIRROR_DB_*`-Variablen (auch keine mit `JSI`/`MYSQL`/`DB_` im Namen) → Verbindung nicht getestet. Ursache klären: andere Umgebung, anderer Variablenname oder nicht gespeichert.

**Schema-Verifikation 2026-10-29 23:32 UTC (live über BlazeSQL):** `information_schema.COLUMNS` neu gelesen und mit `docs/rohdaten/columns.json` (Snapshot 21:50 UTC) verglichen: 190 Tabellen, 1.809 Spalten, **0 Abweichungen** (Name, Typ, Key, NULL, Kommentar). Außerdem: 293 Indexe, 3 FKs, 0 Views/Trigger/Routinen. Letzte Schemaänderung laut `CREATE_TIME`: 2026-10-27 11:07 (u. a. `idk_kandidati`, `mcp_*`) – im Snapshot enthalten. DB-Host `mysql-d7a5876-3`, MySQL 8.4.11 → passt zu **Aiven** (Nutzer: DB läuft auf Aiven; „naiven“ = Aiven). Ob die BlazeSQL-DB die Live-DB oder der Mirror ist, ist **nicht** belegt. Schemaänderungen nach 23:32 sind nicht erfasst → vor dem Server-Bau erneut vergleichen (Mirror vs. Live).

**Mirror-Test 2 (23:31 UTC):** Alle 5 `JSI_MIRROR_DB_*` gesetzt (Umgebung „NO 1!“). Host = Hostname mit öffentlicher IP. **TCP-Verbindung: Timeout nach 10 s** → Version/Rechte/SSL nicht geprüft. Ursache nicht belegt: Cloud-Netzwerkrichtlinie (nur HTTPS-Proxy) oder Aiven-IP-Filter. Optionen: Netzwerkzugriff der Umgebung auf „Full“ bzw. Host unter Allowed domains (ungewiss, ob Proxy rohes TCP durchlässt) + Aiven-IP-Filter prüfen; sonst Entwicklung gegen lokale MySQL in Docker.

**Hosting-Diskussion (offen):** Kandidaten (1) **Aiven Runtime/Apps** – Container im selben Aiven-Projekt wie die DB, Deploy aus GitHub; laut Aiven noch eingeschränkt verfügbar (Zugang anfragen); öffentlicher HTTPS-Endpunkt/eigene Domain nicht belegt. (2) **Manufact Cloud** (Team hinter mcp-use, YC S25) – Deploy aus GitHub, Python 3.11–3.13; EU-Region laut Pricing erst ab Plan „Startup“ (250 USD/Monat), Free/Hobby ohne Regionswahl; feste ausgehende IP nicht belegt (relevant für Aiven-IP-Filter); zusätzlicher Auftragsverarbeiter (AVV). (3) eigener VPS (vom Nutzer nicht bevorzugt). Code bleibt anbieterneutral (Python, offizielles MCP-SDK, Dockerfile).

### 13.1 Authentifizierung & Berechtigungen: WorkOS (✅ entschieden, M6)
- **WorkOS AuthKit** ist der OAuth-Autorisierungsserver, der JSI-MCP-Server der Resource Server. Server liefert `/.well-known/oauth-protected-resource` (`resource` = `JSI_MCP_PUBLIC_URL`, `authorization_servers` = AuthKit-Domain); ohne/ungültiges Token → 401 + `WWW-Authenticate` mit `resource_metadata`.
- Token-Prüfung: JWT gegen `https://<WORKOS_AUTHKIT_DOMAIN>/oauth2/jwks`, `iss` = `https://<WORKOS_AUTHKIT_DOMAIN>`, `aud` = `JSI_MCP_PUBLIC_URL`. In WorkOS: MCP-URL als Resource Indicator eintragen, CIMD (und ggf. DCR) aktivieren.
- **Berechtigungen werden in WorkOS gepflegt** (Rollen → Permissions, mehrere Rollen pro Nutzer möglich). Der Server prüft **pro Tool** den `permissions`-Claim im Token und protokolliert jeden Aufruf mit `sub`. ⚠️ Belegt ist der `permissions`-Claim für AuthKit-Session-Tokens; ob er auch in MCP-OAuth-Tokens (Connect) steht, **muss getestet werden**. Fallback: JWT-Template in WorkOS oder Abfrage der WorkOS-API.
- Vorschlag Permission-Slugs (in WorkOS anzulegen):
  | Slug | erlaubt |
  |---|---|
  | `jsi:kandidati:read` | `kandidaten_suchen` (Anzahl/IDs), `filter_optionen`, `kandidat_profil` ohne Personendaten |
  | `jsi:kandidati:pii` | zusätzlich Name, Telefon, E-Mail in Listen/Profil (ersetzt `"pii": true`, M7) |
  | `jsi:kennzahlen:read` | `kennzahlen`, `nalozi_uebersicht`, `pipeline_verlauf` |
  | `jsi:finansije:read` | Umsatz, Rechnungen, Provisionen |
  | `jsi:dipl:read` | DIPL/Nostrifikation |
  | `jsi:write:<aktion>` | je Schreibaktion einzeln (Liste offen) |
  | `jsi:audit:read` | Aufrufprotokoll lesen |
- Konfiguration (nur Namen, siehe `.env.example`): `WORKOS_AUTHKIT_DOMAIN`, `WORKOS_CLIENT_ID`, `JSI_MCP_PUBLIC_URL`; DB: `JSI_MIRROR_DB_*` (vorhanden), später `JSI_DB_*`, Umschalter `JSI_DB_TARGET`.

**Hosting-Recherche 2026-10-29 (öffentliche Quellen):**
- **Manufact:** Pläne laut manufact.com/pricing: Free (0 $), Pay as you go, **Pro 250 $/Monat** (Regionen US/EU/APAC, SOC 2/ISO 27001), Enterprise (individuell, Self-hosting, RBAC, SSO). Free/PAYG nur „Default“-Region. **Feste ausgehende IP: öffentlich nicht dokumentiert. AVV/DPA: öffentlich nicht gefunden** (Trust Center trust.manufact.com ohne lesbaren Inhalt). → Anfrage an manufact.com/contact durch den Nutzer nötig (Claude kann keine E-Mails senden; Textentwurf im Chat geliefert).
- **Cloudflare (Alternative):** Standard-DPA mit EU-SCC vorhanden. Remote-MCP mit OAuth auf Workers offiziell dokumentiert; MySQL über **Hyperdrive** (Beispiele nur JS/TS, `mysql2`). Hyperdrive verbindet aus den **Cloudflare-IP-Bereichen** → Aiven-IP-Filter auf diese Bereiche begrenzbar (breit, aber nicht offen). **Containers** seit 2026-04-13 GA → Python-Server im Docker-Container möglich (ausgehendes TCP zu MySQL nicht verifiziert). Entscheidung Workers (TypeScript, `build_query.py` portieren) vs. Containers (Python, Code bleibt) offen.

### 13.2 Schreibzugriff (✅ Grundsatz entschieden, M11)
**Beschluss (Nutzer):** Der Server bekommt **alle sinnvollen Schreibaktionen**; eingeschränkt wird **pro Permission in WorkOS**.
**Umsetzungsvorschlag (Claude):**
- **Schreib-Register** (`server/write_registry.yaml`), aus dem Schema generiert und fachlich geprüft: je Entität (Tabelle) erlaubte Aktionen (`create`/`update`/`archive`), erlaubte Spalten, Pflichtfelder, Validierung (Typ, Länge, Codes), Nebenwirkungen (z. B. Pipeline-Log bei Statuswechsel). **Nie beschreibbar:** [TAJNO]-Spalten, PKs, Log-/Audit-/Event-Tabellen, technische Tabellen.
- Permission je Entität und Aktion: `jsi:write:<entitaet>:<create|update|archive>`; Wildcards über WorkOS-Rollen (z. B. Rolle „Admin“ = alle).
- Jede Schreibaktion: `dry_run` (Vorschau vorher/nachher) → Ausführung in Transaktion → Eintrag in **`mcp_aenderung`** (vorher/nachher, Werkzeug, Tabelle, Datensatz, Kandidat, Zustand, Freigabe-Code/-Zeit); Fehler in **`mcp_fehler`**. Kein hartes Löschen (nur Archiv/Status), außer ausdrücklich freigegeben.
- Fachliche Prozess-Tools zusätzlich zu generischem `create/update/archive`: z. B. Bewerbungsstatus setzen, Kandidat einem Auftrag zuordnen, DIPL-Kandidat verknüpfen, Notiz anlegen.
- Zuerst nur gegen Mirror (`JSI_DB_TARGET=mirror`); Produktion erst nach Abnahme.
**Befund 2026-10-29:** In der DB existieren bereits seit 2026-10-27 **`mcp_aenderung`, `mcp_fehler`, `mcp_status_info`** (Änderungsprotokoll mit Freigabe-Workflow, Dokumentstatus mit erlaubten Übergängen) und **`rb_*`** (Approvals mit Preview-Hash, Events, Outbox, Field-State). → Es gibt offenbar schon ein anderes MCP-/Freigabe-Projekt. **Klären (Nutzer):** Wer hat das gebaut, gibt es Code, soll unser Server dieses Schema nutzen?
**Risiko:** Direkte DB-Schreibzugriffe umgehen die Logik der CRM-Anwendung (Logs, Benachrichtigungen, abgeleitete Felder). **Klären (Nutzer):** Gibt es Code/API des CRM (Tabelle `idk_api_clients` deutet auf eine API hin)? Dann Nebenwirkungen daraus übernehmen oder über die API schreiben.

**TCP-Diagnose (Test 4, 23:45 UTC, Network „Full“):** Ausgehend nur Port 443 offen (github.com:443 ok); portquiz.net:3306/25060, github.com:22 und Mirror-Host: Timeout. → Claude-Cloud-Sessions blockieren generell direktes TCP; Ursache ist **nicht** Aiven. Aiven-IP-Filter muss für Tests aus der Cloud nicht geöffnet werden.

**Entscheidung 2026-10-29 (Nutzer): Kein direkter MySQL-Zugang aus den Claude-Sessions nötig.** Mirror-Test 3 (Network „Full“) scheiterte ebenfalls am TCP-Timeout (vor TLS). Vorgehen stattdessen:
- Entwicklung gegen **lokale MySQL 8.4 (Docker)** mit vollständigem Schema aus `docs/rohdaten/columns.json` + Index-/FK-Definitionen (über BlazeSQL lesbar) + Code-/Lookup-Tabellen (ohne Personendaten) + synthetischen Testdaten.
- **Lese-Tools:** generiertes SQL zusätzlich über BlazeSQL gegen die echte DB prüfen (z. B. Elektriker + C = 2.676).
- **Schreib-Tools:** Unit-/Integrationstests lokal; Abnahme gegen Mirror **vom Hosting aus** (Cloudflare), dort mit `JSI_MIRROR_DB_*` + Aiven-CA-Zertifikat (SSL mode REQUIRED; CA ist öffentlich, darf ins Repo: `certs/aiven-mirror-ca.pem`).
- Keine Kopie echter Personendaten in Sessions/Repo.

**Abnahme-Plan (✅ entschieden 2026-10-30):** Echte Verbindung und Schreib-Tools werden **beim Deploy-Test über den MCP-Server selbst** geprüft: Server auf Cloudflare deployen (`JSI_DB_TARGET=mirror`) → Nutzer bindet ihn in claude.ai als **Custom Connector** ein und meldet sich über WorkOS an (OAuth kann Claude nicht selbst durchführen) → neue Claude-Session nutzt die Tools über HTTPS (Port 443, aus der Cloud erlaubt) → Abnahmeliste abarbeiten: Lese-Tools gegen BlazeSQL-Referenzwerte, Schreib-Tools mit `dry_run` → Ausführung → Prüfung in `mcp_aenderung` → Rücknahme. Für den Test eine WorkOS-Rolle mit allen `jsi:*`-Permissions anlegen.

### 13.3 BEFUND 2026-10-30: Es existiert bereits ein produktiver CRM-MCP (Manufact)
> **ERLEDIGT 2026-10-30 (Entscheidung Nutzer):** `Manufact-DB-Roleback-MCP` ist ein vergessenes Altprojekt und für dieses Projekt nicht relevant. JSI-MCP-Claude ist das einzige relevante Projekt. Doppelungsfrage und Hinweis auf `dsactivi-2/manufact-db-roleback-mcp` nicht weiter verfolgen. Der folgende Abschnitt bleibt nur als Historie stehen.

Manufact-Org „Activi“ enthält: **`Manufact-DB-Roleback-MCP`** (läuft, `https://mcp.activi.io/mcp`, Repo `dsactivi-2/Manufact-DB-Roleback-MCP`, TypeScript/mcp-use) und `cloud-crm-mcp` (läuft, älter, Repo `dsactivi-2/Naufact-kopie-710-0232`) sowie zwei inaktive Einträge.
Der Rollback-MCP hat bereits (laut Repo-Doku, Stand 14.–16.10.2026): Weg MCP → Cloudflare Worker → Hyperdrive (TLS verifiziert, Cache aus) → Aiven `jsicrm`; eingeschränkter MySQL-Benutzer (Spalten-GRANTs); **WorkOS-OAuth** (Staging, Org Activi; Rollen Admin / `crm-writer-approval` / `crm-approver`, Mapping in `src/permissions.ts`); Tools `crm_search_kandidaten` (Name, EU, Alter, Position, Sprache/Niveau, Archiv, Telefon, Filterketten), XML-Export, Firmen, Aufträge, Berufsreport, Profil, Stats, Tabellen-Metadaten; **Schreiben mit Preview → Approval (Vier-Augen) → Apply**, History, selektiver Restore, Idempotenz, Outbox → R2; `rb_*`-Tabellen gehören zu diesem Projekt; kein Delete/Drop, kein freies SQL. Schreib-Entitäten: candidate, company, order, candidate_group (+ Insert: education, language, experience).
**Was dort fehlt (= unser Beitrag):** Führerschein (EU-Logik), Bildung/Schule, Wohnland, Staatsangehörigkeit, Geschlecht, Registrierungszeitraum, Pipeline-/Freiheitsstatus, Auftrag/Projekt, Nostrifikation, Kontaktierbarkeit, Zertifikate, Berufssuche über 6 Quellen + `beruf_mapping`, Kennzahlen (Vermittlungen, Umsatz, TF, DIPL), Schema-/Verknüpfungsdoku.
**Empfehlung Claude:** keinen zweiten Server bauen, sondern den bestehenden erweitern (Filter aus `build_query.py` in Worker-SQL + `contracts/read.ts` portieren, neue Tools für Kennzahlen, Doku). Zwei Server mit Schreibzugriff auf dieselbe DB → zwei Historien, doppelte Berechtigungen. **Entscheidung Nutzer offen.**
**Sicherheitsbefund:** `dsactivi-2/manufact-db-roleback-mcp` ist **öffentlich** (anonym klonbar) und enthält u. a. Mitarbeiter-E-Mails, WorkOS-Org-/User-/Client-IDs, Worker-URL und Name + ID eines echten Kandidaten → Repo auf privat stellen, Klarname entfernen (auch aus der Git-Historie).
Herkunft von `mcp_aenderung`/`mcp_fehler`/`mcp_status_info` (27.10.) weiterhin unklar – nicht im Rollback-Repo-Dateibaum benannt.

**Noch offen (Nutzer):** Bedeutung „naiven“ (Hosting), Liste der Schreibaktionen, M5–M10, M12–M15, Gruppe A3 (Punkte 6–12).
