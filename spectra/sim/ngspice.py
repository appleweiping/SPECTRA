"""Thin, robust ngspice batch runner.

Every simulation is a self-contained netlist with a .control block that emits
scalar results as lines of the form ``@@ name value`` and optionally vectors
through ``wrdata``.  Runs are isolated in temporary directories and can be
executed in parallel.
"""
from __future__ import annotations

import hashlib
import os
import re
import shutil
import subprocess
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path

from ..paths import PDK_LIB

SPICEINIT = "set ngbehavior=hsa\nset ng_nomodcheck\nset num_threads=1\n"
_RES_RE = re.compile(r"^@@\s+(\S+)\s+(\S+)")
_FLOAT_RE = re.compile(r"^[-+]?(\d+\.?\d*|\.\d+)([eE][-+]?\d+)?$")

# global counter of simulator invocations (for budget accounting)
SIM_COUNTER = {"calls": 0, "seconds": 0.0}
import threading as _th
try:
    import fcntl as _fcntl
except ImportError:  # Windows has no flock; local runs are unsupported for experiments but imports stay usable.
    _fcntl = None
import contextlib as _ctx
_SIM_SEM = _th.BoundedSemaphore(int(os.environ.get("SPECTRA_SIM_CONCURRENCY", os.cpu_count() or 4)))
_GLOBAL_SLOTS = int(os.environ.get("SPECTRA_GLOBAL_SIM_SLOTS", "5"))     # machine-wide cap across processes
_SLOT_DIR = os.path.join(tempfile.gettempdir(), "spectra_sim_slots")


def _creationflags() -> int:
    """Suppress a console window for headless simulator jobs on Windows."""
    return getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0


@_ctx.contextmanager
def _global_slot():
    """Cross-process limit on concurrent ngspice processes (flock on one of N slot files)."""
    if _fcntl is None:
        yield
        return
    os.makedirs(_SLOT_DIR, exist_ok=True)
    while True:
        for i in range(_GLOBAL_SLOTS):
            f = open(f"{_SLOT_DIR}/slot{i}", "w")
            try:
                _fcntl.flock(f, _fcntl.LOCK_EX | _fcntl.LOCK_NB)
            except BlockingIOError:
                f.close(); continue
            try:
                yield
            finally:
                _fcntl.flock(f, _fcntl.LOCK_UN); f.close()
            return
        time.sleep(0.05)


@dataclass
class SimResult:
    ok: bool
    scalars: dict = field(default_factory=dict)
    vectors: dict = field(default_factory=dict)
    log: str = ""
    error: str = ""
    seconds: float = 0.0


def lib_line(corner: str = "tt") -> str:
    return f'.lib "{PDK_LIB}" {corner}'


def _parse_wrdata(path: Path):
    import numpy as np
    try:
        arr = np.loadtxt(path, ndmin=2)
    except Exception:
        return None
    return arr


_CACHE_DIR = os.environ.get("SPECTRA_SIM_CACHE", str(Path(__file__).resolve().parents[2] / "data" / "sim_cache"))


def _cache_get(key):
    import gzip, pickle
    fp = Path(_CACHE_DIR) / key[:2] / f"{key}.pkl.gz"
    if fp.exists():
        try:
            with gzip.open(fp, "rb") as f:
                return pickle.load(f)
        except Exception:
            return None
    return None


def _cache_put(key, res):
    import gzip, pickle
    fp = Path(_CACHE_DIR) / key[:2] / f"{key}.pkl.gz"
    fp.parent.mkdir(parents=True, exist_ok=True)
    tmp = fp.with_suffix(f".tmp{os.getpid()}_{_th.get_ident()}")
    with gzip.open(tmp, "wb", compresslevel=3) as f:
        pickle.dump(res, f)
    os.replace(tmp, fp)


def run(netlist: str, wrdata_files: tuple = (), timeout: float = 60.0,
        keep_dir: str | None = None) -> SimResult:
    """Run one ngspice batch job. ``wrdata_files`` lists file names the
    control block writes via ``wrdata`` that should be loaded as arrays.
    Results are cached on disk by the hash of (netlist, files): ngspice is deterministic."""
    key = hashlib.sha1((netlist + "|" + ",".join(wrdata_files)).encode()).hexdigest()
    if not keep_dir and os.environ.get("SPECTRA_SIM_CACHE_OFF") != "1":
        hit = _cache_get(key)
        if hit is not None:
            return hit
    t0 = time.time()
    d = tempfile.mkdtemp(prefix="ngs_")
    try:
        Path(d, ".spiceinit").write_text(SPICEINIT)
        Path(d, "c.sp").write_text(netlist)
        try:
            with _SIM_SEM, _global_slot():
                p = subprocess.run(["ngspice", "-b", "c.sp"], cwd=d, capture_output=True,
                                   text=True, timeout=timeout, creationflags=_creationflags())
            out = p.stdout + "\n" + p.stderr
        except subprocess.TimeoutExpired as e:
            SIM_COUNTER["calls"] += 1
            SIM_COUNTER["seconds"] += time.time() - t0
            return SimResult(False, error="timeout", log=str(e)[:2000], seconds=time.time() - t0)
        scalars = {}
        for line in out.splitlines():
            m = _RES_RE.match(line.strip())
            if m:
                v = m.group(2)
                if _FLOAT_RE.match(v):
                    scalars[m.group(1)] = float(v)
                else:
                    scalars[m.group(1)] = None  # failed measurement
        vectors = {}
        for f in wrdata_files:
            fp = Path(d, f)
            if fp.exists():
                vectors[f] = _parse_wrdata(fp)
        err = ""
        low = out.lower()
        fatal_markers = ["error:", "fatal", "singular matrix", "timestep too small",
                         "no convergence", "gmin stepping failed", "source stepping failed",
                         "could not find", "unknown subckt", "unknown model"]
        errs = [l for l in out.splitlines() if any(k in l.lower() for k in fatal_markers)]
        if errs:
            err = "\n".join(errs[:12])
        ok = ("simulation interrupted" not in low) and not any(
            k in low for k in ["singular matrix", "timestep too small", "unknown subckt",
                               "could not find", "too few nodes"])
        if keep_dir:
            shutil.copytree(d, keep_dir, dirs_exist_ok=True)
        dt = time.time() - t0
        SIM_COUNTER["calls"] += 1
        SIM_COUNTER["seconds"] += dt
        res = SimResult(ok, scalars, vectors, out[-6000:], err, dt)
        if not keep_dir:
            try:
                _cache_put(key, res)
            except Exception:
                pass
        return res
    finally:
        shutil.rmtree(d, ignore_errors=True)


def run_many(netlists: list, wrdata_files: tuple = (), timeout: float = 60.0,
             workers: int | None = None) -> list:
    workers = workers or int(os.environ.get("SPECTRA_SIM_WORKERS", os.cpu_count() or 2))
    with ThreadPoolExecutor(max_workers=workers) as ex:
        return list(ex.map(lambda n: run(n, wrdata_files, timeout), netlists))


def netlist_hash(text: str) -> str:
    return hashlib.sha1(text.encode()).hexdigest()[:16]
