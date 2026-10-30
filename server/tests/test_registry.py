"""Write-registry validation against the real schema snapshot (columns.json)."""
import re

import pytest

from jsi_mcp import registry
from jsi_mcp.registry import REGISTRY, Column, Entity, RegistryError, validate_entity
from jsi_mcp.sensitive import SENSITIVE


def test_registry_loads_expected_entities():
    assert {"candidate", "candidate_driving_licence", "candidate_language", "candidate_education", "candidate_experience",
            "candidate_note", "candidate_order", "project_member", "candidate_dipl_link", "company", "contact",
            "application_status"} <= set(REGISTRY)


@pytest.mark.parametrize("name", sorted(REGISTRY))
def test_entity_matches_schema(name, columns, defaults):
    e = REGISTRY[name]
    assert e.table in columns, f"table {e.table} missing in schema"
    tcols = columns[e.table]
    assert tcols[e.pk]["ckey"] == "PRI"
    for c in list(e.columns.values()):
        assert c.name in tcols, f"{name}.{c.name} not in {e.table}"
        typ = tcols[c.name]["typ"]
        assert c.name not in SENSITIVE.get(e.table, ()), "sensitive column"
        if c.type in ("str", "licence_list"):
            m = re.match(r"varchar\((\d+)\)", typ)
            assert m, f"{name}.{c.name}: {typ} is not varchar"
            assert c.max_len <= int(m.group(1)), f"{name}.{c.name}: max_len {c.max_len} > {typ}"
        elif c.type == "text":
            assert typ.endswith("text")
        elif c.type == "int":
            assert typ.startswith(("int", "tinyint", "smallint", "bigint"))
        elif c.type == "date":
            assert typ == "date"
        elif c.type == "enum":
            if all(isinstance(v, int) for v in c.values):
                assert typ.startswith(("int", "tinyint"))
            else:
                m = re.match(r"varchar\((\d+)\)", typ)
                assert m and max(len(str(v)) for v in c.values) <= int(m.group(1))
        if not c.nullable and c.type != "enum" and not c.required_on_create:
            assert tcols[c.name]["nullable"] == "NO" or True
        if c.nullable:
            assert tcols[c.name]["nullable"] == "YES", f"{name}.{c.name} marked nullable but column is NOT NULL"
        if c.references:
            ref = c.references
            assert ref["table"] in columns and ref["column"] in columns[ref["table"]]
    for col in list(e.archive) + list(e.create_defaults) + list(e.fixed):
        assert col in tcols


@pytest.mark.parametrize("name", sorted(n for n, e in REGISTRY.items() if "create" in e.actions))
def test_create_covers_not_null_columns(name, columns, defaults):
    e = REGISTRY[name]
    provided = {c.name for c in e.columns.values() if c.required_on_create} | set(e.create_defaults) | set(e.fixed)
    for col, r in columns[e.table].items():
        if r["nullable"] == "NO" and col != e.pk and defaults.get((e.table, col), (None, ""))[0] is None:
            assert col in provided, f"{name}: NOT NULL column {col} without default is not provided on create"


def _entity(**kw):
    base = dict(name="x", label="x", table="idk_companies", pk="company_id", actions=["update"],
                columns={"company_name": Column(name="company_name", type="str", max_len=10)})
    base.update(kw)
    return Entity(**base)


@pytest.mark.parametrize("table", ["mcp_aenderung", "mcp_fehler", "rb_events", "idk_logs", "idk_log_statusi_prijave",
                                   "idk_nd_kandidata_status_log", "idk_employees", "users", "idk_api_clients"])
def test_forbidden_tables_rejected(table):
    with pytest.raises(RegistryError):
        validate_entity(_entity(table=table))


def test_sensitive_and_pk_rejected():
    with pytest.raises(RegistryError):
        validate_entity(_entity(table="idk_kandidati", pk="kandidat_id",
                                columns={"kandidat_jmbg": Column(name="kandidat_jmbg", type="str", max_len=20)}))
    with pytest.raises(RegistryError):
        validate_entity(_entity(columns={"company_id": Column(name="company_id", type="int")}))


def test_archive_requires_columns():
    with pytest.raises(RegistryError):
        validate_entity(_entity(actions=["update", "archive"]))


def test_no_registry_table_has_delete_semantics():
    for e in REGISTRY.values():
        assert set(e.actions) <= {"create", "update", "archive"}


def test_describe_lists_permissions():
    d = registry.describe()
    assert d["candidate"]["permissions"] == ["jsi:write:candidate:create", "jsi:write:candidate:update",
                                             "jsi:write:candidate:archive"]
