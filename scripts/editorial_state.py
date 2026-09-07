"""Shared chronology, evidence-version and immutable snapshot contracts."""
from __future__ import annotations

import hashlib
import json
import subprocess
import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
LOCAL_ZONE = ZoneInfo("America/Indiana/Indianapolis")
STATE_PATH = ROOT / "data/editorial_state.json"
SNAPSHOT_FILES = (
    "data/current_entries.json", "data/source_ledger.json", "data/source_ledger.csv",
    "data/legacy_entries.json", "data/legacy_revisions.json",
    "data/legacy_restoration_manifest.json", "data/federated_records.json",
    "schemas/federated_record.schema.json", "data/editorial_state.json",
    "schemas/editorial_state.schema.json",
)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_bytes(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def parse_utc(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("timestamp requires an explicit UTC offset")
    return parsed.astimezone(timezone.utc)


def legacy_checked_at(value: str) -> str:
    """Migrate a displayed minute without pretending seconds were measured."""
    local = datetime.strptime(value.rsplit(" ", 1)[0], "%Y-%m-%d %I:%M %p").replace(tzinfo=LOCAL_ZONE)
    return local.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def load_state(root: Path = ROOT) -> dict:
    return json.loads((root / "data/editorial_state.json").read_text())


def entry_content_hash(entry: dict, ledger: dict) -> str:
    # Check-time and package-location changes do not imply new factual content.
    content = {k: v for k, v in entry.items() if k not in {"checked_at", "pack_path", "pack_filename"}}
    return digest(canonical_bytes({"entry": content, "sources": {s: ledger[s] for s in entry["sources"]}}))


def post_content_hash(post: dict) -> str:
    # Engagement-only changes must not invalidate inspection of the actual post.
    return digest(canonical_bytes({k: post.get(k) for k in ("id", "created_at", "content", "media", "url")}))


def developments(entry: dict, state: dict) -> list[dict]:
    return sorted((d for d in state["developments"] if d["entry_id"] == entry["id"]),
                  key=lambda d: (d["as_of_utc"], d["change_id"]), reverse=True)


def activity_date(entry: dict, state: dict) -> str:
    dates = [entry["date"]]
    dates.extend(parse_utc(d["as_of_utc"]).astimezone(LOCAL_ZONE).date().isoformat()
                 for d in developments(entry, state))
    return max(dates)


def activity_key(entry: dict, state: dict) -> tuple:
    return activity_date(entry, state), entry["date"], entry["id"]


def rolling_window(release: dict) -> tuple[str, str]:
    end = parse_utc(release["research_window"]["through_utc"]).astimezone(LOCAL_ZONE).date()
    return (end - timedelta(days=6)).isoformat(), end.isoformat()


def weekly_entries(entries: list[dict], release: dict, state: dict) -> list[dict]:
    start, end = rolling_window(release)
    return sorted((e for e in entries if start <= activity_date(e, state) <= end),
                  key=lambda e: activity_key(e, state), reverse=True)


def matching_review(entry: dict, ledger: dict, state: dict) -> dict | None:
    signature = entry_content_hash(entry, ledger)
    return next((r for r in reversed(state["reviews"]) if r["entry_id"] == entry["id"]
                 and r["content_sha256"] == signature), None)


def artifact_names(release: dict) -> dict[str, str]:
    stem = f'{release["release_iso"]}_v{release["version"]}'
    names = {
        "national_pack": f"THE_RECORD_NATIONAL_UPDATE_PACK_{stem}.zip",
        "complete_pack": f"THE_RECORD_CURRENT_UPDATE_PACK_{stem}.zip",
        "national_brief": f"THE_RECORD_NATIONAL_UPDATE_BRIEF_{stem}.md",
        "in6_brief": f"THE_RECORD_IN6_CURRENT_BRIEF_{stem}.md",
        "receipt": f"THE_RECORD_RUN_RECEIPT_{stem}.md",
    }
    if release.get("artifact_mode") == "feed-only":
        for key in ("national_pack", "complete_pack", "national_brief", "in6_brief"):
            names[key] = Path(release["editorial_snapshot"][key]["path"]).name
    return names


def validate_snapshot(release: dict, root: Path = ROOT) -> None:
    if release.get("artifact_mode", "full") not in {"full", "feed-only"}:
        raise ValueError("unknown artifact_mode")
    if release.get("artifact_mode") != "feed-only":
        return
    if any(release.get(k) for k in ("new_entry_ids", "added_entry_ids", "refreshed_entry_ids", "corrections", "maintenance_revision", "engineering_revision")):
        raise ValueError("feed-only cannot contain editorial or engineering changes")
    snapshot = release["editorial_snapshot"]
    for key in ("national_pack", "complete_pack", "national_brief", "in6_brief"):
        record = snapshot[key]
        relative = Path(record["path"])
        if relative.parent != Path("artifacts") or not relative.name:
            raise ValueError("snapshot paths must be directly inside artifacts/")
        if digest((root / relative).read_bytes()) != record["sha256"]:
            raise ValueError(f"snapshot checksum mismatch: {key}")
        if f'_v{snapshot["version"]}.' not in relative.name:
            raise ValueError("snapshot artifact version mismatch")
    with zipfile.ZipFile(root / snapshot["complete_pack"]["path"]) as archive:
        if archive.testzip() is not None:
            raise ValueError("snapshot ZIP integrity failed")
        prior_release = json.loads(archive.read("data/release.json"))
        if prior_release["version"] != snapshot["version"]:
            raise ValueError("snapshot embedded version mismatch")
        for path in SNAPSHOT_FILES:
            if archive.read(path) != (root / path).read_bytes():
                raise ValueError(f"feed-only changes canonical snapshot input: {path}")
        entries = json.loads((root / "data/current_entries.json").read_text())
        for entry in entries:
            name = entry["pack_filename"]
            if archive.read(f"entries/{name}") != (root / entry["pack_path"]).read_bytes():
                raise ValueError(f"feed-only entry ZIP differs from snapshot: {name}")


def validate_frozen_artifacts(base_ref: str, root: Path = ROOT) -> None:
    original = set(subprocess.check_output(["git", "ls-tree", "-r", "--name-only", base_ref, "--", "artifacts"], cwd=root, text=True).splitlines())
    changed = subprocess.check_output(["git", "diff", "--name-only", base_ref, "--", "artifacts"], cwd=root, text=True).splitlines()
    for name in changed:
        path = Path(name)
        if name in original and path.parent == Path("artifacts") and path.name != "SHA256SUMS.txt":
            raise ValueError(f"immutable historical artifact changed from base: {name}")
