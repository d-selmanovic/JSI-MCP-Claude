"""Write registry: load + structural validation (runs at import / server start)."""
from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from typing import Any

import yaml

from .config import PACKAGE_DIR
from .sensitive import SENSITIVE

REGISTRY_PATH = os.path.join(PACKAGE_DIR, "write_registry.yaml")
ACTIONS = ("create", "update", "archive")
TYPES = ("int", "str", "text", "date", "datetime", "enum", "licence_list")

# Log/audit/event/technical tables are never writable through the registry.
FORBIDDEN_TABLE_RE = re.compile(
    r"^(mcp_.*|rb_.*|idk_logs|idk_log_.*|.*_log|.*_logs|idk_api_clients|idk_employees.*|idk_jobstep_partners|"
    r"idk_pp_users|users|idk_ipwhitelist|idk_settings|idk_modules|idk_module_permissions|idk_obracuni|idk_racuni|idk_predracuni)$"
)


class RegistryError(ValueError):
    pass


@dataclass
class Column:
    name: str
    type: str
    max_len: int | None = None
    values: list[Any] | None = None
    nullable: bool = False
    pii: bool = False
    required_on_create: bool = False
    create_only: bool = False
    references: dict[str, Any] | None = None


@dataclass
class Entity:
    name: str
    label: str
    table: str
    pk: str
    actions: list[str]
    columns: dict[str, Column]
    candidate_ref: str | None = None
    archive: dict[str, Any] = field(default_factory=dict)
    create_defaults: dict[str, Any] = field(default_factory=dict)
    fixed: dict[str, Any] = field(default_factory=dict)
    unique_together: list[str] = field(default_factory=list)
    unique_nonzero: list[str] = field(default_factory=list)
    process_tool: str | None = None


def load(path: str = REGISTRY_PATH) -> dict[str, Entity]:
    with open(path, encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    if not isinstance(raw, dict) or raw.get("version") != 1 or not isinstance(raw.get("entities"), dict):
        raise RegistryError("write_registry.yaml: version 1 + entities erwartet")
    out: dict[str, Entity] = {}
    for name, e in raw["entities"].items():
        if not re.match(r"^[a-z][a-z0-9_]*$", name):
            raise RegistryError(f"Entitätsname ungültig: {name}")
        cols = {}
        for cname, c in (e.get("columns") or {}).items():
            unknown = set(c) - (set(Column.__dataclass_fields__) - {"name"})
            if unknown:
                raise RegistryError(f"{name}.{cname}: unbekannte Felder {sorted(unknown)}")
            cols[cname] = Column(name=cname, **c)
        ent = Entity(
            name=name, label=e.get("label", name), table=e["table"], pk=e["pk"], actions=list(e.get("actions") or []),
            columns=cols, candidate_ref=e.get("candidate_ref"), archive=e.get("archive") or {},
            create_defaults=e.get("create_defaults") or {}, fixed=e.get("fixed") or {},
            unique_together=e.get("unique_together") or [], unique_nonzero=e.get("unique_nonzero") or [],
            process_tool=e.get("process_tool"),
        )
        validate_entity(ent)
        out[name] = ent
    return out


def validate_entity(e: Entity) -> None:
    if FORBIDDEN_TABLE_RE.match(e.table):
        raise RegistryError(f"{e.name}: Tabelle {e.table} ist nie beschreibbar (Log/Audit/Technik)")
    if not e.actions or any(a not in ACTIONS for a in e.actions):
        raise RegistryError(f"{e.name}: actions müssen aus {ACTIONS} sein")
    if "archive" in e.actions and not e.archive:
        raise RegistryError(f"{e.name}: archive ohne archive-Spalten")
    if e.archive and "archive" not in e.actions:
        raise RegistryError(f"{e.name}: archive-Spalten ohne Aktion archive")
    bad = SENSITIVE.get(e.table, frozenset())
    touched = set(e.columns) | set(e.archive) | set(e.create_defaults) | set(e.fixed)
    if touched & bad:
        raise RegistryError(f"{e.name}: [TAJNO]-Spalten nie beschreibbar: {sorted(touched & bad)}")
    if e.pk in touched:
        raise RegistryError(f"{e.name}: Primärschlüssel {e.pk} nie beschreibbar")
    for c in e.columns.values():
        if c.type not in TYPES:
            raise RegistryError(f"{e.name}.{c.name}: Typ {c.type} unbekannt")
        if c.type == "enum" and not c.values:
            raise RegistryError(f"{e.name}.{c.name}: enum ohne values")
        if c.type == "str" and not c.max_len:
            raise RegistryError(f"{e.name}.{c.name}: str ohne max_len")
        if c.references and not {"table", "column"} <= set(c.references):
            raise RegistryError(f"{e.name}.{c.name}: references braucht table+column")
        if not re.match(r"^[a-z][a-z0-9_]*$", c.name, re.IGNORECASE):
            raise RegistryError(f"{e.name}.{c.name}: Spaltenname ungültig")
    if "create" in e.actions and not any(c.required_on_create for c in e.columns.values()):
        raise RegistryError(f"{e.name}: create ohne Pflichtfelder")
    for col in e.unique_together + e.unique_nonzero:
        if col not in e.columns:
            raise RegistryError(f"{e.name}: unique-Spalte {col} nicht in columns")
    if e.candidate_ref and e.candidate_ref != e.pk and e.candidate_ref not in e.columns:
        raise RegistryError(f"{e.name}: candidate_ref {e.candidate_ref} nicht in columns")


REGISTRY: dict[str, Entity] = load()


def describe() -> dict[str, Any]:
    """Public description (for record_preview / filter docs)."""
    out = {}
    for n, e in REGISTRY.items():
        out[n] = {
            "label": e.label, "table": e.table, "actions": e.actions, "process_tool": e.process_tool,
            "columns": {c.name: {k: v for k, v in c.__dict__.items() if k != "name" and v not in (None, False, [])}
                        for c in e.columns.values()},
            "permissions": [f"jsi:write:{n}:{a}" for a in e.actions],
        }
    return out
