# Kandidati (vermittlung) – profil, CV, jezici, obrazovanje

Tabele: 27. Redovi i periodi stanje 2026-10-29.

## `beruf_mapping`

- **Opis**: Maps free-text job titles to standardized occupational group IDs along with confidence scores and the extraction source.
- **Redova**: 35,701 · **Period**: 2026-09-24 → 2026-09-30 (`created_at`) · **PK**: `id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `id` | int | PRI |  |  |
| `freitext_wert` | varchar(255) | UNI |  |  |
| `berufsgruppe_id` | varchar(100) | MUL |  |  |
| `confidence` | decimal(3,2) |  |  |  |
| `quelle` | varchar(20) |  |  |  |
| `created_at` | timestamp |  |  |  |

## `idk_candidate_language_logs`

- **Opis**: Records historical log entries, status updates, and tracking data related to candidate language evaluations or training.
- **Redova**: 5,796 · **Period**: 2022-10-18 → 2025-11-07 (`cll_date`) · **PK**: `cll_id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `cll_id` | int | PRI |  |  |
| `cll_candidate_id` | int |  | FK iz tabele idk_kandidati |  |
| `cll_cvl_id` | int |  | FK iz tabele kandidat_jezici, ujedno i iz tabele candidate_verified_languages |  |
| `cll_status` | int |  | status na kojeg prelazi jezik (Napomena: mozda bude FK iz tabele statusa, za sad je ta info samo u tabeli candidate_verified_languages) |  |
| `cll_date` | datetime |  | vrijeme mijenjanja statusa |  |
| `cll_employee_id` | int |  | FK iz tabele employees, zaposlenik koji je promijenio status ili 0 ako je Cron/sistem prebacio |  |
| `cll_days_count` | int |  | broj dana na tom statusu |  |

## `idk_candidate_verified_languages`

- **Opis**: Records verified language qualifications for candidates, including course timelines, exam dates, certificate details, and verification status.
- **Redova**: 3,897 · **Period**: 2022-10-18 → 2025-11-07 (`cvl_last_updated`) · **PK**: `cvl_id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `cvl_id` | int | PRI | foreign key iz tabele kandidat_jezici |  |
| `cvl_status` | int |  | status jezika: 1-samoprocjena, 2-samostalno uči, 3- pohađa kurs podnivo 1, 4-pohađa kurs podnivo 2, 5-čeka datum polaganja, 6-čeka polaganje(ima termin), 7-čeka se rezultat, 8-ima certfikat, 9-certifikat istekao, 10-napreduje na veći nivo, 11-nije položen, 12- odustao, 13-arhiva, 14-motive    Napomena: mozda se bude pravila tabela samo za ove statuse a ovdje bi onda dolazio FK |  |
| `cvl_active` | int | MUL | podatak koji određuje da li je aktivan taj nivo, i jedan kandidat ce moci imati samo jedan red u ovoj tabeli gdje je ovaj atribut = 1 |  |
| `cvl_course1_started` | date |  | datum pocetka kursa podnivoa 1 |  |
| `cvl_course1_ended` | date |  |  |  |
| `cvl_course2_started` | date |  | datum pocetka kursa podnivoa 2 |  |
| `cvl_course2_ended` | date |  |  |  |
| `cvl_motive_start` | date |  |  |  |
| `cvl_motive_end` | date |  |  |  |
| `cvl_exam_date` | date |  | datum polaganja ispita |  |
| `cvl_certificate_path` | text |  | putanja do file-a certifikata |  |
| `cvl_certificate_upload_date` | datetime |  | vrijeme uploadanja certifikata |  |
| `cvl_certficate_creation_date` | date |  | datum izdavanja certfikata |  |
| `cvl_certificate_expiration_date` | date |  | datum isteka certifikata |  |
| `cvl_last_updated` | datetime |  | vrijeme zadnjeg update-a statusa nivoa jezika |  |

## `idk_documents`

- **Opis**: Stores uploaded document files, including their names, descriptions, file formats, and upload timestamps associated with specific employees and entities.
- **Redova**: 23,614 · **Period**: 2017-08-31 → 2026-02-16 (`document_datetime`) · **PK**: `document_id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `document_id` | int | PRI |  |  |
| `document_name` | varchar(150) |  |  |  |
| `document_special_type` | int |  | 1 - dokazivo radno iskustvo;  2 - dokaz o zavrsenoj srednjoj skoli |  |
| `document_desc` | varchar(250) |  |  |  |
| `document_file` | varchar(150) |  |  |  |
| `document_icon` | varchar(5) |  |  |  |
| `document_datetime` | datetime |  |  | [PII] |
| `document_group` | int |  |  |  |
| `document_dataid` | int |  |  |  |
| `document_employeeid` | int |  |  |  |

## `idk_kandidat_akademija`

- **Opis**: Records candidates' participation in academy programs, including enrollment dates, status, ratings, and notes.
- **Redova**: 0 · **Period**: – · **PK**: `ka_id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `ka_id` | int | PRI |  |  |
| `ka_kandidat_id` | int |  |  |  |
| `ka_nalog_id` | int |  |  |  |
| `ka_status` | int |  | 1 - ici ce,  2 - krenuo,  3 - završio,  4 - odustao,  5 - arhiva |  |
| `ka_date_from` | date |  |  |  |
| `ka_date_to` | date |  |  |  |
| `ka_note` | text |  | Biljeska koja se unosi na Zavrsio. |  |
| `ka_rating` | int |  | Ocjena koja se unosi na Zavrsio 1-5. |  |

## `idk_kandidat_cv`

- **Opis**: Stores candidate CV files and associated details linked to specific candidate IDs, including localized or language-specific resume records.
- **Redova**: 1 · **Period**: – · **PK**: `kcv_id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `kcv_id` | int | PRI |  |  |
| `kcv_kandidatid` | int |  |  |  |
| `kcv_ba` | varchar(255) |  |  |  |
| `kcv_de` | varchar(255) |  |  |  |

## `idk_kandidat_de`

- **Opis**: Stores candidate profile details including gender, citizenship, driver's license status, and job application preferences.
- **Redova**: 3,332 · **Period**: – · **PK**: `kde_id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `kde_id` | int | PRI |  |  |
| `kde_kandidat_id` | int |  |  |  |
| `kde_prijava_na` | varchar(400) |  |  |  |
| `kde_spol` | varchar(255) |  |  |  |
| `kde_drzavljanstvo` | varchar(255) |  |  |  |
| `kde_vozacka` | varchar(100) |  |  |  |

## `idk_kandidat_edukacija`

- **Opis**: Stores educational background records for job candidates, including institutions, degrees, qualifications, dates, locations, and multilingual descriptions.
- **Redova**: 149,473 · **Period**: 1971-03-01 → 2026-02-01 (`ke_datumod`) · **PK**: `ke_id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `ke_id` | int | PRI |  |  |
| `ke_orderid` | int |  |  |  |
| `ke_datumod` | date |  |  |  |
| `ke_datumdo` | date |  |  |  |
| `ke_aktuelno` | int |  | default 0, 1 aktuelno |  |
| `ke_smjer_id` | int |  |  |  |
| `ke_naziv_kvalifikacije` | varchar(100) |  |  |  |
| `ke_naziv_kvalifikacije_de` | varchar(100) |  |  |  |
| `ke_skola_id` | int |  |  |  |
| `ke_naziv` | varchar(100) |  |  |  |
| `ke_naziv_de` | varchar(250) |  |  |  |
| `ke_grad` | varchar(50) |  |  |  |
| `ke_grad_de` | varchar(200) |  |  |  |
| `ke_drzava` | varchar(100) |  |  |  |
| `ke_opis` | text |  |  |  |
| `ke_opis_de` | text |  |  |  |
| `ke_kandidat_id` | int | MUL |  |  |
| `ke_vrsta_obrazovanja` | varchar(50) |  |  |  |
| `ke_prikaz_pp` | int |  | 0 - onemogucen prikaz, 1 - omogucen prikaz |  |

## `idk_kandidat_financije`

- **Opis**: Records financial transactions, invoices, and payment tracking for candidates linked to specific projects and orders.
- **Redova**: 1,067 · **Period**: 2022-03-01 → 2026-08-07 (`kf_datum`) · **PK**: `kf_id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `kf_id` | int | PRI |  |  |
| `nalog_id` | int |  |  |  |
| `projekt_id` | int |  |  |  |
| `kandidat_id` | int |  |  |  |
| `kf_datum` | date |  | Datum aktiviranja. |  |
| `kf_datum_stvarni` | date |  | Datum aktiviranja. |  |
| `kf_nalog_rata_id` | int |  | FK iz tabele idk_nalozi_rate. Za fakture za nostrifikaciju će biti null. |  |
| `kf_type` | int |  | Tip rate/fakture: 0-nostrifikacija, 1-ugovor, 2-dobio vizu, 3-pocetak rada, 4-mjeseci nakon, 5-akademija |  |
| `kf_iznos` | double |  | Iznos fakture |  |
| `kf_placeno` | int |  | Status fakture: 0-NDF, 1-treba fakturisati, 2-fakturisano, 3-placeno. |  |
| `kf_datum_fakturisanja` | date |  |  |  |
| `kf_datum_placanja` | date |  |  |  |
| `kf_status` | int |  | Status za zamjene: default 1-normalna rata za kandidata koji nije zamijenjen, 2-rata za kandidata koji je zamijenjen, 3-rata za kandidata koji je višak |  |
| `kf_zamjena_id` | int |  |  |  |

## `idk_kandidat_jezici`

- **Opis**: Stores candidates' language proficiencies, detailing specific skills such as reading, listening, writing, and speaking in multiple languages and standardized competency levels.
- **Redova**: 82,474 · **Period**: – · **PK**: `kj_id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `kj_id` | int | PRI |  |  |
| `kj_naziv` | varchar(150) | MUL |  |  |
| `kj_naziv_de` | varchar(255) |  |  |  |
| `kj_slusanje` | varchar(50) | MUL |  |  |
| `kj_slusanje_de` | varchar(255) |  |  |  |
| `kj_citanje` | varchar(50) |  |  |  |
| `kj_citanje_de` | varchar(255) |  |  |  |
| `kj_govorna_interakcija` | varchar(50) |  |  |  |
| `kj_govorna_interakcija_de` | varchar(255) |  |  |  |
| `kj_govorna_produkcija` | varchar(50) |  |  |  |
| `kj_govorna_produkcija_de` | varchar(255) |  |  |  |
| `kj_pisanje` | varchar(50) |  |  |  |
| `kj_pisanje_de` | varchar(255) |  |  |  |
| `kj_kandidatid` | int | MUL |  |  |
| `kj_ustanova` | int |  | Ustanova preko koje kandidat uci jezik: 0-samostalno, 1-preklo Glose, 2,3 ... |  |

## `idk_kandidat_kontakt_info`

- **Opis**: Stores contact information and details associated with candidates, organized by type and group.
- **Redova**: 172,673 · **Period**: – · **PK**: `kki_id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `kki_id` | int | PRI |  |  |
| `kki_orderid` | int |  |  |  |
| `kki_grupa` | int |  |  |  |
| `kki_naziv` | varchar(100) |  |  |  |
| `kki_naziv_de` | varchar(255) |  |  |  |
| `kki_podatak` | varchar(100) |  |  | [PII] |
| `kki_kandidat_id` | int | MUL |  |  |
| `kki_primary` | int |  |  |  |

## `idk_kandidat_pozicija`

- **Opis**: Stores candidate job positions or roles along with their multilingual names, descriptions, and status information.
- **Redova**: 133 · **Period**: – · **PK**: `kp_id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `kp_id` | int | PRI |  |  |
| `kp_ime` | varchar(150) |  |  | [PII] |
| `kp_ime_de` | varchar(150) |  |  | [PII] |
| `kp_ime_en` | varchar(150) |  |  | [PII] |
| `kp_ime_rs` | varchar(150) |  |  | [PII] |
| `kp_opis` | text |  |  |  |
| `kp_created_by` | int |  | If source is 1 this is employee id, if source is 2 this is partner id. |  |
| `kp_source` | int |  | 1 - CRM, 2 - Partner app |  |
| `kp_active` | int |  | 1 - Aktivan, 0 - Arhiviran |  |

## `idk_kandidat_projekcije`

- **Opis**: Stores projected employment start dates for candidates.
- **Redova**: 88 · **Period**: 2024-09-01 → 2026-12-22 (`proracunati_pocetak_rada`) · **PK**: `kandidat_id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `kandidat_id` | int | PRI |  |  |
| `proracunati_pocetak_rada` | date |  |  |  |

## `idk_kandidat_radno_iskustvo`

- **Opis**: Stores candidates' work experience records, including company details, job titles, employment dates, descriptions, and multilingual translations.
- **Redova**: 87,844 · **Period**: 1972-01-01 → 2026-04-01 (`kri_darum_od`) · **PK**: `kri_id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `kri_id` | int | PRI |  |  |
| `kri_order` | int |  |  |  |
| `kri_darum_od` | date |  |  |  |
| `kri_datum_do` | date |  |  |  |
| `kri_aktuelno` | int |  | default 0, 1 aktuelno |  |
| `kri_pozicija` | varchar(250) |  |  |  |
| `kri_pozicija_de` | varchar(400) |  |  |  |
| `kri_pozicija_en` | varchar(400) |  |  |  |
| `kri_naziv` | varchar(100) |  |  |  |
| `kri_naziv_de` | varchar(250) |  |  |  |
| `kri_grad` | varchar(100) |  |  |  |
| `kri_grad_de` | varchar(200) |  |  |  |
| `kri_drzava` | varchar(100) |  |  |  |
| `kri_adresa` | varchar(100) |  |  | [PII] |
| `kri_telefon` | varchar(50) |  |  | [PII] |
| `kri_email` | varchar(50) |  |  | [PII] |
| `kri_web` | varchar(50) |  |  |  |
| `kri_opis` | text |  |  |  |
| `kri_opis_de` | text |  |  |  |
| `kri_kandidat_id` | int | MUL |  |  |
| `kri_prikaz_pp` | int |  | 0 - onemogucen prikaz, 1 - omogucen prikaz |  |

## `idk_kandidat_status`

- **Opis**: A lookup table that defines candidate processing statuses, such as under review, in progress, completed, or archived.
- **Redova**: 9 · **Period**: – · **PK**: `id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `id` | int | PRI |  |  |
| `status_id` | int | MUL |  |  |
| `status_naziv` | varchar(255) |  |  |  |

## `idk_kandidat_status_prijave`

- **Opis**: A lookup table that defines candidate application statuses, including their names, display order, active state, and reservation flags.
- **Redova**: 16 · **Period**: – · **PK**: `status_id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `status_id` | int | PRI |  |  |
| `status_naziv` | varchar(100) |  |  |  |
| `status_aktivan` | int |  |  |  |
| `rezervisanje` | int |  | 0-nije, 1-jeste, ako je kandidat pod statusom koji ima ovdje 1 onda je on rezervisan za nalog |  |
| `redoslijed_statusa` | int |  |  |  |

## `idk_kandidat_vjestine`

- **Opis**: Stores candidates' skills, including skill names, descriptions, groups, and German translations associated with each candidate.
- **Redova**: 10,211 · **Period**: – · **PK**: `kv_id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `kv_id` | int | PRI |  |  |
| `kv_naziv` | varchar(150) |  |  |  |
| `kv_naziv_de` | text |  |  |  |
| `kv_grupa` | int |  |  |  |
| `kv_opis` | text |  |  |  |
| `kv_opis_de` | text |  |  |  |
| `kv_kandidat_id` | int |  |  |  |

## `idk_kandidati`

- **Opis**: Stores comprehensive job candidate profiles, tracking personal information, application statuses, employment history, visa details, and recruitment agent assignments.
- **Redova**: 122,006 · **Period**: 2017-09-07 → 2026-10-24 (`kandidat_datetime`) · **PK**: `kandidat_id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `kandidat_id` | int | PRI |  |  |
| `kandidat_check` | varchar(200) |  |  |  |
| `kandidat_ime` | varchar(150) |  |  | [PII] |
| `kandidat_prezime` | varchar(150) |  |  | [PII] |
| `kandidat_prijava_na` | varchar(250) |  |  |  |
| `kandidat_spol` | varchar(10) |  |  |  |
| `kandidat_djevojackoprezime` | varchar(150) |  |  | [PII] |
| `kandidat_jmbg` | varchar(20) |  |  | **[TAJNO]** |
| `kandidat_brojlk` | varchar(50) |  |  | **[TAJNO]** |
| `kandidat_broj_pasosa` | varchar(50) |  |  | **[TAJNO]** |
| `kandidat_datumrodjenja` | date |  |  | [PII] |
| `kandidat_mjestorodjenja` | varchar(150) |  |  | [PII] |
| `kandidat_drzavljanstvo_vrsta` | varchar(100) |  |  |  |
| `kandidat_drzavarodjenja` | varchar(150) |  |  |  |
| `kandidat_drzavljanstvo` | varchar(150) |  |  |  |
| `kandidat_bracnostanje` | varchar(50) |  |  |  |
| `kandidat_bracnostanjeod` | date |  |  |  |
| `kandidat_adresa` | text |  |  | [PII] |
| `kandidat_grad` | varchar(150) |  |  |  |
| `kandidat_pbroj` | int |  |  |  |
| `kandidat_drzava` | varchar(150) |  |  |  |
| `kandidat_email` | varchar(250) |  |  | [PII] |
| `kandidat_mobitel` | varchar(100) |  |  | [PII] |
| `kandidat_vozacka_dozvola` | varchar(20) |  |  |  |
| `kandidat_vozacka_kategorija` | varchar(25) |  |  |  |
| `kandidat_korisnickoime` | varchar(250) |  |  | [PII] |
| `kandidat_password` | varchar(150) |  |  | **[TAJNO]** |
| `kandidat_slika` | varchar(150) |  |  |  |
| `kandidat_status` | int | MUL |  |  |
| `kandidat_status_messenger` | int |  | 0 - default (nije nista rađeno u vezi messengera - stari kandidati koji nisu reagovali na poruke za instaliranje messengera)    1 - Poslan SMS za instalaciju Messengera - Na čekanju!    2 - Logirao se    3 - Odbio instalirati (nakon više slanja poruka za instalaciju)    4 - Italijanske prijave - nekad trebalo i bilo bitno....    5 - U toku popunjavanje profila    6 - U toku dopunjavanje profila |  |
| `kandidat_datetime` | datetime |  |  | [PII] |
| `kandidat_visitedurl` | int | MUL |  |  |
| `kandidat_group` | int | MUL |  |  |
| `kandidat_mailsent` | int |  |  | [PII] |
| `datum_termina` | date |  |  |  |
| `kandidat_bio_na_terminu` | int |  | 1-da, 0-ne |  |
| `datum_aplikacije` | date |  |  |  |
| `kandidat_procjenatermina` | int |  |  |  |
| `kandidat_viza` | int |  |  |  |
| `kandidat_viza_vrijedi_od` | date |  |  |  |
| `kandidat_viza_vrijedi_do` | date |  |  |  |
| `boravak_eu` | varchar(255) |  |  |  |
| `kandidat_status_prijave` | int | MUL |  |  |
| `kandidat_zaposlen_kod` | int |  |  |  |
| `cv_ba` | int |  |  |  |
| `cv_de` | int |  |  |  |
| `profile_ba` | int |  |  |  |
| `profile_de` | int |  |  |  |
| `kandidat_datum_ugovora` | date |  |  |  |
| `kandidat_datum_ugovora_mjesec` | date |  |  |  |
| `kandidat_datum_pocetakrada` | date |  | Kolona koja je sluzila za pocetak rada koja se unosila  preko edit_candidate a prvenstveno je sluzila za finansije |  |
| `kandidat_datum_pocetakrada_mjesec` | date |  | Kolona koja je sluzila za finansije a ovisila je o koloni kandidat_datum_pocetakrada |  |
| `kandidat_potencijalni_pocetak_rada` | varchar(100) |  | Kolona koja je bila privremeno rješenje za unos potencijalnog pocetka rada koji se prikazivao poslodavcima |  |
| `kandidat_dogovoreni_pocetak_rada` | date |  | Kolona koja će služiti za "proces odlaska" |  |
| `kandidat_potvrden_pocetak_rada` | int |  | 1 - potvrden pocetak rada, 0 - kandidat nije poceo sa radom za dogovoreni datum, NULL (default) nema nikakve informacije |  |
| `kandidat_partnerid` | int |  |  |  |
| `kandidat_partner_status` | int |  |  |  |
| `kandidat_poslan_sms` | varchar(255) |  |  |  |
| `kandidat_sms_id` | varchar(255) |  |  |  |
| `kandidat_pogledao_link_prijave` | int |  |  |  |
| `kandidat_poslan_dipl` | int |  | slanje obavijesti kandidatima o diplu: 1=poslana notifikacija na bot, 11= poslana notf na bot po drugi put 2=poslan sms/viber, 3=notifikacija nije prosla, 4-poslan sms za ios korisnike; 21 - poslan sms/viber i pogledan link; 22 poslan SMS/viber(ima dipl); 23 - poslan SMS/viber (nema_dip) |  |
| `povezan_na_dipl` | int |  | 1-povezan, 0-nije povezan |  |
| `kandidat_porijeklo` | int |  | 0=kandidat usao starim putem, 1=kandidat_dosao_sa_dipla, 2=dosao sa dak-a, 3 = dosao po preporuci partnera (Partner -> Dipl -> Kandidati), 4=dosao sa svezavize web (SZV->DIPL->KAN), 5=dosao sa JobStep web (JS->DIPL->KAN) |  |
| `struka_sa_prijave` | int |  |  |  |
| `kandidat_nalog_id` | int | MUL |  |  |
| `kandidat_latest_reserved_time` | datetime |  | Vrijeme kada je posljednji put kandidat prebačen u projekat ili status koji kandidata čini rezervisanim | [PII] |
| `kandidat_ppa_partner_id` | int |  |  |  |
| `kandidat_pp_lokacija` | varchar(400) |  |  |  |
| `kandidat_pp_pozicija` | varchar(400) |  |  |  |
| `kandidat_pp_plata` | varchar(40) |  |  |  |
| `kandidat_pp_povezao_user_id` | int |  |  |  |
| `kandidat_pp_razlog_odbijanja` | varchar(255) |  |  |  |
| `kandidat_pp_datum_prihvatanja` | date |  |  |  |
| `kandidat_dipl_id` | int | MUL |  |  |
| `kandidat_ima_nostrifikaciju` | int |  | 1 - ima, 0 - nema |  |
| `kandidat_glossa` | int |  | 0 - nije glossa lead, 1 - glossa lead, 2 - prihvacen glossa lead, 3 - potencijalni glosa lead (nije otiso, ali je oznaceno pa ce otici na potpis ugovora) |  |
| `kandidat_tf_status` | int | MUL | Status kandidata u task force-u. Ako je null znači da nema aktivnih taskova. |  |
| `kandidat_iskustvo_u_struci` | int |  | null - nije unešena informacija; 0 - nema radno iskustvo u struci; 1 - ima radno iskustvo u struci |  |
| `kandidat_iskustvo_u_struci_trajanje` | int |  | null-nije unesena informacija, 0-nema u zadnjih 5 godina, 1-manje od 1 godine,2,3,4,5,6. Sprema se samo ako je kandidat_iskustvo_u_struci 1. Ako je 0 ovdje ide null. |  |
| `kandidat_termin_za_vizu` | int |  | default null - nije uneseno; 1 - ima termin za vizu: 2 - nema termin za vizu |  |
| `tf_reserved_agent` | int | MUL | Zaposlenik ID(agent) za kojeg je rezervisan kroz TF |  |
| `kandidat_nacin_odlaska` | int |  | 0 - Stručni kadar(normalni tok)/EU kandidat  2 - Zapadno-balkanski sistem    1 je rezervisana za EU kandidate za ispis na frontendu, ali 0 igra ulogu fallbacka ukoliko kandidat nema definisan specifican nacin odlaska, a u to upada EU. |  |
| `kandidat_bracno_stanje` | int |  | 0- Nepoznato; 1- Neoženjen/Neudana; 2- Oženjen/Udana; 3- Udovac/Udovica; 4- Razveden/Razvedena; |  |
| `kandidat_dostavljen_ugovor_jobstepu` | int |  | 1 - dostavljen ugovor |  |
| `kandidat_zeljena_regija` | int |  | NULL-nedefinisano, 1-nema preferenciju, ostalo FK iz idk_pp_regions |  |
| `kandidat_zeljeni_grad` | int |  | NULL-Nedefinisano, 0-nema preferenciju, ostalo FK iz idk_pp_city |  |
| `kandidat_partner_lead_status` | int |  | 1 - Lead; 2 - Klijent; 3 - Nije Zainteresiran; |  |
| `zaduzeni_makler_id` | int |  |  |  |
| `zaduzen_makleru_datum` | datetime |  |  |  |
| `zaduzeni_makler_reminder_datum` | date |  |  |  |
| `kandidat_nivo_obrazovanja` | int |  | null - nepoznato, 1 - fakultet, 2 - srednja škola |  |
| `kandidat_partner_lead_biljeska` | text |  |  |  |
| `kandidat_destinacija_grad` | varchar(255) |  |  |  |
| `kandidat_destinacija_postanski_broj` | varchar(10) |  |  |  |
| `assigned_to_makler` | int |  |  |  |
| `kandidat_paralelno_zb` | int |  | Kandidat paralelno aplicira za zapadni balkan. Value: {0 - NE, 1 - DA} |  |
| `kandidat_pogresan_broj` | int |  | Comment 1-pogresan broj, 0-nije pogresan broj |  |
| `kandidat_nedostupan` | int |  | 1-nedostupan, 0-nije nedostupan |  |
| `kandidat_atu_paket` | int |  | 1 - Paket 1, 2 - Paket 2, 3 - Paket 3 |  |
| `exported` | tinyint(1) |  |  |  |

## `idk_kandidati_contracts`

- **Opis**: Stores records of candidate contracts, including associated candidates, partners, upload metadata, file names, and signature statuses.
- **Redova**: 2,103 · **Period**: 2022-04-24 → 2026-01-29 (`kc_upload_time`) · **PK**: `kc_id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `kc_id` | int | PRI |  |  |
| `kc_file_name` | varchar(100) |  |  |  |
| `kc_candidate_id` | int |  |  |  |
| `kc_source` | int |  | 1 - crm  2 - PP |  |
| `kc_user_id` | int |  |  |  |
| `kc_upload_time` | datetime |  |  | [PII] |
| `kc_nalog_id` | int |  |  |  |
| `kc_partner_id` | int |  |  |  |
| `kc_signed` | int |  | 0 - nije potpisan   1 - potpisan |  |
| `kc_visibility_status` | int |  | 0 - arhiva  1 - nevidljiv  2 - vidljiv |  |

## `idk_kandidati_grupe`

- **Opis**: Stores candidate groups or occupational categories with multilingual titles, status, and related employee identifiers.
- **Redova**: 77 · **Period**: 2017-09-14 → 2025-12-14 (`kg_date`) · **PK**: `kg_id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `kg_id` | int | PRI |  |  |
| `kg_title` | varchar(255) |  |  |  |
| `kg_title_de` | varchar(255) |  |  |  |
| `kg_title_it` | varchar(255) |  |  |  |
| `kg_date` | datetime |  |  |  |
| `kg_employeeid` | int |  |  |  |
| `kg_status` | int |  |  |  |

## `idk_kandidati_reject_reasons`

- **Opis**: Records the rejection reasons, details, and associated metadata for candidates who were rejected during the recruitment or appointment process.
- **Redova**: 1,832 · **Period**: 2022-04-20 → 2025-10-10 (`krr_date`) · **PK**: `krr_id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `krr_id` | int | PRI |  |  |
| `krr_reason_id` | int |  |  |  |
| `krr_candidate_id` | int |  |  |  |
| `krr_nalog_id` | int |  |  |  |
| `krr_partner_id` | int |  |  |  |
| `krr_apointment_id` | int |  |  |  |
| `krr_description` | text |  |  |  |
| `krr_source` | int |  | 1 - crm  2 - PP |  |
| `krr_done_by` | int |  |  |  |
| `krr_date` | datetime |  |  |  |
| `krr_last_status` | int |  |  |  |

## `idk_notes`

- **Opis**: Stores user-entered notes and file attachments created by employees, linked to specific records or groups with associated timestamps.
- **Redova**: 188,224 · **Period**: 2017-09-11 → 2026-10-24 (`note_datetime`) · **PK**: `note_id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `note_id` | int | PRI |  |  |
| `note_txt` | text |  |  |  |
| `note_files` | text |  | Sprema se naziv priloga dodanog na biljesku. Filovi se nalaze na putanji: files/prilozi_kandidati |  |
| `note_datetime` | datetime |  |  | [PII] |
| `note_group` | int |  |  |  |
| `note_dataid` | int |  |  |  |
| `note_employeeid` | int |  |  |  |

## `idk_razlozi_odbijanja`

- **Opis**: Stores predefined rejection reasons categorized by section or block, including names in local and German languages.
- **Redova**: 24 · **Period**: – · **PK**: `ro_id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `ro_id` | int | PRI |  |  |
| `ro_naziv` | text |  |  |  |
| `ro_naziv_de` | varchar(255) |  |  |  |
| `ro_blok` | varchar(255) |  |  |  |
| `ro_dio_bloka` | varchar(255) |  |  |  |

## `idk_reject_reasons`

- **Opis**: Stores predefined rejection reasons and their multilingual descriptions (German, Bosnian, and English) used across the CRM system.
- **Redova**: 8 · **Period**: 2022-04-11 → 2022-04-20 (`rr_doe`) · **PK**: `rr_id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `rr_id` | int | PRI |  |  |
| `rr_name_bs` | text |  |  |  |
| `rr_name_de` | text |  |  |  |
| `rr_name_en` | text |  |  |  |
| `rr_rejected_by` | int |  | 1 - kandidat  2 - poslodavac |  |
| `rr_user_id` | int |  | Uvijek će biti iz tabele employees CRM |  |
| `rr_status` | int |  | 0 - aktivan  1 - neaktivan |  |
| `rr_doe` | datetime |  | doe - date of entry |  |

## `idk_timeline`

- **Opis**: Records timestamped timeline events, activities, and associated text entries logged by employees across different CRM entity types and groups.
- **Redova**: 1,051 · **Period**: 2018-06-20 → 2024-08-23 (`timeline_datetime`) · **PK**: `timeline_id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `timeline_id` | int | PRI |  | [PII] |
| `timeline_type` | int |  |  | [PII] |
| `timeline_txt` | text |  |  | [PII] |
| `timeline_datetime` | datetime |  |  | [PII] |
| `timeline_group` | int |  |  | [PII] |
| `timeline_dataid` | int |  |  | [PII] |
| `timeline_employeeid` | int |  |  | [PII] |

## `idk_validnosti_inputa`

- **Opis**: Records the validation status, reasons, and timestamps of candidate input data evaluated by employees.
- **Redova**: 82,280 · **Period**: 2020-02-18 → 2025-09-08 (`vi_datetime`) · **PK**: `vi_id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `vi_id` | int | PRI |  |  |
| `vi_razlog_id` | int |  |  |  |
| `vi_kandidat_id` | int | MUL |  |  |
| `vi_status` | int |  | 1-validan, 2-nije validan, 3-korigovan i ceka validaciju |  |
| `vi_employee_id` | int |  |  |  |
| `vi_podatak_id` | int |  |  |  |
| `vi_vrsta_podatka` | varchar(25) |  |  |  |
| `vi_datetime` | datetime |  |  | [PII] |

## `users`

- **Opis**: Stores user account details, credentials, device information, notification preferences, and document or qualification flags for job candidates.
- **Redova**: 111,121 · **Period**: 2020-02-18 → 2025-07-02 (`last_online`) · **PK**: `id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `id` | bigint unsigned | PRI |  |  |
| `phone` | varchar(191) |  |  | [PII] |
| `name` | varchar(191) |  |  |  |
| `nalog_id` | int |  |  |  |
| `email` | varchar(191) | UNI |  | [PII] |
| `password` | varchar(191) |  |  | **[TAJNO]** |
| `kandidat_id` | int | UNI |  |  |
| `last_online` | datetime |  |  |  |
| `sim_id` | varchar(255) |  |  |  |
| `token` | varchar(255) |  |  | **[TAJNO]** |
| `type` | varchar(15) |  |  |  |
| `ne_viza` | int |  |  |  |
| `ne_srednja` | int |  |  |  |
| `ne_visoka` | int |  |  |  |
| `ne_dodatna` | int |  |  |  |
| `ne_iskustvo` | int |  |  |  |
| `ne_diploma` | int |  |  |  |
| `ne_pripravnicki` | int |  |  |  |
| `ne_strucni` | int |  |  |  |
| `ne_cert_jezik` | int |  |  |  |
| `ponovno_slanje` | int |  |  |  |
| `dipl_obavijest` | int |  | 1 - zainteresiran(nema nostrificiranu dipl); 2 - nezainteresiran(ima nostrf dipl); 3 - ceka se da kandidat otvori notf; 4 - nije prosla notf; 5 - kandidat otvorio notf, ali nije nista odabrao |  |
| `notifikacije` | int |  | 1 i 4: notf za dipl obradjenim kandidatima, 2 i 5: notf za dipl doradjenim; 3 i 6: notf za dipl nezavrsenim; 7-automatski nakon obrade, 10 - notf za kontrolu(datum rod) - nije prosla, 11 notf za kontrolu jeste prosla, 12 - notf za kontorolu ios |  |
| `jezik` | varchar(10) |  |  |  |
| `notf_new_year` | int |  | 1 - poslana, 2 - pogledana, 3 - nije prosla, 4 - ios |  |

