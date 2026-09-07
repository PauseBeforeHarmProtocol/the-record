"""Shared, offline publication gates with an actual execution receipt."""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEXT_SUFFIXES = {".html", ".js", ".css", ".json", ".md", ".txt", ".csv", ".py", ".yml", ".yaml"}
SECRET_PATTERNS = [re.compile(p) for p in (
    r"github_pat_[A-Za-z0-9_]{20,}", r"ghp_[A-Za-z0-9]{20,}",
    r"moltbook_sk_[A-Za-z0-9_-]{15,}", r"sk-proj-[A-Za-z0-9_-]{20,}",
    r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----",
)]


def now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def scan_text(data: bytes, name: str) -> None:
    if any(p.search(data.decode("utf-8", errors="ignore")) for p in SECRET_PATTERNS):
        raise ValueError(f"possible credential in {name}; matching value withheld")


def zip_gate(path: Path, *, scan: bool = False) -> None:
    def inspect(data, label, depth=0):
        with zipfile.ZipFile(data) as archive:
            bad = archive.testzip()
            if bad:
                raise ValueError(f"ZIP integrity failed: {label}:{bad}")
            if scan:
                for member in archive.infolist():
                    suffix = Path(member.filename).suffix.lower()
                    if suffix in TEXT_SUFFIXES:
                        scan_text(archive.read(member), f"{label}:{member.filename}")
                    elif suffix == ".zip":
                        if depth >= 5:
                            raise ValueError("nested ZIP exceeds inspection depth")
                        inspect(io.BytesIO(archive.read(member)), f"{label}:{member.filename}", depth + 1)
    inspect(path, path.name)


def input_paths() -> list[Path]:
    names = subprocess.check_output(["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"], cwd=ROOT).split(b"\0")
    return [ROOT / os.fsdecode(n) for n in sorted(set(names) - {b""}) if (ROOT / os.fsdecode(n)).is_file()]


def inventory_hash() -> str:
    result = hashlib.sha256()
    for path in input_paths():
        result.update(path.relative_to(ROOT).as_posix().encode() + b"\0")
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                result.update(chunk)
    return result.hexdigest()


def local_gate(name: str) -> None:
    if name == "preflight":
        import bs4  # noqa: F401
        import jsonschema  # noqa: F401
        if not shutil.which("node"):
            raise ValueError("Node is required")
    elif name == "zip-integrity":
        paths = sorted((ROOT / "artifacts").rglob("*.zip"))
        for path in paths:
            zip_gate(path)
        print(f"PASS: {len(paths)} ZIP integrity tests")
    elif name == "credentials":
        for path in input_paths():
            if path.suffix.lower() in TEXT_SUFFIXES:
                scan_text(path.read_bytes(), str(path.relative_to(ROOT)))
        for path in (ROOT / "artifacts").rglob("*.zip"):
            zip_gate(path, scan=True)
        print("PASS: repository and nested package credential scan")


def execute_steps(steps: list, receipt: dict, output: Path, env: dict) -> int:
    failed = False
    receipt["steps"] = []
    for name, command in steps:
        row = {"name": name, "command": command, "status": "not_run"}
        receipt["steps"].append(row)
        if not failed:
            row["started_at"] = now()
            print(f"CHECK: {name}", flush=True)
            try:
                row["exit_code"] = subprocess.run(command, cwd=ROOT, env=env, timeout=900).returncode
            except (OSError, subprocess.TimeoutExpired) as exc:
                row.update(exit_code=1, error=type(exc).__name__)
            row["finished_at"] = now()
            failed = row["exit_code"] != 0
            row["status"] = "failed" if failed else "passed"
        output.write_text(json.dumps(receipt, indent=2) + "\n")
    if not failed and receipt.get("input_sha256"):
        final_hash = inventory_hash()
        receipt["verified_input_sha256"] = final_hash
        failed = final_hash != receipt["input_sha256"]
        receipt["steps"].append({"name": "input-stability", "status": "failed" if failed else "passed",
                                 "finished_at": now(), "note": "Final input inventory must equal the tested inventory."})
    receipt.update(finished_at=now(), status="failed" if failed else "passed")
    output.write_text(json.dumps(receipt, indent=2) + "\n")
    return int(failed)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-ref", default=os.environ.get("RECORD_BASE_REF"))
    parser.add_argument("--receipt", type=Path)
    parser.add_argument("--gate", choices=("preflight", "zip-integrity", "credentials"))
    args = parser.parse_args()
    if args.gate:
        try:
            local_gate(args.gate)
        except (ValueError, OSError, ImportError, zipfile.BadZipFile) as exc:
            print(f"FAIL: {exc}", file=sys.stderr)
            return 1
        return 0
    if not args.receipt or args.receipt.resolve().is_relative_to(ROOT):
        parser.error("--receipt must be outside the checkout to avoid self-referential hashes")
    output = args.receipt.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    receipt = {"schema_version": "1.0.0", "started_at": now(), "status": "failed", "steps": []}
    output.write_text(json.dumps(receipt, indent=2) + "\n")
    try:
        if not args.base_ref or args.base_ref.startswith("-") or re.fullmatch(r"0+", args.base_ref):
            raise ValueError("valid --base-ref required; publication ancestry checks cannot be skipped")
        base = subprocess.check_output(["git", "rev-parse", "--verify", f"{args.base_ref}^{{commit}}"], cwd=ROOT, text=True).strip()
    except (ValueError, subprocess.CalledProcessError) as exc:
        receipt["error"] = str(exc)
        output.write_text(json.dumps(receipt, indent=2) + "\n")
        return 1
    receipt.update(base_commit=base, input_sha256=inventory_hash(),
                   head_commit=subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip())
    py = sys.executable
    specs = [
        ("dependencies", "accept_release.py", ["--gate", "preflight"]),
        ("truth-fallback", "update_truth_social_feed.py", ["--check"]),
        ("source-ledger", "sync_source_ledger.py", ["--check"]),
        ("legacy-revisions", "apply_legacy_remediations.py", ["--check", "--base-ref", base]),
        ("legacy-parity", "sync_legacy_data.py", ["--check"]),
        ("legacy-custody", "restore_v13_legacy_records.py", ["--check"]),
        ("archive-metrics", "build_archive_metrics.py", ["--check"]),
        ("readme-metrics", "sync_readme_metrics.py", ["--check"]),
        ("federation-schema-self-test", "validate_federated_records.py", ["--self-test"]),
        ("editorial-state", "validate_editorial_state.py", ["--base-ref", base]),
        ("archive-bridge", "build_legacy_bridge.py", ["--check"]),
        ("timeline-runtime", "smoke_test_timeline.py", []),
        ("packaging", "package_current_release.py", ["--check"]),
        ("current-pages", "build_current_pages.py", ["--check"]),
        ("repository", "validate.py", []),
    ]
    steps = [(name, [py, f"scripts/{script}", *args]) for name, script, args in specs]
    steps += [("regression-tests", [py, "-m", "unittest", "discover", "-s", "tests", "-v"])]
    steps += [("javascript-" + Path(p).stem, ["node", "--check", p]) for p in ("assets/site.js", "current_layer_bridge.js", "assets/truth-feed.js")]
    steps += [("python-compilation", [py, "-m", "compileall", "-q", "scripts", "tests"]),
              ("zip-integrity", [py, "scripts/accept_release.py", "--gate", "zip-integrity"]),
              ("credential-scan", [py, "scripts/accept_release.py", "--gate", "credentials"]),
              ("whitespace", ["git", "diff", "--check"])]
    with tempfile.TemporaryDirectory(prefix="record-bytecode-") as cache:
        return execute_steps(steps, receipt, output, dict(os.environ, CURRENT_REMEDIATION_BASE_REF=base, PYTHONPYCACHEPREFIX=cache))


if __name__ == "__main__":
    raise SystemExit(main())
