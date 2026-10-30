# DIPL – nostrifikacija diploma (zaseban ID prostor id_broj_nd_kandidata)

Tabele: 26. Redovi i periodi stanje 2026-10-29.

## `idk_dak_kandidati`

- **Opis**: Stores candidate records, including personal contact details, contract and passport information, application statuses, processing timestamps, and installment payment tracking.
- **Redova**: 670 · **Period**: – (`contacttime_dak_kandidat` prazno) · **PK**: `id_dak_kandidat`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `id_dak_kandidat` | int | PRI |  |  |
| `origin_dak_kandidat` | int |  |  |  |
| `tel_dak_kandidat` | varchar(250) |  |  | [PII] |
| `hashedtel_idk_dak_kandidat` | text |  |  | **[TAJNO]** |
| `telconfirm_dak_kandidat` | varchar(250) |  |  |  |
| `pin_dak_kandidat` | text |  |  | **[TAJNO]** |
| `name_dak_kandidat` | varchar(250) |  |  | [PII] |
| `lastname_dak_kandidat` | varchar(250) |  |  | [PII] |
| `email_dak_kandidat` | varchar(250) |  |  | [PII] |
| `contacttime_dak_kandidat` | datetime |  |  | [PII] |
| `daypart_dak_kandidat` | int |  | 0-jutro,1-podne,2-prednoc |  |
| `comment_dak_kandidat` | text |  |  |  |
| `passport_dak_kandidat` | varchar(250) |  |  | **[TAJNO]** |
| `passporttime_dak_kandidat` | datetime |  |  | [PII] |
| `contract_dak_kandidat` | varchar(250) |  |  |  |
| `contracttime_dak_kandidat` | datetime |  |  | [PII] |
| `status_dak_kandidat` | int |  | 0-novi, 1-obrada, 2-poslan, 3-aktivan, 4-zavrsen, 5-storniran poslije aktivacije, 6-storniran,7-arhiviran |  |
| `tipunosa_dak_kandidat` | int |  | 0-app 1-poslovnica |  |
| `datumunosa_dak_kandidat` | datetime |  | Datum kad je unijet, bilo app bilo poslovnica |  |
| `datumobrade_dak_kandidat` | datetime |  |  |  |
| `datumslanja_dak_kandidat` | datetime |  |  |  |
| `pocetakrada_dak_kandidat` | date |  |  |  |
| `datumaktivacije_dak_kandidat` | datetime |  |  |  |
| `datumzavrsetka_dak_kandidat` | datetime |  |  |  |
| `datumstornoaktivacije_dak_kandidat` | datetime |  |  |  |
| `datumstornacije_dak_kandidat` | datetime |  |  |  |
| `company_dak_kandidat` | int |  |  |  |
| `nas_klijent_dak_kandidat` | int |  |  |  |
| `dipl_dak_kandidat` | int |  |  |  |
| `osiguranje_dak_kandidat` | int |  |  |  |
| `poslovnica_dak_kandidat` | int |  | 0-ne zna se, 1-bihac, 2-srajevo,3-bg, 4-svzsar |  |
| `rata1_dak_kandidat` | int |  |  |  |
| `rata1_datum_dak_kandidat` | datetime |  |  |  |
| `rata2_dak_kandidat` | int |  |  |  |
| `rata2_datum_dak_kandidat` | datetime |  |  |  |
| `manager_dak_kandidat` | int |  |  |  |

## `idk_kampanje_dipl`

- **Opis**: Stores marketing and promotional campaign details for diploma programs, including campaign metadata, targeted regions, associated costs, and engagement statistics.
- **Redova**: 228 · **Period**: 2020-10-27 → 2024-02-15 (`kd_datum_kreiranja`) · **PK**: `kd_id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `kd_id` | int | PRI |  |  |
| `kd_naziv` | varchar(255) |  |  |  |
| `kd_skraceni_naziv` | varchar(255) |  |  |  |
| `kd_poruka_kampanje` | text |  |  |  |
| `kd_jezik_forme` | varchar(10) |  |  |  |
| `kd_drzava` | varchar(10) | MUL |  |  |
| `kd_broj_pregleda` | int |  |  |  |
| `kd_broj_prijavljenih` | int |  |  |  |
| `kd_datum_kreiranja` | datetime |  |  |  |
| `kd_troskovi` | double |  |  |  |
| `kd_status` | int |  | 0 arhiviran, 1 aktivan |  |
| `kd_slike` | text |  |  |  |
| `kd_category` | varchar(3) |  | A,B,C |  |

## `idk_nd_cron_export`

- **Opis**: Logs execution details, exported results, and recipient employee records for scheduled cron export tasks.
- **Redova**: 7,581 · **Period**: 2021-10-29 → 2025-07-09 (`datetime_c`) · **PK**: `id_c`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `id_c` | int | PRI |  |  |
| `type_c` | int |  | 1-Obrada |  |
| `result_c` | mediumtext |  | Rezultat u html obliku |  |
| `datetime_c` | datetime |  | Vrijeme kreiranja | [PII] |
| `date_c` | date |  |  |  |
| `sending_type_c` | int |  | 1 - zaposlenicima, 2 - kontroling |  |
| `sent_to_employees_c` | text |  | Zaposlenici kojima je poslan export |  |
| `download_employees_c` | text |  | Zaposlenici koji su preuzeli |  |
| `settings_id` | int |  | Id iz tabele cron_settings |  |

## `idk_nd_cron_settings`

- **Opis**: Stores scheduled cron job configurations and criteria for monitoring employee activities, communication intervals, and candidate statuses within specified date ranges.
- **Redova**: 13 · **Period**: 2021-10-27 → 2023-07-31 (`start_day_s`) · **PK**: `id_s`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `id_s` | int | PRI |  |  |
| `type_s` | int |  | 1-Obrada Dipl |  |
| `status_s` | int |  | 0-nije aktivan, 1-aktivan |  |
| `employees_s` | text |  | Zaposlenici kojima se šalje mail |  |
| `control_employees_s` | text |  | Zaposlenici koji vrše kontrolu |  |
| `candidate_status_s` | int |  | Status kandidata za koji se radi provjera |  |
| `status_days_s` | int |  | Kandidat na statusu dana - broj i više |  |
| `communication_days_s` | int |  | Dana od zadnje komunikacije kod kandidata |  |
| `start_day_s` | datetime |  | Početak provjere |  |
| `end_day_s` | datetime |  | Kraj provjere - ako je prazno onda je aktivan |  |

## `idk_nd_kandidata`

- **Opis**: Stores candidate profiles and application workflows for employment abroad, including personal details, prospective employer information, document tracking, language skills, and communication history.
- **Redova**: 81,330 · **Period**: 2020-04-21 → 2026-02-10 (`vrijeme_kreiranja_nd_kandidata`) · **PK**: `id_broj_nd_kandidata`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `id_broj_nd_kandidata` | int | PRI |  |  |
| `ime_nd_kandidata` | varchar(30) |  |  | [PII] |
| `prezime_nd_kandidata` | varchar(50) |  |  | [PII] |
| `ulica_nd_kandidata` | varchar(100) |  |  | [PII] |
| `postanski_broj_nd_kandidata` | int |  |  |  |
| `grad_nd_kandidata` | varchar(100) |  |  |  |
| `ulica_bor_nd_kandidata` | varchar(100) |  | ulica boravista | [PII] |
| `postanski_broj_bor_nd_kandidata` | int |  | postanski broj boravista |  |
| `grad_bor_nd_kandidata` | varchar(100) |  | grad boravista |  |
| `mobilni_nd_kandidata` | varchar(20) |  |  |  |
| `email_nd_kandidata` | varchar(50) |  |  | [PII] |
| `izdao_licnu_nd_kandidata` | varchar(100) |  | Nadlezni organ koji je izdao licnu kartu - NPR: PU, Krusevac ili MUP USK, Cazin |  |
| `jmbg_nd_kandidata` | varchar(50) |  |  | **[TAJNO]** |
| `broj_licne_karte_nd_kandidata` | varchar(30) |  |  | **[TAJNO]** |
| `skola_nd_kandidata` | int |  | skola_id iz tabele idk_skole |  |
| `skola_smjer_nd_kandidata` | int |  | ss_id iz tabele idk_skole_smjerovi |  |
| `poslodavac_nd_kandidata` | int |  | 1 - ima poslodavca 0 - nema poslodavca |  |
| `poslodavac_nas_nd_kandidata` | int |  | 1 - nasa kompanija 0 - nije nasa |  |
| `poslodavac_naziv_nas_nd_kandidata` | int |  |  |  |
| `poslodavac_naziv_nd_kandidata` | varchar(200) |  |  |  |
| `poslodavac_ulica_nd_kandidata` | varchar(150) |  |  | [PII] |
| `poslodavac_postanski_broj_nd_kandidata` | int |  |  |  |
| `poslodavac_grad_nd_kandidata` | varchar(100) |  |  |  |
| `poslodavac_regija_nd_kandidata` | varchar(50) |  |  |  |
| `poslodavac_drzava_nd_kandidata` | varchar(100) |  |  |  |
| `poslodavac_ime_nd_kandidata` | varchar(50) |  |  | [PII] |
| `poslodavac_prezime_nd_kandidata` | varchar(50) |  |  | [PII] |
| `poslodavac_mail_nd_kandidata` | varchar(100) |  |  | [PII] |
| `poslodavac_mobilni_nd_kandidata` | varchar(50) |  |  |  |
| `komentar_nd_kandidata` | text |  |  |  |
| `vrijeme_kreiranja_nd_kandidata` | datetime | MUL |  |  |
| `dodao_zaposlenik_nd_kandidata` | int |  |  |  |
| `zaduzen_zaposlenik_nd_kandidata` | int |  |  |  |
| `tim_nd_kandidata` | int |  |  |  |
| `status_nd_kandidata` | int | MUL | 1 - Novi 2 - Prikupljanje dokumentacije 3 - Poslana posta 4 - U obradi 5 - Dopuna dokumentacije 6 - Zavrsen 7 - Arhiviran |  |
| `pstatus_nd_kandidata` | int | MUL | 1-Lead, 2-Neusp Lead, 3-Zaint Lead, 4-Nezaint Lead, 5-U obradi Lead |  |
| `idd_ustanova_nd` | int |  |  |  |
| `broj_zahtjeva_na_ustanovi_nd_kandidata` | varchar(100) |  |  |  |
| `idd_kontakt_ustanova_nd` | int |  |  |  |
| `tracking_number_nd_kandidata` | varchar(100) |  |  |  |
| `link_tracking_number_nd_kandidata` | int |  |  |  |
| `vrsta_ugovora_nd_kandidata` | int |  | 1 - Ugovor bez popusta 2 - Ugovor sa popustom |  |
| `rata1_nd_kandidata` | int |  | 0 - NE 1 - DA |  |
| `rata1_vrijeme_nd_kandidata` | datetime |  |  |  |
| `rata2_nd_kandidata` | int |  | 0 - NE 1 - DA |  |
| `rata2_vrijeme_nd_kandidata` | datetime |  |  |  |
| `povijest_nd_kandidata` | int | MUL | 0-CRM 1-KANDIDATI 2-DAK 3-PARTNER 4 - JS WEB 5 -Kampanje |  |
| `povijest_vrsta_nd_kandidata` | int |  | KANDIDATI: 1-SMS 2-BOT 3-CRM 4-Viber DAK: 1-APL 2-WEB PARTNER: 1 - APL JS WEB: 1-WEB Kampanje: 1 - Nesto |  |
| `kandidat_idd` | int | MUL |  |  |
| `partner_nd_status` | int |  | Sprema se trenutni status partnera - onog trenutka kad udje kandidat. |  |
| `kampanja_id` | int | MUL | Kada je povijest_nd_kandidata == 5 - posmatra se ova kolona |  |
| `datum_rodjenja` | date |  |  | [PII] |
| `in_vici_dial` | int |  | Kolona koja govori da li se kandidat nalazi u ViciDialu |  |
| `status_pp` | int |  | 3 - Prioritet 3, 2 - Prioritet 2, 1 - Prioritet 1 |  |
| `vrijeme_zakaznog_poziva` | datetime |  | vrijeme zadnjeg zakazanog poziva - call back |  |
| `status_zakaznog_poziva` | int |  | status zadnjeg zakazanog poziva 0-nije obradjen 1- obradjen |  |
| `zadnja_komunikacija` | datetime |  |  |  |
| `chat_slike` | text |  | Slike razgovora za prioritete sa facebook-instagrama |  |
| `vrsta_obrade` | int |  | 1 - ausbildung, 2 - srednja skola, 3 - fakultet |  |
| `nivo_poznavanja_jezika` | int |  | 0 - nije naznačeno, 1 - bez znanja, 2 - A1, 3 - A2, 4 - B1, 5 - B2, 6 - C1, 7 - C2 |  |
| `certifikat_nd_kandidata` | int |  | Certifikat za njemacki jezik: 0 - nema, 1 - ima |  |
| `inbound_aktivan` | int |  | Kolona koja govori da li je unešena inbound komunikacija. (0 - nije aktivan 1 - aktivan) |  |
| `poslan_spisak_datum` | date |  | Datum koji se unosi kada se neki događaj stvarno desio za određeni status. Naziv je vezan uz status. |  |
| `dokumentacija_kompletna_datum` | date |  | Datum koji se unosi kada se neki događaj stvarno desio za određeni status. Naziv je vezan uz status. |  |
| `na_prevodu_datum` | date |  | Datum koji se unosi kada se neki događaj stvarno desio za određeni status. Naziv je vezan uz status. |  |
| `prevod_zavrsen_datum` | date |  | Datum koji se unosi kada se neki događaj stvarno desio za određeni status. Naziv je vezan uz status. |  |
| `poslana_posta_datum` | date |  | Datum koji se unosi kada se neki događaj stvarno desio za određeni status. Naziv je vezan uz status. |  |
| `zaprimljena_dokumentacija_datum` | date |  | Datum koji se unosi kada se neki događaj stvarno desio za određeni status. Naziv je vezan uz status. |  |
| `stigla_taksa_dopuna_datum` | date |  | Datum koji se unosi kada se neki događaj stvarno desio za određeni status. Naziv je vezan uz status. |  |
| `placena_taksa_poslana_dopuna_datum` | date |  | Datum koji se unosi kada se neki događaj stvarno desio za određeni status. Naziv je vezan uz status. |  |
| `zavrsen_datum` | date |  | Datum koji se unosi kada se neki događaj stvarno desio za određeni status. Naziv je vezan uz status. |  |

## `idk_nd_kandidata_biljeske`

- **Opis**: Stores notes and follow-up records related to candidates, including call schedules, payment details, proforma invoices, and employee interaction logs.
- **Redova**: 928,882 · **Period**: 2020-04-22 → 2025-05-28 (`vrijeme_dodavanja_biljeska_nd`) · **PK**: `id_biljeska_nd`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `id_biljeska_nd` | int | PRI |  |  |
| `id_kandidata_biljeska_nd` | int | MUL |  |  |
| `status_biljeska_nd` | int |  |  |  |
| `tip_biljeska_nd` | int |  | 1-Ostalo, 2- Neuspjesna komunikacija, 3-Nije zainteresiran, 4-Poslana infolista i primjer ugovora, 5-Poslan pravu ugovor i predracun |  |
| `razlog_biljeska_nd` | int | MUL | "id_ro" iz tabele idk_ro_usluge |  |
| `sadrzaj_biljeska_nd` | text |  |  |  |
| `vrijeme_dodavanja_biljeska_nd` | datetime |  |  |  |
| `vrijeme_grupa_biljeska_nd` | int |  |  |  |
| `dodao_zaposlenik_biljeska_nd` | int |  |  |  |
| `predracun_id` | int | MUL | Za biljesku pod statusom 3 evidentira se i predračun id. |  |
| `predracun_status` | int |  |  |  |
| `vrijeme_ponovnog_zvanja` | datetime |  | U slucaju da je tip biljeske 6, onda se unosi vrijeme ponovnog zvanja |  |
| `uplata_na_datum` | datetime |  |  |  |
| `zadnja_inkaso_biljeska` | int |  |  |  |
| `prilog_biljeska_nd` | text |  | Sprema se naziv priloga dodanog na biljesku. Filovi se nalaze na putanji: files/prilozi_dipl |  |

## `idk_nd_kandidata_dokumenti`

- **Opis**: Stores candidate documents and their metadata, including document types, upload timestamps, installment associations, and the employees who added them.
- **Redova**: 52,716 · **Period**: 2020-04-21 → 2025-01-31 (`vrijeme_dodavanja_dokument_nd`) · **PK**: `id_dokument_nd`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `id_dokument_nd` | int | PRI |  |  |
| `naziv_dokument_nd` | varchar(100) |  |  |  |
| `naziv_dokument_ostali_nd` | varchar(300) |  |  |  |
| `status_dokument_nd` | int |  |  |  |
| `id_kandidata_dokument_nd` | int |  |  |  |
| `vrijeme_dodavanja_dokument_nd` | datetime |  |  |  |
| `dodao_zaposlenik_dokument_nd` | int |  |  |  |
| `tip_dokumenta` | int |  | 1 - ugovor; 2 - uplatnica; 3 - certifikat o poznavanju jezika |  |
| `tip_dokumenta_status` | int |  | 1 - aktivan 0 - nije aktivan |  |
| `broj_rate` | int |  |  |  |

## `idk_nd_kandidata_status_log`

- **Opis**: Logs the history of candidate status changes, recording the previous and new status, the timestamp of the change, the employee who made it, and the duration spent in the status.
- **Redova**: 407,806 · **Period**: 2020-04-21 → 2026-02-16 (`vrijeme_promjene_statusa_nd_kandidata`) · **PK**: `id_log_status_nd_kandidata`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `id_log_status_nd_kandidata` | int | PRI |  |  |
| `idd_broj_nd_kandidata` | int | MUL |  |  |
| `status_nd_kandidata` | int |  |  |  |
| `pstatus_nd_kandidata` | int |  |  |  |
| `vrijeme_promjene_statusa_nd_kandidata` | datetime |  |  |  |
| `broj_dana_statusa_nd_kandidata` | int | MUL |  |  |
| `promjenio_zaposlenik_nd_kandidata` | int |  |  |  |

## `idk_nd_kandidati_ciscenje`

- **Opis**: Stores candidate data and status flags used for cleaning and migrating candidate profiles, education, and language skills into the diploma system.
- **Redova**: 58,468 · **Period**: – · **PK**: `kandidat_ciscenje_id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `kandidat_ciscenje_id` | int | PRI |  |  |
| `id_kandidata_dipl` | int |  |  |  |
| `ime_kandidata` | varchar(255) |  |  | [PII] |
| `prezime_kandidata` | varchar(255) |  |  | [PII] |
| `hash_id_dipl` | varchar(255) |  |  |  |
| `status_informacija` | int |  | 1-nema jezik, 2-nema skolu, 3-nema jezik ni skolu |  |
| `status_pracenja` | int |  | 0-nije usao u link, 1-poslan link, 2-usao u link , 3-ispunio formu |  |
| `broj_telefona` | varchar(255) |  |  | [PII] |
| `id_kandidata_posao` | int |  |  |  |
| `arhiva` | int |  |  |  |
| `treba_prebaciti_jezik_u_dipl` | int |  |  |  |
| `znanje_jezika_iz_idk_kan_jezici` | varchar(255) |  |  |  |
| `treba_prebaciti_skolu_smjer_u_dipl` | int |  |  |  |
| `skola` | int |  |  |  |
| `smjer` | int |  |  |  |

## `idk_nd_limiti`

- **Opis**: Stores daily, weekly, and monthly lead or assignment limits and usage counts for employees across different countries and campaign categories.
- **Redova**: 137 · **Period**: – · **PK**: `lt_id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `lt_id` | int | PRI |  |  |
| `lt_emp_id` | int |  | Id zaposlenika iz tabele idk_employees |  |
| `lt_drzava` | varchar(20) |  | Drzava koju agent moze kontaktirati |  |
| `lt_dnevni` | int |  |  |  |
| `lt_sedmicni` | int |  |  |  |
| `lt_mjesecni` | int |  |  |  |
| `lt_dnevni_cnt` | int |  |  |  |
| `lt_sedmicni_cnt` | int |  |  |  |
| `lt_mjesecni_cnt` | int |  |  |  |
| `lt_zadnji_dobio_bih` | int |  |  |  |
| `lt_zadnji_dobio_srb` | int |  |  |  |
| `lt_zadnji_dobio_de` | int |  |  |  |
| `lt_zadnji_dobio_ostalo` | int |  |  |  |
| `lt_campaign_category` | varchar(15) |  | A,B,C |  |

## `idk_nd_menadzeri_statistike`

- **Opis**: Records activity logs and assignment statistics for managers or employees handling specific candidate records over time.
- **Redova**: 260,749 · **Period**: 2020-04-21 → 2026-02-19 (`vrijeme_aktivnosti`) · **PK**: `id_stat`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `id_stat` | int | PRI |  |  |
| `idd_broj_nd_kandidata` | int |  |  |  |
| `zaduzen_zaposlenik_id` | int |  |  |  |
| `prethodni_zaposlenik_id` | int |  |  |  |
| `vrsta_aktivnosti` | int |  |  |  |
| `vrijeme_aktivnosti` | datetime |  |  |  |

## `idk_nd_naplata_preko`

- **Opis**: Stores billing and collection methods categorized by country, indicating activation dates and whether each method is active.
- **Redova**: 8 · **Period**: 2021-05-27 → 2023-08-31 (`datum_aktivacije`) · **PK**: `id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `id` | int | PRI |  |  |
| `naplata_preko` | varchar(200) |  |  |  |
| `drzava` | varchar(10) |  | ISO 3166 Country code |  |
| `fk_naplata_preko` | int |  |  |  |
| `aktivno` | int |  |  |  |
| `datum_aktivacije` | datetime |  |  |  |

## `idk_nd_poste`

- **Opis**: This table stores postal and delivery service providers, including their names and tracking or service links.
- **Redova**: 13 · **Period**: – · **PK**: `id_poste`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `id_poste` | int | PRI |  |  |
| `naziv_poste` | varchar(100) |  |  |  |
| `link_poste` | text |  |  |  |

## `idk_nd_rate`

- **Opis**: Stores timestamped rate or count metrics associated with specific channels or entities identified by candidate IDs.
- **Redova**: 6,201 · **Period**: 2020-04-14 → 2024-10-23 (`vr_u_r`) · **PK**: `id_r`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `id_r` | int | PRI |  |  |
| `id_nd_kan` | int |  | "id_broj_nd_kandidata" iz tabele idk_nd_kandidata |  |
| `br_r` | int |  | Broj rate: 1,2,3,4,5 u zavisnosti od "vrsta_ugovora_nd_kandidata" iz tabele idk_nd_kandidata |  |
| `vr_u_r` | datetime |  | Vrijeme kada je rata uplaćena |  |

## `idk_nd_termini`

- **Opis**: Stores scheduled appointments and interview sessions, including dates, times, statuses, and associated candidate and employee identifiers.
- **Redova**: 450,943 · **Period**: 2021-09-19 → 2025-09-17 (`termin_vrijeme`) · **PK**: `termin_id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `termin_id` | int | PRI | Id termina |  |
| `termin_kandidat_id` | int | MUL | Id kandidata iz tabele idk_nd_kandidata |  |
| `termin_vrijeme` | datetime |  | Vrijeme termina |  |
| `termin_kandidat_status` | int |  | Status kandidata na kojem se kandidat nalazio u vrijeme unosa termina |  |
| `termin_kandidat_pstatus` | int |  | PodStatus kandidata na kojem se kandidat nalazio u vrijeme unosa termina |  |
| `termin_status` | int | MUL | 0 - neaktivan, 1 - aktivan, 2 - obrađen |  |
| `termin_zaposlenik_id` | int |  | Id zaposlenika koji je napravio termin |  |
| `termin_biljeska_id` | int |  | Id biljekse iz tabele idk_nd_kandidata_biljeske |  |

## `idk_nd_ugovori`

- **Opis**: Stores candidate and employee contract records, tracking contract files, language versions, issuance details, acceptance or rejection status, and digital interaction logs.
- **Redova**: 2,518 · **Period**: 2022-01-11 → 2024-08-12 (`ug_datum_slanja`) · **PK**: `ug_id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `ug_id` | int | PRI |  |  |
| `ug_kandidat_id` | int |  |  |  |
| `ug_broj` | varchar(50) |  |  |  |
| `ug_vrsta` | int |  | Vrsta ugovora koja mu je bila izdata |  |
| `ug_zaposlenik_id` | int |  |  |  |
| `ug_token` | varchar(50) |  |  | **[TAJNO]** |
| `ug_jezik` | varchar(10) |  | bs, sr ili de |  |
| `ug_file` | varchar(50) |  |  |  |
| `ug_file_de` | varchar(50) |  |  |  |
| `ug_status` | int |  | 0-arhiviran, 1-poslan, 2-prihvacen, 3-odbijen, 4-otvoren link |  |
| `ug_datum_arhiviranja` | datetime |  |  |  |
| `ug_datum_slanja` | datetime |  |  |  |
| `ug_datum_prihvatanja` | datetime |  |  |  |
| `ug_datum_odbijanja` | datetime |  |  |  |
| `ug_datum_otvaranja_linka` | datetime |  |  |  |
| `ug_ip_adresa` | varchar(100) |  |  | [PII] |
| `ug_timestamp` | varchar(30) |  |  | [PII] |
| `ug_razlog_odbijanja` | int |  |  |  |
| `ug_komentar` | text |  | U slučaju da kandidat odabere razlog odbijanja "Ostalo" - nudi mu se opcija za upis teksta/komentara |  |

## `idk_nd_ustanove`

- **Opis**: Stores details about institutions, including their contact and location information, registration dates, regions, and nostrification periods.
- **Redova**: 93 · **Period**: 2020-03-27 → 2023-11-16 (`datum_registracije_ustanove_nd`) · **PK**: `id_ustanove_nd`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `id_ustanove_nd` | int | PRI |  |  |
| `naziv_ustanove_nd` | varchar(200) |  |  |  |
| `ulica_ustanove_nd` | varchar(100) |  |  | [PII] |
| `postanski_broj_ustanove_nd` | int |  |  |  |
| `grad_ustanove_nd` | varchar(100) |  |  |  |
| `regija_da_ne_ustanove_nd` | int |  |  |  |
| `naziv_regije_ustanove_nd` | varchar(50) |  |  |  |
| `drzava_ustanove_nd` | varchar(100) |  |  |  |
| `period_nostrifikacije_ustanove_nd` | int |  |  |  |
| `napomena_ustanove_nd` | text |  |  |  |
| `datum_registracije_ustanove_nd` | datetime |  |  |  |
| `dodao_zaposlenik_ustanove_nd` | int |  |  |  |

## `idk_nd_ustanove_biljeske`

- **Opis**: Stores notes and comments associated with institutions, including the content, creation timestamp, and the employee who added each note.
- **Redova**: 22 · **Period**: 2020-04-07 → 2022-09-06 (`vrijeme_dodavanja_biljeska_nd`) · **PK**: `id_biljeska_nd`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `id_biljeska_nd` | int | PRI |  |  |
| `id_ustanova_biljeska_nd` | int |  |  |  |
| `sadrzaj_biljeska_nd` | text |  |  |  |
| `vrijeme_dodavanja_biljeska_nd` | datetime |  |  |  |
| `vrijeme_grupa_biljeska_nd` | int |  |  |  |
| `dodao_zaposlenik_biljeska_nd` | int |  |  |  |

## `idk_nd_ustanove_kontakti`

- **Opis**: Stores contact persons for institutions, including their names, phone numbers, email addresses, roles, and associated institution IDs.
- **Redova**: 198 · **Period**: – · **PK**: `id_kontakt_ustanove_nd`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `id_kontakt_ustanove_nd` | int | PRI |  |  |
| `ime_kontakt_ustanove_nd` | varchar(100) |  |  | [PII] |
| `prezime_kontakt_ustanove_nd` | varchar(150) |  |  | [PII] |
| `email_kontakt_ustanove_nd` | varchar(200) |  |  | [PII] |
| `broj_telefona_kontakt_ustanove_nd` | varchar(50) |  |  | [PII] |
| `zaduzenje_kontakt_ustanove_nd` | text |  |  |  |
| `idd_ustanove_nd` | int |  |  |  |

## `idk_nd_ustanove_skola`

- **Opis**: A junction table that maps associations between educational institutions (schools) and their corresponding organizational entities or facilities.
- **Redova**: 567 · **Period**: – · **PK**: `id_skole_ustanove_nd`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `id_skole_ustanove_nd` | int | PRI |  |  |
| `skola_idd` | int |  |  |  |
| `idd_ustanove_nd` | int |  |  |  |

## `idk_nd_ustanove_skole_smjerovi`

- **Opis**: This table links educational institutions to their specific study programs or tracks, establishing the courses or majors offered by each school.
- **Redova**: 2,566 · **Period**: – · **PK**: `id_skole_smjer_ustanove_nd`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `id_skole_smjer_ustanove_nd` | int | PRI |  |  |
| `idd_skole_ustanove_nd` | int |  |  |  |
| `ss_idd` | int |  |  |  |

## `idk_nd_ustanove_tip_dokumenta`

- **Opis**: Defines institution-specific document types, templates, and requirements associated with schools, study programs, and institutions.
- **Redova**: 843 · **Period**: – · **PK**: `id_tip_dokumenta_ustanove_nd`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `id_tip_dokumenta_ustanove_nd` | int | PRI |  |  |
| `povezanost_dokumenta_ustanove_nd` | int |  |  |  |
| `naziv_tip_dokumenta_ustanove_nd` | varchar(200) |  |  |  |
| `obaveznost_dokumenta_ustanove_nd` | int |  |  |  |
| `idd_ustanove_nd` | int |  |  |  |
| `idd_skole_ustanove_nd` | int |  |  |  |
| `idd_skole_smjer_ustanove_nd` | int |  |  |  |
| `template_dokumenta_ustanove_nd` | int |  |  |  |
| `template_naziv_dokumenta_ustanove_nd` | varchar(100) |  |  |  |

## `idk_nostrifikovane_diplome`

- **Opis**: Stores records, files, and recognition status details for candidate nostrified (officially validated foreign) diplomas, along with upload metadata.
- **Redova**: 2,155 · **Period**: 2022-10-18 → 2025-01-31 (`upload_date_nd`) · **PK**: `id_nd`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `id_nd` | int | PRI |  |  |
| `id_cand_dipl` | int | MUL | kandidat id sa dipla |  |
| `id_cand_job` | int | MUL | kandidat id sa poslovi |  |
| `file_nd` | text |  | file - apsolutna putanja |  |
| `upload_date_nd` | datetime |  | datum uploada |  |
| `upload_employee_id` | int |  | zaposlenik uploadovao |  |
| `full_recognition` | int |  | NULL - default value, 0 - nepotpuno priznata, 1 - poptuno priznata |  |

## `idk_ponovne_prijave`

- **Opis**: Records historical log entries and details for re-applications submitted by job candidates across various campaigns.
- **Redova**: 12,764 · **Period**: 2021-01-15 → 2026-01-09 (`datum_pp`) · **PK**: `id_pp`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `id_pp` | int | PRI | id ponovne prijave |  |
| `porijeklo_pp` | int |  | 1 - DIPL, .... |  |
| `id_kandidata` | int |  | id_broj_nd_kandidata iz tabele idk_nd_kandidata |  |
| `employee_pp` | int |  | Zaduzen menager u trenutku ponovne prijave |  |
| `datum_pp` | datetime |  | Datum i vrijeme u kojem se ponovna prijava desila |  |
| `povijest_pp` | int |  | Prema koloni povijest_nd_kandidata iz tabele idk_nd_kandidata |  |
| `povijest_vrsta_pp` | int |  | Prema koloni povijest_vrsta_nd_kandidata iz tabele idk_nd_kandidata |  |
| `kampanja_pp` | int |  | Prema koloni kampanja_id iz tabele idk_nd_kandidata |  |
| `opis_pp` | text |  | U ovu kolonu upisuju se podaci (u obliku tekstualnog opisa) koje je kandidat unio u trenutku ponovne prijave. |  |

## `idk_reminders`

- **Opis**: Stores employee reminders and notifications associated with candidates, tracking scheduled dates, statuses, and reminder types.
- **Redova**: 16,009 · **Period**: 2021-11-07 → 2026-10-26 (`reminder_date_time`) · **PK**: `reminder_id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `reminder_id` | int | PRI | Reminder ID |  |
| `reminder_type` | int |  | 1 - Obrada dipl, 2 - odbijeni ugovori |  |
| `reminder_candidate_id` | int |  | Id kandidata |  |
| `reminder_date_time` | datetime |  | Vrijeme | [PII] |
| `reminder_candidate_status` | int |  | Status kandidata u vrijeme kreiranja reminder-a |  |
| `reminder_candidate_substatus` | int |  | Podstatus kandidata u vrijeme kreiranja reminder-a (ako postoji) |  |
| `reminder_employee` | int |  | Zaposlenik koji je postavio reminder |  |
| `reminder_status` | int |  | Status: 0 - neaktivan 1 - aktivan |  |
| `reminder_foreign_key` | int |  | Ako je reminder_type = 1 onda je strani ključ id biljeske iz tabele idk_nd_kandidata_biljeske |  |

## `idk_ro_usluge`

- **Opis**: Stores a multilingual reference catalog of service cancellation or refusal reasons, along with recall timing, approval statuses, and categorization details.
- **Redova**: 389 · **Period**: – · **PK**: `id_ro`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `id_ro` | int | PRI |  |  |
| `naziv_ro_bs` | text |  |  |  |
| `naziv_ro_sr` | text |  |  |  |
| `naziv_ro_de` | text |  |  |  |
| `tip_ro` | int |  | 1->DIPL 2->DAK 3->RO_Ugovora 4-Inkaso DIPL |  |
| `status_ro` | int |  | 0->Na cekanju,1->Aktivan,  2->Odbijen, 3->Deaktiviran |  |
| `ponovno_zvanje_ro` | int |  | DIPL - Ova kolona cuva informaciju o tome da li ce se kandidat ponovo zvati pod tim razlogom za uslugu nostrifikacije. 0->NE 1->DA |  |
| `br_dana_ro` | int |  | Ako je prethodna kolona oznacena sa 1, u ovoj koloni se cuva informacija o periodu nakon kojeg ce se zvati. Period je izrazen u danima. |  |
| `odobrio_ro` | int |  |  |  |
| `dodao_ro` | int |  |  |  |

