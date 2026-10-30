# Filteri – izvori, pokrivenost, šifre (stanje 2026-10-29)

Svi brojevi izmjereni preko BlazeSQL na `idk_kandidati` (122.006 redova, 117.559 bez arhive).

## Pokrivenost polja (koliko kandidata uopšte ima podatak)

| Filter | Kolona / tabela | Popunjeno | Napomena |
|---|---|---:|---|
| zanimanje – grupa | `kandidat_group` ≠ 7 (Ostalo) | 46.619 (38 %) | 75k je u grupi 'Ostalo' |
| zanimanje – prijava | `kandidat_prijava_na` ≠ 'Ostalo' | 52.998 (43 %) | slobodni tekst, mapiran preko `beruf_mapping` (95 %) |
| zanimanje – iskustvo | `idk_kandidat_radno_iskustvo` | 35.774 kandidata | `kri_pozicija` mapiran 100 % |
| zanimanje – kvalifikacija/smjer | `idk_kandidat_edukacija` | 78.349 kandidata | `ke_naziv_kvalifikacije` mapiran 66 %; `ke_smjer_id` → `idk_skole_smjerovi` 100 % |
| zanimanje – DE profil | `idk_kandidat_de.kde_prijava_na` | 3.332 | njemački tekst, puno tipfelera |
| vozačka | `kandidat_vozacka_kategorija` (+ legacy `kandidat_vozacka_dozvola`) | 51.511 | lista tipa `B,C1,C,CE`; 'Da' = ima, kategorija nepoznata |
| njemački | `idk_kandidat_jezici` (`kj_naziv` 'Njemački') | 67.308 kandidata | samoprocjena po 5 vještina (A1–C2, 'Bez znanja') |
| certifikat jezika | `idk_candidate_verified_languages.cvl_certificate_path` | 367 | `cvl_status = 8` samo 2 reda – nepouzdano; većina prešla u 9 'istekao' |
| obrazovanje vrsta | `idk_kandidat_edukacija.ke_vrsta_obrazovanja` | srednje 126.704 / visoko 5.459 redova | `kandidat_nivo_obrazovanja` gotovo prazan (25) – ne koristiti |
| iskustvo u struci | `kandidat_iskustvo_u_struci` | 21.441 (18 %) | `_trajanje`: 0 nema u zadnjih 5 g., 1 < 1 g., 2–6 godine (tačna skala nije dokumentovana → `min_godina` je približno) |
| država | `kandidat_drzava` | 42.444 (35 %) | slobodni tekst ('BIH', 'Bosna i Hercegovina', 'RS'…); 'RS' je dvosmislen (Republika Srpska vs Srbija) |
| državljanstvo vrsta | `kandidat_drzavljanstvo_vrsta` | 53.652 (44 %) | 'NON-EU državljanin' / 'EU državljanin' + varijante |
| spol | `kandidat_spol` | 15.337 (13 %) | |
| starost | `kandidat_datumrodjenja` | 73.708 (60 %) | |
| kontaktabilni | `kandidat_pogresan_broj`, `kandidat_nedostupan`, `kandidat_mobitel` | mobitel 119.170 | 6.056 pogrešnih brojeva |
| želja regija/grad | `kandidat_zeljena_regija`, `kandidat_zeljeni_grad` | 11 / 0 | praktično neupotrebljivo – nije uključeno |

## Vozačka – EU logika (2006/126/EC)

Kategorija iz filtera je zadovoljena ako kandidat ima bilo koju od sljedećih:

| Traži se | Prihvata |
|---|---|
| AM | AM, A1, A2, A, B, BE, C1, C1E, C, CE, D1, D1E, D, DE |
| A1 | A1, A2, A |
| A2 | A2, A |
| A | A |
| B1 | B1, B, BE, C1, C1E, C, CE, D1, D1E, D, DE |
| B | B, BE, C1, C1E, C, CE, D1, D1E, D, DE |
| BE | BE, C1E, CE, D1E, DE |
| C1 | C1, C1E, C, CE |
| C1E | C1E, CE |
| C | C, CE |
| CE | CE |
| D1 | D1, D1E, D, DE |
| D1E | D1E, DE |
| D | D, DE |
| DE | DE |
| E | E, BE, CE, C1E, DE, D1E |
| F | F |
| G | G |
| M | M |

`strict: true` → samo tačno ta kategorija. Kandidati sa samo 'Da' (bez kategorije) se ne broje kod konkretne kategorije, samo kod `vozacka: true`.

## Država – normalizacija (REGEXP na `kandidat_drzava`)

| Kod | Uzorak |
|---|---|
| BIH | `^(B ?I ?H|R ?BIH|BOS|BIS|BOSNIA|REPUBLIKA SRPSKA|RS ?/? ?BIH|BIH)` |
| SRB | `^(SRB|SERB|R[.]? ?SRBIJA|REPUBLIKA SRBIJA|СРБ|Срб)` |
| HRV | `^(HRV|CROA|KROAT|REPUBLIKA HRVATSKA)` |
| DEU | `^(NJEM|NEM|DEUT|GERM)` |
| MNE | `^(CRNA|MONTEN|CG$)` |
| SVN | `^(SLOVEN)` |
| MKD | `^(MAKED|SJEVERNA MAKED|NORTH MACED)` |
| XKX | `^(KOSOV)` |
| AUT | `^(AUSTR|ÖSTERR|OESTERR)` |

## Šifre statusa

**`kandidat_status`**: 0 Na provjeri; 1 U obradi; 2 Obrađen; 3 Arhiviran; 4 Kontrola; 5 Dopuna; 6 Odbio Messenger; 7 U obradi više od 3 dana; 8 Na dopuni više od 3 dana.

**`kandidat_status_prijave`**: 1 Slobodan; 2 U projektu NR; 3 Casting; 4 Završen; 5 Odbijen; 6 U projektu RZ; 7 Čeka ugovor; 8 Poslan ugovor; 9 Potpisan ugovor; 10 Početak rada; 12 Prikupljanje dokumentacije; 15 Čeka termin; 18 Čeka vizu; 21 Dopuna dokumenata; 24 Odbijena viza; 27 Dobio vizu. Slobodni (`slobodni: true`) = NULL, 0, 1, 2, 5.

## Katalog zanimanja (`scripts/occupations.json`)

| Ključ | Sinonimi | berufsgruppe | grupe (kg_id) | ključne riječi | smjer | široko dodaje |
|---|---|---|---|---|---|---|
| `elektriker` | elektriker, elektricar, električar, electrician, elektroinstalater, elektroinstallateur, elektroniker | elektriker | 38, 39, 41 | elektri, elektroinstal, elektroniker | elektri, elektroinstal, elektromonter | hilfselektriker, elektrotechniker, elektromechaniker, autoelektriker, ingenieur_elektro |
| `elektrotehnicar` | elektrotehnicar, elektrotehničar, elektrotechniker, electrical technician | elektrotechniker | 73 | elektrotehni, elektrotechni | elektrotehni | elektriker, ingenieur_elektro, elektromechaniker |
| `kfz_mechaniker` | automehanicar, automehaničar, kfz-mechaniker, kfz mechaniker, automechaniker, car mechanic, mehanicar | kfz_mechaniker | 22 | automehani, auto mehani, kfz, automechani | automehani, mehaničar motornih, mehanicar motornih, autoelektri | mechaniker, autoelektriker, karosseriebauer, mechatroniker, reifenmonteuer |
| `lkw_fahrer` | vozac, vozač, lkw-fahrer, lkw fahrer, berufskraftfahrer, kraftfahrer, truck driver, driver, fahrer | lkw_fahrer | 50 | vozac, vozač, kraftfahrer, lkw, kamion | vozač, vozac | kurier, taxifahrer, staplerfahrer, baggerfahrer |
| `solar_monteur` | monter solarnih panela, solarmonteur, solar monteur, pv monteur, solar installer, solar | monteur | 68 | solar, fotonapon, photovolt, pv-anlag, pv anlag | – | elektriker, hilfselektriker, dachdecker |
| `telekom_monteur` | internet monter, montazer kablovske opreme, montažer kablovske opreme, telekom monteur, kabelmonteur, glasfaser, telecom installer | telekom_monteur | 25, 64 | kablov, optičk, optick, glasfaser, internet monter, telekom | telekomunikac, ptt | servicetechniker, telecom_ingenieur |
| `servicetechniker` | servisni tehnicar, servisni tehničar, servicetechniker, service technician, serviser | servicetechniker | 46 | servis, servicetechn | – | maschinenwartung, elektromechaniker |
| `klima_monteur` | ac montazer, ac montažer, klima monter, klimamonteur, kältetechniker, hvac | klima_monteur | 82 | klima, hvac, kälte, rashlad, frigo | klima, rashlad, frigo | installateur |
| `installateur` | instalater, vodoinstalater, installateur, anlagenmechaniker, shk, plumber | installateur | – | instalater, vodoinstal, installateur, sanitär, grijanj | instalater, vodoinstal | klima_monteur |
| `autoglas` | autostaklar, autoglas tehnicar, autoglas, carglass, kfz-glaser | glaserei | 71, 79 | autostakl, autoglas, carglass, vjetrobran | – | kfz_mechaniker |
| `krankenpfleger` | medicinski tehnicar, medicinski tehničar, medicinska sestra, krankenpfleger, pflegefachkraft, nurse, pflege | krankenpfleger | 2, 23, 48 | medicinsk, sestra, krankenpfleg, pflegefach, njegovatelj | medicinsk, zdravstv, sestra | hebamme, physiotherapeut, pharmazeutisch, laborant |
| `pflegehelfer` | pomocnik njegovatelja, pomoćnik njegovatelja, njegovatelj, pflegehelfer, caregiver, altenpflegehelfer | krankenpfleger | 3 | njegovatelj, pflegehelf, gerontodomaćic, gerontodomacic | njegovatelj, gerontodom | sozialarbeiter |
| `physiotherapeut` | fizioterapeut, physiotherapeut, physiotherapist | physiotherapeut | 45 | fizioterap, physiotherap | fizioterap | – |
| `bauarbeiter` | gradjevinski radnik, građevinski radnik, bauarbeiter, bauhelfer, construction worker | bauarbeiter | 59 | građevin, gradjevin, gradevin, bauarbeit, bauhelf | građevin, gradjevin, gradevin | maurer, armierer, trockenbauer, fassadenbauer, fliesenleger, dachdecker, zimmermann, hilfsarbeiter |
| `baumaschinenfuehrer` | rukovodilac gradjevinskih masina, rukovaoc gradjevinskih masina, bagerista, baggerfahrer, baumaschinenführer, excavator operator | baggerfahrer | 83 | bager, rovokop, baumaschin, građevinskih maš, gradjevinskih mas | rukovalac, rukovaoc | maschinenfuehrer, staplerfahrer |
| `staplerfahrer` | viljuskarista, viljuškarista, staplerfahrer, gabelstaplerfahrer, forklift | staplerfahrer | 34 | viljušk, viljusk, stapler | – | lagerist |
| `lagerist` | skladistar, skladištar, lagerist, lagermitarbeiter, warehouse | lagerist | 37 | skladišt, skladist, magacin, lager | – | staplerfahrer, wareneingang, logistiker |
| `parkettleger` | parketar, parkettleger, bodenleger | parkettleger | 36 | parket, bodenleg | – | fliesenleger, schreiner |
| `schweisser` | varioc, zavarivac, zavarivač, schweißer, schweisser, welder | schweisser | – | varioc, zavariv, schweiß, schweiss | zavariv, varioc | schlosser, metallbau_monteur |
| `cnc_operater` | cnc operater, cnc, cnc-fräser, cnc operator | cnc_operater | – | cnc | cnc | maschinenbediener, werkzeugmacher |
| `baecker` | pekar, bäcker, baecker, baker | baecker | 33 | pekar, bäck | pekar | konditor |
| `koch` | kuhar, kuvar, koch, cook, chef | koch | 81 | kuhar, kuvar, koch | kuhar, kuvar | kuechenhilfe, gastroberufe |
| `admin_buero` | administrativni radnik, administracija, bürokaufmann, verwaltung, office | admin_buero | 10, 43, 51, 54 | administrativ, administracij | administrat, ekonomsk | buchhalter, project_assistant |
| `call_agent` | call centar agent, call center, operater za primanje poziva, kundenservice, call agent | call_agent, kundenservice | 1, 13, 19, 21, 60 | call cent, call centar, pozivni | – | – |
| `it` | it tehnicar, it techniker, programer, programmierer, software developer, it support, it | it_support, it_administrator, programmierer, it_ingenieur | 14, 31, 62 | programer, informati, softver, software | informati, računar, racunar | daten_operater |
| `handwerker` | majstor za sve, majstor, handwerker, hausmeister | handwerker | 40, 47 | majstor za sve, domar, hausmeister | – | hilfsarbeiter |
| `pvc_monteur` | montazer pvc, montažer pvc, pvc monter, fenstermonteur | pvc_monteur | 53 | pvc, alu stolar, fenstermont | – | moebelmonteur, metallbau_monteur |

Novo zanimanje dodati u `occupations.json` (+ test). Za zanimanja izvan kataloga radi pretraga po ključnoj riječi; preciznije je proslijediti `{"berufsgruppen": [...]}` iz liste ispod.

## Sve `berufsgruppe_id` vrijednosti u `beruf_mapping` (194)

`admin_buero`, `akquisiteur`, `allgemeintechniker`, `anaesthesist`, `animator`, `architekt`, `archiv`, `armierer`, `arzt`, `au_pair`, `autoelektriker`, `autolackierer`, `autovermietung`, `autowaesche`, `baecker`, `baggerfahrer`, `bankkaufmann`, `bauarbeiter`, `bautechniker`, `berater`, `berater_allgemein`, `bergmann`, `bibliothekar`, `broker`, `buchhalter`, `call_agent`, `cnc_operater`, `dachdecker`, `daten_operater`, `defektologe`, `demineur`, `disponent`, `druckerei`, `dtp_operator`, `elektriker`, `elektromechaniker`, `elektrotechniker`, `erzieher`, `fahrlehrer`, `fassadenbauer`, `feuerwehrmann`, `filialleiter`, `fliesenleger`, `flugbegleiter`, `foerster`, `forscher`, `fotograf`, `friseur`, `fussballer`, `gaertner`, `galvaniseur`, `gastroberufe`, `gastronomie`, `geodaet`, `geschaeftsfuehrer`, `glaserei`, `gluecksspiel`, `grafikdesigner`, `handwerker`, `hebamme`, `hilfsarbeiter`, `hilfselektriker`, `imam`, `immobilienmakler`, `ingenieur`, `ingenieur_bau`, `ingenieur_elektro`, `ingenieur_maschinenbau`, `inkasso`, `installateur`, `instruktor`, `it_administrator`, `it_ingenieur`, `it_support`, `journalist`, `jurist`, `kameramann`, `karosseriebauer`, `kassierer`, `kein_beruf`, `kfz_mechaniker`, `klima_monteur`, `koch`, `kommerzialist`, `kommunal`, `konditor`, `kontrolleur`, `kosmetiker`, `krankenpfleger`, `kuechenhilfe`, `kundenservice`, `kurier`, `laborant`, `lagerist`, `landwirt`, `lehrer`, `lift_monteur`, `lkw_fahrer`, `logistiker`, `logopaede`, `lokfuehrer`, `maler`, `manager`, `marketing`, `maschinenbauer_fach`, `maschinenbediener`, `maschinenfuehrer`, `maschinentechniker`, `maschinenwartung`, `matrose`, `maurer`, `mechaniker`, `mechatroniker`, `mehrfach`, `merchandiser`, `messebauer`, `metallbau_monteur`, `metallschleifer`, `metzger`, `moebelmonteur`, `moebelproduktion`, `monteur`, `musiker`, `naeher`, `oekonom`, `optiker`, `ordner`, `parkettleger`, `pharmazeutisch`, `physiotherapeut`, `polizist`, `polsterer`, `portier`, `postbote`, `praktikant`, `produktionshelfer`, `programmierer`, `project_assistant`, `projektleiter`, `promoter`, `psychologe`, `pvc_monteur`, `qualitaetskontrolle`, `rangierer`, `recruiter`, `redakteur`, `referent_einkauf`, `reifenmonteuer`, `reinigungskraft`, `reiseleiter`, `rettungsschwimmer`, `rezeption`, `saegewerk`, `schaffner`, `schichtleiter`, `schlosser`, `schmied`, `schreiner`, `schuelerpraktikum`, `schuhmacher`, `schweisser`, `security`, `servicetechniker`, `sicherheitstechniker`, `soldat`, `sonstiges`, `sozialarbeiter`, `spengler`, `staplerfahrer`, `steinmetz`, `tankstellenmitarbeiter`, `taxifahrer`, `technik_vorbereitung`, `technologe`, `telecom_ingenieur`, `telekom_monteur`, `tontechniker`, `trainer`, `trgovac`, `trockenbauer`, `uebersetzer`, `unklar`, `unternehmer`, `versicherung`, `veterinaer`, `wareneingang`, `werkzeugmacher`, `wettannahme`, `zahnarzt`, `zahntechniker`, `zimmermaedchen`, `zimmermann`, `zollbeamter`, `zolldeklarant`

`mehrfach` (6.748 tekstova) = više zanimanja u jednom tekstu; `unklar`, `kein_beruf`, `sonstiges` = nije zanimanje. Za njih pomažu `keywords` iz kataloga.

## Poznate slabosti podataka

- Zanimanje 'samo prijava' znači da se kandidat prijavio na oglas za to zanimanje – ne nužno da ima kvalifikaciju. Koristiti `izlaz: izvori` i `broj_izvora` (sortiranje 'relevantnost').
- Nivoi jezika su samoprocjena (npr. 20-godišnjaci s 'C2'); za provjereno znanje koristiti `certifikat`.
- Kandidatska aktivnost u bazi uglavnom prestaje u februaru 2026.
- `kde_vozacka` (DE profil, 3.332) je slobodni tekst i nije uključen u filter vozačke.
