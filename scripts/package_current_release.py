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
ARCHIVE_METRICS = json.loads((ROOT / "data/archive_metrics.json").read_text(encoding="utf-8"))
TRUTH_META = json.loads((ROOT / "data/truth_social_feed_meta.json").read_text(encoding="utf-8"))
RELEASE_ISO = RELEASE["release_iso"]
RELEASE_HUMAN = RELEASE["release_human"]
CHECKED_AT = RELEASE["checked_at"]
VERSION = RELEASE["version"]
NEW_ENTRY_IDS = set(RELEASE["new_entry_ids"])
year, month, day = (int(part) for part in RELEASE_ISO.split("-"))
FIXED_ZIP_TIME = (year, month, day, 12, 0, 0)
RELEASE_ARTIFACT_STEM = f"{RELEASE_ISO}_v{VERSION}"
NATIONAL_BRIEF_NAME = f"THE_RECORD_NATIONAL_UPDATE_BRIEF_{RELEASE_ARTIFACT_STEM}.md"
IN6_CURRENT_BRIEF_NAME = f"THE_RECORD_IN6_CURRENT_BRIEF_{RELEASE_ARTIFACT_STEM}.md"
RUN_RECEIPT_NAME = f"THE_RECORD_RUN_RECEIPT_{RELEASE_ARTIFACT_STEM}.md"
NATIONAL_PACK_NAME = f"THE_RECORD_NATIONAL_UPDATE_PACK_{RELEASE_ARTIFACT_STEM}.zip"
COMPLETE_PACK_NAME = f"THE_RECORD_CURRENT_UPDATE_PACK_{RELEASE_ARTIFACT_STEM}.zip"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def stable_zip(files: dict[str, bytes], *, compress: bool = True) -> bytes:
    buffer = io.BytesIO()
    compression = zipfile.ZIP_DEFLATED if compress else zipfile.ZIP_STORED
    with zipfile.ZipFile(buffer, "w", compression=compression, compresslevel=9 if compress else None) as archive:
        for name in sorted(files):
            info = zipfile.ZipInfo(name, FIXED_ZIP_TIME)
            info.compress_type = compression
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
    analysis_text = entry["goalpost"]
    if entry.get("maybe_therefore"):
        analysis_text += f'\n\n## MAYBE / THEREFORE\n\n{entry["maybe_therefore"]}'
    text = f'''# {entry["title"]}

**Entry ID:** {entry["id"]}
**Date:** {entry["display_date"]}
**Checked:** {entry["checked_at"]}
**Evidence state:** {entry["evidence"]}
**Review state:** {entry["review_status"]}

{entry["dek"]}

## THE FACTS

{facts}

## SIGNIFICANCE

{entry["significance"]}

## GOALPOST / RESPONSE

{analysis_text}
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


def scoped_brief(
    entries: list[dict], ledger: dict, *, scope: str, title: str
) -> bytes:
    sections = [
        f"# The Record — {title}",
        "",
        f"**Release:** {VERSION} · {RELEASE_HUMAN}",
        f"**Release editorial cutoff:** {CHECKED_AT}",
        "",
        "Each item preserves its own evidence-check time and The Record's labeled distinction between facts, significance, the strongest observed response or goalpost, and any separately reviewed Maybe / Therefore layer.",
    ]
    selected = sorted(
        (entry for entry in entries if entry["scope"] == scope),
        key=lambda entry: (entry["date"], entry["id"]),
        reverse=True,
    )
    for entry in selected:
        sections.extend([
            "",
            f'## {entry["display_date"]} — {entry["title"]}',
            "",
            entry["dek"],
            "",
            f'**Entry evidence checked:** {entry["checked_at"]}',
            "",
            f'**Review state:** {entry["review_status"]}',
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
            *(
                ["", "**MAYBE / THEREFORE**", "", entry["maybe_therefore"]]
                if entry.get("maybe_therefore")
                else []
            ),
            "",
            "**Sources**",
            "",
            *source_lines(entry, ledger),
        ])
    return ("\n".join(sections) + "\n").encode()


def national_brief(entries: list[dict], ledger: dict) -> bytes:
    return scoped_brief(
        entries, ledger, scope="national", title="National Update Brief"
    )


def in6_current_brief(entries: list[dict], ledger: dict) -> bytes:
    return scoped_brief(
        entries, ledger, scope="in6", title="IN-6 Current Brief"
    )


def run_receipt(entries: list[dict], ledger: dict) -> bytes:
    by_id = {entry["id"]: entry for entry in entries}
    changed = [by_id[entry_id] for entry_id in RELEASE["new_entry_ids"]]
    added = [by_id[entry_id] for entry_id in RELEASE.get("added_entry_ids", [])]
    refreshed = [by_id[entry_id] for entry_id in RELEASE.get("refreshed_entry_ids", [])]
    rejected = RELEASE.get("rejected_candidates", [])
    maintenance = RELEASE.get("maintenance_revision")
    remediated_ids = (
        maintenance.get("remediated_entry_ids", [])
        if isinstance(maintenance, dict)
        else []
    )
    review_status_ids = (
        maintenance.get("review_status_materialized_entry_ids", [])
        if isinstance(maintenance, dict)
        else []
    )
    base_editorial_version = (
        maintenance.get("base_editorial_version")
        if isinstance(maintenance, dict)
        else None
    )
    lines = [
        "# The Record — Maintenance Run Receipt",
        "",
        f"- Release: {VERSION}",
        f"- Checked: {CHECKED_AT}",
        f"- Editorial window: {RELEASE.get('window_started_at', RELEASE['cutoff_start'])} through {RELEASE.get('window_ended_at', CHECKED_AT)}",
        f"- Current layer: {len(entries)} records backed by {len(ledger)} source-ledger records",
        f"- Full archive runtime: {ARCHIVE_METRICS['totals']['full_archive_runtime_entries']:,} records; {ARCHIVE_METRICS['totals']['full_archive_runtime_source_references']:,} source references; {ARCHIVE_METRICS['totals']['full_archive_runtime_unique_urls']:,} distinct stored URLs",
        f"- Legacy custody: {ARCHIVE_METRICS['totals']['canonical_legacy_rows']:,} stored rows; {ARCHIVE_METRICS['totals']['active_legacy_entries']:,} active; {ARCHIVE_METRICS['totals']['superseded_legacy_tombstones']:,} duplicate tombstones excluded from totals",
        f"- Truth Social source: {TRUTH_META['source_post_count']:,} posts; {TRUTH_META['fallback_post_count']:,} retained in the validated local fallback",
        f"- Newest Truth Social post: {TRUTH_META['latest_post_at_eastern']}",
        f"- Truth Social fallback checked: {TRUTH_META['checked_at_eastern']}",
    ]
    if maintenance:
        restored_legacy_count = int(maintenance.get("restored_legacy_entry_count", 0))
        excluded_duplicate_count = int(
            maintenance.get("excluded_same_event_duplicate_count", 0)
        )
        corrected_legacy_ids = maintenance.get("corrected_legacy_entry_ids", [])
        restored_historical_versions = maintenance.get("restored_historical_versions", [])
        lines.extend([
            f"- Base editorial release: {base_editorial_version or 'not recorded'}",
            f"- Base editorial records carried forward: {len(changed)} ({len(added)} added; {len(refreshed)} materially refreshed)",
            f"- Current-layer Maybe / Therefore records remediated: {len(remediated_ids)}",
            f"- Current-layer review statuses materialized: {len(review_status_ids)}",
            f"- Previously published legacy records restored: {restored_legacy_count}",
            f"- Same-event legacy candidates excluded: {excluded_duplicate_count}",
            f"- Recovered or surviving legacy records corrected: {len(corrected_legacy_ids)}",
            f"- Historical aggregate versions recovered: {', '.join(restored_historical_versions) or 'none'}",
            "",
            "## Base editorial findings carried forward (no factual or Maybe / Therefore edits in this maintenance)",
            "",
            *(f'- `{entry["id"]}` — {entry["title"]}' for entry in changed),
            "",
            "## Base editorial withheld candidates carried forward",
            "",
        ])
    else:
        lines.extend([
            f"- Added: {len(added)} national record{'s' if len(added) != 1 else ''}",
            f"- Materially refreshed: {len(refreshed)} national record{'s' if len(refreshed) != 1 else ''}",
            "",
            "## Added or materially refreshed records",
            "",
            *(f'- `{entry["id"]}` — {entry["title"]}' for entry in changed),
            "",
            "## Withheld candidates",
            "",
        ])
    if rejected:
        lines.extend(f'- {item["title"]}: {item["reason"]}' for item in rejected)
    else:
        lines.append(
            "- None recorded in the base editorial release."
            if maintenance
            else "- None recorded in this run."
        )
    if maintenance:
        lines.extend([
            "",
            "## Maintenance revision",
            "",
            f'- Recorded: {maintenance.get("recorded_at", "not recorded")}',
            f'- Scope: {maintenance.get("scope", "not recorded")}',
            f'- Artifact identity: {maintenance.get("artifact_identity_rule", "not recorded")}',
            f'- Prior aggregate artifacts preserved byte-for-byte: {len(maintenance.get("preserved_aggregate_artifacts", []))}',
            f'- Publication acceptance authority: {maintenance.get("publication_acceptance_authority", "not recorded")}',
        ])
        if remediated_ids:
            lines.extend([
                "",
                "### Remediated current records",
                "",
                *(f'- `{entry_id}` — {by_id[entry_id]["title"]}' for entry_id in remediated_ids),
            ])
        if review_status_ids:
            lines.extend([
                "",
                "Explicit current-standard review status was materialized for "
                f"{len(review_status_ids)} current records.",
            ])
    lines.extend([
        "",
        "## Verification",
        "",
        "Current front-door pages, canonical datasets, archive bridge, individual evidence packs, versioned aggregate packs, source ledgers, and checksums are generated deterministically. Earlier date-only base aggregates remain byte-frozen and separately addressable; every new same-day aggregate is version-keyed. Candidate publication requires the repository validator and GitHub Actions to pass, followed by acceptance from the publication authority named above.",
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
    maintenance = RELEASE.get("maintenance_revision")
    remediated_ids = (
        maintenance.get("remediated_entry_ids", [])
        if isinstance(maintenance, dict)
        else []
    )
    missing_remediated_ids = set(remediated_ids) - set(by_id)
    if missing_remediated_ids:
        raise ValueError(
            "release.json names unknown remediated entries: "
            f"{sorted(missing_remediated_ids)}"
        )

    outputs: dict[Path, bytes] = {}
    for entry in entries:
        entry_path = ENTRY_DIR / entry["pack_filename"]
        # Entry packs are canonical derivatives, not immutable snapshots. Rebuild
        # every one on every run so a source-ledger correction or a refreshed
        # existing entry cannot leave an internally stale ZIP behind.
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

    in6_brief_bytes = in6_current_brief(entries, ledger)
    in6_brief_path = ARTIFACTS / IN6_CURRENT_BRIEF_NAME
    outputs[in6_brief_path] = in6_brief_bytes

    receipt_bytes = run_receipt(entries, ledger)
    receipt_path = ARTIFACTS / RUN_RECEIPT_NAME
    outputs[receipt_path] = receipt_bytes

    national_entries = [entry for entry in entries if entry["scope"] == "national"]
    in6_entries = [entry for entry in entries if entry["scope"] == "in6"]
    base_editorial_version = (
        maintenance.get("base_editorial_version")
        if isinstance(maintenance, dict)
        else None
    )
    national_release_note = (
        f"The factual and Maybe / Therefore content of the {len(NEW_ENTRY_IDS)} base "
        f"editorial records is carried forward from release {base_editorial_version}; "
        "review-status metadata is materialized separately, and this maintenance remediates "
        f"Maybe / Therefore reasoning in {len(remediated_ids)} current records and "
        "does not imply a new post-cutoff finding.\n"
        if maintenance
        else f"{len(NEW_ENTRY_IDS)} records were added or materially refreshed in this run.\n"
    )
    national_files = {
        "README.md": (
            "# NATIONAL update pack\n\n"
            f"Release: {VERSION} · {RELEASE_HUMAN}\nEditorial cutoff: {CHECKED_AT}\n"
            f"Contains {len(national_entries)} national records. {national_release_note}"
        ).encode(),
        NATIONAL_BRIEF_NAME: brief_bytes,
        RUN_RECEIPT_NAME: receipt_bytes,
        "data/release.json": (ROOT / "data/release.json").read_bytes(),
        "data/archive_metrics.json": (ROOT / "data/archive_metrics.json").read_bytes(),
        "source_ledger.csv": (ROOT / "data/source_ledger.csv").read_bytes(),
        "source_ledger.json": (ROOT / "data/source_ledger.json").read_bytes(),
    }
    for entry in national_entries:
        pack_path = ENTRY_DIR / entry["pack_filename"]
        national_files[f'entries/{entry["pack_filename"]}'] = artifact_bytes(pack_path)
        national_files[f'entries/{entry["pack_filename"]}.sha256'] = artifact_bytes(
            pack_path.with_suffix(pack_path.suffix + ".sha256")
        )
    # Aggregate packs already contain compressed entry ZIPs. Store their members
    # without an outer DEFLATE pass so the bytes remain identical across zlib
    # patch versions used by local builders and GitHub Actions.
    national_pack = stable_zip(national_files, compress=False)
    national_path = ARTIFACTS / NATIONAL_PACK_NAME
    outputs[national_path] = national_pack
    outputs[national_path.with_suffix(national_path.suffix + ".sha256")] = adjacent_checksum(
        national_path.name, national_pack
    )

    complete_files = {
        "README.md": (
            "# The Record current update pack\n\n"
            f"Release: {VERSION}\nRelease date: {RELEASE_HUMAN}\nEditorial/base-release cutoff: {CHECKED_AT}\n\n"
            f"Contains {len(national_entries)} national and {len(in6_entries)} IN-6 current-layer records. "
            "Each brief and entry pack preserves the individual record's evidence-check time; the release cutoff does not imply that every record was re-researched on that date. "
            "The national and IN-6 briefs at the pack root are generated from the current canonical layer. "
            "A separately labeled snapshots directory preserves the immutable July 18 IN-6 brief without presenting it as current. "
            f"The full searchable Trump archive renders {ARCHIVE_METRICS['totals']['full_archive_runtime_entries']:,} active canonical/bridged entries. "
            f"It retains {ARCHIVE_METRICS['totals']['superseded_legacy_tombstones']:,} duplicate tombstones outside that count. "
            "External archive units and normalized crosslinks remain separate until source review and deduplication promote a distinct event.\n"
        ).encode(),
        NATIONAL_BRIEF_NAME: brief_bytes,
        IN6_CURRENT_BRIEF_NAME: in6_brief_bytes,
        RUN_RECEIPT_NAME: receipt_bytes,
        "EDITORIAL_AUTOMATION.md": (ROOT / "EDITORIAL_AUTOMATION.md").read_bytes(),
        "AI_PROVENANCE.md": (ROOT / "AI_PROVENANCE.md").read_bytes(),
        "current_layer_bridge.js": (ROOT / "current_layer_bridge.js").read_bytes(),
        "data/current_entries.json": (ROOT / "data/current_entries.json").read_bytes(),
        "data/archive_metrics.json": (ROOT / "data/archive_metrics.json").read_bytes(),
        "data/archive_registry.json": (ROOT / "data/archive_registry.json").read_bytes(),
        "data/federated_records.json": (ROOT / "data/federated_records.json").read_bytes(),
        "data/legacy_entries.json": (ROOT / "data/legacy_entries.json").read_bytes(),
        "data/legacy_revisions.json": (ROOT / "data/legacy_revisions.json").read_bytes(),
        "data/legacy_restoration_manifest.json": (ROOT / "data/legacy_restoration_manifest.json").read_bytes(),
        "data/release.json": (ROOT / "data/release.json").read_bytes(),
        "data/source_ledger.csv": (ROOT / "data/source_ledger.csv").read_bytes(),
        "data/source_ledger.json": (ROOT / "data/source_ledger.json").read_bytes(),
        "schemas/federated_record.schema.json": (ROOT / "schemas/federated_record.schema.json").read_bytes(),
    }
    in6_brief = ARTIFACTS / "THE_RECORD_IN6_UPDATE_BRIEF_2026-07-18.md"
    if in6_brief.exists():
        complete_files[f"snapshots/{in6_brief.name}"] = in6_brief.read_bytes()
        complete_files["snapshots/README.md"] = (
            "# Preserved snapshots\n\n"
            f"`{in6_brief.name}` is the immutable July 18 IN-6 brief. "
            f"The current canonical IN-6 brief for release {VERSION} is "
            f"`../{IN6_CURRENT_BRIEF_NAME}`. The snapshot and current per-entry "
            "packs must not be treated as one contemporaneous package.\n"
        ).encode()
    for entry in entries:
        pack_path = ENTRY_DIR / entry["pack_filename"]
        complete_files[f'entries/{entry["pack_filename"]}'] = artifact_bytes(pack_path)
        complete_files[f'entries/{entry["pack_filename"]}.sha256'] = artifact_bytes(
            pack_path.with_suffix(pack_path.suffix + ".sha256")
        )
    complete_pack = stable_zip(complete_files, compress=False)
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
