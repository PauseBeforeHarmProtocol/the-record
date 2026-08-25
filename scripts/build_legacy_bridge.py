from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "the-record.html"
BRIDGE_ASSET = ROOT / "current_layer_bridge.js"
START = "/* CURRENT_LAYER_BRIDGE_START */"
END = "/* CURRENT_LAYER_BRIDGE_END */"
ASSET_MARKER = "<!-- CURRENT_LAYER_BRIDGE_ASSET -->"
MAIN_SCRIPT = "<script>\n// Step 1: Parse entries (3.4 MB) via JSON.parse — much faster than JS literal on iOS Safari"
ARCHIVE_HOOK = f'''{START}
// The small generated asset is the live layer; the 14 MB historical application stays stable.
const CURRENT_LAYER_BRIDGE=Array.isArray(window.CURRENT_LAYER_BRIDGE)?window.CURRENT_LAYER_BRIDGE:[];
E.push(...CURRENT_LAYER_BRIDGE);
{END}'''


def canonical_data() -> tuple[list[dict], dict, dict]:
    entries = json.loads((ROOT / "data/current_entries.json").read_text(encoding="utf-8"))
    ledger = json.loads((ROOT / "data/source_ledger.json").read_text(encoding="utf-8"))
    release = json.loads((ROOT / "data/release.json").read_text(encoding="utf-8"))
    return entries, ledger, release


def bridge_entries(entries: list[dict], ledger: dict) -> list[dict]:
    bridge = []
    for entry in sorted(
        (item for item in entries if item["scope"] == "national"),
        key=lambda item: (item["date"], item["id"]),
    ):
        bridge.append({
            "era": "term2",
            "sort": entry["date"],
            "date": entry["display_date"],
            "text": f'{entry["title"]}. ' + " ".join(entry["facts"]),
            "sig": entry["significance"],
            "goal": entry["goalpost"],
            **({"mt": entry["maybe_therefore"]} if entry.get("maybe_therefore") else {}),
            "hi": 0,
            "gp": 1,
            "etype": "event",
            "dprec": "day",
            "src": [
                {"t": ledger[source_id]["name"], "url": ledger[source_id]["url"]}
                for source_id in entry["sources"]
            ],
            "current_id": entry["id"],
            "review_status": entry["review_status"],
            "evidence": entry["evidence"],
            "checked_at": entry["checked_at"],
            "institutions": entry["institutions"],
            "pack_path": entry["pack_path"],
        })
    return bridge


def bridge_asset_text() -> str:
    entries, ledger, release = canonical_data()
    bridge = bridge_entries(entries, ledger)
    metrics = json.loads((ROOT / "data/archive_metrics.json").read_text(encoding="utf-8"))
    maintenance = release.get("maintenance_revision")
    maintenance_active = isinstance(maintenance, dict)
    meta = {
        "version": release["version"],
        "release": release["release_human"],
        "checked_at": release["checked_at"],
        "week_label": release["week_label"],
        "national_entry_count": len(bridge),
        "added_this_release": (
            0 if maintenance_active else len(release.get("added_entry_ids", []))
        ),
        "refreshed_this_release": (
            0 if maintenance_active else len(release.get("refreshed_entry_ids", []))
        ),
        "base_editorial_version": (
            maintenance.get("base_editorial_version") if maintenance_active else None
        ),
        "base_editorial_change_count": (
            len(release["new_entry_ids"]) if maintenance_active else 0
        ),
        "maintenance_remediated_entry_count": (
            len(maintenance.get("remediated_entry_ids", []))
            if maintenance_active
            else 0
        ),
        "review_status_materialized_entry_count": (
            len(maintenance.get("review_status_materialized_entry_ids", []))
            if maintenance_active
            else 0
        ),
        "canonical_legacy_entries": metrics["totals"]["canonical_legacy_entries"],
        "canonical_legacy_rows": metrics["totals"]["canonical_legacy_rows"],
        "superseded_legacy_tombstones": metrics["totals"]["superseded_legacy_tombstones"],
        "runtime_entry_count": metrics["totals"]["full_archive_runtime_entries"],
        "runtime_source_references": metrics["totals"]["full_archive_runtime_source_references"],
        "runtime_unique_urls": metrics["totals"]["full_archive_runtime_unique_urls"],
        "legacy_review_states": metrics["legacy"]["review_states"],
        "legacy_maybe_therefore": metrics["legacy"]["interpretive_layers"],
        "known_coverage_gap": metrics["coverage"],
    }
    meta_payload = json.dumps(meta, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    bridge_payload = json.dumps(bridge, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    return (
        "// Generated from data/current_entries.json and data/release.json. Do not edit by hand.\n"
        f"window.CURRENT_LAYER_META={meta_payload};\n"
        f"window.CURRENT_LAYER_BRIDGE={bridge_payload};\n"
    )


def expected_archive_text() -> str:
    text = ARCHIVE.read_text(encoding="utf-8")
    start = text.index(START)
    end = text.index(END, start) + len(END)
    text = text[:start] + ARCHIVE_HOOK + text[end:]
    if ASSET_MARKER not in text:
        asset_tag = f'{ASSET_MARKER}\n<script src="current_layer_bridge.js"></script>\n'
        if MAIN_SCRIPT not in text:
            raise ValueError("legacy archive main-script insertion point not found")
        text = text.replace(MAIN_SCRIPT, asset_tag + MAIN_SCRIPT, 1)
    return text


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the live current-entry bridge consumed by the historical archive.")
    parser.add_argument("--check", action="store_true", help="fail if the bridge asset or stable archive hook is stale")
    args = parser.parse_args()
    expected_asset = bridge_asset_text()
    current_asset = BRIDGE_ASSET.read_text(encoding="utf-8") if BRIDGE_ASSET.exists() else ""
    current_archive = ARCHIVE.read_text(encoding="utf-8")
    expected_archive = expected_archive_text()

    if args.check:
        stale = []
        if current_asset != expected_asset:
            stale.append("current_layer_bridge.js")
        if current_archive != expected_archive:
            stale.append("the-record.html stable bridge hook")
        if stale:
            print("Legacy current-layer bridge is stale:")
            print("\n".join(f"- {item}" for item in stale))
            return 1
        print("Verified live archive bridge asset and stable historical hook.")
        return 0

    BRIDGE_ASSET.write_text(expected_asset, encoding="utf-8")
    if current_archive != expected_archive:
        ARCHIVE.write_text(expected_archive, encoding="utf-8")
        print("Installed stable live-layer hook in the historical archive.")
    print(f"Built archive bridge with {len(bridge_entries(*canonical_data()[:2]))} national current-layer records.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
