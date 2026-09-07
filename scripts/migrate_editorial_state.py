"""One-time, explicit migration of publication provenance, never source review."""
from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path

from editorial_state import ROOT, canonical_bytes, digest, entry_content_hash, legacy_checked_at


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-ref", required=True)
    args = parser.parse_args()
    target = ROOT / "data/editorial_state.json"
    if target.exists():
        raise SystemExit("Refusing to overwrite an existing editorial-state ledger")
    base = subprocess.check_output(["git", "rev-parse", args.base_ref], cwd=ROOT, text=True).strip()
    entries = json.loads((ROOT / "data/current_entries.json").read_text())
    ledger = json.loads((ROOT / "data/source_ledger.json").read_text())
    by_id = {e["id"]: e for e in entries}
    changes = []
    for path in sorted((ROOT / "artifacts").glob("THE_RECORD_RUN_RECEIPT_*_v10.*.md")):
        text = path.read_text()
        version = re.search(r"^- Release: (\S+)", text, re.M)
        checked = re.search(r"^- Checked: (.+)", text, re.M)
        section = re.search(r"## Added or materially refreshed records\n(.*?)(?:\n## |\Z)", text, re.S)
        if not version or not checked or not section:
            continue
        for entry_id in re.findall(r"^- `(NAT-[^`]+)`", section[1], re.M):
            if entry_id not in by_id:
                continue
            changes.append({"change_id": f"{version[1]}:{entry_id}", "entry_id": entry_id,
                            "as_of_utc": legacy_checked_at(checked[1]), "timestamp_precision": "minute",
                            "kind": "published_development", "release_version": version[1],
                            "summary": f"Added or materially refreshed in release {version[1]}.",
                            "provenance_path": path.relative_to(ROOT).as_posix(), "provenance_sha256": digest(path.read_bytes()),
                            "note": "Migrated from the publication receipt, not a fresh source inspection or a new event date."})
    state = {"schema_version": "1.0.0", "baseline": {"commit": base, "release_version": "10.31.1",
             "policy": "Existing content retains its prior review state; claim-level review has not been retroactively asserted.",
             "entry_hashes": {e["id"]: entry_content_hash(e, ledger) for e in entries}},
             "developments": sorted(changes, key=lambda d: (d["as_of_utc"], d["change_id"])),
             "reviews": [], "deferred_candidates": []}
    target.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n")


if __name__ == "__main__":
    main()
