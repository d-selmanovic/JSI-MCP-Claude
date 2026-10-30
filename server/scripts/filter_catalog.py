#!/usr/bin/env python3
"""Single source for the candidate filter catalogue (Stand 2026-10-30, gemessen über BlazeSQL).

Writes:
  server/src/jsi_mcp/filter_catalog.json                       (maschinenlesbar, vom Server ausgeliefert)
  server/src/jsi_mcp/skills/jsi-kandidat-filter/references/filteri.md  (Doku, aus derselben Quelle generiert)
Fill rates and pitfalls come from docs/rohdaten/kandidat_profil.tsv and veze_komplett.tsv.
Run: python3 -I server/scripts/filter_catalog.py   (after changing a filter in server/src/jsi_mcp/build_query.py)
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
N = 122006  # idk_kandidati rows 2026-10-30

# key, group, title, source, join, values, fill (candidates with data), pitfalls, example
F = [
    ("zanimanje", "Beruf", "Beruf / Zanimanje",
     "kandidat_prijava_na, kandidat_pp_pozicija, kandidat_group, kri_pozicija(_de), ke_naziv_kvalifikacije, idk_skole_smjerovi.ss_naziv(_de), kde_prijava_na",
     "beruf_mapping.freitext_wert = Freitext → berufsgruppe_id; idk_kandidat_radno_iskustvo.kri_kandidat_id, idk_kandidat_edukacija.ke_kandidat_id (+ ke_smjer_id → ss_id), idk_kandidat_de.kde_kandidat_id",
     "28 Katalogberufe mit Synonymen (occupations.json) + alle 194 berufsgruppe_id (berufsgruppen.json); freie Stichwörter",
     "prijava_na 100 % (95 % gemappt), iskustvo 35.774 Kand. (100 % gemappt), kvalifikacija 78.349 Kand. (67 % gemappt), de_profil 3.332 (45 % gemappt)",
     "Bewerbung ≠ Qualifikation → izlaz='izvori' zeigt Beweisstärke; 'mehrfach' (6.748 Texte) und 'unklar' sind Sammelgruppen",
     {"zanimanje": "Elektriker", "izlaz": "izvori"}),
    ("vozacka", "Führerschein", "Führerschein (EU-Logik)", "kandidat_vozacka_kategorija (Liste 'B,C1,C,CE'), Legacy kandidat_vozacka_dozvola",
     "–", "AM, A1, A2, A, B1, B, BE, C1, C1E, C, CE, D1, D1E, D, DE, E, F, G, M; strict, mode any/all, true = irgendeiner",
     "kategorija 42,2 % (51.511), dozvola 49,2 % (Da 51.556, Ne 8.059)", "höhere Klasse erfüllt niedrigere (C ⇐ CE); DE-Profil kde_vozacka ist Freitext ('zu', 'B') und wird NICHT genutzt",
     {"vozacka": ["C", "CE"]}),
    ("jezik", "Sprache", "Sprache + CEFR je Fertigkeit + Zertifikat", "idk_kandidat_jezici.kj_naziv, kj_govorna_interakcija/_produkcija, kj_citanje, kj_slusanje, kj_pisanje; idk_candidate_verified_languages.cvl_certificate_path/_expiration_date",
     "kj_kandidatid = kandidat_id; cvl_id = kj_id (1:1)", "njemacki, engleski, talijanski, spanjolski, francuski, ruski, arapski, turski; A1–C2; vjestina; certifikat true|'vazeci'",
     "67.648 Kand. mit Sprache (Njemački 69.999 Zeilen); Zertifikat 351 Kand. (367 Dateien, alle Deutsch, 309 davon A2)",
     "Selbstauskunft; 'Bez znanja'/'Bezznanja' = 0; Zertifikate fast nur Techniker-Gruppen (0 Pflegekräfte); cvl_status 8 'ima certifikat' nur 2× – Datei zählt",
     {"jezik": {"jezik": "de", "min_nivo": "B1", "certifikat": True}}),
    ("obrazovanje", "Ausbildung", "Ausbildung / Schule / Fachrichtung", "ke_vrsta_obrazovanja, ke_skola_id, ke_smjer_id, ss_naziv, ke_naziv_kvalifikacije",
     "ke_kandidat_id; ke_skola_id → idk_skole.skola_id (99,9 %), ke_smjer_id → idk_skole_smjerovi.ss_id (99,9 %)",
     "vrsta srednje|visoko|ostalo; smjer (Stichwort); skola_id/smjer_id [..]", "78.349 Kand.; vrsta srednje 126.704 / visoko 5.459 / ostalo 1.250 Zeilen",
     "kandidat_nivo_obrazovanja fast leer (25) – nicht verwenden", {"obrazovanje": {"vrsta": "srednje", "smjer": "elektro"}}),
    ("iskustvo_u_struci", "Erfahrung", "Berufserfahrung (Selbstauskunft-Flag)", "kandidat_iskustvo_u_struci, kandidat_iskustvo_u_struci_trajanje (0–6)", "–",
     "true | {'min_godina':1..6}", "17,6 % (21.441); Dauer 7,9 %", "Skala 2–6 nicht sicher dokumentiert (HANDOVER A3/9)", {"iskustvo_u_struci": {"min_godina": 2}}),
    ("radno_iskustvo", "Erfahrung", "Berufserfahrung in Jahren aus dem CV (+ Branche)", "kri_darum_od, kri_datum_do, kri_aktuelno, kri_pozicija → beruf_mapping",
     "kri_kandidat_id", "{'min_godina': 0..50, 'zanimanje': Katalogberuf}", "35.774 Kand.; Enddatum 69 %", "Überlappende Stellen werden addiert; ohne Enddatum zählt nur 'aktuelno'",
     {"radno_iskustvo": {"min_godina": 2, "zanimanje": "elektriker"}}),
    ("drzava", "Herkunft", "Wohnland", "kandidat_drzava (Freitext)", "–", "BIH, SRB, HRV, DEU, MNE, SVN, MKD, XKX, AUT", "34,8 % (42.444)",
     "Freitextvarianten ('BIH', 'Bosna i Hercegovina', 'Bosna') per REGEXP normalisiert", {"drzava": ["BIH", "SRB"]}),
    ("drzavljanstvo", "Herkunft", "Staatsangehörigkeit", "kandidat_drzavljanstvo_vrsta (EU/NON-EU), kandidat_drzavljanstvo (Freitext)", "–",
     "EU, NON-EU, BIH, SRB, HRV, MNE, MKD, SVN, BGR, HUN, DEU, ITA, AUT, XKX, ALB", "vrsta 44,0 %, Land 14,3 %",
     "'nova_prijava' (217) als Wert in vrsta", {"drzavljanstvo": ["BIH"]}),
    ("grad", "Herkunft", "Wohnort", "kandidat_grad (Freitext, Personendatum – nur als Filter)", "–", "Stichwort ≥ 3 Zeichen", "34,9 %", "nie in Ausgabe ohne PII-Recht", {"grad": "Tuzla"}),
    ("starost", "Person", "Alter", "kandidat_datumrodjenja", "–", "{'od':..,'do':..}", "60,4 % (73.711)", "Platzhalter 1900, Zukunftsdaten (max 2996) → nur > 1940 gezählt", {"starost": {"od": 25, "do": 45}}),
    ("spol", "Person", "Geschlecht", "kandidat_spol", "–", "m (Muško 12.347), z (Žensko 2.990)", "12,6 %", "DE-Profil kde_spol nicht genutzt", {"spol": "z"}),
    ("bracno_stanje", "Person", "Familienstand", "kandidat_bracno_stanje", "–", "0 unbekannt, 1 ledig, 2 verheiratet, 3 verwitwet, 4 geschieden", "3,2 % ≠ 0",
     "Altspalte kandidat_bracnostanje (Text) leer", {"bracno_stanje": [2]}),
    ("registriran", "Aktivität", "Registrierung", "kandidat_datetime", "–", "{'od','do'}", "100 %", "Platzhalter 1970-01-01 vorhanden", {"registriran": {"od": "2024-01-01"}}),
    ("aktivan", "Aktivität", "Aktivität (Statuswechsel im Zeitraum)", "idk_log_statusi_prijave.lsp_datetime", "lsp_kandidat_id", "{'od','do'}",
     "80.765 Kand. mit Log (ab 2021-12)", "Aktivität endet weitgehend Feb 2026", {"aktivan": {"od": "2025-01-01"}}),
    ("porijeklo", "Kanal", "Herkunft / Kanal", "kandidat_porijeklo", "–", "0 alt/CRM (53.894), 1 DIPL (1.887), 2 DAK (58), 3 Partner, 4 svezavize (63.208), 5 JobStep-Web (964), 6/7/8 undokumentiert",
     "100 %", "6–8 nicht im Spaltenkommentar", {"porijeklo": [4, 5]}),
    ("messenger_status", "Kanal", "Messenger-Status", "kandidat_status_messenger", "–", "0–6 (3 abgelehnt 76.369, 2 eingeloggt 30.843 …)", "100 %", "", {"messenger_status": [2]}),
    ("glossa", "Kanal", "Glossa-Lead", "kandidat_glossa", "–", "0–3 (1 = 64, 3 = 21)", "85 Kand. ≠ 0", "", {"glossa": [1, 2, 3]}),
    ("makler", "Partner", "Makler / JobStep-Partner", "kandidat_partnerid", "→ idk_jobstep_partners.jp_id (99,8 %)", "true | [jp_id]", "2.009 Kand. (1,6 %)",
     "zaduzeni_makler_id/assigned_to_makler praktisch leer", {"makler": True}),
    ("pp_partner_id", "Partner", "Arbeitgeber-Partner (Partnerportal)", "kandidat_ppa_partner_id", "→ idk_pp_partners.ppa_id (99,8 %)", "[ppa_id]", "584 Kand.", "", {"pp_partner_id": [10]}),
    ("kandidat_status", "Pipeline", "Bearbeitungsstatus", "kandidat_status", "→ idk_kandidat_status.status_id (100 %)", "0–8 (3 = Archiv, Standard ausgeschlossen)", "100 %",
     "Log lks_status_obrade enthält Code 9, der in der Lookup fehlt (78 % Treffer)", {"kandidat_status": [1, 2]}),
    ("status_prijave", "Pipeline", "Bewerbungs-/Pipelinestatus (aktuell)", "kandidat_status_prijave", "→ idk_kandidat_status_prijave.status_id (100 %)",
     "1 Slobodan … 9 Potpisan ugovor … 27 Dobio vizu", "66,2 %", "NULL = nie im Prozess (41.299)", {"status_prijave": [9]}),
    ("faza_min", "Pipeline", "Mindestphase (redoslijed_statusa)", "idk_kandidat_status_prijave.redoslijed_statusa", "status_id", "1–15 (7 = Vertrag unterschrieben oder weiter)",
     "66,2 %", "Status 5 'Odbijen' hat keine Phase → fällt raus", {"faza_min": 7}),
    ("status_historija", "Pipeline", "War jemals im Status", "idk_log_statusi_prijave", "lsp_kandidat_id; lsp_projekt_id → idk_projects (98,8 %) → project_nalogid",
     "{'status':[..],'od','do','nalog_id','projekt_id'}", "80.765 Kand.", "Log erst ab 2021-12-07; Auftrag nur über Projekt des Logs", {"status_historija": {"status": [9], "nalog_id": [254]}}),
    ("slobodni", "Pipeline", "Frei (nicht reserviert)", "kandidat_status_prijave + rezervisanje", "–", "true = NULL/0/1/2/5", "100 %", "", {"slobodni": True}),
    ("nalog_id", "Auftrag", "Auftrag", "kandidat_nalog_id (+ nalog_izvor=projekt|oba: idk_project_kandidati → idk_projects.project_nalogid)",
     "→ idk_nalozi.nalog_id (100 %); project_nalogid varchar → CAST (97 %)", "[nalog_id], nalog_izvor kandidat|projekt|oba", "2.961 Kand. direkt; Projekte 113.960 Kand.",
     "kandidat_nalog_id = nur aktuelle Zuordnung", {"nalog_id": [254], "status_prijave": [9]}),
    ("projekt_id", "Auftrag", "Projektmitglied", "idk_project_kandidati.pk_projectid", "pk_kandidatid (98,8 %)", "[project_id]", "113.960 Kand.", "", {"projekt_id": [100]}),
    ("firma_id", "Auftrag", "Firma", "kandidat_zaposlen_kod, idk_projects.project_companyid", "→ idk_companies (100 %)", "[company_id]", "354 direkt + Projekte", "", {"firma_id": [1]}),
    ("tf_status", "Task-Force", "Aktiver Task-Force-Status", "kandidat_tf_status", "→ idk_tf_statusi.tfs_id (100 %)", "true | [tfs_id]", "1.704 Kand.", "nur aktive Tasks", {"tf_status": True}),
    ("tf_agent_id", "Task-Force", "Reserviert für Agent", "tf_reserved_agent", "→ idk_employees (100 %)", "[employee_id]", "320 Kand.", "", {"tf_agent_id": [12]}),
    ("casting", "Task-Force", "Casting-Ergebnis", "idk_tf_stats_reservations.tsr_status, tsr_nalog_id; idk_pp_appointment_groups.ppaq_start_date",
     "tsr_candidate_id (100 %), tsr_interview_id → ppaq_id (99,5 %)", "status 1 Došao, 2 Nije došao, 3 Odustao (4/5 undok.); nalog_id; od/do", "3.271 Kand. (3.852 Reservierungen)",
     "Castings 2026 ohne 'Došao' (HANDOVER A3/10)", {"casting": {"status": [1]}}),
    ("intervju", "Partnerportal", "Interview / Arbeitgeber-Empfehlung", "idk_pp_cand_appts.pca_recommendation, pca_status; idk_pp_appointments.pap_nalog_id",
     "pca_kandidat_id (100 %), pca_appointment_id → pap_id (99,9 %)", "preporuka hire|reject|not_sure, nalog_id, aktivan", "5.551 Kand.; Empfehlung nur 567 Termine", "", {"intervju": {"preporuka": "hire"}}),
    ("odbijen", "Partnerportal", "Absage + Grund", "idk_kandidati_reject_reasons.krr_reason_id → idk_reject_reasons", "krr_candidate_id (100 %)",
     "razlog_id 1,4,7,10,13,16,19,22; odbio kandidat|poslodavac; nalog_id", "1.693 Kand.", "krr_partner_id ist leer", {"odbijen": {"odbio": "poslodavac"}}),
    ("dokument_status", "Dokumente", "Dokumentstatus (Partnerportal)", "idk_pp_documents.doc_status → idk_pp_documents_statuses", "doc_candidate_id (100 %)",
     "3 Uploadan, 6 Provjeren, 9 Čekamo original, 12 Poslan, 15 Imamo original, 18 Spreman, 21 Nije prošao, 24 Odbijen, 27 Arhiviran", "574 Kand.", "", {"dokument_status": [18]}),
    ("ima_dokumente", "Dokumente", "Hat Dokumente", "idk_documents (Gruppe 2) ∪ idk_pp_documents", "document_dataid (Gruppe 2 = Kandidat, 99,97 %)", "true", "Dokumente 23.076", "Gruppe 2 = Kandidat ist abgeleitet", {"ima_dokumente": True}),
    ("ima_biljeske", "Dokumente", "Hat Notizen", "idk_notes (note_group 2)", "note_dataid (99,98 %)", "true", "182.850 Notizen", "Gruppe 2 = Kandidat abgeleitet", {"ima_biljeske": True}),
    ("ugovor", "Dokumente", "Vertrag hochgeladen / unterschrieben", "idk_kandidati_contracts.kc_signed, kc_visibility_status", "kc_candidate_id (100 %)", "postoji | potpisan", "1.059 Kand.; signiert 975 Zeilen", "", {"ugovor": "potpisan"}),
    ("cv_de", "Dokumente", "Deutscher CV", "cv_de", "–", "true", "1.663", "", {"cv_de": True}),
    ("profil_de", "Dokumente", "Deutsches Profil", "profile_de", "–", "true", "916", "", {"profil_de": True}),
    ("viza", "Visum", "Visum", "kandidat_viza; Log Status 27; idk_pp_visa_incomplete.vi_type", "vi_cand_id (100 %)", "ima, nema, dobio, odbijena, dopuna",
     "kandidat_viza 39,8 % (1 = 1.231); Partnerportal 49 Zeilen", "'odbijena'/'dopuna' nur Partnerportal", {"viza": "dobio"}),
    ("termin_za_vizu", "Visum", "Visatermin", "kandidat_termin_za_vizu", "–", "true/false", "2,0 %", "", {"termin_za_vizu": True}),
    ("nacin_odlaska", "Visum", "Ausreiseweg", "kandidat_nacin_odlaska", "–", "0 Fachkraft/EU (120.994), 2 Westbalkan (999), 3 undok. (13)", "100 %", "0 ist Default", {"nacin_odlaska": [2]}),
    ("pocetak_rada_potvrden", "Visum", "Arbeitsbeginn bestätigt", "kandidat_potvrden_pocetak_rada", "–", "true", "515", "", {"pocetak_rada_potvrden": True}),
    ("nostrifikacija", "Nostrifikation", "Nostrifikation / Diplom-Anerkennung", "idk_nostrifikovane_diplome.full_recognition", "id_cand_job → kandidat_id (97,8 %)",
     "true/potpuno (447 Zeilen), djelimicno (1.305), status_2 (388, undok.), bilo_koje", "2.105 Kand.", "Wert 2 nicht dokumentiert; nur 4 Pflegekräfte voll anerkannt", {"nostrifikacija": "potpuno"}),
    ("dipl", "Nostrifikation", "DIPL-Verknüpfung / DIPL-Status", "kandidat_dipl_id → idk_nd_kandidata.status_nd_kandidata", "kandidat_dipl_id (99,96 %)",
     "true | {'povezan':bool,'status':[..]}", "77.616 Kand. (63,6 %)", "Status braucht jsi:dipl:read; nie über kandidat_id joinen", {"dipl": {"povezan": True}}),
    ("kontaktabilni", "Kontakt", "Kontaktierbar", "kandidat_pogresan_broj, kandidat_nedostupan, kandidat_mobitel", "–", "true", "Mobil 97,7 %; falsche Nr. 6.056; nicht erreichbar 57", "", {"kontaktabilni": True}),
    ("vjestina", "Fähigkeiten", "Fähigkeit", "idk_kandidat_vjestine.kv_naziv(_de)", "kv_kandidat_id (100 %)", "Stichwort(e)", "5.267 Kand.", "Freitext ('Ms Office', 'Komunikativnost')", {"vjestina": "Office"}),
    ("grupa_id", "Beruf", "Bewerbungsgruppe", "kandidat_group", "→ idk_kandidati_grupe.kg_id (100 %)", "[kg_id] (74 Gruppen)", "100 %", "", {"grupa_id": [38, 39]}),
    ("ukljuci_arhivu", "Steuerung", "Archiv einschließen", "kandidat_status = 3", "–", "true", "4.447 archiviert", "Standard: ausgeschlossen", {"ukljuci_arhivu": True}),
]
OUTPUT = {"izlaz": "broj | izvori | lista | id", "limit": "1–5000 (Standard 200)", "offset": "0–1000000 (Standard 0): Seite – so viele Treffer überspringen; der Server liefert dazu stranica (ukupno, prikazano_od/do, sljedeci_offset, pregled „Prikazano X–Y od N“)", "pii": "Name/Telefon/E-Mail nur mit jsi:kandidati:pii",
          "sortiraj": "relevantnost | novi"}
NOT_FILTERABLE = [
    ("Wunschgehalt", "kandidat_pp_plata 0,3 % befüllt (Freitext)"),
    ("Wunschregion/-stadt", "kandidat_zeljena_regija 9 Werte, kandidat_zeljeni_grad leer"),
    ("Aufenthalt EU (boravak_eu)", "21 % befüllt, Freitext NE/NN/Ländernamen – als Filter nicht aufgenommen"),
    ("DE-Profil-Führerschein / -Geschlecht", "kde_vozacka/kde_spol Freitext ('zu', 'Frau'), 3.332 Profile"),
    ("Agent der Bewerbung", "lsp_employee_id (69 % befüllt) – als Kennzahl, nicht als Kandidatenfilter"),
    ("Polymorphe Notizen/Dokumente anderer Gruppen", "note_group 1, 3–8 nicht eindeutig zuordenbar (poly_results.tsv)"),
]


def main():
    cat = {"stand": "2026-10-30", "kandidaten_gesamt": N, "filter": [], "ausgabe": OUTPUT,
           "nicht_filterbar": [{"dimension": d, "grund": g} for d, g in NOT_FILTERABLE]}
    for key, grp, title, src, join, vals, fill, trap, ex in F:
        cat["filter"].append({"schluessel": key, "gruppe": grp, "titel": title, "quelle": src, "join": join, "werte": vals,
                              "fuellgrad": fill, "fallstricke": trap, "beispiel": ex})
    js = json.dumps(cat, ensure_ascii=False, indent=1)
    for p in (os.path.join(REPO, "server", "src", "jsi_mcp", "filter_catalog.json"),):
        with open(p, "w", encoding="utf-8") as f:
            f.write(js + "\n")
    md = ["# Filterkatalog `search_candidates` (Stand 2026-10-30)", "",
          "Generiert aus `server/scripts/filter_catalog.py` (gleiche Quelle wie `filter_catalog.json` im Server). Füllgrade gemessen über BlazeSQL",
          f"(Basis {N:,} Kandidaten, `docs/rohdaten/kandidat_profil.tsv`), Join-Trefferquoten aus `docs/rohdaten/veze_komplett.tsv`.".replace(",", "."),
          "Alle Filter werden mit UND kombiniert; Kindtabellen immer als CTE (`SELECT DISTINCT kid`) – nie korreliertes EXISTS.", "",
          f"**{len(F)} Filter** (vorher 19) + {len(OUTPUT)} Ausgabeoptionen. Ein Tool-Aufruf genügt, z. B.", "",
          "```json", '{"zanimanje":"Elektriker","jezik":{"jezik":"de","min_nivo":"A2"},"vozacka":"B"}', "```", ""]
    groups = []
    for f_ in F:
        if f_[1] not in groups:
            groups.append(f_[1])
    for g in groups:
        md += [f"## {g}", "", "| Schlüssel | Bedeutung | Quelle (Tabelle.Spalte) | Join | Gültige Werte | Füllgrad | Fallstricke | Beispiel |",
               "|---|---|---|---|---|---|---|---|"]
        for key, grp, title, src, join, vals, fill, trap, ex in F:
            if grp == g:
                md.append(f"| `{key}` | {title} | {src} | {join} | {vals} | {fill} | {trap or '–'} | `{json.dumps(ex, ensure_ascii=False)}` |")
        md.append("")
    md += ["## Ausgabe", "", "| Schlüssel | Werte |", "|---|---|"] + [f"| `{k}` | {v} |" for k, v in OUTPUT.items()] + [""]
    md += ["## Bewusst nicht als Filter", "", "| Dimension | Grund |", "|---|---|"] + [f"| {d} | {g} |" for d, g in NOT_FILTERABLE] + [""]
    md += ["## Abnahme-Beispiele (BlazeSQL 2026-10-30, Tool-SQL = Gegenprobe)", "",
           "| Anfrage | Spec | Tool-SQL | Gegenprobe |", "|---|---|---|---|",
           '| Elektriker, Deutsch A2, Führerschein B | `{"zanimanje":"Elektriker","jezik":{"jezik":"de","min_nivo":"A2"},"vozacka":"B"}` | 3.199 | – (Teilfilter wie Ref. Elektriker+C 2.672) |',
           '| Schweißer aus BiH 25–45, frei, C/CE | `{"zanimanje":"Schweißer","drzava":"BIH","starost":{"od":25,"do":45},"slobodni":true,"vozacka":["C","CE"]}` | 45 | 45 |',
           '| Pflegekräfte, DE-Zertifikat B1, Nostrifikation abgeschlossen | `{"zanimanje":["krankenpfleger","pflegehelfer"],"jezik":{"jezik":"de","min_nivo":"B1","certifikat":true},"nostrifikacija":true}` | 0 | 0 (auch ohne Niveau 0; DIPL-Zertifikat 0) |',
           '| Auftrag 254, Status Vertrag unterschrieben | `{"nalog_id":[254],"status_prijave":[9]}` | 15 | 15 (Phase ≥ 7: 165; jemals Status 9 im Auftrag: 276) |', ""]
    with open(os.path.join(REPO, "server", "src", "jsi_mcp", "skills", "jsi-kandidat-filter", "references", "filteri.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(md))
    print(len(F), "Filter geschrieben")


if __name__ == "__main__":
    main()
