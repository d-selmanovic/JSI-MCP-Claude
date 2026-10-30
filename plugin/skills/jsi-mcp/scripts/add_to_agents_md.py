#!/usr/bin/env python3
"""Writes (or updates) the JSI-MCP block in an AGENTS.md so the agent knows it has the JSI tools.

Idempotent: the block between the JSI-MCP markers is replaced, everything else stays untouched.
Usage: python3 -I add_to_agents_md.py [path/to/AGENTS.md]   (default: ./AGENTS.md)
       python3 -I add_to_agents_md.py --remove [path]
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SNIPPET = os.path.join(HERE, "..", "references", "AGENTS.snippet.md")
BLOCK = re.compile(r"<!-- JSI-MCP:BEGIN.*?<!-- JSI-MCP:END -->\n?", re.S)


def main(argv):
    remove = "--remove" in argv
    args = [a for a in argv if a != "--remove"]
    target = args[0] if args else "AGENTS.md"
    text = open(target, encoding="utf-8").read() if os.path.exists(target) else ""
    block = "" if remove else open(SNIPPET, encoding="utf-8").read()
    if BLOCK.search(text):
        new = BLOCK.sub(lambda _: block, text, count=1)
    elif remove:
        new = text
    else:
        new = (text.rstrip("\n") + "\n\n" if text.strip() else "") + block
    if remove:
        new = new.rstrip("\n") + "\n" if new.strip() else ""
    if new != text:
        with open(target, "w", encoding="utf-8") as f:
            f.write(new)
    print(("removed from " if remove else "updated ") + target if new != text else "unchanged " + target)


if __name__ == "__main__":
    main(sys.argv[1:])
