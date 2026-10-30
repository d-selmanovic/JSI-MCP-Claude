#!/usr/bin/env python3
"""Klassifiziert ALLE 1.809 Spalten aus columns.json nach "verweisartig" (gemessen) oder "ausgeschlossen" (mit Grund).

Ausgabe: verweis_kandidaten.tsv  (eine Zeile je Spalte -> Vollständigkeit prüfbar)
Spalten: tabelle, spalte, typ, klasse, ziel(e), grund

Klassen (aufgenommen):
  FK      Verweis auf eine Entität (Ziel = Tabelle.PK), gemessen per Join
  LOOKUP  Code mit Lookup-/Stammtabelle, gemessen per Join
  POLY    polymorpher Verweis (Wert gehört je nach Gruppen-/Quellen-Spalte zu verschiedenen Zielen), je Gruppenwert gemessen
  TEXTREF Text-Verweis (Freitext -> beruf_mapping.freitext_wert)
  LISTE   kommagetrennte ID-Liste (nur Plausibilität)
  CODE    Status-/Typ-/Gruppen-/Flag-Code ohne Lookup-Tabelle -> Werteverteilung gemessen
Klassen (ausgeschlossen): PK, SENSIBEL, DATUM, TEXT, PII, ZAHL, TECH

Zielbestimmung: Namensregeln + Kommentare + Wertebereich-Abgleich (mehrere Ziele = Hypothesen; das beste Ergebnis
steht in veze_komplett.tsv). Aufruf: python3 -I gen_verweise.py  (im Ordner docs/rohdaten)
"""
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))

K = "idk_kandidati.kandidat_id"
D = "idk_nd_kandidata.id_broj_nd_kandidata"
E = "idk_employees.employee_id"
N = "idk_nalozi.nalog_id"
P = "idk_projects.project_id"
C = "idk_companies.company_id"
JP = "idk_jobstep_partners.jp_id"
PPA = "idk_pp_partners.ppa_id"
PU = "idk_pp_users.pu_id"
CL = "idk_clients.client_id"
CT = "idk_contacts.contact_id"
SS = "idk_skole_smjerovi.ss_id"
SK = "idk_skole.skola_id"
LG = "idk_link_generator.lg_id"
SP = "idk_kandidat_status_prijave.status_id"
TFV = "idk_tf_vrste.id"
PPAQ = "idk_pp_appointment_groups.ppaq_id"
PAP = "idk_pp_appointments.pap_id"
PCA = "idk_pp_cand_appts.pca_id"
PR = "idk_predracuni.pr_id"
UST = "idk_nd_ustanove.id_ustanove_nd"
ROU = "idk_ro_usluge.id_ro"

# (tabelle, spalte) -> (klasse, [ziele], grund)
M = {}


def fk(t, c, targets, why="Name/Kommentar", klass="FK"):
    M[(t, c)] = (klass, targets if isinstance(targets, list) else [targets], why)


def poly(t, c, by, targets, why):
    M[(t, c)] = ("POLY", targets, f"gruppiert nach {by}; {why}")


# --- Kandidaten (Vermittlung)
for c, tg in [("kandidat_group", "idk_kandidati_grupe.kg_id"), ("kandidat_status", "idk_kandidat_status.status_id"),
              ("kandidat_status_prijave", SP), ("kandidat_tf_status", "idk_tf_statusi.tfs_id"),
              ("struka_sa_prijave", "idk_struke.id_struke"), ("kandidat_zeljena_regija", "idk_pp_regions.pr_id"),
              ("kandidat_zeljeni_grad", "idk_pp_city.pc_id")]:
    fk("idk_kandidati", c, tg, "Lookup laut Name/Kommentar", "LOOKUP")
for c, tg in [("kandidat_nalog_id", N), ("kandidat_ppa_partner_id", PPA), ("kandidat_dipl_id", D),
              ("tf_reserved_agent", E), ("zaduzeni_makler_id", [JP, E]), ("kandidat_partnerid", JP),
              ("kandidat_zaposlen_kod", C), ("kandidat_pp_povezao_user_id", [PU, E]), ("assigned_to_makler", [JP, E]),
              ("kandidat_visitedurl", LG), ("kandidat_sms_id", "idk_sms_messages.sms_id")]:
    fk("idk_kandidati", c, tg)
fk("idk_kandidati", "kandidat_prijava_na", "beruf_mapping.freitext_wert", "Freitext -> Berufsgruppe", "TEXTREF")
fk("idk_kandidat_radno_iskustvo", "kri_pozicija", "beruf_mapping.freitext_wert", "Freitext -> Berufsgruppe", "TEXTREF")
fk("idk_kandidat_edukacija", "ke_naziv_kvalifikacije", "beruf_mapping.freitext_wert", "Freitext -> Berufsgruppe", "TEXTREF")
fk("idk_kandidat_de", "kde_prijava_na", "beruf_mapping.freitext_wert", "Freitext -> Berufsgruppe", "TEXTREF")
fk("beruf_mapping", "berufsgruppe_id", [], "Berufsgruppen-Code (194 Werte), keine Stammtabelle", "CODE")

# --- Kandidaten-Kindtabellen
for t, c in [("idk_kandidat_jezici", "kj_kandidatid"), ("idk_kandidat_edukacija", "ke_kandidat_id"),
             ("idk_kandidat_radno_iskustvo", "kri_kandidat_id"), ("idk_kandidat_de", "kde_kandidat_id"),
             ("idk_kandidat_cv", "kcv_kandidatid"), ("idk_kandidat_kontakt_info", "kki_kandidat_id"),
             ("idk_kandidat_vjestine", "kv_kandidat_id"), ("idk_kandidat_akademija", "ka_kandidat_id"),
             ("idk_kandidat_financije", "kandidat_id"), ("idk_kandidati_contracts", "kc_candidate_id"),
             ("idk_kandidati_reject_reasons", "krr_candidate_id"), ("idk_candidate_language_logs", "cll_candidate_id"),
             ("idk_log_statusi_prijave", "lsp_kandidat_id"), ("idk_log_kandidat_statusi", "lks_kandidat_id"),
             ("idk_task_force", "tf_candidate_id"), ("idk_tf_reservations", "tf_kandidat_id"),
             ("idk_tf_stats_reservations", "tsr_candidate_id"), ("idk_project_kandidati", "pk_kandidatid"),
             ("idk_pp_documents", "doc_candidate_id"), ("idk_pp_cand_appts", "pca_kandidat_id"),
             ("idk_pp_cand_required_documents", "crd_cand_id"), ("idk_pp_contract_sent", "cs_kandidat_id"),
             ("idk_pp_ratings", "pra_kandidat_id"), ("idk_pp_reminders", "pr_candidate_id"),
             ("idk_pp_visa_incomplete", "vi_cand_id"), ("idk_messenger_obavijesti", "mo_kandidat_id"),
             ("idk_bot_obavijesti", "bo_kandidat_id"), ("idk_viber_obavijesti", "vo_kandidati_id"),
             ("idk_appointment_invite_links", "candidate_id"), ("idk_validnosti_inputa", "vi_kandidat_id"),
             ("idk_nedostupan_log", "kandidat"), ("users", "kandidat_id"), ("idk_nostrifikovane_diplome", "id_cand_job"),
             ("idk_nd_kandidati_ciscenje", "id_kandidata_posao"), ("idk_nd_kandidata", "kandidat_idd"),
             ("mcp_aenderung", "a_kandidat_id")]:
    fk(t, c, K)
fk("idk_project_candidate_queue", "queue_candidate_id", K, "varchar(7) -> CAST")
fk("idk_kandidat_financije", "kf_zamjena_id", [K, "idk_kandidat_financije.kf_id"], "Zamjena = Ersatz (Hypothesen)")
fk("idk_notification", "not_kandidatid", [K, D], "Typ 2 = ponovna prijava (DIPL?) -> beide ID-Räume geprüft")
fk("idk_glossa_log", "candidate", K, "Kommentar: FK idk_kandidati (text) -> CAST")
poly("idk_partner_uplate", "jp_uplate_kandidatid", "jp_uplate_vrsta", [K, D], "1 = NALOG (Kandidat), 2 = DIPL")

# --- DIPL-ID-Raum
for t, c in [("idk_predracuni", "pr_kandidat_id"), ("idk_racuni", "racun_kandidat_id"),
             ("idk_nd_kandidata_biljeske", "id_kandidata_biljeska_nd"), ("idk_nd_kandidata_status_log", "idd_broj_nd_kandidata"),
             ("idk_nd_kandidata_dokumenti", "id_kandidata_dokument_nd"), ("idk_nd_termini", "termin_kandidat_id"),
             ("idk_nd_ugovori", "ug_kandidat_id"), ("idk_nd_rate", "id_nd_kan"), ("idk_nd_menadzeri_statistike", "idd_broj_nd_kandidata"),
             ("idk_ponovne_prijave", "id_kandidata"), ("idk_nostrifikovane_diplome", "id_cand_dipl"),
             ("idk_nd_kandidati_ciscenje", "id_kandidata_dipl"), ("idk_tf_reservations", "tf_dipl_id")]:
    fk(t, c, [D, K] if t in ("idk_predracuni", "idk_racuni") else D, "DIPL-ID-Raum (HANDOVER §5)")
poly("idk_reminders", "reminder_candidate_id", "reminder_type", [D, K], "1 = Obrada dipl, 2 = odbijeni ugovori")
poly("idk_reminders", "reminder_foreign_key", "reminder_type",
     ["idk_nd_kandidata_biljeske.id_biljeska_nd", "idk_nd_ugovori.ug_id"], "Kommentar: Typ 1 -> Biljeska-ID")
for c in ["lt_zadnji_dobio_bih", "lt_zadnji_dobio_srb", "lt_zadnji_dobio_de", "lt_zadnji_dobio_ostalo"]:
    fk("idk_nd_limiti", c, [D, K], "'zuletzt erhalten' -> Kandidat-ID (Hypothese)")
fk("idk_nd_kandidata", "skola_nd_kandidata", SK, "Kommentar")
fk("idk_nd_kandidata", "skola_smjer_nd_kandidata", SS, "Kommentar")
fk("idk_nd_kandidata", "poslodavac_naziv_nas_nd_kandidata", C, "Arbeitgeber = unsere Firma (Hypothese)")
fk("idk_nd_kandidata", "tim_nd_kandidata", "idk_timovi.id_t")
fk("idk_nd_kandidata", "idd_ustanova_nd", UST)
fk("idk_nd_kandidata", "idd_kontakt_ustanova_nd", "idk_nd_ustanove_kontakti.id_kontakt_ustanove_nd")
fk("idk_nd_kandidata", "kampanja_id", "idk_kampanje_dipl.kd_id")
fk("idk_nd_kandidata", "link_tracking_number_nd_kandidata", LG, "Hypothese")
fk("idk_nd_kandidata_biljeske", "razlog_biljeska_nd", ROU, "Kommentar", "LOOKUP")
fk("idk_nd_kandidata_biljeske", "predracun_id", PR, "Kommentar")
fk("idk_nd_termini", "termin_biljeska_id", "idk_nd_kandidata_biljeske.id_biljeska_nd", "Kommentar")
fk("idk_nd_ugovori", "ug_razlog_odbijanja", ROU, "RO-Usluge Typ 3 (Hypothese)", "LOOKUP")
fk("idk_nd_kandidati_ciscenje", "skola", SK)
fk("idk_nd_kandidati_ciscenje", "smjer", SS)
fk("idk_nd_ustanove_biljeske", "id_ustanova_biljeska_nd", UST)
fk("idk_nd_ustanove_kontakti", "idd_ustanove_nd", UST)
fk("idk_nd_ustanove_skola", "idd_ustanove_nd", UST)
fk("idk_nd_ustanove_skola", "skola_idd", SK)
fk("idk_nd_ustanove_skole_smjerovi", "idd_skole_ustanove_nd", "idk_nd_ustanove_skola.id_skole_ustanove_nd")
fk("idk_nd_ustanove_skole_smjerovi", "ss_idd", SS)
fk("idk_nd_ustanove_tip_dokumenta", "idd_ustanove_nd", UST)
fk("idk_nd_ustanove_tip_dokumenta", "idd_skole_ustanove_nd", "idk_nd_ustanove_skola.id_skole_ustanove_nd")
fk("idk_nd_ustanove_tip_dokumenta", "idd_skole_smjer_ustanove_nd", "idk_nd_ustanove_skole_smjerovi.id_skole_smjer_ustanove_nd")
fk("idk_nd_cron_export", "settings_id", "idk_nd_cron_settings.id_s", "Kommentar")
fk("idk_ponovne_prijave", "kampanja_pp", "idk_kampanje_dipl.kd_id", "Kommentar")
fk("idk_racuni", "predracun_id", PR, "varchar(11) -> CAST")
fk("idk_obracuni", "predracun_id", PR)
fk("idk_obracuni", "kategorija_provizije", "idk_kategorije_provizija.kp_id", "Hypothese", "LOOKUP")
fk("idk_dak_kandidati", "company_dak_kandidat", C)
fk("idk_dak_kandidati", "dipl_dak_kandidat", D, "Hypothese (evtl. Flag)")

# --- Mitarbeiter (employee) – alle *employee*/zaposlenik/agent/menadzer
for t, c in [("idk_agenti_activity", "employee_id"), ("idk_candidate_language_logs", "cll_employee_id"),
             ("idk_clients", "client_manager"), ("idk_clients", "client_sales_manager"), ("idk_clients_stats", "zaposlenik_id"),
             ("idk_contacts", "contact_ownerid"), ("idk_dak_kandidati", "manager_dak_kandidat"),
             ("idk_documents", "document_employeeid"), ("idk_employees", "employee_nostrifikacija_zadnji_menadzer"),
             ("idk_employees", "employee_nostrifikacija_zadnji_menadzer_app"), ("idk_employees_info", "ei_employeeid"),
             ("idk_employees_reports", "er_employeeid"), ("idk_jobstep_partners", "jp_representative_employee_id"),
             ("idk_kandidati_grupe", "kg_employeeid"), ("idk_kategorije_provizija", "kp_employee_id"),
             ("idk_korisni_dokumenti", "kd_employee_id"), ("idk_korisni_linkovi", "kl_employee_id"),
             ("idk_link_generator", "lg_employeeid"), ("idk_log_kandidat_statusi", "lks_employee_id"),
             ("idk_log_statusi_prijave", "lsp_employee_id"), ("idk_logs", "log_employeeid"), ("idk_messages", "message_sentid"),
             ("idk_messages_users", "mu_employeeid"), ("idk_nalog_profil", "zaposlenik"), ("idk_nalozi", "employee_id"),
             ("idk_nalozi", "nalog_marketing_menadzer"), ("idk_nalozi_log", "n_log_employeeid"),
             ("idk_nd_kandidata", "dodao_zaposlenik_nd_kandidata"), ("idk_nd_kandidata", "zaduzen_zaposlenik_nd_kandidata"),
             ("idk_nd_kandidata_biljeske", "dodao_zaposlenik_biljeska_nd"), ("idk_nd_kandidata_dokumenti", "dodao_zaposlenik_dokument_nd"),
             ("idk_nd_kandidata_status_log", "promjenio_zaposlenik_nd_kandidata"), ("idk_nd_limiti", "lt_emp_id"),
             ("idk_nd_menadzeri_statistike", "zaduzen_zaposlenik_id"), ("idk_nd_menadzeri_statistike", "prethodni_zaposlenik_id"),
             ("idk_nd_termini", "termin_zaposlenik_id"), ("idk_nd_ugovori", "ug_zaposlenik_id"), ("idk_nd_ustanove", "dodao_zaposlenik_ustanove_nd"),
             ("idk_nd_ustanove_biljeske", "dodao_zaposlenik_biljeska_nd"), ("idk_nedostupan_log", "agent"),
             ("idk_nostrifikovane_diplome", "upload_employee_id"), ("idk_notes", "note_employeeid"),
             ("idk_notifications", "notification_employeeid"), ("idk_obracuni", "employee_id"), ("idk_ostatci_obracuna", "oo_employee_id"),
             ("idk_partner_meetings", "meeting_employee"), ("idk_partner_notification_logs", "employee_id"),
             ("idk_partner_tutorials", "employee_id"), ("idk_partner_uplate", "jp_uplate_zaposlenikid"), ("idk_ponovne_prijave", "employee_pp"),
             ("idk_pp_appointment_hours", "pah_employee_id"), ("idk_pp_contract_sent", "cs_entry_employee_id"),
             ("idk_pp_contract_sent", "cs_received_employee_id"), ("idk_pp_contract_sent", "cs_archived_employee_id"),
             ("idk_pp_document_types", "doc_type_entered_user"), ("idk_pp_documents_status_logs", "dsl_user_id"),
             ("idk_pp_reminders", "pr_done_by_crm_employee"), ("idk_predracuni", "pr_zaposlenik"), ("idk_predracuni", "pr_inkaso_agent"),
             ("idk_projects", "project_employeeid"), ("idk_projects", "project_pmanagerid"), ("idk_projects_tasks", "pt_employeeid"),
             ("idk_pushnotifications", "pushnot_employeeid"), ("idk_reject_reasons", "rr_user_id"), ("idk_reminders", "reminder_employee"),
             ("idk_ro_usluge", "odobrio_ro"), ("idk_ro_usluge", "dodao_ro"), ("idk_sales_reminders", "sr_employee_id"),
             ("idk_skladiste_zaposlenici", "sz_employeeid"), ("idk_task_force", "tf_agent_id"), ("idk_tasks", "task_assignedid"),
             ("idk_tasks", "task_employeeid"), ("idk_tf_agent_nalog", "tfan_agent"), ("idk_tf_reservations", "tf_agent_id"),
             ("idk_tf_stats_reservations", "tsr_agent_id"), ("idk_tf_transfered_candidates_logs", "tcl_employee_id"),
             ("idk_ticketi", "ticket_posiljaoc"), ("idk_ticketi", "ticket_primatelj"), ("idk_ticketi_komentari", "ticket_k_posiljaoc"),
             ("idk_timeline", "timeline_employeeid"), ("idk_validnosti_inputa", "vi_employee_id")]:
    fk(t, c, E, "Mitarbeiter laut Name/Kommentar")
fk("idk_pp_cand_required_documents", "crd_user_activated", [E, PU], "Benutzer CRM oder PP (Hypothesen)")
fk("idk_pp_cand_required_documents", "crd_user_archived", [E, PU], "Benutzer CRM oder PP (Hypothesen)")
fk("idk_pp_nalog_required_documents", "nrd_user_activated", [E, PU], "Benutzer CRM oder PP (Hypothesen)")
fk("idk_pp_nalog_required_documents", "nrd_user_archived", [E, PU], "Benutzer CRM oder PP (Hypothesen)")
fk("idk_pp_questions", "pqu_user_id", [E, PU], "Benutzer CRM oder PP (Hypothesen)")
fk("idk_pp_reminders", "pr_user_assigned", [PU, "idk_pp_user_access.pua_id", E], "zugewiesener PP-Benutzer (Hypothesen)")
fk("idk_partner_user_log", "user_id", [JP, PU], "Partner-App-Benutzer (Hypothesen)")
poly("idk_kandidat_pozicija", "kp_created_by", "kp_source", [E, JP], "Kommentar: 1 = Employee, 2 = Partner")
poly("idk_kandidati_contracts", "kc_user_id", "kc_source", [E, PU], "1 = CRM, 2 = PP")
poly("idk_kandidati_reject_reasons", "krr_done_by", "krr_source", [E, PU], "1 = CRM, 2 = PP")
fk("idk_pp_documents_status_logs", "dsl_pp_user_id", PU, "Kommentar")
fk("idk_module_permissions", "mp_employees", E, "Liste von Mitarbeiter-IDs", "LISTE")
fk("idk_pp_reminder_settings", "prs_employee_ids", E, "Liste", "LISTE")
fk("idk_pp_reminder_settings", "prs_controlling_employee_ids", E, "Liste (Kommentar)", "LISTE")
fk("idk_pp_reminder_settings", "prs_pua_ids", "idk_pp_user_access.pua_id", "Liste", "LISTE")
fk("idk_pp_reminder_settings", "prs_controlling_pua_ids", "idk_pp_user_access.pua_id", "Liste (Kommentar)", "LISTE")
fk("idk_employees", "employee_team", "idk_timovi.id_t", "Kommentar", "LOOKUP")
fk("idk_employees", "employee_poslovnica", "idk_poslovnice.branch_id", "Filiale", "LOOKUP")
fk("idk_employees", "employee_warehouse", ["idk_skladiste.skl_id", "idk_poslovnice.branch_id"], "Hypothesen")
fk("idk_tipovi_provizija", "tp_tim", "idk_timovi.id_t", "Kommentar (0 = alle Teams)", "LOOKUP")

# --- Aufträge / Projekte / Firmen / Partner
for t, c in [("idk_bot_obavijesti", "bo_nalog_id"), ("idk_employees_reports", "er_nalogid"), ("idk_jobstep_partners_pregledi", "jpp_nalogid"),
             ("idk_kandidat_akademija", "ka_nalog_id"), ("idk_kandidat_financije", "nalog_id"), ("idk_kandidati_contracts", "kc_nalog_id"),
             ("idk_kandidati_reject_reasons", "krr_nalog_id"), ("idk_link_generator", "lg_nalogid"), ("idk_nalog_financije", "nf_nalog_id"),
             ("idk_nalog_profil", "nalog_id"), ("idk_nalog_smjer", "nalog_id"), ("idk_nalozi_blokovi_prijave", "nbp_nalogid"),
             ("idk_nalozi_log", "n_log_nalogid"), ("idk_nalozi_opis", "no_nalogid"), ("idk_nalozi_rate", "nr_nalog"),
             ("idk_nedostupan_log", "nalog"), ("idk_pp_appointments", "pap_nalog_id"), ("idk_pp_cand_required_documents", "crd_nalog_id"),
             ("idk_pp_contract_sent", "cs_nalog_id"), ("idk_pp_documents", "doc_nalog_id"), ("idk_pp_nalog_profil", "pnp_nalog_id"),
             ("idk_pp_nalog_required_documents", "nrd_nalog_id"), ("idk_pp_partners", "ppa_nalog_id"), ("idk_pp_questions", "pqu_nalog_id"),
             ("idk_pp_reminder_settings", "prs_nalog_id"), ("idk_pp_user_access", "pua_nalog_id"), ("idk_pp_visa_incomplete", "vi_nalog_id"),
             ("idk_pushnotifications", "pushnot_nalogid"), ("idk_task_force", "tf_nalog_id"), ("idk_tf_agent_nalog", "tfan_nalog"),
             ("idk_tf_reservations", "tf_nalog_id"), ("idk_tf_stats_reservations", "tsr_nalog_id"), ("idk_viber_obavijesti", "vo_nalogid"),
             ("users", "nalog_id")]:
    fk(t, c, N, "Auftrag laut Name/Kommentar")
fk("idk_pp_appointment_groups", "papq_nalog_id", N, "varchar(7) -> CAST")
fk("idk_projects", "project_nalogid", N, "varchar(25) -> CAST")
for t, c in [("idk_employees_reports", "er_projectid"), ("idk_kandidat_financije", "projekt_id"), ("idk_link_generator", "lg_project"),
             ("idk_link_projects", "lp_projectid"), ("idk_log_statusi_prijave", "lsp_projekt_id"), ("idk_project_kandidati", "pk_projectid"),
             ("idk_projects_tasks", "pt_projectid"), ("idk_task_force", "tf_project_id"), ("idk_tf_reservations", "tf_projekt_id"),
             ("idk_tf_transfered_candidates_logs", "tcl_destination_project_id")]:
    fk(t, c, P, "Projekt laut Name")
fk("idk_project_candidate_queue", "queue_project_id", P, "varchar(7) -> CAST")
for t, c in [("idk_clients", "client_recommendation_company"), ("idk_companies_info", "comi_companyid"), ("idk_contacts", "contact_companyid"),
             ("idk_nalozi", "kompanija_id"), ("idk_partner_meetings", "meeting_company_id"), ("idk_pp_partners", "ppa_company_id"),
             ("idk_pp_users", "pu_company_id"), ("idk_projects", "project_companyid")]:
    fk(t, c, C, "Firma laut Name/Kommentar")
for t, c in [("idk_companies", "js_partner_id"), ("idk_nalozi", "nalog_js_partner_id"), ("idk_jobstep_partners", "jp_preporuka_id"),
             ("idk_partner_notification", "notification_partner_id"), ("idk_partner_notification_status", "partner_id"),
             ("idk_partner_personal_notifications_preferences", "partner_id"), ("idk_partner_pushnot", "idk_partnerid"),
             ("idk_partner_uplate", "jp_uplate_partnerid"), ("idk_project_candidate_queue", "queue_partner_id")]:
    fk(t, c, JP, "JobStep-Partner (Makler) laut Name/Kommentar")
fk("idk_jobstep_partners_pregledi", "jpp_partnerid", JP, "varchar(255) -> CAST")
for t, c in [("idk_kandidati_contracts", "kc_partner_id"), ("idk_kandidati_reject_reasons", "krr_partner_id"),
             ("idk_pp_documents", "doc_partner_id"), ("idk_pp_reminder_settings", "prs_partner_id"), ("idk_pp_user_access", "pua_partner_id"),
             ("idk_pp_visa_incomplete", "vi_pp_partner_id")]:
    fk(t, c, [PPA, JP], "Partner-Portal-Partner (Arbeitgeber), Hypothese gegen Makler geprüft")
fk("idk_pp_contract_sent", "cs_partner_id", [PPA, JP], "Kommentar: Partner aus idk_kandidati (= kandidat_ppa_partner_id?)")
fk("idk_clients", "client_recommendation", [CL, JP, CT], "Empfehlung (Hypothesen)")
fk("idk_companies", "company_reccomendation", [JP, CL, CT], "Empfehlung (Hypothesen)")
fk("idk_companies", "company_ceo", CT, "Kontakt (Hypothese)")
fk("idk_companies", "company_contact", CT, "Kontakt (Hypothese)")
fk("idk_contacts", "contact_clientid", CL)
fk("idk_contacts_info", "ci_contactid", CT)
fk("idk_clients_stats", "client_id", CL)
fk("idk_sales_reminders", "sr_client_id", CL)
fk("idk_jobstep_partners", "jp_partner_company", "idk_partner_companies.pc_id", "Kommentar", "LOOKUP")
fk("idk_jobstep_partners", "jp_posta", "idk_nd_poste.id_poste", "Hypothese", "LOOKUP")
fk("idk_jobstep_partners", "jp_received_last_lead", [K, D], "Hypothese (letzter Lead)")
fk("idk_partner_notification", "notification_type_id", "idk_partner_personal_notification_types.type_id", "Name", "LOOKUP")
fk("idk_partner_notification_status", "notification_id", "idk_partner_notification.notification_id")
fk("idk_kandidat_financije", "kf_nalog_rata_id", "idk_nalozi_rate.nr_id", "Kommentar")
fk("idk_nalog_smjer", "smjer_id", [SS, "idk_struke.id_struke"], "Hypothesen", "LOOKUP")
fk("idk_profil_kriterij", "profil_id", ["idk_nalog_profil.id", "idk_pp_informacije_profil.pip_id"], "Hypothesen")

# --- Lookups / sonstige Verweise
fk("idk_appointment_invite_links", "interview_id", PCA, "Kommentar")
fk("idk_candidate_language_logs", "cll_cvl_id", ["idk_candidate_verified_languages.cvl_id", "idk_kandidat_jezici.kj_id"], "Kommentar")
fk("idk_candidate_verified_languages", "cvl_id", "idk_kandidat_jezici.kj_id", "PK = kj_id (1:1-Erweiterung)")
fk("idk_chat_question", "parentQuestion", "idk_chat_question.id", "Kommentar")
fk("idk_chat_question", "type", "idk_chat_type.id", "Kommentar (text) -> CAST", "LOOKUP")
fk("idk_kandidat_edukacija", "ke_smjer_id", SS, "Name", "LOOKUP")
fk("idk_kandidat_edukacija", "ke_skola_id", SK, "Name", "LOOKUP")
fk("idk_kandidati_reject_reasons", "krr_reason_id", "idk_reject_reasons.rr_id", "Name", "LOOKUP")
fk("idk_kandidati_reject_reasons", "krr_apointment_id", [PCA, PAP, PPAQ], "Hypothesen")
fk("idk_kandidati_reject_reasons", "krr_last_status", SP, "Status vor Absage", "LOOKUP")
fk("idk_kategorije_provizija", "kp_tip_id", "idk_tipovi_provizija.tp_id", "Name", "LOOKUP")
fk("idk_link_generator_rel", "lr_lgid", LG)
fk("idk_link_generator_rel", "lr_groupid", "idk_kandidati_grupe.kg_id", "Name", "LOOKUP")
fk("idk_link_projects", "lp_linkid", LG)
fk("idk_log_kandidat_statusi", "lks_status_obrade", "idk_kandidat_status.status_id", "Name", "LOOKUP")
fk("idk_log_kandidat_statusi", "lks_link_id", LG, "Kommentar")
fk("idk_log_statusi_prijave", "lsp_status_prijave_id", SP, "Name", "LOOKUP")
fk("idk_messages_users", "mu_messageid", "idk_messages.message_id")
fk("idk_pp_appointment_hours", "pap_id", PAP, "Kommentar")
fk("idk_pp_appointments", "pap_group_id", PPAQ, "varchar(7) -> CAST")
fk("idk_pp_appointments_questions", "papq_question_id", "idk_pp_questions.pqu_id")
fk("idk_pp_appointments_questions", "papq_appointment_id", PAP)
fk("idk_pp_cand_appts", "pca_appointment_id", PAP)
fk("idk_pp_cand_appts", "pca_pah_id", "idk_pp_appointment_hours.pah_id")
fk("idk_pp_cand_required_documents", "crd_type_id", "idk_pp_document_types.doc_type_id", "Kommentar", "LOOKUP")
fk("idk_pp_cand_required_documents", "crd_vi_id", "idk_pp_visa_incomplete.vi_id", "Kommentar")
fk("idk_pp_city", "pc_region", "idk_pp_regions.pr_id", "Kommentar", "LOOKUP")
fk("idk_pp_contract_sent", "cs_entry_pua_id", "idk_pp_user_access.pua_id", "Kommentar")
fk("idk_pp_documents", "doc_nrd_id", "idk_pp_nalog_required_documents.nrd_id", "Kommentar")
fk("idk_pp_documents", "doc_crd_id", "idk_pp_cand_required_documents.crd_id", "Kommentar")
fk("idk_pp_documents", "doc_status", "idk_pp_documents_statuses.ds_id", "Kommentar", "LOOKUP")
fk("idk_pp_documents_status_logs", "dsl_doc_id", "idk_pp_documents.doc_id", "PK-Teil")
fk("idk_pp_documents_status_logs", "dsl_doc_status", "idk_pp_documents_statuses.ds_id", "PK-Teil", "LOOKUP")
fk("idk_pp_nalog_profil", "pnp_info_id", "idk_pp_informacije_profil.pip_id", "Kommentar", "LOOKUP")
fk("idk_pp_nalog_required_documents", "nrd_type_id", "idk_pp_document_types.doc_type_id", "Kommentar", "LOOKUP")
fk("idk_pp_question_options", "pqo_question_id", "idk_pp_questions.pqu_id", "Kommentar")
fk("idk_pp_questions", "pqu_category_id", "idk_pp_question_categories.pqc_id", "Kommentar", "LOOKUP")
fk("idk_pp_ratings", "pra_appointment_question_id", "idk_pp_appointments_questions.papq_id")
fk("idk_pp_ratings", "pra_options_value", ["idk_pp_question_options.pqo_id", "idk_pp_question_options.pqo_value"], "Hypothesen")
fk("idk_pp_reminder_documents", "prd_prs_id", "idk_pp_reminder_settings.prs_id")
fk("idk_pp_reminder_documents", "prd_nrd_id", "idk_pp_nalog_required_documents.nrd_id")
fk("idk_pp_reminder_documents", "prd_crd_id", "idk_pp_cand_required_documents.crd_id")
fk("idk_pp_reminder_settings", "prs_reminder_type_id", "idk_pp_reminder_types.prt_id", "Name", "LOOKUP")
fk("idk_pp_reminders", "pr_reminder_setting_id", "idk_pp_reminder_settings.prs_id")
fk("idk_pp_reminders", "pr_reminder_document_id", "idk_pp_reminder_documents.prd_id")
fk("idk_pp_user_access", "pua_user_id", PU, "Kommentar")
fk("idk_pp_user_access", "pua_permission_id", "idk_pp_permissions.ppe_id", "Kommentar", "LOOKUP")
fk("idk_skladiste", "skl_branch", "idk_poslovnice.branch_id", "Name", "LOOKUP")
fk("idk_skladiste", "skl_kategorija", "idk_skladiste_kategorije.isk_id", "Name", "LOOKUP")
fk("idk_skladiste_product", "isp_skl_id", "idk_skladiste.skl_id")
fk("idk_skladiste_zaposlenici", "isz_sklid", "idk_skladiste.skl_id")
fk("idk_skladiste_zaposlenici", "sz_branch", "idk_poslovnice.branch_id", "Name", "LOOKUP")
fk("idk_skladiste_zaposlenici", "isz_product_id", "idk_skladiste_product.isp_id")
fk("idk_skole_smjerovi", "ss_skola_id", SK)
fk("idk_skole_smjerovi", "ss_struka_id", "idk_struke.id_struke", "Name", "LOOKUP")
fk("idk_task_force", "tf_casting_id", PPAQ, "Kommentar: ID iz grupe termina")
fk("idk_task_force", "tf_status_id", "idk_tf_statusi.tfs_id", "Name", "LOOKUP")
fk("idk_task_force", "tf_vrsta_id", TFV, "Kommentar", "LOOKUP")
fk("idk_tf_agent_nalog", "tfan_vrsta_id", TFV, "Kommentar", "LOOKUP")
fk("idk_tf_reservations", "tf_vrsta_id", TFV, "Kommentar", "LOOKUP")
fk("idk_tf_stats_reservations", "tsr_interview_id", PPAQ, "Kommentar: ID grupe castinga")
fk("idk_tf_stats_reservations", "tsr_link_id", LG, "Kommentar")
fk("idk_tf_statusi", "tfs_status_prijave", SP, "Kommentar", "LOOKUP")
fk("idk_tf_statusi", "tfs_vrsta_id", TFV, "Kommentar", "LOOKUP")
fk("idk_ticketi_komentari", "ticket_k_id_tiketa", "idk_ticketi.ticket_id")
fk("idk_tutorijali", "tutorijal_kategorija_id", "idk_kategorije.kategorija_id", "deklarierter FK", "LOOKUP")
fk("idk_validnosti_inputa", "vi_razlog_id", "idk_razlozi_odbijanja.ro_id", "Hypothese", "LOOKUP")
poly("idk_validnosti_inputa", "vi_podatak_id", "vi_vrsta_podatka", [K, "idk_kandidat_jezici.kj_id", "idk_kandidat_edukacija.ke_id",
     "idk_kandidat_radno_iskustvo.kri_id"], "Datensatz je Datenart")

# --- polymorph *_group + *_dataid
POLY_T = [K, C, CT, N, P, E, CL, D, "idk_tasks.task_id", "users.id"]
poly("idk_notes", "note_dataid", "note_group", POLY_T, "Gruppen undokumentiert")
poly("idk_documents", "document_dataid", "document_group", POLY_T, "Gruppen undokumentiert")
poly("idk_timeline", "timeline_dataid", "timeline_group", POLY_T, "Gruppen undokumentiert")
poly("idk_tasks", "task_dataid", "task_group", POLY_T, "Gruppen undokumentiert")
poly("mcp_aenderung", "a_datensatz_id", "a_tabelle", [], "Tabelle leer (0 Zeilen)")
poly("rb_baselines", "entity_id", "entity_type", [], "Fremdprojekt rb_*, 1 Zeile")
poly("rb_events", "entity_id", "entity_type", [], "Fremdprojekt rb_*, 2 Zeilen")
poly("rb_entity_state", "entity_id", "entity_type", [], "Fremdprojekt rb_*, PK-Teil")
poly("rb_field_state", "entity_id", "entity_type", [], "Fremdprojekt rb_*, PK-Teil")
fk("rb_approvals", "consumed_by_request_id", "rb_requests.request_id", "Name (Fremdprojekt)")
fk("rb_events", "request_id", "rb_requests.request_id", "Name (Fremdprojekt)")
fk("rb_events", "source_event_id", "rb_events.event_id", "Name (Fremdprojekt)")

# --- explizit ausgeschlossen (Name sieht nach Code/ID aus, ist es aber nicht)
X = {
    ("idk_companies", "company_idnum"): ("PII", "Firmen-Registernummer (Identifikator der Firma, kein Verweis)"),
    ("idk_companies", "company_taxnum"): ("PII", "Steuernummer"),
    ("idk_companies", "company_zipcode"): ("ZAHL", "PLZ"), ("idk_contacts", "contact_zipcode"): ("ZAHL", "PLZ"),
    ("idk_kandidati", "kandidat_pbroj"): ("ZAHL", "PLZ"), ("idk_kandidati", "kandidat_destinacija_postanski_broj"): ("ZAHL", "PLZ"),
    ("idk_nd_kandidata", "postanski_broj_nd_kandidata"): ("ZAHL", "PLZ"), ("idk_nd_kandidata", "postanski_broj_bor_nd_kandidata"): ("ZAHL", "PLZ"),
    ("idk_nd_kandidata", "poslodavac_postanski_broj_nd_kandidata"): ("ZAHL", "PLZ"), ("idk_nd_ustanove", "postanski_broj_ustanove_nd"): ("ZAHL", "PLZ"),
    ("idk_jobstep_partners", "jp_postanskibroj"): ("ZAHL", "PLZ"),
    ("idk_jobstep_partners", "jp_makler_id"): ("TEXT", "externe Makler-Nummer (varchar 255), kein interner Verweis"),
    ("idk_jobstep_partners", "jp_makler_broj_direkcije"): ("TEXT", "externe Direktionsnummer"),
    ("idk_nd_ugovori", "ug_broj"): ("TEXT", "Vertragsnummer (Belegnummer)"), ("idk_predracuni", "pr_broj_predracuna"): ("TEXT", "Belegnummer"),
    ("idk_racuni", "racun_broj"): ("TEXT", "Belegnummer"), ("idk_racuni", "racun_bf"): ("TEXT", "Belegnummer"),
    ("idk_nalozi", "nalog_ugovor"): ("TEXT", "Vertragsnummer/Datei"), ("idk_pp_contract_sent", "cs_tracking_code"): ("TEXT", "Sendungsnummer"),
    ("idk_sms_messages", "sms_response_nthsmsid"): ("TECH", "ID beim SMS-Anbieter (extern)"),
    ("idk_kandidati", "kandidat_check"): ("TECH", "Prüfsumme/Hash"), ("idk_nd_kandidati_ciscenje", "hash_id_dipl"): ("TECH", "Hash"),
    ("users", "sim_id"): ("TECH", "Geräte-ID"), ("rb_requests", "idempotency_key"): ("TECH", "Idempotenzschlüssel"),
    ("mcp_aenderung", "a_freigabe_code"): ("TECH", "Hash"), ("rb_outbox", "lease_token"): ("TECH", "Token"),
    ("idk_appointment_invite_links", "send_key"): ("SENSIBEL", "Schlüssel"),
    ("idk_kandidat_status", "status_id"): ("ZIEL", "Code-Schlüssel der Lookup-Tabelle (Ziel, kein Verweis)"),
}

CODE_X = {
    ("beruf_mapping", "quelle"): "Herkunft der Zuordnung", ("idk_kandidat_jezici", "kj_naziv"): "Sprachname (Freitext-Code)",
    ("idk_kandidat_jezici", "kj_slusanje"): "CEFR-Niveau", ("idk_kandidat_jezici", "kj_citanje"): "CEFR-Niveau",
    ("idk_kandidat_jezici", "kj_govorna_interakcija"): "CEFR-Niveau", ("idk_kandidat_jezici", "kj_govorna_produkcija"): "CEFR-Niveau",
    ("idk_kandidat_jezici", "kj_pisanje"): "CEFR-Niveau", ("idk_nalozi_blokovi_prijave", "nbp_ostali_jezici"): "Konfiguration",
    ("idk_tasks", "task_repeatnotifi"): "Flag", ("mcp_fehler", "f_exportiert"): "Flag",
    ("idk_companies_info", "comi_primary"): "Flag primär", ("idk_contacts_info", "ci_primary"): "Flag primär",
    ("idk_employees_info", "ei_primary"): "Flag primär", ("idk_kandidat_kontakt_info", "kki_primary"): "Flag primär",
    ("idk_kandidati", "kandidat_drzavljanstvo_vrsta"): "EU/NON-EU (Freitext-Code)", ("idk_kandidati", "kandidat_drzava"): "Wohnland (Freitext)",
    ("idk_kandidati", "kandidat_drzavljanstvo"): "Staatsangehörigkeit (Freitext)", ("idk_kandidati", "boravak_eu"): "Aufenthalt EU (Freitext)",
    ("idk_kandidati", "kandidat_bracnostanje"): "Familienstand alt (Freitext)", ("idk_kandidat_edukacija", "ke_drzava"): "Land Ausbildung",
    ("idk_kandidat_radno_iskustvo", "kri_drzava"): "Land Erfahrung", ("idk_kandidat_de", "kde_vozacka"): "Führerschein DE-Profil",
    ("idk_employees", "employee_status"): "Mitarbeiterstatus (Text-Code)", ("idk_companies", "company_size"): "Größenklasse",
    ("idk_companies", "company_contact_type"): "Kontaktart", ("idk_jobstep_partners", "jp_drzava"): "Land Partner",
    ("idk_jobstep_partners", "jp_lang"): "Sprache", ("idk_partner_meetings", "meeting_type"): "Kommentar: Typ",
    ("idk_kandidat_kontakt_info", "kki_naziv"): "Kontaktart (Telefon/E-Mail …)", ("idk_kandidat_de", "kde_spol"): "Geschlecht DE-Profil",
    ("idk_kandidat_de", "kde_drzavljanstvo"): "Staatsangehörigkeit DE-Profil", ("idk_kandidat_vjestine", "kv_naziv"): "Fähigkeit (Freitext-Code)",
    ("idk_nalozi_blokovi_prijave", "nbp_vozacka_kategorija"): "Konfiguration", ("idk_clients", "client_country"): "Land",
    ("idk_companies", "company_country"): "Land", ("idk_bot_obavijesti", "bo_odgovor"): "Kommentar: Antwort-Code",
    ("idk_jobstep_partners", "jp_confirmedaccount"): "Kommentar: 0/1/2", ("idk_kandidati", "kandidat_spol"): "Geschlecht",
    ("idk_kandidati", "kandidat_procjenatermina"): "Code", ("idk_kandidati", "kandidat_iskustvo_u_struci_trajanje"): "Skala 0-6 (Kommentar)",
    ("idk_kandidati", "kandidat_pogresan_broj"): "Flag", ("idk_nalozi", "nalog_placena_prva_rata"): "Kommentar 0/1/2",
    ("idk_nalozi", "nalog_prioritet"): "Prioritätsklasse TF", ("idk_nalog_profil", "prioritet"): "Prioritätsklasse",
    ("idk_pp_questions", "pqu_has_rating"): "Flag", ("idk_predracuni", "pr_naplata_preko"): "Kommentar 0/1",
    ("idk_nd_naplata_preko", "fk_naplata_preko"): "Code (unklar)", ("idk_nalozi_blokovi_prijave", "nbp_iskustvo_u_struci_trajanje"): "Skala",
    ("idk_tasks", "task_emailnotifi"): "Flag", ("mcp_aenderung", "a_tabelle"): "Diskriminator für a_datensatz_id",
    ("rb_baselines", "entity_type"): "Diskriminator", ("rb_events", "entity_type"): "Diskriminator",
    ("idk_pp_documents_statuses", "ds_name"): "Statusname (Lookup-Text)",
}
ZAHL_X = {("idk_companies", "company_total_workers_required"), ("idk_nalozi", "nalog_potrebno_kandidata"),
          ("idk_nalozi", "nalog_dospijece"), ("idk_nalozi_rate", "nr_mjeseci_nakon"), ("idk_pp_partners", "ppa_number_of_candidates"),
          ("idk_pp_question_options", "pqo_value"), ("idk_projects", "project_plannedhours"), ("idk_chat_question", "question_order"),
          ("idk_nd_kandidata_status_log", "broj_dana_statusa_nd_kandidata"), ("idk_nd_cron_settings", "status_days_s"),
          ("idk_nalozi", "nalog_provizija_akademija"), ("idk_nd_ustanove", "period_nostrifikacije_ustanove_nd")}
X[("idk_nd_ugovori", "ug_timestamp")] = ("DATUM", "Zeitstempel als Text")
X[("idk_ticketi_komentari", "ticket_k_dokument")] = ("TEXT", "Dateiname")
X[("users", "name")] = ("PII", "Name")
X[("users", "phone")] = ("PII", "Telefon")
X[("idk_pp_users", "pu_fname")] = ("PII", "Vorname")
X[("idk_pp_users", "pu_lname")] = ("PII", "Nachname")
X[("idk_sms_messages", "sms_number")] = ("PII", "Telefonnummer")

SENS = set()
with open(os.path.join(HERE, "..", "..", "plugin", "skills", "jsi-data-analyst", "references", "schema", "osjetljive_kolone.md"),
          encoding="utf-8") as f:
    for line in f:
        m = re.match(r"\|\s*`([^`]+)`\s*\|\s*`([^`]+)`\s*\|", line)
        if m:
            SENS.add((m.group(1), m.group(2)))

PII_RE = re.compile(r"(^|_)(ime|prezime|imeprezime|mobitel|mobilni|telefon|tel|email|mail|adresa|ulica|jmbg|pasos|djevojack|"
                    r"korisnickoime|username|name|naziv|title|opis|desc|txt|text|content|comment|komentar|poruka|message|"
                    r"file|slika|logo|icon|url|link|path|putanja|key|token|hash|ip|lozinka|password|grad|mjesto|city|lokacija|"
                    r"question|odgovor|biljeska|napomena|note|subject|naslov|body|request|response|color|boja|web|banka|swift|iban)",
                    re.I)
COUNT_RE = re.compile(r"(broj|count|cnt|brojac|order|sort|rating|ocjena|trajanje|duration|days|dana|procenat|iznos|kolicina|quantity|"
                      r"zip|postanski|revision|attempts|tries|prioritet|limit|dnevni|sedmicni|mjesecni|_rata$|^rata$|br_r|ukupno|"
                      r"starost|godina|cijena|plata|troskovi|pregled|_od$|_do$|freq|after|minimum|maksimum|counter|level)", re.I)
CODE_RE = re.compile(r"(status|stat$|tip|type|vrsta|group|grupa|kategor|category|code|kod|source|izvor|origin|porijeklo|povijest|"
                     r"nivo|aktiv|active|aktuelno|prikaz|flag|is_|has_|ima_|^ne_|valuta|jezik|language|spol|gender|odjel|"
                     r"daypart|tipunosa|poslovnica|drzava|signed|visibility|recommendation|preporuka|decision|operation|art$|"
                     r"zustand|aktion|setzt|exported|default|mute|archive|arhiva|available|inventar|faktorizacija|cron|"
                     r"potvrden|placen|uplac|storn|izdan|placa|nacin|pristup|partneri|slanje|kriterij|koristi|trazi|dostavljen|"
                     r"paralelno|pogresan|nedostupan|paket|glossa|termin|viza|poslan|povezan|mailsent|pogledao|bio_na|procjena|"
                     r"cv_|profile_|reset|dvag|representative|confirmed|position|permission|user_type|racun$|posta$|"
                     r"skilled|west|work_|done_by|complaint|controling|vozacka|njemacki|engleski|francuski|italijanski|"
                     r"jezika|obr$|obr_|korak|slika$|diploma|pripravnicki|strucni|cert|struka$|iskustvo|smjerovi|"
                     r"zakaznog|vici|inbound|obrade|osiguranje|nas_klijent|rata1|rata2|regija|obaveznost|povezanost|template|"
                     r"vrijeme_grupa|ponovno|informacija|pracenja|treba_|hitnost|primatelj_odjel|box|eukandidati|zadnja_|"
                     r"executed|enabled|ustanova$|_pp$|client_pp|contract$|fc_or_sales|origin|fk_naplata|notifikacije|"
                     r"dipl_obavijest|notf_|full_recognition|interview|appointment$|bracn|spol|aktivno|tfs_|important|last_active|"
                     r"prijava|jezik$|fc_status|sales_status|financije$|nostrifikacij|akademija$|partner_active|razlog_storniranja)", re.I)


def classify(r):
    t, c, typ = r["t"], r["col"], r["typ"]
    base = re.match(r"[a-z]+", typ).group()
    ln = int(m.group(1)) if (m := re.search(r"\((\d+)", typ)) else 0
    if (t, c) in SENS:
        return "SENSIBEL", "", "osjetljive_kolone.md – nie selektieren"
    if (t, c) in M:
        k, tg, why = M[(t, c)]
        return k, ",".join(tg), why
    if (t, c) in X:
        k, why = X[(t, c)]
        return k, "", why
    if r["ckey"] == "PRI":
        return "PK", "", "Primärschlüssel (Ziel, kein Verweis)"
    if base in ("datetime", "date", "time", "timestamp", "year"):
        return "DATUM", "", "Datum/Zeit"
    if base in ("decimal", "float", "double"):
        return "ZAHL", "", "Betrag/Messwert"
    if base in ("json", "blob", "longblob") or base.endswith("text"):
        return "TEXT", "", "Freitext/JSON"
    if (t, c) in CODE_X:
        return "CODE", "", CODE_X[(t, c)]
    if (t, c) in ZAHL_X:
        return "ZAHL", "", "Zahl/Menge laut Name"
    if base in ("varchar", "char") and PII_RE.search(c) and not CODE_RE.search(c):
        return ("PII" if re.search(r"(ime|prezime|mobi|tel|mail|adresa|ulica|jmbg|pasos|grad|mjesto)", c, re.I) else "TEXT"), "", \
            "Personen-/Freitextfeld laut Name"
    if base in ("varchar", "char") and ln > 60:
        return "TEXT", "", f"Freitext ({typ})"
    if COUNT_RE.search(c) and not re.search(r"(status|tip|type|vrsta)", c, re.I):
        return "ZAHL", "", "Zähler/Menge/Reihenfolge/Bewertung laut Name"
    if CODE_RE.search(c) or re.search(r"\d\s*[-=:]\s*\D", r["cmt"] or ""):
        return "CODE", "", "Status-/Typ-/Gruppen-/Flag-Code laut Name/Kommentar"
    return "UNKLAR", "", "keine Regel"


def main():
    rows = json.load(open(os.path.join(HERE, "columns.json"), encoding="utf-8"))["rows"]
    out = ["tabelle\tspalte\ttyp\tklasse\tziele\tgrund"]
    stats = {}
    for r in rows:
        k, tg, why = classify(r)
        stats[k] = stats.get(k, 0) + 1
        out.append("\t".join([r["t"], r["col"], r["typ"], k, tg, why]))
    missing = [k for k in M if not any(r["t"] == k[0] and r["col"] == k[1] for r in rows)]
    if missing:
        raise SystemExit(f"Mapping verweist auf unbekannte Spalten: {missing}")
    with open(os.path.join(HERE, "verweis_kandidaten.tsv"), "w", encoding="utf-8") as f:
        f.write("\n".join(out) + "\n")
    print(stats)


if __name__ == "__main__":
    main()
