import json, re, sys, os, collections
S = sys.argv[1]; OUT = sys.argv[2]
cols = json.load(open(f"{S}/columns.json"))["rows"]
meta = {t["name"]: t for t in json.load(open(f"{S}/gen/tables_meta.json"))["tables"]}
counts = dict(l.rstrip("\n").split("\t") for l in open(f"{S}/counts.tsv"))
dates = {}
for l in open(f"{S}/dates.tsv"):
    p = l.rstrip("\n").split("\t")
    dates[p[0]] = p[1:]
DOMAINS = [
 ("01_kandidati", "Kandidati (vermittlung) – profil, CV, jezici, obrazovanje", r"^(idk_kandidati$|idk_kandidat_|idk_kandidati_|idk_candidate_|users$|beruf_mapping$|idk_validnosti_inputa$|idk_documents$|idk_notes$|idk_timeline$|idk_reject_reasons$|idk_razlozi_odbijanja$)"),
 ("02_pipeline_logovi", "Pipeline historija i logovi", r"^(idk_log_|idk_logs$|idk_duration_per_status$)"),
 ("03_task_force_casting", "Task force, casting, intervjui", r"^(idk_task_force$|idk_tf_|idk_agenti_activity$|idk_nedostupan_log$|idk_pp_appointment|idk_pp_cand_appts$|idk_appointment_invite_links$|idk_pp_question|idk_pp_questions$|idk_pp_ratings$)"),
 ("04_komunikacija", "Komunikacija s kandidatima (SMS, Viber, Messenger, bot, notifikacije)", r"^(idk_sms_messages$|idk_viber_obavijesti$|idk_messenger_obavijesti$|idk_bot_obavijesti$|idk_notification$|idk_provider_for_sending_messages$|idk_email_text$|idk_chat_|idk_glossa_log$|idk_triggerurl$)"),
 ("05_nalozi_projekti_firme", "Nalozi, projekti, firme, klijenti (sales)", r"^(idk_nalozi|idk_nalog_|idk_projects|idk_project_|idk_companies|idk_contacts|idk_clients|idk_sales_reminders$|idk_profil_kriterij$|idk_struke$|idk_skole|idk_link_|idk_partner_meetings$)"),
 ("06_partner_portal_poslodavci", "Partner portal (PP) – poslodavci, dokumenti, vize, reminderi", r"^idk_pp_"),
 ("07_jobstep_partneri_makleri", "JobStep partner app – makleri/preporučitelji", r"^(idk_jobstep_partners|idk_partner_)"),
 ("08_dipl_nostrifikacija", "DIPL – nostrifikacija diploma (zaseban ID prostor id_broj_nd_kandidata)", r"^(idk_nd_|idk_nostrifikovane_diplome$|idk_kampanje_dipl$|idk_ponovne_prijave$|idk_reminders$|idk_ro_usluge$|idk_dak_kandidati$)"),
 ("09_finansije_provizije", "Finansije, fakture, provizije", r"^(idk_kandidat_financije$|idk_predracuni$|idk_racuni$|idk_obracuni$|idk_ostatci_obracuna$|idk_kategorije_provizija$|idk_tipovi_provizija$)"),
 ("10_interno_admin", "Interno: zaposlenici, timovi, tiketi, skladište, postavke", r"^(idk_employees|idk_timovi$|idk_poslovnice$|idk_ticketi|idk_tasks$|idk_messages|idk_notifications$|idk_pushnotifications$|idk_skladiste|idk_korisni_|idk_tutorijali$|idk_kategorije$|idk_modules$|idk_module_permissions$|idk_settings$|idk_ipwhitelist$|idk_api_clients$|idk_otherdata$|idk_analitika$)"),
 ("11_tehnicki_mcp_audit", "Tehnički: MCP/audit/event sourcing", r"^(mcp_|rb_)"),
]
NOTSENS = re.compile(r"(last_password|reset_password$|reset_token_doe|password_reset_datetime|password_reset_tries|foreign_key|idempotency|passporttime|lease_token)", re.I)
SENS = re.compile(r"(password|pass$|vicipass|viciuser|token|_key$|^key$|pu_key|employee_key|jmbg|iban|swift|rfid|secret|reset_code|socialid|social_token|fcmtoken|broj_pasosa|passport|licne|brojlk|pin_dak|hashedtel)", re.I)
PII = re.compile(r"(ime|prezime|firstname|lastname|lname|fname|imeprezime|email|mail|mobitel|telefon|phone|tel_|adresa|address|ulica|datumrodjenja|datum_rodjenja|dob$|_dob$|name_dak|lastname_dak|djevojack|mjestorodjenja|ip_adresa|ipwl_ip|kki_podatak|ci_data|sms_number|brtelefona)", re.I)
def domain(t):
    for key, title, rx in DOMAINS:
        if re.search(rx, t): return key
    return "99_ostalo"
by_t = collections.defaultdict(list)
for r in cols: by_t[r["t"]].append(r)
groups = collections.defaultdict(list)
for t in sorted(by_t): groups[domain(t)].append(t)
assert "99_ostalo" not in groups, groups.get("99_ostalo")
os.makedirs(OUT, exist_ok=True)
titles = {k: v for k, v, _ in DOMAINS}
def period(t):
    d = dates.get(t)
    if not d: return "–"
    c, f, mn, mx = d
    return f"{mn} → {mx} (`{c}`)" if mn else f"– (`{c}` prazno)"
# index
idx = ["# JSI CRM – katalog svih tabela (schema `jsicrm`)", "",
       "Generisano 2026-10-29 iz `information_schema.COLUMNS`, `COUNT(*)` svake tabele i MIN/MAX glavne datumske kolone (BlazeSQL, MySQL „Mysql JSI“).",
       f"**{len(by_t)} tabela, {len(cols)} kolona.** Prazne tabele: " + ", ".join(f"`{t}`" for t in sorted(by_t) if counts.get(t) == "0") + ".", "",
       "Oznake u fajlovima po domenima: **[TAJNO]** = kredencijali/tokeni/bankovni podaci – nikad ne selektovati; **[PII]** = lični podaci – samo kad je izričito potrebno.", "",
       "| Domen | Fajl | Tabela |", "|---|---|---|"]
for key in sorted(groups):
    idx.append(f"| {titles[key]} | `{key}.md` | {len(groups[key])} |")
idx += ["", "## Sve tabele", "", "| Tabela | Domen | Redova | Period (kolona) | PK | Kolona | Opis |", "|---|---|---:|---|---|---:|---|"]
for t in sorted(by_t):
    pk = ",".join(r["col"] for r in by_t[t] if r["ckey"] == "PRI") or "–"
    desc = (meta.get(t, {}).get("description") or "").replace("|", "/")
    idx.append(f"| `{t}` | {domain(t)[3:]} | {int(counts[t]):,} | {period(t)} | {pk} | {len(by_t[t])} | {desc} |")
open(f"{OUT}/README.md", "w").write("\n".join(idx) + "\n")
for key, ts in groups.items():
    out = [f"# {titles[key]}", "", f"Tabele: {len(ts)}. Redovi i periodi stanje 2026-10-29.", ""]
    for t in ts:
        pk = ",".join(r["col"] for r in by_t[t] if r["ckey"] == "PRI") or "–"
        out += [f"## `{t}`", "", f"- **Opis**: {meta.get(t, {}).get('description', '')}",
                f"- **Redova**: {int(counts[t]):,} · **Period**: {period(t)} · **PK**: `{pk}`", "",
                "| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |", "|---|---|---|---|---|"]
        for r in sorted(by_t[t], key=lambda x: x["pos"]):
            flag = "**[TAJNO]**" if (SENS.search(r["col"]) and not NOTSENS.search(r["col"])) else ("[PII]" if PII.search(r["col"]) else "")
            cmt = (r["cmt"] or "").replace("|", "/").strip()
            out.append(f"| `{r['col']}` | {r['typ']} | {r['ckey'] or ''} | {cmt} | {flag} |")
        out.append("")
    open(f"{OUT}/{key}.md", "w").write("\n".join(out) + "\n")
sens = sorted({(r["t"], r["col"]) for r in cols if (SENS.search(r["col"]) and not NOTSENS.search(r["col"]))})
open(f"{OUT}/osjetljive_kolone.md", "w").write("# Osjetljive kolone ([TAJNO])\n\nNikad ne selektovati, ne exportovati, ne prikazivati. Preporuka: isključiti ih u BlazeSQL (column-level permissions).\n\n| Tabela | Kolona |\n|---|---|\n" + "\n".join(f"| `{t}` | `{c}` |" for t, c in sens) + "\n")
print(len(by_t), len(cols), {k: len(v) for k, v in sorted(groups.items())}, "sensitive:", len(sens))
