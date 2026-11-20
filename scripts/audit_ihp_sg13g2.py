"""Audit the IHP SG13G2 PDK and run a minimal native ngspice smoke.

This is a capability audit. It never promotes a PDK checkout to a sizing
benchmark row because a matched task, independent verifier and external row
are required for ranking.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import time
from pathlib import Path


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def osdi_inventory(osdi_dir: Path | None) -> list[dict] | None:
    if osdi_dir is None:
        return None
    return [
        {
            "name": path.name,
            "size_bytes": path.stat().st_size,
            "sha256": sha256_file(path),
        }
        for path in sorted(osdi_dir.glob("*.osdi"))
    ]


def git_value(root: Path, *args: str) -> str | None:
    try:
        return subprocess.check_output(
            ["git", "-C", str(root), *args], text=True, stderr=subprocess.DEVNULL
        ).strip()
    except (OSError, subprocess.SubprocessError):
        return None


def source_digest(root: Path) -> tuple[int, str]:
    names = []
    for path in root.rglob("*"):
        # OpenVAF writes generated OSDI binaries under libs.tech/ngspice/osdi.
        # They are runtime artifacts and must not change the pinned source-tree
        # inventory when the audit is rerun after model compilation.
        if (
            path.is_file()
            and ".git" not in path.parts
            and "osdi" not in path.relative_to(root).parts
        ):
            names.append(path.relative_to(root).as_posix())
    names.sort()
    payload = "\0".join(names).encode("utf-8")
    return len(names), hashlib.sha256(payload).hexdigest()


def run_smoke(
    pdk_root: Path,
    simulator: Path,
    work_root: Path,
    timeout: int,
    osdi_dir: Path | None = None,
) -> dict:
    model_dir = pdk_root / "ihp-sg13g2" / "libs.tech" / "ngspice" / "models"
    model_file = model_dir / "cornerMOSlv.lib"
    netlist = work_root / "pmos_nmos_op.cir"
    stdout_path = work_root / "pmos_nmos_op.stdout"
    netlist.write_text(
        """IHP SG13G2 native ngspice smoke
.lib {model} mos_tt
VDD vdd 0 1.2
VG in 0 0.7
RLOAD vdd out 10k
XMN out in 0 0 sg13_lv_nmos w=2u l=0.5u
.op
.control
set filetype=ascii
op
print v(out) i(VDD)
quit
.endc
.end
""".format(model=model_file),
        encoding="utf-8",
    )
    env = None
    if osdi_dir is not None:
        osdi_files = sorted(osdi_dir.glob("*.osdi"))
        if not osdi_files:
            raise FileNotFoundError(f"No OSDI models found in {osdi_dir}")
        spiceinit = work_root / ".spiceinit"
        spiceinit.write_text(
            "\n".join(f"osdi {path}" for path in osdi_files) + "\n",
            encoding="utf-8",
        )
        env = {**os.environ, "HOME": str(work_root)}
    started = time.monotonic()
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    try:
        proc = subprocess.run(
            [str(simulator), "-b", str(netlist)],
            cwd=str(model_dir),
            capture_output=True,
            text=True,
            timeout=timeout,
            creationflags=flags,
            env=env,
        )
        output = proc.stdout + proc.stderr
        rc = proc.returncode
        status = "pass" if rc == 0 else "model_runtime_blocked"
        error = None if rc == 0 else "ngspice returned a non-zero status"
    except subprocess.TimeoutExpired as exc:
        output = (exc.stdout or "") + (exc.stderr or "")
        rc = None
        status = "timeout"
        error = "ngspice smoke exceeded timeout"
    stdout_path.write_text(output, encoding="utf-8")
    return {
        "netlist": netlist.name,
        "attempted": "op",
        "return_code": rc,
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "status": status,
        "error": error,
        "stdout": stdout_path.name,
    }


def run_xyce_smoke(
    pdk_root: Path, xyce: Path, work_root: Path, timeout: int
) -> dict:
    """Probe whether Xyce can consume the source PDK's ngspice deck.

    Xyce does not load ngspice OSDI model plugins. The probe is retained as a
    simulator-coverage boundary and never contributes a sizing score.
    """

    model_file = pdk_root / "ihp-sg13g2" / "libs.tech" / "ngspice" / "models" / "cornerMOSlv.lib"
    netlist = work_root / "pmos_nmos_op_xyce.cir"
    stdout_path = work_root / "pmos_nmos_op_xyce.stdout"
    netlist.write_text(
        """IHP SG13G2 Xyce capability smoke
.lib {model} mos_tt
VDD vdd 0 1.2
VG in 0 0.7
RLOAD vdd out 10k
XMN out in 0 0 sg13_lv_nmos w=2u l=0.5u
.OP
.PRINT OP V(out) I(VDD)
.END
""".format(model=model_file),
        encoding="utf-8",
    )
    started = time.monotonic()
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    try:
        proc = subprocess.run(
            [str(xyce), str(netlist)],
            cwd=str(work_root),
            capture_output=True,
            text=True,
            timeout=timeout,
            creationflags=flags,
        )
        output = proc.stdout + proc.stderr
        rc = proc.returncode
        status = "pass" if rc == 0 else "pdk_deck_unsupported"
        error = None if rc == 0 else "Xyce could not resolve the SG13_LV_NMOS source device"
    except subprocess.TimeoutExpired as exc:
        output = (exc.stdout or "") + (exc.stderr or "")
        rc = None
        status = "timeout"
        error = "Xyce smoke exceeded timeout"
    stdout_path.write_text(output, encoding="utf-8")
    return {
        "netlist": netlist.name,
        "attempted": "op",
        "return_code": rc,
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "status": status,
        "error": error,
        "stdout": stdout_path.name,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdk-root", type=Path, required=True)
    parser.add_argument("--simulator", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--work-root", type=Path, required=True)
    parser.add_argument(
        "--osdi-dir",
        type=Path,
        default=None,
        help="Optional directory of compiled OSDI models. The audit writes a local .spiceinit.",
    )
    parser.add_argument(
        "--xyce",
        type=Path,
        default=None,
        help="Optional Xyce binary for a source-deck compatibility probe.",
    )
    parser.add_argument("--timeout", type=int, default=60)
    args = parser.parse_args()

    pdk_root = args.pdk_root.resolve()
    args.work_root.mkdir(parents=True, exist_ok=True)
    model_file = pdk_root / "ihp-sg13g2" / "libs.tech" / "ngspice" / "models" / "cornerMOSlv.lib"
    file_count, tree_digest = source_digest(pdk_root)
    smoke = run_smoke(
        pdk_root,
        args.simulator.resolve(),
        args.work_root.resolve(),
        args.timeout,
        args.osdi_dir.resolve() if args.osdi_dir else None,
    )
    xyce_smoke = (
        run_xyce_smoke(
            pdk_root,
            args.xyce.resolve(),
            args.work_root.resolve(),
            args.timeout,
        )
        if args.xyce
        else None
    )
    receipt = {
        "schema": "spectra-ihp-sg13g2-capability/v1",
        "source": "IHP-GmbH/IHP-Open-PDK",
        "source_url": "https://github.com/IHP-GmbH/IHP-Open-PDK",
        "source_commit": git_value(pdk_root, "rev-parse", "HEAD"),
        "source_file_count": file_count,
        "source_tree_filelist_sha256": tree_digest,
        "pdk": "ihp-sg13g2",
        "model_file": str(model_file),
        "model_sha256": sha256_file(model_file) if model_file.exists() else None,
        "simulator": "ngspice-44.2",
        "osdi_dir": str(args.osdi_dir.resolve()) if args.osdi_dir else None,
        "osdi_inventory": osdi_inventory(args.osdi_dir.resolve() if args.osdi_dir else None),
        "ranking_eligible": False,
        "ranking_reason": "No matched sizing task, independent verifier or AnaFlow cell.",
        "smoke": smoke,
        "xyce": {
            "binary": str(args.xyce.resolve()) if args.xyce else None,
            "smoke": xyce_smoke,
        },
    }
    if smoke["status"] != "pass":
        receipt["status"] = "source_audit_pass_" + smoke["status"]
        receipt["ranking_reason"] += " Native smoke did not complete a valid device simulation."
    else:
        receipt["status"] = "source_audit_and_native_smoke_pass"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
