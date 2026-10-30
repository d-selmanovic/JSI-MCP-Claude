"""table_describe / table_read gegen MySQL 8.4 mit dem Read-only-Benutzer (Spalten-GRANTs aus gen_grants.py)."""
import pytest

from jsi_mcp import tools_tables
from jsi_mcp.permissions import Principal
from jsi_mcp.tools_read import InputError
from jsi_mcp.permissions import PermissionDenied

ALL = Principal(sub="it-admin", permissions=frozenset({"*"}))
READER = Principal(sub="it-reader", permissions=frozenset({"jsi:tabele:kandidati", "jsi:tabele:pipeline"}))


def test_every_catalog_table_and_column_is_readable(ro_cfg):
    """Katalog passt zum echten Schema und zu den GRANTs: jede Tabelle mit allen freigegebenen Spalten lesbar."""
    n = 0
    for area in tools_tables.catalog()["podrucja"].values():
        for t in area["tabele"]:
            r = tools_tables.table_read(ro_cfg, ALL, t, limit=1, pii=True)
            assert r["stranica"]["ukupno"] is not None
            n += 1
    assert n == 135


def test_describe_respects_permissions(ro_cfg):
    d = tools_tables.table_describe(ro_cfg, READER)
    allowed = {a["podrucje"]: a["dozvoljeno"] for a in d["podrucja"]}
    assert allowed["kandidati"] and allowed["pipeline"] and not allowed["komunikacija"]
    assert next(a for a in d["podrucja"] if a["podrucje"] == "komunikacija")["tabele"] is None
    det = tools_tables.table_describe(ro_cfg, READER, tabela="idk_kandidati")
    names = {c["kolona"] for c in det["kolone"]}
    assert "kandidat_ime" in names and "kandidat_jmbg" not in names  # pii listed, [TAJNO] absent
    with pytest.raises(PermissionDenied):
        tools_tables.table_describe(ro_cfg, READER, tabela="idk_sms_messages")


def test_read_hides_pii_by_default_and_pages(ro_cfg):
    r = tools_tables.table_read(ro_cfg, READER, "idk_kandidati", limit=2)
    assert r["rezultat"] and all("kandidat_ime" not in row and "kandidat_mobitel" not in row for row in r["rezultat"])
    assert any("kandidat_ime" in n for n in r["napomene"])
    st = r["stranica"]
    assert st["prikazano_od"] == 1 and st["ukupno"] >= len(r["rezultat"])
    if st["ima_jos"]:
        r2 = tools_tables.table_read(ro_cfg, READER, "idk_kandidati", limit=2, offset=st["sljedeci_offset"])
        ids1 = {x["kandidat_id"] for x in r["rezultat"]}
        assert not ids1 & {x["kandidat_id"] for x in r2["rezultat"]}


def test_pii_needs_flag_and_permission(ro_cfg):
    with pytest.raises(InputError):
        tools_tables.table_read(ro_cfg, READER, "idk_kandidati", kolone=["kandidat_ime"])
    with pytest.raises(InputError):  # no leaking through filters either
        tools_tables.table_read(ro_cfg, READER, "idk_kandidati",
                                filteri=[{"kolona": "kandidat_email", "op": "like", "vrijednost": "@"}])
    with pytest.raises(PermissionDenied):
        tools_tables.table_read(ro_cfg, READER, "idk_kandidati", kolone=["kandidat_ime"], pii=True)
    p = Principal(sub="x", permissions=frozenset({"jsi:tabele:kandidati", "jsi:kandidati:pii"}))
    r = tools_tables.table_read(ro_cfg, p, "idk_kandidati", kolone=["kandidat_id", "kandidat_ime"], pii=True, limit=1)
    assert set(r["rezultat"][0]) == {"kandidat_id", "kandidat_ime"}


def test_secret_and_unknown_columns_rejected(ro_cfg):
    for col in ("kandidat_jmbg", "pu_password", "kandidat_id`; DROP TABLE idk_kandidati; --"):
        with pytest.raises(InputError):
            tools_tables.table_read(ro_cfg, ALL, "idk_kandidati", kolone=[col], pii=True)
    with pytest.raises(InputError):
        tools_tables.table_read(ro_cfg, ALL, "mcp_aenderung")  # not in any area


def test_filters_are_parameters(ro_cfg):
    base = tools_tables.table_read(ro_cfg, ALL, "idk_kandidati", limit=1)["stranica"]["ukupno"]
    for payload in ("1 OR 1=1", "x' OR '1'='1", "1); DROP TABLE idk_kandidati; --"):
        r = tools_tables.table_read(ro_cfg, ALL, "idk_kandidati",
                                    filteri=[{"kolona": "kandidat_drzava", "op": "eq", "vrijednost": payload}])
        assert r["stranica"]["ukupno"] == 0
        r = tools_tables.table_read(ro_cfg, ALL, "idk_kandidati",
                                    filteri=[{"kolona": "kandidat_drzava", "op": "like", "vrijednost": payload}])
        assert r["stranica"]["ukupno"] == 0
    assert tools_tables.table_read(ro_cfg, ALL, "idk_kandidati", limit=1)["stranica"]["ukupno"] == base


def test_grouping_and_aggregates(ro_cfg):
    r = tools_tables.table_read(ro_cfg, ALL, "idk_kandidati", grupiraj_po=["kandidat_status"],
                                agregati=[{"fn": "count"}], sortiraj=[{"kolona": "broj", "smjer": "desc"}])
    total = tools_tables.table_read(ro_cfg, ALL, "idk_kandidati", limit=1)["stranica"]["ukupno"]
    assert sum(x["broj"] for x in r["rezultat"]) == total
    assert r["stranica"]["ukupno"] == len(r["rezultat"])
    one = tools_tables.table_read(ro_cfg, ALL, "idk_kandidati", agregati=[{"fn": "max", "kolona": "kandidat_id"}])
    assert len(one["rezultat"]) == 1 and "max_kandidat_id" in one["rezultat"][0]
    with pytest.raises(InputError):
        tools_tables.table_read(ro_cfg, ALL, "idk_kandidati", agregati=[{"fn": "drop"}])


def test_finance_table_needs_finance_permission(ro_cfg):
    p = Principal(sub="x", permissions=frozenset({"jsi:tabele:firme"}))
    with pytest.raises(PermissionDenied):
        tools_tables.table_read(ro_cfg, p, "idk_nalog_financije")
    p2 = Principal(sub="x", permissions=frozenset({"jsi:tabele:firme", "jsi:finansije:read"}))
    tools_tables.table_read(ro_cfg, p2, "idk_nalog_financije", limit=1)
