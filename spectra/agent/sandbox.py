"""Run design programs in an isolated subprocess (timeout, no shared state)."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from ..paths import ROOT


def _creationflags() -> int:
    """Keep non-interactive helper processes headless on Windows."""
    return getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0


def run_program(src: str, params_list=None, spec=None, timeout=60):
    params_list = params_list if params_list is not None else [{}]
    d = tempfile.mkdtemp(prefix="prog_")
    Path(d, "prog.py").write_text(src)
    Path(d, "jobs.json").write_text(json.dumps({"spec": spec or {}, "params": params_list}, default=float))
    env = dict(os.environ, PYTHONPATH=str(ROOT))
    try:
        p = subprocess.run([sys.executable, "-m", "spectra.agent.sandbox_worker", f"{d}/prog.py", f"{d}/jobs.json",
                            f"{d}/out.json"], capture_output=True, text=True, timeout=timeout, env=env, cwd=d,
                            creationflags=_creationflags())
        if not Path(d, "out.json").exists():
            return {"ok": False, "error": (p.stderr or p.stdout)[-2500:] or "program produced no output"}
        return json.loads(Path(d, "out.json").read_text())
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": f"program timed out after {timeout}s"}
    finally:
        shutil.rmtree(d, ignore_errors=True)
