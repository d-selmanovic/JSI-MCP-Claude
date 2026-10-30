"""Skills on the server: extension io.modelcontextprotocol/skills (skills/list, skills/get, skill:// resources) and
the tool skill_lesen, through an in-process MCP client (no DB needed)."""
import hashlib
import json
import os
import re
from typing import Literal

import pytest
from mcp import Client, types
from mcp.shared.exceptions import MCPError
from pydantic import TypeAdapter

from jsi_mcp import config, server, skills_ext
from jsi_mcp.sensitive import SENSITIVE
from jsi_mcp.skills_ext import SkillsGetParams, SkillsListParams

from testenv import LOCAL_ENV

REQUIRED = {"jsi-data-analyst", "jsi-kandidat-filter"}


class ListReq(types.Request[SkillsListParams, Literal["skills/list"]]):
    method: Literal["skills/list"] = "skills/list"
    params: SkillsListParams


class GetReq(types.Request[SkillsGetParams, Literal["skills/get"]]):
    method: Literal["skills/get"] = "skills/get"
    params: SkillsGetParams


def client():
    return Client(server.build_mcp(config.load({**LOCAL_ENV, "JSI_DEV_PERMISSIONS": ""})))


def text(res):
    return "".join(c.text for c in res.content if getattr(c, "type", "") == "text")


def test_skill_files_are_valid():
    cat = skills_ext.skills()
    assert REQUIRED <= set(cat)
    for name, s in cat.items():
        assert s.frontmatter["name"] == name and s.frontmatter["description"]
        assert s.files[0].path == "SKILL.md"
        for f in s.files:
            assert f.uri == f"skill://{name}/{f.path}"
            assert not f.path.startswith(("agents/", "scripts/")), f"{f.uri}: client-specific file on the server"


def test_no_sql_skills_and_no_secret_column_values():
    # The server does not hand out skills that tell agents to write SQL against the CRM.
    assert not {"sql-queries", "write-query", "data-context-extractor"} & set(skills_ext.skills())
    for s in skills_ext.skills().values():
        for f in s.files:
            assert "BlazeSQL connector" not in f.text, f.uri
            assert not re.search(r"(?<!\d)\d{13}(?!\d)", f.text), f"{f.uri}: 13-digit number (JMBG?)"


def test_relative_references_resolve_inside_the_skill():
    for s in skills_ext.skills().values():
        paths = {f.path for f in s.files}
        for f in s.files:
            for ref in re.findall(r"`((?:\.\./)*(?:references)/[\w./-]+\.md)`", f.text):
                base = os.path.dirname(f.path)
                target = os.path.normpath(os.path.join(base, ref) if ref.startswith("..") else ref).replace(os.sep, "/")
                assert target in paths, f"{f.uri}: reference {ref} → {target} not in manifest"


async def test_extension_capability_list_get_and_read():
    async with client() as c:
        assert c.server_capabilities.extensions == {"io.modelcontextprotocol/skills": {"directoryRead": False}}
        assert c.server_capabilities.resources is not None
        listing = await c.session.send_request(ListReq(params=SkillsListParams()), TypeAdapter(dict))
        assert (listing["resultType"], listing["cacheScope"]) == ("complete", "public") and listing["ttlMs"] > 0
        entries = {e["frontmatter"]["name"]: e for e in listing["skills"]}
        assert set(entries) == set(skills_ext.skills())
        entry = entries["jsi-kandidat-filter"]
        assert entry["uri"] == "skill://jsi-kandidat-filter/SKILL.md"
        assert {r["uri"] for r in entry["resources"]} == {"skill://jsi-kandidat-filter/SKILL.md",
                                                          "skill://jsi-kandidat-filter/references/filteri.md"}
        for r in entries["jsi-data-analyst"]["resources"] + entry["resources"]:
            content = (await c.read_resource(r["uri"])).contents[0]
            raw = content.text.encode("utf-8")
            assert r["digest"] == "sha256:" + hashlib.sha256(raw).hexdigest() and r["size"] == len(raw), r["uri"]
            assert content.mime_type == "text/markdown"
        got = await c.session.send_request(GetReq(params=SkillsGetParams(uri=entry["uri"])), TypeAdapter(dict))
        assert got["skill"] == entry and got["resultType"] == "complete"


async def test_unknown_skill_and_file():
    async with client() as c:
        with pytest.raises(MCPError) as e:
            await c.session.send_request(GetReq(params=SkillsGetParams(uri="skill://nope/SKILL.md")), TypeAdapter(dict))
        assert e.value.code == -32602
        with pytest.raises(MCPError) as e:
            await c.read_resource("skill://jsi-data-analyst/../../config.py")
        assert e.value.code == -32602


async def test_skill_lesen_tool_without_permissions():
    async with client() as c:
        cat = json.loads(text(await c.call_tool("skill_lesen", {})))
        assert REQUIRED <= {s["skill"] for s in cat["skillovi"]}
        main = json.loads(text(await c.call_tool("skill_lesen", {"skill": "jsi-data-analyst"})))
        assert main["sadrzaj"].startswith("---\nname: jsi-data-analyst") and "references/metrics.md" in main["datoteke"]
        ref = json.loads(text(await c.call_tool("skill_lesen", {"skill": "jsi-data-analyst",
                                                                 "datei": "references/metrics.md"})))
        assert ref["sadrzaj"] == skills_ext.skills()["jsi-data-analyst"].file("references/metrics.md").text
        for bad in ({"skill": "nope"}, {"skill": "jsi-data-analyst", "datei": "../../config.py"}):
            res = await c.call_tool("skill_lesen", bad)
            assert res.is_error, bad


def test_sensitive_doc_lists_names_only():
    doc = skills_ext.skills()["jsi-data-analyst"].file("references/schema/osjetljive_kolone.md").text
    assert any(col in doc for cols in SENSITIVE.values() for col in cols)  # documents the banned column names
