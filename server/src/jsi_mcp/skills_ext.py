"""Skills served by the MCP server (extension io.modelcontextprotocol/skills, SEP-2640) plus the tool skill_lesen.

Source: src/jsi_mcp/skills/<name>/SKILL.md (+ supporting files). Hosts that implement the extension discover them via
skills/list / skills/get and read files via resources/read (skill://<name>/<path>). Hosts without the extension get
the same content through the tool skill_lesen. Contents are static documentation shipped with the server (no CRM
data); the whole /mcp endpoint is behind the OAuth login anyway.
"""
from __future__ import annotations

import functools
import hashlib
import os
from dataclasses import dataclass
from typing import Any

import yaml
from mcp.server.extension import Extension, MethodBinding, ResourceBinding
from mcp.server.mcpserver.resources import TextResource
from mcp.shared.exceptions import MCPError
from mcp_types import INVALID_PARAMS, RequestParams

from .tools_read import InputError

EXTENSION_ID = "io.modelcontextprotocol/skills"
SKILLS_DIR = os.path.join(os.path.dirname(__file__), "skills")
TTL_MS = 300_000
MAX_FILES = 512
MAX_BYTES = 16 * 1024 * 1024
MIME = {".md": "text/markdown", ".json": "application/json", ".py": "text/x-python", ".yaml": "application/yaml"}


@dataclass(frozen=True)
class SkillFile:
    path: str  # relative to the skill root, "/" separated
    uri: str
    text: str
    digest: str
    size: int
    mime: str


@dataclass(frozen=True)
class Skill:
    name: str
    frontmatter: dict
    files: tuple[SkillFile, ...]

    @property
    def uri(self) -> str:
        return f"skill://{self.name}/SKILL.md"

    def entry(self) -> dict:
        return {"uri": self.uri, "frontmatter": self.frontmatter,
                "resources": [{"uri": f.uri, "digest": f.digest, "size": f.size} for f in self.files]}

    def file(self, path: str) -> SkillFile | None:
        return next((f for f in self.files if f.path == path), None)


def _frontmatter(text: str, where: str) -> dict:
    if not text.startswith("---\n"):
        raise ValueError(f"{where}: SKILL.md must begin with YAML frontmatter")
    end = text.find("\n---", 4)
    if end < 0:
        raise ValueError(f"{where}: frontmatter not closed")
    fm = yaml.safe_load(text[4:end])
    if not isinstance(fm, dict) or not fm.get("name") or not fm.get("description"):
        raise ValueError(f"{where}: frontmatter needs name and description")
    return fm


def _load_skill(name: str) -> Skill:
    root = os.path.join(SKILLS_DIR, name)
    files = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if not d.startswith((".", "__")))
        for fn in sorted(filenames):
            if fn.startswith(".") or fn.endswith(".pyc"):
                continue
            rel = os.path.relpath(os.path.join(dirpath, fn), root).replace(os.sep, "/")
            raw = open(os.path.join(dirpath, fn), "rb").read()
            files.append(SkillFile(rel, f"skill://{name}/{rel}", raw.decode("utf-8"),
                                   "sha256:" + hashlib.sha256(raw).hexdigest(), len(raw),
                                   MIME.get(os.path.splitext(fn)[1], "text/plain")))
    files.sort(key=lambda f: (f.path != "SKILL.md", f.path))
    if not files or files[0].path != "SKILL.md":
        raise ValueError(f"skill {name}: SKILL.md missing")
    fm = _frontmatter(files[0].text, f"skill {name}")
    if fm["name"] != name:
        raise ValueError(f"skill {name}: frontmatter name {fm['name']!r} must match the directory name")
    if len(files) > MAX_FILES or sum(f.size for f in files) > MAX_BYTES:
        raise ValueError(f"skill {name}: more than {MAX_FILES} files or {MAX_BYTES} bytes")
    return Skill(name, fm, tuple(files))


@functools.lru_cache(maxsize=1)
def skills() -> dict[str, Skill]:
    names = sorted(d for d in os.listdir(SKILLS_DIR)
                   if os.path.isfile(os.path.join(SKILLS_DIR, d, "SKILL.md")))
    return {n: _load_skill(n) for n in names}


def _by_uri(uri: str) -> Skill | None:
    return next((s for s in skills().values() if s.uri == uri), None)


# ---------------------------------------------------------------- extension (SEP-2640)
class SkillsListParams(RequestParams):
    cursor: str | None = None


class SkillsGetParams(RequestParams):
    uri: str


def _cache_fields() -> dict:
    return {"resultType": "complete", "ttlMs": TTL_MS, "cacheScope": "public"}


async def _skills_list(ctx: Any, params: SkillsListParams) -> dict:
    return {"skills": [s.entry() for s in skills().values()], **_cache_fields()}  # one page, no nextCursor


async def _skills_get(ctx: Any, params: SkillsGetParams) -> dict:
    s = _by_uri(params.uri)
    if s is None:
        raise MCPError(code=INVALID_PARAMS, message=f"Unknown skill: {params.uri}", data={"uri": params.uri})
    return {"skill": s.entry(), **_cache_fields()}


class SkillsExtension(Extension):
    identifier = EXTENSION_ID

    def settings(self) -> dict[str, Any]:
        return {"directoryRead": False}

    def resources(self) -> list[ResourceBinding]:
        out = []
        for s in skills().values():
            for f in s.files:
                out.append(ResourceBinding(TextResource(
                    uri=f.uri, name=f"{s.name}/{f.path}", mime_type=f.mime, text=f.text,
                    description=str(s.frontmatter["description"])[:300] if f.path == "SKILL.md" else None)))
        return out

    def methods(self) -> list[MethodBinding]:
        return [MethodBinding("skills/list", SkillsListParams, _skills_list),
                MethodBinding("skills/get", SkillsGetParams, _skills_get)]


# ---------------------------------------------------------------- tool for hosts without the extension
def skill_lesen(skill: str | None = None, datei: str | None = None) -> dict:
    """No skill: catalogue. Skill: SKILL.md + file list. Skill + datei: that supporting file."""
    cat = skills()
    if not skill:
        return {"skillovi": [{"skill": s.name, "opis": s.frontmatter["description"], "datoteke": len(s.files)}
                             for s in cat.values()],
                "napomena": "Učitaj skill: skill_lesen(skill='…'); pomoćnu datoteku: skill_lesen(skill='…', datei='references/…')."}
    s = cat.get(skill)
    if s is None:
        raise InputError(f"Skill unbekannt / nepoznat skill: {skill!r}; erlaubt: {sorted(cat)}")
    path = (datei or "SKILL.md").strip().removeprefix("./")
    f = s.file(path)
    if f is None:
        raise InputError(f"Datei {datei!r} nicht im Skill {skill}; vorhanden: {[x.path for x in s.files]}")
    out = {"skill": s.name, "datei": f.path, "uri": f.uri, "sadrzaj": f.text}
    if f.path == "SKILL.md":
        out["datoteke"] = [x.path for x in s.files if x.path != "SKILL.md"]
        out["napomena"] = "Relativne putanje u tekstu odnose se na korijen skilla – učitaj ih sa datei='…'."
    return out
