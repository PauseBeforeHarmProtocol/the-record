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
RELEASE_ISO = "2026-07-19"
RELEASE_HUMAN = "July 19, 2026"
CHECKED_AT = "2026-07-19 08:15 AM EDT"
FIXED_ZIP_TIME = (2026, 7, 19, 12, 15, 0)
NEW_ENTRY_ID = "NAT-2026-07-19-001"
NATIONAL_BRIEF_NAME = f"THE_RECORD_NATIONAL_UPDATE_BRIEF_{RELEASE_ISO}.md"
NATIONAL_PACK_NAME = f"THE_RECORD_NATIONAL_UPDATE_PACK_{RELEASE_ISO}.zip"
COMPLETE_PACK_NAME = f"THE_RECORD_JULY_19_UPDATE_PACK_{RELEASE_ISO}.zip"


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
    lines = []
    for source_id in entry["sources"]:
        source = ledger[source_id]
        lines.append(f'- [{source["name"]}]({source["url"]}) — {source["type"]}')
    return lines


def entry_markdown(entry: dict, ledger: dict) -> bytes:
    facts = "\n".join(f'- {fact}' for fact in entry["facts"])
    sources = "\n".join(source_lines(entry, ledger))
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
        "Each item preserves The Record’s three-layer distinction: facts, significance, and the observed response or goalpost.",
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


def adjacent_checksum(name: str, data: bytes) -> bytes:
    return f"{digest(data)}  {name}\n".encode()


def build_outputs() -> dict[Path, bytes]:
    entries = json.loads((ROOT / "data/current_entries.json").read_text(encoding="utf-8"))
    ledger = json.loads((ROOT / "data/source_ledger.json").read_text(encoding="utf-8"))
    by_id = {entry["id"]: entry for entry in entries}
    new_entry = by_id[NEW_ENTRY_ID]

    outputs: dict[Path, bytes] = {}
    new_entry_bytes = entry_pack(new_entry, ledger)
    new_entry_path = ENTRY_DIR / new_entry["pack_filename"]
    outputs[new_entry_path] = new_entry_bytes
    outputs[new_entry_path.with_suffix(new_entry_path.suffix + ".sha256")] = adjacent_checksum(
        new_entry_path.name, new_entry_bytes
    )

    brief_bytes = national_brief(entries, ledger)
    brief_path = ARTIFACTS / NATIONAL_BRIEF_NAME
    outputs[brief_path] = brief_bytes

    def entry_artifact(entry: dict, suffix: str = "") -> bytes:
        path = ENTRY_DIR / f'{entry["pack_filename"]}{suffix}'
        if path in outputs:
            return outputs[path]
        return path.read_bytes()

    national_files = {
        "README.md": f"# NATIONAL update pack\n\nRelease: {RELEASE_HUMAN}\nChecked: {CHECKED_AT}\n".encode(),
        NATIONAL_BRIEF_NAME: brief_bytes,
        "source_ledger.csv": (ROOT / "data/source_ledger.csv").read_bytes(),
        "source_ledger.json": (ROOT / "data/source_ledger.json").read_bytes(),
    }
    for entry in entries:
        if entry["scope"] != "national":
            continue
        national_files[f'entries/{entry["pack_filename"]}'] = entry_artifact(entry)
        national_files[f'entries/{entry["pack_filename"]}.sha256'] = entry_artifact(entry, ".sha256")
    national_pack = stable_zip(national_files)
    national_path = ARTIFACTS / NATIONAL_PACK_NAME
    outputs[national_path] = national_pack
    outputs[national_path.with_suffix(national_path.suffix + ".sha256")] = adjacent_checksum(
        national_path.name, national_pack
    )

    complete_files = {
        "README.md": (
            "# The Record current update pack\n\n"
            f"Release candidate: 8.0.1-rc1\nRelease date: {RELEASE_HUMAN}\n"
            f"Checked: {CHECKED_AT}\n\n"
            "Contains the six national and four IN-6 current-layer records. Historical archives remain separate and preserved.\n"
        ).encode(),
        NATIONAL_BRIEF_NAME: brief_bytes,
        "THE_RECORD_IN6_UPDATE_BRIEF_2026-07-18.md": (
            ARTIFACTS / "THE_RECORD_IN6_UPDATE_BRIEF_2026-07-18.md"
        ).read_bytes(),
        "data/current_entries.json": (ROOT / "data/current_entries.json").read_bytes(),
        "data/source_ledger.csv": (ROOT / "data/source_ledger.csv").read_bytes(),
        "data/source_ledger.json": (ROOT / "data/source_ledger.json").read_bytes(),
    }
    for entry in entries:
        complete_files[f'entries/{entry["pack_filename"]}'] = entry_artifact(entry)
        complete_files[f'entries/{entry["pack_filename"]}.sha256'] = entry_artifact(entry, ".sha256")
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
        brief_path,
        national_path,
        complete_path,
        new_entry_path,
    }
    checksum_rows = []
    for path in sorted(checksum_candidates, key=lambda item: item.relative_to(ARTIFACTS).as_posix()):
        data = outputs.get(path, path.read_bytes() if path.exists() else b"")
        checksum_rows.append(f"{digest(data)}  {path.relative_to(ARTIFACTS).as_posix()}")
    outputs[ARTIFACTS / "SHA256SUMS.txt"] = ("\n".join(checksum_rows) + "\n").encode()
    return outputs


def main() -> int:
    parser = argparse.ArgumentParser(description="Build deterministic July 19 current-release artifacts.")
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
