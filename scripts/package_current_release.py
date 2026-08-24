from __future__ import annotations

import argparse
import hashlib
import io
import json
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts"
ENTRY_DIR = ARTIFACTS / "entries"
RELEASE = json.loads((ROOT / "data/release.json").read_text(encoding="utf-8"))
RELEASE_ISO = RELEASE["release_iso"]
RELEASE_HUMAN = RELEASE["release_human"]
CHECKED_AT = RELEASE["checked_at"]
VERSION = RELEASE["version"]
NEW_ENTRY_IDS = set(RELEASE["new_entry_ids"])
year, month, day = (int(part) for part in RELEASE_ISO.split("-"))
FIXED_ZIP_TIME = (year, month, day, 12, 0, 0)
NATIONAL_BRIEF_NAME = f"THE_RECORD_NATIONAL_UPDATE_BRIEF_{RELEASE_ISO}.md"
RUN_RECEIPT_NAME = f"THE_RECORD_RUN_RECEIPT_{RELEASE_ISO}.md"
NATIONAL_PACK_NAME = f"THE_RECORD_NATIONAL_UPDATE_PACK_{RELEASE_ISO}.zip"
COMPLETE_PACK_NAME = f"THE_RECORD_CURRENT_UPDATE_PACK_{RELEASE_ISO}.zip"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def stable_zip(files: dict[str, bytes]) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name in sorted(files):
            info = zipfile.ZipInfo(name, FIXED_ZIP_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            info.create_system = 3
            archive.writestr(info, files[name])
    return buffer.getvalue()


def as_json(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode()


def source_lines(entry: dict, ledger: dict) -> list[str]:
    return [
        f'- [{ledger[source_id]["name"]}]({ledger[source_id]["url"]}) — {ledger[source_id]["type"]}'
        for source_id in entry["sources"]
    ]


def entry_markdown(entry: dict, ledger: dict) -> bytes:
    facts = "\n".join(f'- {fact}' for fact in entry["facts"])
    sources = "\n".join(source_lines(entry, ledger))
    corrections = ""
    if entry.get("corrections"):
        correction_lines = "\n".join(
            f'- **{item["timestamp"]}** — {item["note"]}' for item in entry["corrections"]
        )
        corrections = f"\n## CORRECTIONS\n\n{correction_lines}\n"
    text = f'''# {entry["title"]}

**Entry ID:** {entry["id"]}
**Date:** {entry["display_date"]}
**Checked:** {entry["checked_at"]}
**Evidence state:** {entry["evidence"]}

{entry["dek"]}

## THE FACTS

{facts}

## SIGNIFICANCE

{entry["significance"]}

## GOALPOST / RESPONSE

{entry["goalpost"]}
{corrections}

## SOURCES

{sources}

## SCOPE NOTE

This entry is a dated, source-bound update. It does not by itself revalidate every legacy entry in The Record.
'''
    return text.encode()


def entry_pack(entry: dict, ledger: dict) -> bytes:
    source_subset = {source_id: ledger[source_id] for source_id in entry["sources"]}
    return stable_zip({
        "ENTRY.md": entry_markdown(entry, ledger),
        "VERIFY.txt": b"Verify this pack by comparing its SHA-256 digest with the adjacent .sha256 file.\n",
        "entry.json": as_json(entry),
        "sources.json": as_json(source_subset),
    })


def national_brief(entries: list[dict], ledger: dict) -> bytes:
    sections = [
        "# The Record — National Update Brief",
        "",
        f"**Release:** {RELEASE_HUMAN}",
        f"**Checked:** {CHECKED_AT}",
        "",
        "Each item preserves The Record's three-layer distinction: facts, significance, and the observed response or goalpost.",
    ]
    national = sorted(
        (entry for entry in entries if entry["scope"] == "national"),
        key=lambda entry: (entry["date"], entry["id"]),
        reverse=True,
    )
    for entry in national:
        sections.extend([
            "",
            f'## {entry["display_date"]} — {entry["title"]}',
            "",
            entry["dek"],
            "",
            "**THE FACTS**",
            "",
            *(f'- {fact}' for fact in entry["facts"]),
            "",
            "**SIGNIFICANCE**",
            "",
            entry["significance"],
            "",
            "**GOALPOST / RESPONSE**",
            "",
            entry["goalpost"],
            "",
            "**Sources**",
            "",
            *source_lines(entry, ledger),
        ])
    return ("\n".join(sections) + "\n").encode()


def run_receipt(entries: list[dict], ledger: dict) -> bytes:
    by_id = {entry["id"]: entry for entry in entries}
    added = [by_id[entry_id] for entry_id in RELEASE["new_entry_ids"]]
    rejected = RELEASE.get("rejected_candidates", [])
    lines = [
        "# The Record — Maintenance Run Receipt",
        "",
        f"- Release: {VERSION}",
        f"- Checked: {CHECKED_AT}",
        f"- Editorial cutoff: {RELEASE['cutoff_start']} through {RELEASE_ISO}",
        f"- Added or materially refreshed: {len(added)} national records",
        f"- Current layer: {len(entries)} records backed by {len(ledger)} source-ledger records",
        "",
        "## Added or materially refreshed records",
        "",
        *(f'- `{entry["id"]}` — {entry["title"]}' for entry in added),
        "",
        "## Withheld candidates",
        "",
    ]
    if rejected:
        lines.extend(f'- {item["title"]}: {item["reason"]}' for item in rejected)
    else:
        lines.append("- None recorded in this run.")
    lines.extend([
        "",
        "## Verification",
        "",
        "Current front-door pages, the archive's lightweight live bridge, individual evidence packs, aggregate packs, source ledgers, and checksums are generated deterministically. The 14 MB historical application stays stable while current national entries are supplied by current_layer_bridge.js. Publication requires the repository validator and GitHub Actions to pass.",
    ])
    return ("\n".join(lines) + "\n").encode()


def adjacent_checksum(name: str, data: bytes) -> bytes:
    return f"{digest(data)}  {name}\n".encode()


def build_outputs() -> dict[Path, bytes]:
    entries = json.loads((ROOT / "data/current_entries.json").read_text(encoding="utf-8"))
    ledger = json.loads((ROOT / "data/source_ledger.json").read_text(encoding="utf-8"))
    by_id = {entry["id"]: entry for entry in entries}
    missing_new_ids = NEW_ENTRY_IDS - set(by_id)
    if missing_new_ids:
        raise ValueError(f"release.json names unknown entries: {sorted(missing_new_ids)}")

    outputs: dict[Path, bytes] = {}
    for entry in entries:
        entry_path = ENTRY_DIR / entry["pack_filename"]
        if entry["id"] in NEW_ENTRY_IDS or not entry_path.exists():
            entry_bytes = entry_pack(entry, ledger)
            outputs[entry_path] = entry_bytes
            outputs[entry_path.with_suffix(entry_path.suffix + ".sha256")] = adjacent_checksum(
                entry_path.name, entry_bytes
            )

    def artifact_bytes(path: Path) -> bytes:
        if path in outputs:
            return outputs[path]
        return path.read_bytes()

    brief_bytes = national_brief(entries, ledger)
    brief_path = ARTIFACTS / NATIONAL_BRIEF_NAME
    outputs[brief_path] = brief_bytes

    receipt_bytes = run_receipt(entries, ledger)
    receipt_path = ARTIFACTS / RUN_RECEIPT_NAME
    outputs[receipt_path] = receipt_bytes

    national_entries = [entry for entry in entries if entry["scope"] == "national"]
    in6_entries = [entry for entry in entries if entry["scope"] == "in6"]
    national_files = {
        "README.md": (
            "# NATIONAL update pack\n\n"
            f"Release: {RELEASE_HUMAN}\nChecked: {CHECKED_AT}\n"
            f"Contains {len(national_entries)} national records; {len(NEW_ENTRY_IDS)} were added or materially refreshed in this run.\n"
        ).encode(),
        NATIONAL_BRIEF_NAME: brief_bytes,
        RUN_RECEIPT_NAME: receipt_bytes,
        "data/release.json": (ROOT / "data/release.json").read_bytes(),
        "source_ledger.csv": (ROOT / "data/source_ledger.csv").read_bytes(),
        "source_ledger.json": (ROOT / "data/source_ledger.json").read_bytes(),
    }
    for entry in national_entries:
        pack_path = ENTRY_DIR / entry["pack_filename"]
        national_files[f'entries/{entry["pack_filename"]}'] = artifact_bytes(pack_path)
        national_files[f'entries/{entry["pack_filename"]}.sha256'] = artifact_bytes(
            pack_path.with_suffix(pack_path.suffix + ".sha256")
        )
    national_pack = stable_zip(national_files)
    national_path = ARTIFACTS / NATIONAL_PACK_NAME
    outputs[national_path] = national_pack
    outputs[national_path.with_suffix(national_path.suffix + ".sha256")] = adjacent_checksum(
        national_path.name, national_pack
    )

    complete_files = {
        "README.md": (
            "# The Record current update pack\n\n"
            f"Release: {VERSION}\nRelease date: {RELEASE_HUMAN}\nChecked: {CHECKED_AT}\n\n"
            f"Contains {len(national_entries)} national and {len(in6_entries)} IN-6 current-layer records. "
            "The complete Trump archive consumes the national layer through current_layer_bridge.js while its historical body remains stable.\n"
        ).encode(),
        NATIONAL_BRIEF_NAME: brief_bytes,
        RUN_RECEIPT_NAME: receipt_bytes,
        "EDITORIAL_AUTOMATION.md": (ROOT / "EDITORIAL_AUTOMATION.md").read_bytes(),
        "current_layer_bridge.js": (ROOT / "current_layer_bridge.js").read_bytes(),
        "data/current_entries.json": (ROOT / "data/current_entries.json").read_bytes(),
        "data/release.json": (ROOT / "data/release.json").read_bytes(),
        "data/source_ledger.csv": (ROOT / "data/source_ledger.csv").read_bytes(),
        "data/source_ledger.json": (ROOT / "data/source_ledger.json").read_bytes(),
    }
    in6_brief = ARTIFACTS / "THE_RECORD_IN6_UPDATE_BRIEF_2026-07-18.md"
    if in6_brief.exists():
        complete_files[in6_brief.name] = in6_brief.read_bytes()
    for entry in entries:
        pack_path = ENTRY_DIR / entry["pack_filename"]
        complete_files[f'entries/{entry["pack_filename"]}'] = artifact_bytes(pack_path)
        complete_files[f'entries/{entry["pack_filename"]}.sha256'] = artifact_bytes(
            pack_path.with_suffix(pack_path.suffix + ".sha256")
        )
    complete_pack = stable_zip(complete_files)
    complete_path = ARTIFACTS / COMPLETE_PACK_NAME
    outputs[complete_path] = complete_pack
    outputs[complete_path.with_suffix(complete_path.suffix + ".sha256")] = adjacent_checksum(
        complete_path.name, complete_pack
    )

    checksum_candidates = {
        *ARTIFACTS.glob("*.md"),
        *ARTIFACTS.glob("*.zip"),
        *ENTRY_DIR.glob("*.zip"),
        *(path for path in outputs if path.suffix in {".md", ".zip"}),
    }
    checksum_rows = []
    for path in sorted(checksum_candidates, key=lambda item: item.relative_to(ARTIFACTS).as_posix()):
        data = artifact_bytes(path)
        checksum_rows.append(f"{digest(data)}  {path.relative_to(ARTIFACTS).as_posix()}")
    outputs[ARTIFACTS / "SHA256SUMS.txt"] = ("\n".join(checksum_rows) + "\n").encode()
    return outputs


def main() -> int:
    parser = argparse.ArgumentParser(description="Build deterministic current-release artifacts from data/release.json.")
    parser.add_argument("--check", action="store_true", help="fail if committed artifacts differ from generated bytes")
    args = parser.parse_args()
    outputs = build_outputs()
    mismatches = []
    for path, expected in outputs.items():
        if args.check:
            if not path.exists() or path.read_bytes() != expected:
                mismatches.append(path.relative_to(ROOT).as_posix())
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(expected)
    if mismatches:
        print("Release artifacts are stale:")
        print("\n".join(f"- {path}" for path in mismatches))
        return 1
    print(f"{'Verified' if args.check else 'Built'} {len(outputs)} deterministic release artifacts.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
