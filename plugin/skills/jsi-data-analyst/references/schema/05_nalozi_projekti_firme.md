# Nalozi, projekti, firme, klijenti (sales)

Tabele: 28. Redovi i periodi stanje 2026-10-29.

## `idk_clients`

- **Opis**: Stores client records, including contact and location details, assigned managers, call dates, and sales or contract statuses.
- **Redova**: 387 · **Period**: 1996-10-07 → 2021-10-01 (`client_datum_zvanja`) · **PK**: `client_id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `client_id` | int | PRI |  |  |
| `client_name` | varchar(250) |  |  |  |
| `client_country` | varchar(255) |  |  |  |
| `client_region` | varchar(100) |  |  |  |
| `client_city` | varchar(250) |  |  |  |
| `client_address` | varchar(250) |  |  | [PII] |
| `client_pp` | int |  |  |  |
| `client_telephone` | varchar(250) |  |  | [PII] |
| `client_email` | varchar(250) |  |  | [PII] |
| `client_origin` | int |  | 0-rucno,1-dipl,2-dak |  |
| `client_recommendation` | int |  |  |  |
| `client_recommendation_company` | int |  |  |  |
| `client_fc_or_sales` | int |  | 0-fc,1-sales |  |
| `client_fc_status` | int |  | 0-lead,1-inprogr,2-akt,3-arh |  |
| `client_sales_status` | int |  | 0-lead,1-inprogr, 2-cekaug ,3-akt,4-arh |  |
| `client_manager` | int |  |  |  |
| `client_sales_manager` | int |  |  |  |
| `client_datum_zvanja` | date |  |  |  |
| `client_contract` | int |  |  |  |
| `client_description` | text |  |  |  |

## `idk_clients_stats`

- **Opis**: Stores dated client statistics, status updates, and descriptive activity logs associated with specific employees and sales or financial channels.
- **Redova**: 858 · **Period**: 2020-03-23 → 2024-08-14 (`date`) · **PK**: `id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `id` | int | PRI |  |  |
| `client_id` | int |  |  |  |
| `status` | int |  |  |  |
| `fc_or_sales` | int |  | 0-fc,1-sales |  |
| `date` | datetime |  |  |  |
| `zaposlenik_id` | int |  |  |  |
| `stats_desc` | text |  |  |  |

## `idk_companies`

- **Opis**: Stores CRM company profiles including business details, identification numbers, addresses, contact types, and workforce requirements.
- **Redova**: 1,223 · **Period**: 2018-04-13 → 2025-01-16 (`company_datetime`) · **PK**: `company_id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `company_id` | int | PRI |  |  |
| `company_name` | varchar(150) |  |  |  |
| `company_type` | varchar(50) |  |  |  |
| `company_idnum` | varchar(50) |  |  |  |
| `company_taxnum` | varchar(50) |  |  |  |
| `company_ceo` | int |  |  |  |
| `company_contact` | int |  |  |  |
| `company_address` | varchar(250) |  |  | [PII] |
| `company_zipcode` | varchar(50) |  |  |  |
| `company_city` | varchar(150) |  |  |  |
| `company_state` | varchar(150) |  |  |  |
| `company_country` | varchar(150) |  |  |  |
| `company_info` | text |  |  |  |
| `company_inote` | text |  |  |  |
| `company_logo` | varchar(50) |  |  |  |
| `company_contact_type` | varchar(150) |  |  |  |
| `company_datetime` | datetime |  |  | [PII] |
| `company_status` | int |  |  |  |
| `company_origin` | int |  | 0-normalno, 1-dipl,2-dak, 5 - partner_app |  |
| `company_reccomendation` | int |  |  |  |
| `company_size` | varchar(255) |  |  |  |
| `js_partner_id` | int |  | id iz tabele idk_jobstep_partners |  |
| `company_message` | text |  |  |  |
| `company_total_workers_required` | int |  |  |  |
| `company_professions` | text |  | Array of profession ids |  |

## `idk_companies_info`

- **Opis**: Stores additional categorized details, attributes, and custom information associated with companies.
- **Redova**: 1,698 · **Period**: – · **PK**: `comi_id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `comi_id` | int | PRI |  |  |
| `comi_group` | int |  |  |  |
| `comi_title` | varchar(150) |  |  |  |
| `comi_data` | varchar(250) |  |  |  |
| `comi_primary` | int |  |  |  |
| `comi_companyid` | int | MUL |  |  |

## `idk_contacts`

- **Opis**: Stores individual contact profiles, including personal details, job titles, addresses, company affiliations, and CRM relationship statuses.
- **Redova**: 628 · **Period**: 2018-04-12 → 2024-11-15 (`contact_datetime`) · **PK**: `contact_id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `contact_id` | int | PRI |  |  |
| `contact_firstname` | varchar(150) |  |  | [PII] |
| `contact_lastname` | varchar(150) |  |  | [PII] |
| `contact_nickname` | varchar(150) |  |  |  |
| `contact_dob` | date |  |  | [PII] |
| `contact_address` | varchar(250) |  |  | [PII] |
| `contact_zipcode` | int |  |  |  |
| `contact_city` | varchar(150) |  |  |  |
| `contact_state` | varchar(150) |  |  |  |
| `contact_country` | varchar(150) |  |  |  |
| `contact_info` | text |  |  |  |
| `contact_inote` | text |  |  |  |
| `contact_image` | varchar(250) |  |  |  |
| `contact_type` | varchar(50) |  |  |  |
| `contact_companyid` | int |  |  |  |
| `contact_clientid` | int |  |  |  |
| `contact_ownerid` | int |  |  |  |
| `contact_datetime` | datetime |  |  | [PII] |
| `contact_status` | int |  |  |  |
| `contact_job_title` | varchar(255) |  |  |  |

## `idk_contacts_info`

- **Opis**: Stores specific contact details and associated metadata, such as titles and grouped data entries, linked to individual contacts.
- **Redova**: 1,128 · **Period**: – · **PK**: `ci_id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `ci_id` | int | PRI |  |  |
| `ci_group` | int |  |  |  |
| `ci_title` | varchar(150) |  |  |  |
| `ci_data` | varchar(250) |  |  | [PII] |
| `ci_primary` | int |  |  |  |
| `ci_contactid` | int |  |  |  |

## `idk_link_generator`

- **Opis**: Stores generated application and tracking links, along with their associated projects, employees, visit counts, costs, and metadata.
- **Redova**: 1,411 · **Period**: 2017-09-06 → 2026-02-10 (`lg_datetime`) · **PK**: `lg_id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `lg_id` | int | PRI |  |  |
| `lg_link_prijave` | varchar(255) |  |  |  |
| `idk_urlimg_prijave` | varchar(500) |  |  |  |
| `lg_url` | varchar(255) |  |  |  |
| `lg_desc` | varchar(255) |  |  |  |
| `lg_status` | int |  |  |  |
| `lg_employeeid` | int |  |  |  |
| `lg_datetime` | datetime |  |  | [PII] |
| `lg_project` | int |  |  |  |
| `lg_nalogid` | int | MUL |  |  |
| `lg_language` | varchar(20) |  |  |  |
| `lg_troskovi` | double |  |  |  |
| `lg_broj_pregleda` | int |  |  |  |
| `lg_partner_app` | int |  | 0 - nije link za partner app, 1 - link za partner app |  |

## `idk_link_generator_rel`

- **Opis**: Stores association mappings between user groups and link generator entries.
- **Redova**: 2,166 · **Period**: – · **PK**: `lr_id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `lr_id` | int | PRI |  |  |
| `lr_lgid` | int |  |  |  |
| `lr_groupid` | int |  |  |  |

## `idk_link_projects`

- **Opis**: A junction table mapping relationships between links and projects.
- **Redova**: 82 · **Period**: – · **PK**: `lp_id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `lp_id` | int | PRI |  |  |
| `lp_linkid` | int |  |  |  |
| `lp_projectid` | int |  |  |  |

## `idk_nalog_financije`

- **Opis**: Stores financial transaction details for work orders, including installment numbers, billing and payment dates, amounts, and payment statuses.
- **Redova**: 126 · **Period**: 2021-12-01 → 2025-02-24 (`nf_datum_aktiviranja`) · **PK**: `nf_id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `nf_id` | int | PRI |  |  |
| `nf_nalog_id` | int |  |  |  |
| `nf_datum_aktiviranja` | date |  |  |  |
| `nf_type` | int |  | Tip rate: 1 - avans kod standardnog načina, 2 - avans kod mjesečnog načina, 3 - mjesečne rate, 4 - rate za nostrifikaciju |  |
| `nf_broj_rate` | int |  | Broj rate u slučaje da je nf_type = 3 |  |
| `nf_iznos` | double |  | Iznos fakture |  |
| `nf_placeno` | int |  | Status fakture: 0-NDF, 1-treba fakturisati, 2-fakturisano, 3-placeno, 4-athivirano. |  |
| `nf_datum_fakturisanja` | date |  |  |  |
| `nf_datum_placanja` | date |  |  |  |
| `nf_desc` | varchar(255) |  | Služi samo za nalog 254 zbog specifičnih rata |  |

## `idk_nalog_profil`

- **Opis**: Stores profile configurations and criteria associated with work orders, including status, priority, and assigned employees.
- **Redova**: 83 · **Period**: 2024-03-12 → 2025-11-10 (`doe`) · **PK**: `id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `id` | int | PRI |  |  |
| `naziv` | varchar(250) |  |  |  |
| `zaposlenik` | int |  |  |  |
| `status` | int |  |  |  |
| `prioritet` | int |  |  |  |
| `doe` | timestamp |  |  |  |
| `nalog_id` | int | MUL |  |  |

## `idk_nalog_smjer`

- **Opis**: This table represents a junction linking work orders or invoices (nalog) to specific study directions or courses (smjer).
- **Redova**: 2,092 · **Period**: – · **PK**: `id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `id` | int | PRI |  |  |
| `nalog_id` | int |  |  |  |
| `smjer_id` | int |  |  |  |

## `idk_nalozi`

- **Opis**: Stores client job orders and service contracts, including hiring requirements, financial commission terms, academy and nostrification details, and fulfillment statuses.
- **Redova**: 239 · **Period**: 2018-10-25 → 2026-09-24 (`nalog_kreirano`) · **PK**: `nalog_id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `nalog_id` | int | PRI |  |  |
| `kompanija_id` | int |  |  |  |
| `employee_id` | int |  |  |  |
| `nalog_broj` | varchar(255) |  |  |  |
| `nalog_naziv` | varchar(255) |  |  |  |
| `nalog_opis` | text |  |  |  |
| `nalog_kreirano` | timestamp |  |  |  |
| `nalog_datum_potpisa_naloga` | date |  |  |  |
| `nalog_status` | int |  |  |  |
| `nalog_marketing_menadzer` | int |  |  |  |
| `nalog_ugovor` | varchar(25) |  |  |  |
| `nalog_potrebno_kandidata` | int |  | Broj kandidata koji se traži nalogom. |  |
| `nalog_provizija` | double |  | Iznos provizije po kandidatu. |  |
| `nalog_provizija_po_plati` | float |  | Iznos provizije za kandidate po plati kandidata. |  |
| `nalog_broj_rata` | int |  |  |  |
| `nalog_procenat_avansa` | int |  | Iznos procenta za avans ako postoji i to samo kod mjesečnog plaćanja. |  |
| `nalog_placa_nostrifikaciju` | int |  | 0-ne placa, 1-placa |  |
| `nalog_nacin_nostrifikacije` | int |  | 1-standardni način (poslana pošta), 2-mjesečne rate. |  |
| `nalog_provizija_nostrifikacija` | double |  | Iznos fakture po kandidatu za nostrifikaciju. |  |
| `nalog_broj_rata_nostrifikacija` | int |  | Broj rata za fakturisanje nostrifikacije po nalogu. |  |
| `nalog_firma_fakturisanja` | int |  | default NULL-nemamo informaciju,   1: DE - Jobstep GmbH  2: CH - Jobstep Int Gmbh |  |
| `nalog_placena_prva_rata` | int |  | 2=NDF; 1=placeno; 0=neplaceno |  |
| `nalog_financije` | int |  |  |  |
| `nalog_akademija` | int |  | 0 - nalog ne plaća akademiju za kandidate,  1 - plaća |  |
| `nalog_provizija_akademija` | int |  | Iznos fakture za akademiju po kandidatu. |  |
| `nalog_nacin_akademija` | int |  | 1 - x dana prije početka akademije,  2 - x dana poslije početka akademije |  |
| `nalog_broj_dana_akademija` | int |  | Broj dana za plaćanje akademije |  |
| `nalog_partner_active` | int |  |  |  |
| `nalog_partner_provizija` | double |  |  |  |
| `pristup_poslodavcima` | int |  | 0 - nema pristup, 1 - ima pristup |  |
| `partneri_pp` | int |  | 0 - nema grupacija, 1 - ima grupacije |  |
| `nalog_prioritet` | int | MUL | Prioritet za algoritam kod task force-a. Ako je null znači da nalog nije uključen u algoritam za pozive. |  |
| `nalog_slanje_na_glosu` | int |  | 0 - kandidati se ne salju na glosu, 1 - salju se |  |
| `nalog_dospijece` | int |  | Broj dana od fakturisanja do uplate |  |
| `nalog_smjerovi_kriterij` | int |  | Kolona koja govori da li su smjerovi iz taba Smjerovi naloga kriterij za nalog ili ne. 0 - NE; 1 - DA; |  |
| `nalog_js_partner_id` | int |  | id iz tabele idk_jobstep_partners |  |
| `nalog_partner_app_title` | varchar(255) |  | Naslov koji ce se prikazivati u partner app-u kao naziv posla |  |
| `nalog_partner_app_location` | varchar(255) |  | Lokacija posla koja se prikazuje u partner app-u |  |
| `nalog_partner_app_until` | datetime |  | Datum do kad traju prijave na posao koji se prikazuje u partner app-u |  |
| `nalog_partner_app_salary` | varchar(255) |  | Plata za koju se prijavljuje koja ce se prikazivati u partner appu |  |
| `nalog_poslodavac_trazi_jezik` | int |  | 0 - poslodavac ne traži jezik; 1 - poslodavac traži jezik; Ovaj parametar se uzima u slučaju potpune/evaluacije diplome. Ako je označeno sa 1 na tom nalogu u slučaju da kandidat ima potpunu/evaluaciju, i dalje ce biti potrebno ispuniti uslov za jezik. |  |
| `nalog_poslodavac_koristi_pp` | int |  | Po ugovoru poslodavac se obavezuje na korištenje aplikacije JobSoft. Odnosno, obavezuje se na to da ako ne uradi neku akciju za nekog kandidata na istoj aplikaciji a JobStep ga pri tom obavijesti N puta, slijede ugovorom definisane akcije sa JobStep strane. |  |
| `offers_and_benefits_of_employers` | text |  |  |  |

## `idk_nalozi_blokovi_prijave`

- **Opis**: Stores application criteria and blocking conditions for job orders, specifying required candidate age, qualifications, language proficiency, driver's licenses, and professional experience.
- **Redova**: 205 · **Period**: – · **PK**: `nbp_id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `nbp_id` | int | PRI |  |  |
| `nbp_nalogid` | int |  |  |  |
| `nbp_vozacka` | varchar(50) |  |  |  |
| `nbp_vozacka_kategorija` | varchar(255) |  |  |  |
| `nbp_visoko_obr` | int |  |  |  |
| `nbp_dodatno_obr` | int |  |  |  |
| `nbp_korak4` | int |  |  |  |
| `nbp_njemacki_jezik` | varchar(10) |  |  |  |
| `nbp_ostali_jezici` | varchar(50) |  |  |  |
| `nbp_korak7` | int |  |  |  |
| `nbp_slika` | int |  |  |  |
| `nbp_diploma` | int |  |  |  |
| `nbp_pripravnicki` | int |  |  |  |
| `nbp_strucni` | int |  |  |  |
| `nbp_jezik_cert` | int |  |  |  |
| `nbp_struka` | varchar(50) |  |  |  |
| `nbp_iskustvo_u_struci` | int |  | 0 - nije potrebno; 1 - potrebno radno iskustvo u struci |  |
| `nbp_iskustvo_u_struci_trajanje` | int |  | null-nedefinirano,0-ne treba, 1-vise od 0, 2-vise od 1 godine, ... Unosi se samo ako je nbp_iskustvo_struci 1, suprotno se unosi null |  |
| `nbp_kandidat_starost_od` | int |  |  |  |
| `nbp_kandidat_starost_do` | int |  |  |  |

## `idk_nalozi_log`

- **Opis**: This table records an audit log of status changes for orders or work orders, including the associated employee and timestamp of each action.
- **Redova**: 908 · **Period**: 2018-10-16 → 2026-09-24 (`n_log_vrijeme`) · **PK**: `n_log_id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `n_log_id` | int | PRI |  |  |
| `n_log_nalogid` | int |  |  |  |
| `n_log_employeeid` | int |  |  |  |
| `n_log_status` | int |  |  |  |
| `n_log_vrijeme` | timestamp |  |  |  |

## `idk_nalozi_opis`

- **Opis**: Stores multilingual titles and descriptions for orders or work orders (nalozi) in multiple languages such as Italian, Bosnian, German, English, and Serbian.
- **Redova**: 106 · **Period**: – · **PK**: `no_id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `no_id` | int | PRI |  |  |
| `no_lang` | varchar(255) |  |  |  |
| `no_nalogid` | int |  |  |  |
| `no_nalognaziv` | varchar(255) |  |  |  |
| `no_nalogopis` | text |  |  |  |

## `idk_nalozi_rate`

- **Opis**: Stores installment payment schedules, due dates, percentages, and payment timing details associated with work orders.
- **Redova**: 89 · **Period**: 2019-10-30 → 2025-11-10 (`nr_datum`) · **PK**: `nr_id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `nr_id` | int | PRI |  |  |
| `nr_nalog` | int |  |  |  |
| `nr_rata` | int |  |  |  |
| `nr_procenat` | int |  |  |  |
| `nr_vrijeme_placanja` | varchar(35) |  |  |  |
| `nr_datum` | date |  |  |  |
| `nr_mjeseci_nakon` | int |  |  |  |

## `idk_partner_meetings`

- **Opis**: Stores scheduled partner meeting appointments, including the meeting type, associated company, and responsible employee.
- **Redova**: 11 · **Period**: 2024-01-16 → 2024-06-26 (`meeting_appointment`) · **PK**: `id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `id` | int | PRI |  |  |
| `meeting_appointment` | datetime |  |  |  |
| `meeting_type` | varchar(255) |  | 1- Company creation meeting |  |
| `meeting_company_id` | int |  | If meeting type is 1, this is mandatory |  |
| `meeting_employee` | int |  |  |  |

## `idk_profil_kriterij`

- **Opis**: Stores candidate qualification criteria and requirements, such as age limits, work experience, language proficiency levels, and driver's license categories, linked to specific profiles.
- **Redova**: 83 · **Period**: – · **PK**: `id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `id` | int | PRI |  |  |
| `vozacka_dozvola` | int |  |  |  |
| `kategorija_vozacke_dozvole` | varchar(50) |  |  |  |
| `smjerovi_naloga` | int |  |  |  |
| `radno_iskustvo_struka` | int |  |  |  |
| `radno_iskustvo_struka_trajanje` | int |  |  |  |
| `starost` | int |  |  |  |
| `starost_minimum` | int |  |  |  |
| `starost_maksimum` | int |  |  |  |
| `njemacki_jezik` | int |  |  |  |
| `nivo_njemackog_jezika` | varchar(11) |  |  |  |
| `znanje_drugog_jezika` | int |  |  |  |
| `engleski_jezik` | int |  |  |  |
| `nivo_engleskog_jezika` | varchar(11) |  |  |  |
| `francuski_jezik` | int |  |  |  |
| `nivo_francuskog_jezika` | varchar(11) |  |  |  |
| `italijanski_jezik` | int |  |  |  |
| `nivo_italijanskog_jezika` | varchar(11) |  |  |  |
| `profil_id` | int | MUL |  |  |

## `idk_project_candidate_queue`

- **Opis**: Tracks candidates queued for assignment to projects, including the entry date, partner association, and assignment status.
- **Redova**: 1,691 · **Period**: 2022-03-28 → 2026-02-13 (`queue_entry_date`) · **PK**: `queue_id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `queue_id` | int | PRI |  |  |
| `queue_project_id` | varchar(7) |  |  |  |
| `queue_candidate_id` | varchar(7) |  |  |  |
| `queue_partner_id` | int |  | ID partnera koji preko čijeg linka je ušao kandidat. |  |
| `queue_entry_date` | datetime |  |  |  |
| `queue_is_assigned` | tinyint(1) |  | 0 - Još uvijek čeka, kandidat nije dodijeljen ovom projektu 1 - Kandidat je dodijeljen ovom projektu |  |

## `idk_project_kandidati`

- **Opis**: This table links candidates to their associated projects within the CRM system.
- **Redova**: 207,679 · **Period**: – · **PK**: `pk_id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `pk_id` | int | PRI |  |  |
| `pk_projectid` | int | MUL |  |  |
| `pk_kandidatid` | int | MUL |  |  |

## `idk_projects`

- **Opis**: Stores details about company projects, including project management assignments, scheduling, status, descriptions, and planned hours.
- **Redova**: 2,740 · **Period**: 2018-04-13 → 2026-09-24 (`project_datetime`) · **PK**: `project_id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `project_id` | int | PRI |  |  |
| `project_order` | int |  |  |  |
| `project_name` | varchar(250) |  |  |  |
| `project_desc` | text |  |  |  |
| `project_plannedhours` | varchar(20) |  |  |  |
| `project_companyid` | int |  |  |  |
| `project_employeeid` | int |  |  |  |
| `project_pmanagerid` | int |  |  |  |
| `project_datetime` | datetime |  |  | [PII] |
| `project_status` | int |  |  |  |
| `project_nalogid` | varchar(25) | MUL |  |  |
| `project_datumtermina` | date |  |  |  |
| `project_datumterminado` | date |  |  |  |
| `project_eukandidati` | int |  |  |  |

## `idk_projects_settings`

- **Opis**: Stores configuration settings and status definitions for projects, such as task progress stages.
- **Redova**: 5 · **Period**: – · **PK**: `ps_id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `ps_id` | int | PRI |  |  |
| `ps_name` | varchar(150) |  |  |  |
| `ps_group` | int |  |  |  |

## `idk_projects_tasks`

- **Opis**: Stores individual tasks associated with projects, including task names, descriptions, due dates, sorting order, and assigned employees.
- **Redova**: 169 · **Period**: 2018-04-13 → 2020-02-20 (`pt_datetime`) · **PK**: `pt_id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `pt_id` | int | PRI |  |  |
| `pt_name` | varchar(250) |  |  |  |
| `pt_desc` | text |  |  |  |
| `pt_datetime` | datetime |  |  | [PII] |
| `pt_duedatetime` | datetime |  |  | [PII] |
| `pt_projectid` | int |  |  |  |
| `pt_employeeid` | int |  |  |  |
| `pt_box` | int |  |  |  |
| `pt_sort` | int |  |  |  |

## `idk_sales_reminders`

- **Opis**: Stores sales reminder records, tracking scheduled call dates, types, statuses, and associated employees and clients.
- **Redova**: 1 · **Period**: 2024-07-03 → 2024-07-03 (`sr_doe`) · **PK**: `sr_id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `sr_id` | int | PRI |  |  |
| `sr_employee_id` | int |  |  |  |
| `sr_client_id` | int |  |  |  |
| `sr_doe` | datetime |  |  |  |
| `sr_call_datetime` | datetime |  |  | [PII] |
| `sr_status` | int |  | 1 - active;  2 - finished |  |
| `sr_type` | int |  | 0 - first call;  ... |  |

## `idk_skole`

- **Opis**: Stores a reference list of secondary and higher education schools, including their names in local and German languages along with their education level.
- **Redova**: 368 · **Period**: – · **PK**: `skola_id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `skola_id` | int | PRI |  |  |
| `skola_naziv` | varchar(255) |  |  |  |
| `skola_naziv_de` | varchar(255) |  |  |  |
| `skola_tip_obrazovanja` | varchar(50) |  |  |  |

## `idk_skole_smjerovi`

- **Opis**: Stores information about educational programs or majors offered by schools, including multilingual names, duration, and related profession identifiers.
- **Redova**: 1,848 · **Period**: – · **PK**: `ss_id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `ss_id` | int | PRI |  |  |
| `ss_naziv` | varchar(255) |  |  |  |
| `ss_naziv_de` | varchar(255) |  |  |  |
| `ss_naziv_en` | varchar(255) |  |  |  |
| `ss_skola_id` | int |  |  |  |
| `ss_trajanje_skole` | int |  |  |  |
| `ss_struka_id` | int |  |  |  |

## `idk_struke`

- **Opis**: Lookup table storing profession and trade specialties, containing identifiers alongside their names in Bosnian/Croatian/Serbian and German.
- **Redova**: 7 · **Period**: – · **PK**: `id_struke`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `id_struke` | int | PRI |  |  |
| `naziv_struke` | varchar(255) |  |  |  |
| `naziv_struke_de` | varchar(255) |  |  |  |

