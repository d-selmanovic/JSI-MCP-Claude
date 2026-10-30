# Osjetljive kolone ([TAJNO])

Nikad ne selektovati, ne exportovati, ne prikazivati. Zaštita: MCP-server ih blokira prije izvršenja i MySQL GRANT-ovi MCP-korisnika ih isključuju (column-level).

| Tabela | Kolona |
|---|---|
| `idk_api_clients` | `client_token` |
| `idk_appointment_invite_links` | `send_key` |
| `idk_dak_kandidati` | `hashedtel_idk_dak_kandidat` |
| `idk_dak_kandidati` | `passport_dak_kandidat` |
| `idk_dak_kandidati` | `pin_dak_kandidat` |
| `idk_employees` | `employee_jmbg` |
| `idk_employees` | `employee_key` |
| `idk_employees` | `employee_password` |
| `idk_employees` | `employee_reset_token` |
| `idk_employees` | `employee_rfid` |
| `idk_employees` | `employee_vicipass` |
| `idk_employees` | `employee_viciuser` |
| `idk_jobstep_partners` | `jp_fcmtoken` |
| `idk_jobstep_partners` | `jp_iban` |
| `idk_jobstep_partners` | `jp_mailconfirmation_token` |
| `idk_jobstep_partners` | `jp_password` |
| `idk_jobstep_partners` | `jp_password_reset_code` |
| `idk_jobstep_partners` | `jp_social_token` |
| `idk_jobstep_partners` | `jp_socialid` |
| `idk_jobstep_partners` | `jp_swift` |
| `idk_kandidati` | `kandidat_broj_pasosa` |
| `idk_kandidati` | `kandidat_brojlk` |
| `idk_kandidati` | `kandidat_jmbg` |
| `idk_kandidati` | `kandidat_password` |
| `idk_nd_kandidata` | `broj_licne_karte_nd_kandidata` |
| `idk_nd_kandidata` | `jmbg_nd_kandidata` |
| `idk_nd_ugovori` | `ug_token` |
| `idk_pp_users` | `pu_key` |
| `idk_pp_users` | `pu_password` |
| `users` | `password` |
| `users` | `token` |
