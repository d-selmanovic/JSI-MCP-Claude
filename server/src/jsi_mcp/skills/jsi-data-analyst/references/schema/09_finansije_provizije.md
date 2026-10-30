# Finansije, fakture, provizije

Tabele: 6. Redovi i periodi stanje 2026-10-29.

## `idk_kategorije_provizija`

- **Opis**: Stores definitions, types, amounts, and associated department or employee configurations for commission categories.
- **Redova**: 17 · **Period**: – · **PK**: `kp_id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `kp_id` | int | PRI |  |  |
| `kp_naziv` | varchar(100) |  |  |  |
| `kp_iznos` | double |  |  |  |
| `kp_iznos_rs` | double |  |  |  |
| `kp_faktorizacija` | int |  | 0 - ne, 1 -da |  |
| `kp_tip_id` | int |  |  |  |
| `kp_status` | int |  | 1-aktivan, 2-arhiviran |  |
| `kp_odjeli` | text |  | ako je NULL nisu bitni odjeli |  |
| `kp_vrsta` | int |  | 1 - samo agent, 2 - vise zaposlenika po odjelu, 3 - on top, 4 - vise zaposlenika bez obzira na odjel, 5 - on top za agente, 6 -on top specijalni, ide po uplati |  |
| `kp_employee_id` | int |  | samo ako je ontop onda treba id zaposlenika |  |

## `idk_obracuni`

- **Opis**: Stores commission calculation and payout records for employees tied to proforma invoices, detailing amounts across multiple currencies, installment information, and payment statuses.
- **Redova**: 168,233 · **Period**: 2021-01-04 → 2024-08-16 (`vrijeme_kreiranja`) · **PK**: `id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `id` | int | PRI |  |  |
| `employee_id` | int |  |  |  |
| `predracun_id` | int |  |  |  |
| `status_predracuna` | int |  | 0 - neuplacen, 1 - uplacen |  |
| `status_obracuna` | int |  | 0 - neisplacen, 1 - isplacen, 2 - arhiviran |  |
| `valuta` | varchar(10) |  | BAM ili RSD |  |
| `rata` | int |  |  |  |
| `broj_rata` | int |  |  |  |
| `vrijednost_tipa` | double |  |  |  |
| `vrijednost_kategorije` | double |  |  |  |
| `iznos_obracuna_bam` | double |  |  |  |
| `iznos_obracuna_rsd` | double |  |  |  |
| `iznos_obracuna_eur` | float |  |  |  |
| `vrijeme_kreiranja` | datetime |  |  |  |
| `vrijeme_uplate` | datetime |  |  |  |
| `vrijeme_isplate` | datetime |  |  |  |
| `tip_provizije` | int |  | 1-normal, 2-ontop1, 3-provizija od tima, 4-ontop72h, 5-ontop48h, 99-za inkaso agente, 98-normal minus inkaso |  |
| `kategorija_provizije` | int |  | sluzi da se oznaci kategorija provizija, kako bi u "Normal" tipu znali da se radi o agentu, a ne o dijeljenim provizijama, 1-agent, 2-inkaso_agent |  |

## `idk_ostatci_obracuna`

- **Opis**: Stores records of employee payroll calculation balances and remaining amounts, including currency, calculation period, and status.
- **Redova**: 2,783 · **Period**: 2021-02-10 → 2024-04-09 (`oo_vrijeme_kreiranja`) · **PK**: `oo_id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `oo_id` | int | PRI |  |  |
| `oo_employee_id` | int |  |  |  |
| `oo_valuta` | varchar(10) |  |  |  |
| `oo_iznos` | double |  |  |  |
| `oo_vrijeme_kreiranja` | datetime |  |  |  |
| `oo_period_od` | datetime |  |  |  |
| `oo_period_do` | datetime |  |  |  |
| `oo_status` | int |  | 0-neisplacen,1-isplacen |  |

## `idk_predracuni`

- **Opis**: Stores proforma invoice records for candidates, including multi-currency amounts, payment and cancellation statuses, associated employees, and related document files.
- **Redova**: 10,701 · **Period**: 2020-09-02 → 2024-11-13 (`pr_datum_kreiranja`) · **PK**: `pr_id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `pr_id` | int | PRI |  |  |
| `pr_naplata_preko` | int |  | Aktivna firma za naplate: 1 - CH; 0 - stari nacin: BiH i SRB zasebno |  |
| `pr_kandidat_id` | int | MUL |  |  |
| `pr_broj_predracuna` | varchar(50) |  | DIPL(drz B/S)-(broj: 1,2,3..)-(godina 20,21...) |  |
| `pr_datum_kreiranja` | timestamp |  |  |  |
| `pr_zaposlenik` | int |  |  |  |
| `pr_vrsta_predracuna` | int |  | 1-DIPL... |  |
| `pr_rata` | int |  | Broj rate: 1,2,3,4,5 |  |
| `pr_status` | int |  | 1-aktivan; 0-arhiviran(u slucaju da kandidat odustane nakon slanja predracuna a prije uplate prve rate); 2-uplacen; 3,4,5: inkaso 1,2,3 |  |
| `pr_domaca_valuta` | varchar(50) |  | valuta u kojoj ce se iznos ispisivati na predracunu: BAM, RSD |  |
| `pr_vrijednost_BAM` | double |  |  |  |
| `pr_vrijednost_RSD` | double |  |  |  |
| `pr_vrijednost_EUR` | double |  |  |  |
| `pr_file` | varchar(100) |  | naziv filea: YYMMDDHHIISS(brojpr)DIPL(drzava) |  |
| `pr_file_de` | varchar(100) |  |  |  |
| `pr_uplaceno` | int |  | 0-nije uplaceno, 1-uplaceno |  |
| `pr_datum_uplate` | date |  |  |  |
| `pr_opis` | varchar(255) |  |  |  |
| `pr_stornirano` | int |  | 0-ne, 1-da |  |
| `pr_datum_storniranja` | datetime |  |  |  |
| `pr_vrsta_placanja` | int |  | gotovniski, virman, kartica...??? |  |
| `pr_izdan_racun` | int |  | 0 nije, 1 jeste |  |
| `pr_stari_ink_status` | int |  | 3-IK1, 4-IK2, 5-IK3; inkaso status starog predracuna kojeg je ovaj zamijenio (samo preko inkaso odjela) |  |
| `pr_inkaso_agent` | int |  |  |  |

## `idk_racuni`

- **Opis**: Stores invoice records, including amounts across multiple currencies, payment and cancellation statuses, associated candidates, and links to generated invoice files.
- **Redova**: 4,509 · **Period**: 2020-12-10 → 2024-10-24 (`racun_datum_kreiranja`) · **PK**: `racun_id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `racun_id` | int | PRI |  |  |
| `predracun_id` | varchar(11) |  |  |  |
| `racun_broj` | varchar(50) |  |  |  |
| `racun_kandidat_id` | int |  |  |  |
| `racun_datum_kreiranja` | timestamp |  |  |  |
| `racun_vrsta_racuna` | int |  | 1 - DIPL... |  |
| `racun_status` | int |  |  |  |
| `racun_domaca_valuta` | varchar(50) |  |  |  |
| `racun_vrijednost_BAM` | double |  |  |  |
| `racun_vrijednost_RSD` | double |  |  |  |
| `racun_vrijednost_EUR` | double |  |  |  |
| `racun_file` | varchar(255) |  |  |  |
| `racun_file_de` | varchar(255) |  |  |  |
| `racun_uplaceno` | int |  | 0-nije uplaceno, 1-uplaceno |  |
| `racun_datum_uplate` | date |  |  |  |
| `racun_opis` | text |  |  |  |
| `racun_stornirano` | int |  |  |  |
| `racun_datum_storniranja` | datetime |  |  |  |
| `racun_razlog_storniranja` | int |  | Unosi se vrijednost razloga koja je postavljena u modalu za storniranje računa sa label "Odaberite razlog storniranja racuna" |  |
| `racun_komentar_storniranja` | text |  | Pored izbora razloga - potrebno da uposlenik navede kratki komentar zbog kojeg se stornacija izvršava |  |
| `racun_bf` | varchar(25) |  |  |  |

## `idk_tipovi_provizija`

- **Opis**: Stores definitions of commission types, including their names, standard amounts, team associations, and status flags.
- **Redova**: 11 · **Period**: – · **PK**: `tp_id`

| Kolona | Tip | Ključ | Komentar u bazi | Oznaka |
|---|---|---|---|---|
| `tp_id` | int | PRI |  |  |
| `tp_naziv` | varchar(100) |  |  |  |
| `tp_iznos` | double |  |  |  |
| `tp_iznos_rs` | double |  |  |  |
| `tp_tip` | int |  | 1- normal, 2 - on top |  |
| `tp_tim` | int |  | id tima, a ako je 0 onda vrijedi za sve timove |  |
| `tp_status` | int |  | 1-aktivan, 2-arhiviran |  |

