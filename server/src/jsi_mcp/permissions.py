"""Permission matrix (WorkOS permission slugs, HANDOVER §13.1)."""
from __future__ import annotations

from dataclasses import dataclass, field

KANDIDATI_READ = "jsi:kandidati:read"
KANDIDATI_PII = "jsi:kandidati:pii"
KENNZAHLEN_READ = "jsi:kennzahlen:read"
FINANSIJE_READ = "jsi:finansije:read"
DIPL_READ = "jsi:dipl:read"
AUDIT_READ = "jsi:audit:read"

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
    "record_preview": [],
    "record_write": [],
    "set_application_status": [],
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
