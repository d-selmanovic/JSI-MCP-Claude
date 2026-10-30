# CRM-Automationen – aus den Daten abgeleitet (Stand 2026-10-30)

**Ausgangslage:** Die DB hat 0 Trigger, 0 Prozeduren, 0 Events (geprüft 2026-10-29). Alles, was bei einem Ereignis zusätzlich geschrieben wird, macht der CRM-/Bot-/Partnerportal-Code oder ein Cron. Diese Datei leitet das **nur aus den Daten** ab: gleiche Kandidat-ID + Zeitabstand (Sekunden/Minuten) und Uhrzeit-Häufungen. Kein Quellcode gesehen.

**Methode:** Für jede Zeile in `idk_log_statusi_prijave` (Pipeline-Statuswechsel, `lsp_izvor` 1 CRM, 2 Partnerportal (PP), 3 Bot, 4 Queue, 5 Cron, 6 Transfer) wurde gezählt, ob für denselben Kandidaten in einem Fenster von −5 s … +120 s (Benachrichtigungen +300 s) eine Zeile in einer anderen Tabelle entsteht. Zeitraum ab 2025-01-01 (46.185 Statuswechsel), wo nicht anders angegeben. Alle Zahlen BlazeSQL, nur Aggregate.

**Sicherheit:** **belegt** = ≥ 95 % gemeinsames Auftreten und plausibler Mechanismus · **wahrscheinlich** = 60–95 % oder belegtes Muster mit kleiner Basis · **vermutet** = Hinweis aus Spaltenkommentar/Uhrzeit, Kausalität offen.

## 1. Ereignis → Folgeschreibungen

| # | Ereignis (Auslöser) | Folgeschreibung | Beleg (Zahlen) | Sicherheit |
|---|---|---|---|---|
| A1 | Neue Bewerbung/Registrierung (`idk_kandidati` neu) | Zeile in `idk_log_kandidat_statusi` (Bearbeitungsstatus) innerhalb 2 min, i. d. R. mit `lks_link_id` des Bewerbungslinks | 3.720 / 3.721 Registrierungen ab 2024-07 (99,97 %); mit Link-ID 3.585 (= exakt die 3.585 mit `kandidat_porijeklo = 0`) | belegt |
| A2 | Neue Registrierung | Pipeline-Status per **Bot** gesetzt (`lsp_izvor = 3`): Status 2 „U projektu NR“ (2.745), 6 „U projektu RZ“ (593), 1 (134) | 3.472 Bot-Statuszeilen innerhalb 2 min bei 3.721 Registrierungen | belegt |
| A3 | Neue Registrierung | Zeile in `idk_notification` innerhalb 5 min | 2.563 / 3.721 (69 %) | wahrscheinlich |
| A4 | Neue Registrierung | Task-Force-Aufgabe (`idk_task_force`) innerhalb 10 min | 919 / 3.721 (25 %) | vermutet (nur bei manchen Aufträgen/Projekten) |
| A5 | Neue Registrierung mit DIPL-Bezug | DIPL-Datensatz (`idk_nd_kandidata`) im selben 10-min-Fenster angelegt, Verknüpfung über `kandidat_dipl_id` | 166 / 3.721; vorher angelegt: 1 | wahrscheinlich |
| B1 | Bot setzt Status 2/6/1 (`lsp_izvor = 3`) | Zeile in `idk_log_kandidat_statusi` | Status 2: 1.526/1.528 · 6: 621/634 · 1: 95/95 | belegt |
| B2 | Bot setzt Status 2/6 | Notiz `idk_notes` (Gruppe 2 = Kandidat) | 925/1.528 (61 %) · 384/634 (61 %) | wahrscheinlich |
| B3 | Bot setzt Status 2/6 | `idk_notification` innerhalb 5 min | 1.104/1.528 (72 %) · 453/634 (71 %) | wahrscheinlich |
| C1 | Task-Force-Aktion im CRM (Agent wählt TF-Status) | Neue Zeile `idk_task_force` **und** Pipeline-Statuswechsel im selben Moment (`lsp_izvor = 1`) | Status 1: 17.260/17.300 (99,8 %) · Status 2: 5.197/5.337 (97 %) · Status 3 Casting: 333/357 (93 %) | belegt |
| C2 | TF-Status mit Ziel-Pipeline-Status | Pipeline-Status laut `idk_tf_statusi.tfs_status_prijave` (6 Nije zainteresiran → 1, 10 → 1, 16 Pristao → 3 Casting) | Lookup-Werte + C1 | belegt (Mapping), Übernahme wahrscheinlich |
| C3 | Status mit `rezervisanje = 1` gesetzt | `idk_kandidati.kandidat_latest_reserved_time` = Zeitpunkt des Wechsels (±2 s) | Status 10: 28/28 · Status 3: 34/357 · Status 6 Transfer: 324/20.598 (Feld hält nur die letzte Reservierung) | belegt für „letzte Reservierung“ |
| C4 | Jeder Statuswechsel | `lsp_broj_dana` der **vorherigen** Log-Zeile = Tage im alten Status | 27.300/27.313 seit 2025 ±1 Tag (BUILD_LOG) | belegt |
| D1 | Arbeitgeber lehnt im Partnerportal ab | Status 5 „Odbijen“ (`lsp_izvor = 2`) **und** Absagegrund `idk_kandidati_reject_reasons` (`krr_source = 2`, `krr_last_status = 3`) innerhalb 2 min | 1.312 Absagegründe ↔ 1.312 Status-5-Zeilen (100 % der PP-Gründe); 1.486 Status-5-Zeilen insgesamt seit 2022-04 | belegt |
| D2 | Status 8 „Poslan ugovor“ / 9 „Potpisan ugovor“ im CRM | Vertragsdatei `idk_kandidati_contracts` ±2 min | 36/36 (8) · 36/36 (9) ab 2025; Status 7: 12/50 | belegt |
| D3 | Status 8/9 | Dokumentstatus-Log `idk_pp_documents_status_logs` | 18/36 · 19/36 | wahrscheinlich |
| D4 | Status 10 „Početak rada“ | Notiz (Gruppe 2) | 10/28 | vermutet |
| E1 | Status 6 per Transfer (`lsp_izvor = 6`) | Massenvorgang an einzelnen Tagen, keine Folgeschreibungen gemessen | 2024-01-10: 3.697 · 2025-02-20: 2.382 · 2023-11-24: 1.441 …; `idk_tf_transfered_candidates_logs` (725 Zeilen, Kandidatenliste als Text) | belegt (Massenaktion) |
| E2 | Statuswechsel im CRM (allgemein) | **keine** Zeile in `idk_messenger_obavijesti`, `idk_viber_obavijesti`, `idk_appointment_invite_links`, `idk_pp_reminders` im 5-min-Fenster | 0 Treffer in allen Status/Quellen ab 2025 | belegt (keine Sofort-Benachrichtigung) |

## 2. Cron-/Zeitplan-Muster

| # | Job (abgeleitet) | Schreibt | Beleg | Sicherheit |
|---|---|---|---|---|
| K1 | Täglicher Messenger-/SMS-Versand ca. 19:00 | `idk_messenger_obavijesti` (Typ 1 „SMS za instalaciju“, Typ 2 undok.) | 260.420 von 260.423 Zeilen mit Stunde 19; Volumen 2021 98,6k → 2025 626 | belegt |
| K2 | Casting-Cron 21:00 (2023-05 … 2024-09) | Status 3 „Casting“ mit `lsp_izvor = 5` | 1.921 Zeilen, alle Stunde 21, Sekunde 0–5 nach voller Stunde | belegt |
| K3 | Früherer Cron (2022-04 … 2023-03) | Status 2 mit `lsp_izvor = 5`, Stunden 7/13/16 | 395 Zeilen | wahrscheinlich |
| K4 | DIPL-Export täglich 00:00 | `idk_nd_cron_export` (Einstellungen `idk_nd_cron_settings`: Status/Tage/Kommunikationstage) | 7.581/7.581 Zeilen Stunde 0 | belegt |
| K5 | Queue-Zuweisung abends | Pipeline-Status mit `lsp_izvor = 4` (Queue), Spitzen 20–21 Uhr | 1.406 Zeilen; 20 h: 419, 21 h: 312 | wahrscheinlich |
| K6 | Casting-/Interview-Crons je Termingruppe | Flags `idk_pp_appointment_groups.ppaq_casting_cron_executed`, `ppaq_interview_cron_executed` | Spaltenkommentare; Inhalte nicht ausgewertet | vermutet |
| K7 | System-Aufgaben in Task-Force (Agent 0/NULL) | TF-Status 20 Došao (2.033), 18 Dolazi (1.259), 22 Nije došao (1.168), 16 Pristao (1.069) | 5.542 Zeilen, Arbeitszeit 8–18 Uhr (Spitze 9 Uhr) → eher ereignisgesteuert (Bestätigungslinks/Termine) als Cron | wahrscheinlich |
| K8 | Erinnerungen Partnerportal | `idk_pp_reminders` nach `idk_pp_reminder_settings` (`prs_create_after`, `prd_day_freq`) | 22.348 Zeilen; Zeitplan aus Spalten, nicht gemessen | vermutet |

## 3. Was das für Schreib-Tools bedeutet (Grundlage nach Go-live)

| Schreibaktion | Muss zusätzlich passieren (sonst Inkonsistenz) | Quelle |
|---|---|---|
| Pipeline-Status setzen (`set_application_status`) | Log-Zeile, `lsp_broj_dana` der Vorzeile, bei `rezervisanje = 1` `kandidat_latest_reserved_time` – **bereits umgesetzt**; zusätzlich i. d. R. `idk_task_force`-Zeile mit passendem TF-Status (C1) und ggf. `kandidat_tf_status` | C1, C3, C4 |
| Status 5 durch Arbeitgeber | Absagegrund `idk_kandidati_reject_reasons` (`krr_source`, `krr_last_status`, `krr_reason_id`) | D1 |
| Status 8/9 | Vertragsdatei `idk_kandidati_contracts`; ggf. Dokumentstatus-Log | D2, D3 |
| Neuer Kandidat | `idk_log_kandidat_statusi`, Bot-Status, `idk_notification`, ggf. DIPL-Datensatz | A1–A5 |
| Massen-Transfer | `idk_tf_transfered_candidates_logs` + Status 6 Quelle 6 | E1 |
| Benachrichtigungen | **nicht** synchron – Crons (K1) und Bot; direkte DB-Schreibungen lösen keinen Versand aus | E2, K1 |

**Offen (nicht messbar ohne Code):** Inhalt/Empfänger der Benachrichtigungen, ob `idk_logs` (3 Mio. Zeilen, nur Mitarbeiter-ID + Text) Statuswechsel protokolliert, Cron-Zeitpläne nach 2024, Wirkung von `idk_triggerurl`/`idk_api_clients`. Empfehlung bleibt: CRM-Code oder -API beschaffen, Automationen je Aktion bestätigen, erst dann `JSI_WRITES_ENABLED=true`.
