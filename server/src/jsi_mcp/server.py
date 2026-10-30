"""JSI MCP server – Streamable HTTP on /mcp, health on /health, WorkOS AuthKit resource server."""

import functools
import inspect
import json
import logging
import sys
import time
from typing import Annotated, Any, Literal

import uvicorn
from mcp.server.auth.settings import AuthSettings
from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp.types import ToolAnnotations
from pydantic import Field
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from . import config as config_mod
from . import db, registry, tools_read, writes
from .auth import WorkOSTokenVerifier, current_principal
from .permissions import TOOL_PERMISSIONS, PermissionDenied, require
from .sensitive import SensitiveColumnError

VERSION = "0.1.0"
log = logging.getLogger("jsi_mcp")
calls = logging.getLogger("jsi_mcp.calls")

INSTRUCTIONS = (
    "JSI CRM (JobStep) – feste Tools statt SQL. Kandidaten suchen/zählen: search_candidates (Standard izlaz='broj'; "
    "zuerst izlaz='izvori' für die Beweisstärke). Gültige Werte: filter_options. Ein Kandidat: candidate_profile. "
    "Kennzahlen: kpis. Aufträge: orders_overview. Pipeline: pipeline_history. Schreiben: immer zuerst record_preview / "
    "dry_run=true, dann record_write bzw. set_application_status mit dry_run=false und preview_hash. "
    "Antworten für JSI auf Bosnisch. Personendaten nur auf ausdrücklichen Wunsch (Permission jsi:kandidati:pii). "
    "/ Fiksni alati umjesto SQL-a; lični podaci samo na izričit zahtjev."
)

RO = ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=False)
RW = ToolAnnotations(read_only_hint=False, destructive_hint=False, idempotent_hint=False, open_world_hint=False)


def _count_rows(result: Any) -> int | None:
    if isinstance(result, dict):
        if "broj_redova" in result:
            return result["broj_redova"]
        if "rezultat" in result and isinstance(result["rezultat"], list):
            return len(result["rezultat"])
    return None


def tool_wrapper(cfg: config_mod.Config, name: str):
    """Permission check, error mapping and one log line per call (sub, tool, duration, rows – no contents)."""

    def deco(fn):
        @functools.wraps(fn)
        async def wrapper(*args, **kwargs):
            t0 = time.monotonic()
            p = current_principal(cfg)
            status, rows = "ok", None
            try:
                require(p, TOOL_PERMISSIONS[name])
                import anyio

                result = await anyio.to_thread.run_sync(functools.partial(fn, cfg, p, *args, **kwargs))
                rows = _count_rows(result)
                return result
            except PermissionDenied as e:
                status = "denied"
                raise ToolError(str(e)) from None
            except (tools_read.InputError, writes.WriteError) as e:
                status = "input_error" if isinstance(e, tools_read.InputError) else type(e).__name__
                raise ToolError(f"{e}") from None
            except (db.DbNotConfigured, db.DbError) as e:
                status = "db_error"
                raise ToolError(str(e)) from None
            except SensitiveColumnError as e:
                status = "blocked_sensitive"
                raise ToolError(str(e)) from None
            except PermissionError as e:
                status = "denied"
                raise ToolError(str(e)) from None
            except Exception as e:
                status = "error:" + type(e).__name__
                log.exception("tool %s failed", name)
                raise ToolError(f"Interner Fehler / Interna greška ({type(e).__name__}).") from None
            finally:
                calls.info(json.dumps({"event": "tool_call", "sub": p.sub, "tool": name, "status": status,
                                       "duration_ms": round((time.monotonic() - t0) * 1000), "rows": rows}))

        # hide (cfg, p) from the schema: signature without the first two params
        sig = inspect.signature(fn)
        params = list(sig.parameters.values())[2:]
        wrapper.__signature__ = sig.replace(parameters=params)
        wrapper.__annotations__ = {k: v for k, v in fn.__annotations__.items() if k not in ("cfg", "p")}
        return wrapper

    return deco


# ---------------------------------------------------------------- tool definitions (schemas live in the signatures)
JsonObj = dict[str, Any]


def t_whoami(cfg, p) -> dict:
    return {"sub": p.sub, "client_id": p.client_id, "org_id": p.org_id, "permissions": sorted(p.permissions),
            "db_target": cfg.db_target, "db_konfiguriert": cfg.db_ready(), "schreiben_aktiv": cfg.writes_allowed,
            "konfigurationsfehler": cfg.errors, "version": VERSION}


def t_search_candidates(
    cfg, p,
    zanimanje: Annotated[str | list[str] | JsonObj | None, Field(description="Beruf/Zanimanje: 'Elektriker' | ['elektriker','elektrotehnicar'] | {'name':'elektriker','broad':true,'sources':[...]} | {'keywords':[...]} | {'berufsgruppen':[...]}")] = None,
    vozacka: Annotated[str | list[str] | bool | JsonObj | None, Field(description="Führerschein/Vozačka: 'C' | ['C','CE'] | {'kategorije':['C'],'strict':true,'mode':'any|all'} | true (bilo koja). EU-Regel: höhere Klasse erfüllt niedrigere.")] = None,
    jezik: Annotated[JsonObj | None, Field(description="Sprache/Jezik: {'jezik':'njemacki|engleski|talijanski|spanjolski|francuski|ruski|arapski|turski','min_nivo':'A1..C2','vjestina':'govorna_interakcija|...|bilo_koja','certifikat':true|'vazeci'}")] = None,
    jezici: Annotated[list[JsonObj] | None, Field(description="Mehrere Sprachen (Liste wie 'jezik').")] = None,
    obrazovanje: Annotated[JsonObj | None, Field(description="Ausbildung: {'vrsta':'srednje|visoko|ostalo','smjer':'elektro'}")] = None,
    iskustvo_u_struci: Annotated[bool | JsonObj | None, Field(description="Berufserfahrung: true | {'min_godina':1..6} (nur ~18 % befüllt)")] = None,
    drzava: Annotated[str | list[str] | None, Field(description="Wohnland: BIH, SRB, HRV, DEU, MNE, SVN, MKD, XKX, AUT")] = None,
    drzavljanstvo: Annotated[str | list[str] | None, Field(description="Staatsangehörigkeit: 'EU' | 'NON-EU' | Land BIH, SRB, HRV, MNE, MKD, SVN, BGR, HUN, DEU, ITA, AUT, XKX, ALB (Land nur ~14 % befüllt)")] = None,
    spol: Annotated[Literal["m", "z"] | None, Field(description="Geschlecht m/z (nur ~13 % befüllt)")] = None,
    starost: Annotated[JsonObj | None, Field(description="Alter: {'od':20,'do':45}")] = None,
    registriran: Annotated[JsonObj | None, Field(description="Registrierung: {'od':'YYYY-MM-DD','do':'YYYY-MM-DD'}")] = None,
    status_prijave: Annotated[list[int] | None, Field(description="Pipeline-Status-Codes (siehe filter_options)")] = None,
    slobodni: Annotated[bool | None, Field(description="Nur nicht reservierte Kandidaten (Status NULL/0/1/2/5)")] = None,
    kandidat_status: Annotated[list[int] | None, Field(description="Bearbeitungsstatus-Codes")] = None,
    ukljuci_arhivu: Annotated[bool | None, Field(description="Archivierte einschließen (Standard: nein)")] = None,
    kontaktabilni: Annotated[bool | None, Field(description="Ohne falsche Nummer / nicht erreichbar / ohne Mobil")] = None,
    nacin_odlaska: Annotated[list[int] | None, Field(description="0 Fachkraft/EU, 2 Westbalkanregelung")] = None,
    nalog_id: Annotated[list[int] | None, Field(description="Zugeordneter Auftrag")] = None,
    projekt_id: Annotated[list[int] | None, Field(description="Projektmitglied")] = None,
    nostrifikacija: Annotated[bool | Literal["potpuno", "djelimicno", "status_2", "bilo_koje"] | None, Field(description="Nostrifikation: true/'potpuno' = voll anerkannt, 'djelimicno' = teilweise, 'bilo_koje' = Bescheid vorhanden")] = None,
    izlaz: Annotated[Literal["broj", "izvori", "lista", "id"], Field(description="Ausgabe: broj=Anzahl, izvori=Anzahl je Berufsquelle, lista=Liste, id=nur IDs")] = "broj",
    limit: Annotated[int | None, Field(ge=1, le=5000, description="Zeilen für lista/id (Standard 200, max 5000)")] = None,
    pii: Annotated[bool, Field(description="Name/Telefon/E-Mail in 'lista' – nur auf ausdrücklichen Wunsch, Permission jsi:kandidati:pii")] = False,
    sortiraj: Annotated[Literal["relevantnost", "novi"] | None, Field(description="Sortierung der Liste")] = None,
    nalog_izvor: Annotated[Literal["kandidat", "projekt", "oba"] | None, Field(description="nalog_id gilt für: kandidat=aktuell zugeordnet (Standard) | projekt=Mitglied eines Projekts des Auftrags | oba=beides")] = None,
    porijeklo: Annotated[list[int] | None, Field(description="Herkunft/Kanal kandidat_porijeklo: 0 alt/CRM, 1 DIPL, 2 DAK, 3 Partner-Empfehlung, 4 svezavize-Web, 5 JobStep-Web (6–8 undokumentiert)")] = None,
    messenger_status: Annotated[list[int] | None, Field(description="Messenger 0–6 (2 eingeloggt, 3 abgelehnt …), siehe filter_options")] = None,
    bracno_stanje: Annotated[list[int] | None, Field(description="Familienstand 0 unbekannt, 1 ledig, 2 verheiratet, 3 verwitwet, 4 geschieden (97 % = 0)")] = None,
    viza: Annotated[Literal["ima", "nema", "dobio", "odbijena", "dopuna"] | None, Field(description="Visum: ima/nema (kandidat_viza), dobio = je Status 27, odbijena/dopuna = Partnerportal")] = None,
    termin_za_vizu: Annotated[bool | None, Field(description="Visatermin vorhanden (true) / nicht (false); nur ~2 % befüllt")] = None,
    casting: Annotated[JsonObj | None, Field(description="Casting/Task-Force-Reservierung: {'status':[1 Došao,2 Nije došao,3 Odustao],'nalog_id':[..],'od':'YYYY-MM-DD','do':..}")] = None,
    intervju: Annotated[JsonObj | None, Field(description="Interview Partnerportal: {'preporuka':['hire'|'reject'|'not_sure'],'nalog_id':[..],'aktivan':bool}")] = None,
    odbijen: Annotated[JsonObj | None, Field(description="Absage: {'razlog_id':[..],'odbio':'kandidat'|'poslodavac','nalog_id':[..]} (Gründe: filter_options razlozi_odbijanja)")] = None,
    dokument_status: Annotated[list[int] | None, Field(description="Dokumentstatus Partnerportal (idk_pp_documents_statuses: 3 Uploadan … 18 Spreman, 24 Odbijen, 27 Arhiviran)")] = None,
    makler: Annotated[bool | list[int] | None, Field(description="Über Makler/Partner (idk_jobstep_partners): true = irgendeiner, [ids] = bestimmte")] = None,
    pp_partner_id: Annotated[list[int] | None, Field(description="Arbeitgeber-Partner im Partnerportal (idk_pp_partners.ppa_id)")] = None,
    tf_agent_id: Annotated[list[int] | None, Field(description="Reserviert für Task-Force-Agent (employee_id)")] = None,
    tf_status: Annotated[bool | list[int] | None, Field(description="Aktiver Task-Force-Status: true = irgendeiner, [tfs_id] (filter_options tf_status)")] = None,
    vjestina: Annotated[str | list[str] | None, Field(description="Fähigkeit (Freitext, z. B. 'Office', 'Schweißen')")] = None,
    grad: Annotated[str | None, Field(description="Wohnort (Freitext, min. 3 Zeichen; ~35 % befüllt)")] = None,
    aktivan: Annotated[JsonObj | None, Field(description="Aktivität = Statuswechsel im Zeitraum {'od':'YYYY-MM-DD','do':..}")] = None,
    status_historija: Annotated[JsonObj | None, Field(description="War jemals im Status: {'status':[9],'od':..,'do':..,'nalog_id':[..],'projekt_id':[..]}")] = None,
    faza_min: Annotated[int | None, Field(ge=1, le=15, description="Aktueller Status mindestens Phase (redoslijed_statusa), 7 = Vertrag unterschrieben oder weiter")] = None,
    ima_biljeske: Annotated[bool | None, Field(description="Hat Notizen (idk_notes)")] = None,
    ima_dokumente: Annotated[bool | None, Field(description="Hat Dokumente (CRM oder Partnerportal)")] = None,
    firma_id: Annotated[list[int] | None, Field(description="Firma: angestellt bei oder Mitglied eines Projekts der Firma (company_id)")] = None,
    dipl: Annotated[JsonObj | bool | None, Field(description="DIPL-Verknüpfung: true | {'povezan':bool,'status':[status_nd_kandidata]} – status braucht jsi:dipl:read")] = None,
    cv_de: Annotated[bool | None, Field(description="Deutscher Lebenslauf vorhanden")] = None,
    profil_de: Annotated[bool | None, Field(description="Deutsches Profil vorhanden")] = None,
    ugovor: Annotated[Literal["potpisan", "postoji"] | None, Field(description="Vertrag hochgeladen (postoji) / unterschrieben (potpisan)")] = None,
    pocetak_rada_potvrden: Annotated[bool | None, Field(description="Arbeitsbeginn bestätigt")] = None,
    grupa_id: Annotated[list[int] | None, Field(description="Bewerbungsgruppe kg_id (filter_options grupe)")] = None,
    radno_iskustvo: Annotated[JsonObj | None, Field(description="Berufserfahrung aus CV: {'min_godina':2,'zanimanje':'elektriker'} (Summe der Perioden)")] = None,
    glossa: Annotated[list[int] | None, Field(description="Glossa-Lead 0–3")] = None,
    include_sql: Annotated[bool, Field(description="Generiertes SQL mitliefern (Transparenz)")] = False,
) -> dict:
    spec = dict(zanimanje=zanimanje, vozacka=vozacka, jezik=jezik, jezici=jezici, obrazovanje=obrazovanje,
                iskustvo_u_struci=iskustvo_u_struci, drzava=drzava, drzavljanstvo=drzavljanstvo, spol=spol, starost=starost,
                registriran=registriran, status_prijave=status_prijave, slobodni=slobodni, kandidat_status=kandidat_status,
                ukljuci_arhivu=ukljuci_arhivu, kontaktabilni=kontaktabilni, nacin_odlaska=nacin_odlaska, nalog_id=nalog_id,
                projekt_id=projekt_id, nostrifikacija=nostrifikacija, izlaz=izlaz, limit=limit, pii=pii or None, sortiraj=sortiraj,
                nalog_izvor=nalog_izvor, porijeklo=porijeklo, messenger_status=messenger_status, bracno_stanje=bracno_stanje,
                viza=viza, termin_za_vizu=termin_za_vizu, casting=casting, intervju=intervju, odbijen=odbijen,
                dokument_status=dokument_status, makler=makler, pp_partner_id=pp_partner_id, tf_agent_id=tf_agent_id,
                tf_status=tf_status, vjestina=vjestina, grad=grad, aktivan=aktivan, status_historija=status_historija,
                faza_min=faza_min, ima_biljeske=ima_biljeske, ima_dokumente=ima_dokumente, firma_id=firma_id, dipl=dipl,
                cv_de=cv_de, profil_de=profil_de, ugovor=ugovor, pocetak_rada_potvrden=pocetak_rada_potvrden,
                grupa_id=grupa_id, radno_iskustvo=radno_iskustvo, glossa=glossa)
    return tools_read.search_candidates(cfg, p, spec, include_sql=include_sql)


def t_filter_options(cfg, p, section: Annotated[str | None, Field(description="Optional ein Abschnitt, z. B. 'zanimanje', 'vozacka', 'status_prijave', 'berufsgruppen', 'grupe'")] = None) -> dict:
    out = tools_read.filter_options(cfg, p, section)
    if not section:
        out["schreib_register"] = registry.describe()
    return out


def t_candidate_profile(cfg, p, kandidat_id: Annotated[int, Field(gt=0, description="idk_kandidati.kandidat_id")],
                        pii: Annotated[bool, Field(description="Name/Telefon/E-Mail/Notiztexte – Permission jsi:kandidati:pii")] = False) -> dict:
    return tools_read.candidate_profile(cfg, p, kandidat_id, pii)


def t_kpis(cfg, p,
           bereich: Annotated[Literal["vermittlungen", "neue_kandidaten", "pipeline_bestand", "umsatz", "task_force", "casting", "dipl_funnel"], Field(description="Bereich; umsatz braucht jsi:finansije:read, dipl_funnel jsi:dipl:read")],
           od: Annotated[str | None, Field(description="von (inkl.) YYYY-MM-DD")] = None,
           do: Annotated[str | None, Field(description="bis (exkl.) YYYY-MM-DD")] = None,
           gruppierung: Annotated[Literal["jahr", "monat", "tag"], Field(description="Periode")] = "jahr",
           limit: Annotated[int | None, Field(ge=1, le=5000)] = None) -> dict:
    return tools_read.kpis(cfg, p, bereich, od, do, gruppierung, limit)


def t_orders_overview(cfg, p,
                      nalog_status: Annotated[list[int] | None, Field(description="nalog_status-Codes")] = None,
                      firma: Annotated[str | None, Field(description="Teil des Firmennamens")] = None,
                      nalog_id: Annotated[list[int] | None, Field(description="Bestimmte Aufträge")] = None,
                      samo_sa_kandidatima: Annotated[bool, Field(description="Nur Aufträge mit Kandidaten")] = False,
                      limit: Annotated[int | None, Field(ge=1, le=5000)] = None) -> dict:
    return tools_read.orders_overview(cfg, p, nalog_status, firma, nalog_id, samo_sa_kandidatima, limit)


def t_pipeline_history(cfg, p,
                       kandidat_id: Annotated[int | None, Field(gt=0, description="Verlauf eines Kandidaten; ohne = Aggregat")] = None,
                       status_id: Annotated[list[int] | None, Field(description="Nur diese Status (Aggregat)")] = None,
                       projekt_id: Annotated[int | None, Field(gt=0)] = None,
                       od: Annotated[str | None, Field(description="YYYY-MM-DD")] = None,
                       do: Annotated[str | None, Field(description="YYYY-MM-DD (exkl.)")] = None,
                       gruppierung: Annotated[Literal["jahr", "monat", "tag"], Field()] = "monat",
                       limit: Annotated[int | None, Field(ge=1, le=5000)] = None) -> dict:
    return tools_read.pipeline_history(cfg, p, kandidat_id, status_id, projekt_id, od, do, gruppierung, limit)


def t_change_log(cfg, p,
                 tabelle: Annotated[str | None, Field(description="Tabelle filtern")] = None,
                 kandidat_id: Annotated[int | None, Field(gt=0)] = None,
                 limit: Annotated[int | None, Field(ge=1, le=5000)] = None,
                 mit_werten: Annotated[bool, Field(description="vorher/nachher-Werte (Permission jsi:kandidati:pii)")] = False) -> dict:
    return tools_read.change_log(cfg, p, tabelle, kandidat_id, limit, mit_werten)


ENTITY_DESC = "Entität aus dem Schreib-Register: " + ", ".join(sorted(n for n, e in registry.REGISTRY.items() if not e.process_tool))


def t_record_preview(cfg, p,
                     entity: Annotated[str, Field(description=ENTITY_DESC)],
                     action: Annotated[Literal["create", "update", "archive"], Field()],
                     record_id: Annotated[int | None, Field(gt=0, description="PK bei update/archive")] = None,
                     values: Annotated[JsonObj | None, Field(description="Spalte -> neuer Wert (nur Register-Spalten)")] = None) -> dict:
    return writes.record_preview(cfg, p, entity, action, record_id, values)


def t_record_write(cfg, p,
                   entity: Annotated[str, Field(description=ENTITY_DESC)],
                   action: Annotated[Literal["create", "update", "archive"], Field()],
                   record_id: Annotated[int | None, Field(gt=0)] = None,
                   values: Annotated[JsonObj | None, Field()] = None,
                   dry_run: Annotated[bool, Field(description="Standard true = nur Vorschau; false = ausführen")] = True,
                   preview_hash: Annotated[str | None, Field(description="preview_hash aus record_preview; bei Abweichung Abbruch")] = None,
                   grund: Annotated[str | None, Field(max_length=200, description="Begründung fürs Audit")] = None) -> dict:
    return writes.record_write(cfg, p, entity, action, record_id, values, dry_run, preview_hash, grund)


def t_set_application_status(cfg, p,
                             kandidat_id: Annotated[int, Field(gt=0)],
                             status_id: Annotated[int, Field(gt=0, description="idk_kandidat_status_prijave.status_id")],
                             projekt_id: Annotated[int | None, Field(gt=0, description="Projekt für den Log-Eintrag")] = None,
                             dry_run: Annotated[bool, Field(description="Standard true = nur Vorschau")] = True,
                             preview_hash: Annotated[str | None, Field()] = None,
                             grund: Annotated[str | None, Field(max_length=200)] = None) -> dict:
    return writes.set_application_status(cfg, p, kandidat_id, status_id, projekt_id, dry_run, preview_hash, grund)


# Display titles (Claude.ai requires tool.title).
TOOL_TITLES: dict[str, str] = {
    "whoami": "Wer bin ich",
    "search_candidates": "Kandidaten suchen",
    "filter_options": "Filterwerte",
    "candidate_profile": "Kandidatenprofil",
    "kpis": "Kennzahlen",
    "orders_overview": "Auftragsübersicht",
    "pipeline_history": "Pipeline-Verlauf",
    "change_log": "Änderungsprotokoll",
    "record_preview": "Schreibvorschau",
    "record_write": "Datensatz schreiben",
    "set_application_status": "Bewerbungsstatus setzen",
}

TOOLS: list[tuple[str, Any, str, ToolAnnotations]] = [
    ("whoami", t_whoami, "Wer bin ich, welche Permissions, Serverstatus. / Ko sam, ovlaštenja, status servera.", RO),
    ("search_candidates", t_search_candidates,
     "Kandidaten filtern/zählen (Beruf über 6 Quellen, Führerschein EU-Logik, Sprache, Ausbildung, Land, Alter, Status …). "
     "Standard: Anzahl. / Pretraga i brojanje kandidata po filterima; standardno broj.", RO),
    ("filter_options", t_filter_options, "Gültige Filterwerte, Codes, Berufskatalog, Schreib-Register. / Dozvoljene vrijednosti filtera i šifre.", RO),
    ("candidate_profile", t_candidate_profile, "Profil eines Kandidaten (ohne Personendaten, außer pii mit Permission). / Profil jednog kandidata.", RO),
    ("kpis", t_kpis, "Kennzahlen: Vermittlungen, neue Kandidaten, Pipeline, Umsatz, Task-Force, Casting, DIPL. / Ključni pokazatelji.", RO),
    ("orders_overview", t_orders_overview, "Aufträge: Bedarf vs. Kandidaten vs. unterschrieben. / Pregled naloga.", RO),
    ("pipeline_history", t_pipeline_history, "Pipeline-Verlauf eines Kandidaten oder Statuswechsel pro Periode. / Historija statusa prijave.", RO),
    ("change_log", t_change_log, "Änderungsprotokoll der MCP-Schreibaktionen (mcp_aenderung). / Dnevnik promjena.", RO),
    ("record_preview", t_record_preview, "Vorschau einer Schreibaktion (vorher/nachher, Prüfungen, preview_hash) – schreibt nichts. / Pregled promjene bez upisa.", RO),
    ("record_write", t_record_write, "Datensatz anlegen/ändern/archivieren laut Schreib-Register; Standard dry_run=true; Audit in mcp_aenderung; kein Löschen. / Upis uz audit.", RW),
    ("set_application_status", t_set_application_status, "Bewerbungs-/Pipeline-Status setzen inkl. Pipeline-Log; Standard dry_run=true. / Promjena statusa prijave uz log.", RW),
]


# ---------------------------------------------------------------- app
def build_mcp(cfg: config_mod.Config) -> MCPServer:
    kwargs: dict[str, Any] = {}
    if not cfg.auth_disabled:
        kwargs["auth"] = AuthSettings(issuer_url=cfg.issuer, resource_server_url=cfg.public_url, validate_token_resource=False)
        kwargs["token_verifier"] = WorkOSTokenVerifier(cfg.issuer, cfg.public_url, cfg.jwks_url)
    mcp = MCPServer(name="JSI-MCP-Claude", title="JSI CRM", version=VERSION, instructions=INSTRUCTIONS, **kwargs)
    for name, fn, desc, ann in TOOLS:
        mcp.add_tool(tool_wrapper(cfg, name)(fn), name=name, title=TOOL_TITLES[name], description=desc, annotations=ann,
                     structured_output=False)

    @mcp.custom_route("/health", methods=["GET"])
    async def health(request: Request):
        return JSONResponse(_health(cfg))

    if not cfg.auth_disabled:
        @mcp.custom_route("/.well-known/oauth-protected-resource", methods=["GET"])
        async def prm_root(request: Request):
            return JSONResponse({"resource": cfg.public_url, "authorization_servers": [cfg.issuer],
                                 "bearer_methods_supported": ["header"]})

        # Clients following the older MCP auth spec look for authorization-server metadata on the MCP host
        # itself; serve AuthKit's metadata here so discovery works either way.
        _as_cache: dict[str, Any] = {}

        @mcp.custom_route("/.well-known/oauth-authorization-server", methods=["GET"])
        async def as_metadata(request: Request):
            if "doc" not in _as_cache:
                import httpx

                try:
                    async with httpx.AsyncClient(timeout=10) as client:
                        r = await client.get(f"{cfg.issuer}/.well-known/oauth-authorization-server")
                    r.raise_for_status()
                    _as_cache["doc"] = r.json()
                except Exception as e:
                    log.warning("AuthKit metadata not reachable: %s", type(e).__name__)
                    return JSONResponse({"error": "authorization_server_unreachable", "issuer": cfg.issuer}, status_code=502)
            return JSONResponse(_as_cache["doc"])
    return mcp


def build_app(cfg: config_mod.Config) -> Starlette:
    auth_ok = cfg.auth_disabled or (cfg.authkit_domain and cfg.public_url)
    if not auth_ok:
        return _unconfigured_app(cfg)
    mcp = build_mcp(cfg)

    from mcp.server.transport_security import TransportSecuritySettings

    return mcp.streamable_http_app(streamable_http_path="/mcp", stateless_http=True, json_response=True,
                                   transport_security=TransportSecuritySettings(enable_dns_rebinding_protection=False),
                                   host="0.0.0.0")


def _health(cfg: config_mod.Config) -> dict:
    return {"status": "ok" if not cfg.errors else "degraded", "version": VERSION, "db_target": cfg.db_target,
            "db_konfiguriert": cfg.db_ready(), "auth": "disabled(local)" if cfg.auth_disabled else "workos",
            "schreiben_aktiv": cfg.writes_allowed, "konfigurationsfehler": cfg.errors,
            "tools": [t[0] for t in TOOLS]}


def _unconfigured_app(cfg: config_mod.Config) -> Starlette:
    async def health(request: Request):
        return JSONResponse(_health(cfg))

    async def mcp_unavailable(request: Request):
        # 401 like a protected server (hosts' MCP health checks accept an auth challenge, not a 503);
        # no tool can run until WorkOS is configured.
        auth_errors = [e for e in cfg.errors if e.startswith("Auth")] or cfg.errors
        desc = "; ".join(auth_errors).replace('"', "'")
        return JSONResponse({"error": "server_not_configured", "error_description": "; ".join(cfg.errors)}, status_code=401,
                            headers={"WWW-Authenticate": f'Bearer error="invalid_token", error_description="{desc}"'})

    return Starlette(routes=[Route("/health", health), Route("/mcp", mcp_unavailable, methods=["GET", "POST", "DELETE"])])


def main() -> None:
    logging.basicConfig(level=logging.INFO, stream=sys.stdout, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    try:
        cfg = config_mod.load()
    except config_mod.StartupRefused as e:
        log.error("%s", e)
        sys.exit(2)
    for err in cfg.errors:
        log.warning("Konfiguration: %s", err)
    log.info("JSI-MCP-Claude %s: db_target=%s db_ready=%s writes=%s auth=%s port=%s", VERSION, cfg.db_target,
             cfg.db_ready(), cfg.writes_allowed, "disabled(local)" if cfg.auth_disabled else "workos", cfg.port)
    app = build_app(cfg)
    host = "127.0.0.1" if cfg.auth_disabled else "0.0.0.0"
    uvicorn.run(app, host=host, port=cfg.port, log_level="info", proxy_headers=True, forwarded_allow_ips="*")


if __name__ == "__main__":
    main()
