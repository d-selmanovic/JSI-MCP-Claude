import pytest

from jsi_mcp import sensitive
from jsi_mcp.sensitive import SensitiveColumnError, assert_clean_sql


def test_md_parsed_31_columns():
    assert sum(len(v) for v in sensitive.SENSITIVE.values()) == 31
    assert "kandidat_jmbg" in sensitive.SENSITIVE["idk_kandidati"]


@pytest.mark.parametrize("sql", [
    "SELECT kandidat_jmbg FROM idk_kandidati",
    "SELECT k.Kandidat_Password FROM idk_kandidati k",
    "select employee_vicipass from idk_employees",
    "SELECT password FROM users",
    "SELECT u.token FROM users u",
])
def test_blocked(sql):
    with pytest.raises(SensitiveColumnError):
        assert_clean_sql(sql)


def test_allowed():
    assert_clean_sql("SELECT kandidat_id, kandidat_vozacka_kategorija FROM idk_kandidati WHERE kandidat_status <> 3")
    assert_clean_sql("SELECT pu_id FROM idk_pp_users")  # table name contains 'users' but is not `users`
