"""Entry point for hosts that start Python apps with `python app.py` (Manufact auto-detection).

Uses the uv-created .venv next to this file if the current interpreter is not that venv.
Equivalent to the `jsi-mcp-server` console script.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
VENV = os.path.join(HERE, ".venv")
VENV_PY = os.path.join(VENV, "bin", "python")

if os.path.exists(VENV_PY) and os.path.realpath(sys.prefix) != os.path.realpath(VENV):
    os.execv(VENV_PY, [VENV_PY, os.path.abspath(__file__), *sys.argv[1:]])

sys.path.insert(0, os.path.join(HERE, "src"))

from jsi_mcp.server import main  # noqa: E402

if __name__ == "__main__":
    main()
