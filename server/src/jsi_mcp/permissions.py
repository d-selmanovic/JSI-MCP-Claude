"""Permission matrix (WorkOS permission slugs, HANDOVER §13.1)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

KANDIDATI_READ = "jsi:kandidati:read"
KANDIDATI_PII = "jsi:kandidati:pii"
KENNZAHLEN_READ = "jsi:kennzahlen:read"
FINANSIJE_READ = "jsi:finansije:read"
DIPL_READ = "jsi:dipl:read"
AUDIT_READ = "jsi:audit:read"
SQL_READ = "jsi:sql:read"  # sql_query: free read-only SQL, only admins/developers, confirmed per call

# table_read / table_describe: one permission per area of tabele_katalog.json
TABELE_AREAS = ("kandidati", "pipeline", "taskforce", "komunikacija", "firme", "partner_portal", "dipl")
TABELE = {a: f"jsi:tabele:{a}" for a in TABELE_AREAS}

READ_PERMISSIONS = frozenset({
    KANDIDATI_READ, KANDIDATI_PII, KENNZAHLEN_READ, FINANSIJE_READ, DIPL_READ, AUDIT_READ, *TABELE.values(),
})

# WorkOS Connect/MCP tokens carry role slugs, not a permissions claim.
# Only these JSI roles expand. WorkOS admin / crm-* roles grant nothing here.
JSI_READER = frozenset({KANDIDATI_READ, KENNZAHLEN_READ}) | frozenset(
    TABELE[a] for a in ("kandidati", "pipeline", "taskforce", "firme", "partner_portal"))
JSI_ANALYST = JSI_READER | frozenset({FINANSIJE_READ, DIPL_READ, TABELE["komunikacija"], TABELE["dipl"]})


def _write_permissions() -> frozenset[str]:
    from .registry import REGISTRY
    return frozenset(f"jsi:write:{name}:{action}" for name, entity in REGISTRY.items() for action in entity.actions)


def admin_test_permissions() -> frozenset[str]:
    """All jsi:* slugs: 6 reads + 7 table areas + every write action in the registry + sql (33)."""
    return READ_PERMISSIONS | _write_permissions() | {SQL_READ}


ROLE_PERMISSIONS: dict[str, frozenset[str]] = {
    "jsi-reader": JSI_READER,
    "jsi-analyst": JSI_ANALYST,
    "jsi-admin-test": admin_test_permissions(),
}


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, str):
        return value.split() if value else []
    if isinstance(value, (list, tuple, set, frozenset)):
        return list(value)
    return []


def _slug(item: Any) -> str | None:
    if isinstance(item, str) and item.strip():
        return item.strip()
    if isinstance(item, dict):
        raw = item.get("slug") or item.get("role")
        if isinstance(raw, str) and raw.strip():
            return raw.strip()
    return None


def permissions_from_claims(claims: dict[str, Any] | None) -> frozenset[str]:
    """Use an explicit permissions claim when it is non-empty.

    Connect tokens omit that claim. Then map known JSI role slugs. An empty
    list is treated as absent so a template that emits "permissions": [] still
    falls through to roles.
    """
    data = claims or {}
    explicit = {_slug(p) for p in _as_list(data.get("permissions"))}
    explicit.discard(None)
    if explicit:
        return frozenset(explicit)
    slugs: list[str] = []
    for item in _as_list(data.get("roles")):
        slug = _slug(item)
        if slug and slug not in slugs:
            slugs.append(slug)
    single = _slug(data.get("role"))
    if single and single not in slugs:
        slugs.append(single)
    out: set[str] = set()
    for slug in slugs:
        out.update(ROLE_PERMISSIONS.get(slug, ()))
    return frozenset(out)

# Base permission per tool. Write tools need jsi:write:<entity>:<action> (checked per call).
TOOL_PERMISSIONS: dict[str, list[str]] = {
    "whoami": [],
    "search_candidates": [KANDIDATI_READ],
    "filter_options": [KANDIDATI_READ],
    "candidate_profile": [KANDIDATI_READ],
    "kpis": [KENNZAHLEN_READ],
    "orders_overview": [KENNZAHLEN_READ],
    "pipeline_history": [KENNZAHLEN_READ],
    "change_log": [AUDIT_READ],
    "set_application_status": [],
    "table_describe": [],  # lists areas; details need the area permission
    "table_read": [],  # area permission (+ jsi:finansije:read for finance tables) checked per call
    "skill_lesen": [],  # static documentation shipped with the server, no CRM data
    "sql_query": [SQL_READ],  # checked in tools_sql before the confirmation dialog
}

# Extra permission per kpis area.
KPI_AREA_PERMISSIONS: dict[str, list[str]] = {
    "vermittlungen": [KENNZAHLEN_READ],
    "neue_kandidaten": [KENNZAHLEN_READ],
    "pipeline_bestand": [KENNZAHLEN_READ],
    "umsatz": [KENNZAHLEN_READ, FINANSIJE_READ],
    "task_force": [KENNZAHLEN_READ],
    "casting": [KENNZAHLEN_READ],
    "dipl_funnel": [KENNZAHLEN_READ, DIPL_READ],
}


def write_permission(entity: str, action: str) -> str:
    return f"jsi:write:{entity}:{action}"


@dataclass
class Principal:
    sub: str
    permissions: frozenset[str] = field(default_factory=frozenset)
    client_id: str | None = None
    org_id: str | None = None

    def has(self, perm: str) -> bool:
        if "*" in self.permissions or perm in self.permissions:
            return True
        # wildcard slugs like jsi:write:* or jsi:write:candidate:*
        parts = perm.split(":")
        for i in range(1, len(parts)):
            if ":".join(parts[:i]) + ":*" in self.permissions:
                return True
        return False

    def missing(self, perms: list[str]) -> list[str]:
        return [p for p in perms if not self.has(p)]


class PermissionDenied(PermissionError):
    def __init__(self, missing: list[str]):
        self.missing_permissions = missing
        super().__init__(
            "Keine Berechtigung / Nema ovlaštenja. Fehlende WorkOS-Permission(s): " + ", ".join(missing)
        )


def require(principal: Principal, perms: list[str]) -> None:
    miss = principal.missing(perms)
    if miss:
        raise PermissionDenied(miss)
