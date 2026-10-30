# Spaltenprofil Kandidaten (Punkt 18) – Zusammenfassung (Stand 2026-10-30)

Rohdaten: `docs/rohdaten/kandidat_profil.tsv` (eine Zeile je Spalte: Klasse, befüllt, Füllgrad, distinct, min/max nur für Zahl/Datum, Top-Werte nur für Codes, Plausibilität, Filtertyp). Generator: `build_profil.py` aus `profil_stat_raw.tsv`, `profil_top_raw.json`, `profil_top2_raw.json` (BlazeSQL-Abfragen aus `gen_profil_sql.py`).

**Umfang:** 279 Spalten in 17 Tabellen (`idk_kandidati` 96 + 4 [TAJNO] nicht gemessen, `idk_kandidat_jezici`, `_edukacija`, `_radno_iskustvo`, `_de`, `_cv`, `_kontakt_info`, `_vjestine`, `_akademija`, `_financije`, `idk_candidate_verified_languages`, `idk_candidate_language_logs`, `idk_kandidati_contracts`, `idk_kandidati_reject_reasons`, `idk_validnosti_inputa`, `users`, `idk_nostrifikovane_diplome`). Die in HANDOVER genannte Zahl „288 Spalten in 20 Tabellen“ war nicht reproduzierbar dokumentiert; dieses Set ist explizit.

**Datenschutz:** Für Personen-/Freitextspalten nur Füllgrad und Anzahl verschiedener Werte, nie Werte, Minimum oder Maximum. Text-Codes nur Werte mit ≥ 5 Vorkommen. [TAJNO]-Spalten (`kandidat_jmbg`, `_brojlk`, `_broj_pasosa`, `_password`) nicht berührt.

## Wichtigste Befunde (`idk_kandidati`, 122.006 Zeilen)

| Bereich | Spalte | Füllgrad | Bemerkung |
|---|---|---:|---|
| Beruf | `kandidat_prijava_na` | 100 % | 418 verschiedene Texte, 95 % über `beruf_mapping` normalisiert |
| Führerschein | `kandidat_vozacka_kategorija` / `_dozvola` | 42 % / 49 % | 49 Kombinationen; Legacy „Da“ 51.556 |
| Geburt | `kandidat_datumrodjenja` | 60 % | Platzhalter 1900, Zukunftswerte bis 2996 |
| Geschlecht | `kandidat_spol` | 12,6 % | Muško 12.347, Žensko 2.990, 69 leere Strings |
| Land | `kandidat_drzava` | 34,8 % | 683 Schreibweisen (BIH 14.101, „Bosna i Hercegovina“ 13.406 …) |
| Staatsang. | `kandidat_drzavljanstvo_vrsta` / `_drzavljanstvo` | 44 % / 14 % | NON-EU 48.423, EU 5.012; „nova_prijava“ 217 als Fehlwert |
| Familienstand | `kandidat_bracno_stanje` | 3,2 % ≠ 0 | Altspalte `kandidat_bracnostanje` leer |
| Erfahrung | `kandidat_iskustvo_u_struci` | 17,6 % | Dauer 7,9 % |
| Visum | `kandidat_viza` | 39,8 % | 1 = 1.231; Gültigkeitsdaten < 2 %, Zukunft bis 2050 |
| Pipeline | `kandidat_status_prijave` | 66,2 % | 1 Slobodan 54.276, 2 U projektu NR 22.817 |
| Herkunft | `kandidat_porijeklo` | 100 % | 4 svezavize 63.208, 0 alt 53.894; Codes 6–8 undokumentiert |
| Messenger | `kandidat_status_messenger` | 100 % | 3 abgelehnt 76.369 |
| DIPL | `kandidat_dipl_id` | 63,6 % | 77.584 distinct |
| Kontakt | `kandidat_mobitel` | 97,7 % | falsche Nummer 6.056, nicht erreichbar 57 |
| Fast leer (< 1 %) | Wunschregion/-stadt, Makler-Zuweisung, Bildungsniveau, Vertragsdaten, `kandidat_dostavljen_ugovor_jobstepu` (0) | | als Filter ungeeignet |

**Kindtabellen:** Sprachen 67.648 Kandidaten (Deutsch 69.999 Zeilen; Niveau „Bez znanja“ 34.707, A1 19.322, A2 10.603, B1 6.951 …), Ausbildung 78.349 (srednje 85 %), Erfahrung 35.774, Fähigkeiten 5.267 (Freitext), Zertifikate 351 Kandidaten (alle Deutsch, 309 A2, `cvl_status` 9 „istekao“ 362), Nostrifikation 2.105 (voll 447 Zeilen, teilweise 1.305, Wert 2 = 388 undokumentiert), Verträge 1.059 (signiert 975), Absagegründe 1.693 Kandidaten.

**Plausibilitätsfallen (für alle Filter):** leere Strings neben NULL in fast allen Textcodes; 0 als Default-Code (= unbekannt) bei `bracno_stanje`, `nacin_odlaska`, `viza`; Datumsplatzhalter 1900-01-01/1970-01-01; Zukunftsdaten; `full_recognition = 2` und `kandidat_porijeklo` 6–8 ohne Doku.
