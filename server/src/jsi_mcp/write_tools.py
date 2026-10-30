"""One MCP tool per (entity, action) from the write registry – explicit, reviewable contracts instead of a
generic executor (OpenAI plugin guidelines: tool independence and exposure).

Each tool has typed fields for exactly the registry columns of that entity/action, its own permission
(jsi:write:<entity>:<action>) and the same two-step flow: dry_run=true (default) returns the preview with
preview_hash; dry_run=false + preview_hash executes after the user confirmed. Validation, audit and the
[TAJNO] ban stay in writes.py.
"""
from __future__ import annotations

import inspect
from dataclasses import dataclass
from typing import Annotated, Any, Literal

from mcp.types import ToolAnnotations
from pydantic import Field

from . import writes
from .registry import REGISTRY, Column, Entity

ACTION_LABEL = {"create": ("anlegen", "kreiranje"), "update": ("ändern", "izmjena"), "archive": ("archivieren", "arhiviranje")}
ACTION_TITLE = {"create": "anlegen", "update": "ändern", "archive": "archivieren"}

_COMMON = [
    ("dry_run", Annotated[bool, Field(description="Standard true = nur Vorschau (liefert preview_hash, schreibt nichts); "
                                                  "false = ausführen – nur nach ausdrücklicher Bestätigung des Nutzers")], True),
    ("preview_hash", Annotated[str | None, Field(max_length=128, description="preview_hash aus der Vorschau; bei "
                                                                              "Abweichung wird abgebrochen")], None),
    ("grund", Annotated[str | None, Field(max_length=200, description="Begründung fürs Audit (mcp_aenderung)")], None),
]


@dataclass(frozen=True)
class WriteTool:
    name: str
    entity: str
    action: str
    title: str
    description: str
    annotations: ToolAnnotations
    fn: Any


def _py_type(c: Column) -> Any:
    desc = c.name + (" (Personendaten – braucht jsi:kandidati:pii)" if c.pii else "")
    if c.references:
        desc += f"; Verweis auf {c.references['table']}.{c.references['column']}"
    if c.type == "int":
        t: Any = Annotated[int, Field(description=desc)]
    elif c.type == "enum":
        t = Annotated[Literal[tuple(c.values)], Field(description=desc)]  # type: ignore[misc]
    elif c.type == "date":
        t = Annotated[str, Field(pattern=r"^\d{4}-\d{2}-\d{2}$", description=desc + " (YYYY-MM-DD)")]
    elif c.type == "datetime":
        t = Annotated[str, Field(pattern=r"^\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}(:\d{2})?$", description=desc + " (YYYY-MM-DD HH:MM[:SS])")]
    elif c.type == "licence_list":
        t = Annotated[str, Field(max_length=c.max_len or 25, description=desc + " (Kategorien kommagetrennt, z. B. 'B,C,CE')")]
    else:  # str, text
        t = Annotated[str, Field(max_length=c.max_len or 65535, description=desc)]
    return t


def _columns_for(e: Entity, action: str) -> list[Column]:
    if action == "archive":
        return []
    return [c for c in e.columns.values() if not (action == "update" and c.create_only)]


def _build(e: Entity, action: str) -> WriteTool:
    name = f"{e.name}_{action}"
    cols = _columns_for(e, action)
    params: list[inspect.Parameter] = [
        inspect.Parameter("cfg", inspect.Parameter.POSITIONAL_OR_KEYWORD),
        inspect.Parameter("p", inspect.Parameter.POSITIONAL_OR_KEYWORD),
    ]
    ann: dict[str, Any] = {}
    if action in ("update", "archive"):
        ann["record_id"] = Annotated[int, Field(gt=0, description=f"{e.table}.{e.pk} des Datensatzes")]
        params.append(inspect.Parameter("record_id", inspect.Parameter.KEYWORD_ONLY, annotation=ann["record_id"]))
    required = [c for c in cols if action == "create" and c.required_on_create]
    optional = [c for c in cols if c not in required]
    for c in required:
        ann[c.name] = _py_type(c)
        params.append(inspect.Parameter(c.name, inspect.Parameter.KEYWORD_ONLY, annotation=ann[c.name]))
    for c in optional:
        ann[c.name] = _py_type(c) | None
        params.append(inspect.Parameter(c.name, inspect.Parameter.KEYWORD_ONLY, annotation=ann[c.name], default=None))
    nullable = [c.name for c in optional if c.nullable]
    if action == "update" and nullable:
        ann["leeren"] = Annotated[list[Literal[tuple(nullable)]] | None,  # type: ignore[misc]
                                  Field(description="Spalten, die auf NULL gesetzt werden sollen")]
        params.append(inspect.Parameter("leeren", inspect.Parameter.KEYWORD_ONLY, annotation=ann["leeren"], default=None))
    for pname, ptype, default in _COMMON:
        ann[pname] = ptype
        params.append(inspect.Parameter(pname, inspect.Parameter.KEYWORD_ONLY, annotation=ptype, default=default))
    col_names = [c.name for c in cols]

    def fn(cfg, p, **kw) -> dict:
        values = {k: kw[k] for k in col_names if kw.get(k) is not None}
        for k in kw.get("leeren") or []:
            if k in values:
                raise writes.InputError(f"{k}: gleichzeitig Wert und leeren angegeben")
            values[k] = None
        return writes.record_write(cfg, p, e.name, action, kw.get("record_id"), values or None,
                                   kw.get("dry_run", True), kw.get("preview_hash"), kw.get("grund"))

    fn.__name__ = f"t_{name}"
    fn.__signature__ = inspect.Signature(params, return_annotation=dict)  # type: ignore[attr-defined]
    fn.__annotations__ = {**ann, "return": dict}

    de, bs = ACTION_LABEL[action]
    label_de, _, label_bs = e.label.partition(" / ")
    effect = {"create": f"legt eine neue Zeile in {e.table} an",
              "update": f"ändert die angegebenen Spalten von {e.table} (Zeile {e.pk}=record_id)",
              "archive": f"setzt {', '.join(f'{k}={v}' for k, v in e.archive.items())} in {e.table} (kein Löschen)"}[action]
    description = (f"{label_de} {de}: {effect}. Permission jsi:write:{e.name}:{action}. Standard dry_run=true = Vorschau mit "
                   f"vorher/nachher und preview_hash; dry_run=false mit preview_hash nur nach Bestätigung des Nutzers. "
                   f"Audit in mcp_aenderung. / {label_bs or label_de}: {bs} (prvo pregled, upis tek nakon potvrde).")
    annotations = ToolAnnotations(read_only_hint=False, destructive_hint=(action == "archive"),
                                  idempotent_hint=(action != "create"), open_world_hint=False)
    return WriteTool(name, e.name, action, f"{label_de} {ACTION_TITLE[action]}", description, annotations, fn)


def build_all() -> list[WriteTool]:
    out = []
    for e in REGISTRY.values():
        if e.process_tool:
            continue
        for a in e.actions:
            out.append(_build(e, a))
    return out


WRITE_TOOLS: list[WriteTool] = build_all()
