import json
import os
import sys

import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
REPO = os.path.abspath(os.path.join(ROOT, ".."))
sys.path.insert(0, os.path.join(ROOT, "src"))

from jsi_mcp import config  # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from testenv import LOCAL_ENV  # noqa: E402


@pytest.fixture
def local_cfg():
    return config.load(dict(LOCAL_ENV))


@pytest.fixture(scope="session")
def columns():
    rows = json.load(open(os.path.join(REPO, "docs", "rohdaten", "columns.json"), encoding="utf-8"))["rows"]
    out = {}
    for r in rows:
        out.setdefault(r["t"], {})[r["col"]] = r
    return out


@pytest.fixture(scope="session")
def defaults():
    rows = json.load(open(os.path.join(REPO, "docs", "rohdaten", "column_defaults.json"), encoding="utf-8"))["rows"]
    return {(r[0], r[1]): (r[2], r[3]) for r in rows}
