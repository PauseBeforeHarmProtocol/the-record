from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import subprocess
import sys
import zipfile
from collections import Counter
from datetime import date, datetime
from difflib import SequenceMatcher
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse
from zoneinfo import ZoneInfo

from bs4 import BeautifulSoup


ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site" if (ROOT / "site").is_dir() else ROOT
ERRORS: list[str] = []
CURRENT_ROUTES = [
    "index.html",
    "weekly/index.html",
    "national/index.html",
    "in6/index.html",
    "agencies/index.html",
    "institutions/index.html",
    "methodology/index.html",
    "sources/index.html",
    "downloads/index.html",
    "archive/index.html",
    "quality/index.html",
    "404.html",
]
CURRENT_AI = ("ChatGPT 5.6 Sol Max", "Claude Fable 5 Max (Cowork)")
DEPRECATED_AI = ("ChatGPT 5.6 Pro", "ChatGPT 5.4 Extended Thinking")
CURRENT_PUBLISHABLE_REVIEW_STATES = {"current-standard-reviewed", "corrected"}
ALLOWED_MAINTENANCE_KINDS = {"current_maybe_therefore_backfill"}
BASE_EDITORIAL_CARRY_EXCEPTIONS = {
    "version",
    "previous_version",
    "previous_checked_at",
    "maintenance_revision",
}
AGGREGATE_ARTIFACT_SPECS = (
    ("THE_RECORD_CURRENT_UPDATE_PACK", (".zip", ".zip.sha256")),
    ("THE_RECORD_IN6_CURRENT_BRIEF", (".md",)),
    ("THE_RECORD_NATIONAL_UPDATE_BRIEF", (".md",)),
    ("THE_RECORD_NATIONAL_UPDATE_PACK", (".zip", ".zip.sha256")),
    ("THE_RECORD_RUN_RECEIPT", (".md",)),
)
RELEASE = json.loads((ROOT / "data/release.json").read_text(encoding="utf-8"))
RELEASE_ISO = RELEASE["release_iso"]
RELEASE_HUMAN = RELEASE["release_human"]
WEEK_START = RELEASE["week_start"]
WEEK_END = RELEASE["week_end"]
NEW_ENTRY_IDS = set(RELEASE["new_entry_ids"])
RELEASE_ARTIFACT_STEM = f'{RELEASE_ISO}_v{RELEASE["version"]}'
NATIONAL_PACK_NAME = f"THE_RECORD_NATIONAL_UPDATE_PACK_{RELEASE_ARTIFACT_STEM}.zip"
COMPLETE_PACK_NAME = f"THE_RECORD_CURRENT_UPDATE_PACK_{RELEASE_ARTIFACT_STEM}.zip"
RUN_RECEIPT_NAME = f"THE_RECORD_RUN_RECEIPT_{RELEASE_ARTIFACT_STEM}.md"
IN6_CURRENT_BRIEF_NAME = f"THE_RECORD_IN6_CURRENT_BRIEF_{RELEASE_ARTIFACT_STEM}.md"


def fail(message: str) -> None:
    ERRORS.append(message)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalized_text(value: object) -> str:
    return re.sub(r"\W+", " ", str(value or "").casefold()).strip()


def current_maybe_therefore_parts(value: object) -> tuple[str, str] | None:
    if not isinstance(value, str):
        return None
    match = re.fullmatch(
        r"Maybe\b(?P<maybe>.*?)\bTherefore\b(?P<therefore>.*)",
        value.strip(),
        flags=re.DOTALL,
    )
    if match is None:
        return None
    maybe = normalized_text(match.group("maybe"))
    therefore = normalized_text(match.group("therefore"))
    if (
        len(maybe.split()) < 3
        or len(therefore.split()) < 3
        or maybe == therefore
    ):
        return None
    return match.group("maybe"), match.group("therefore")


def git_file_bytes(ref: str, relative_path: str) -> bytes:
    return subprocess.run(
        ["git", "show", f"{ref}:{relative_path}"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    ).stdout


def git_json(ref: str, relative_path: str) -> object:
    return json.loads(git_file_bytes(ref, relative_path))


def aggregate_inventory(
    repository_paths: set[str], release: dict
) -> set[str]:
    release_iso = str(release.get("release_iso") or "")
    version = str(release.get("version") or "")

    def matching(stem: str) -> set[str]:
        return {
            f"artifacts/{prefix}_{stem}{suffix}"
            for prefix, suffixes in AGGREGATE_ARTIFACT_SPECS
            for suffix in suffixes
            if f"artifacts/{prefix}_{stem}{suffix}" in repository_paths
        }

    versioned = matching(f"{release_iso}_v{version}")
    return versioned or matching(release_iso)


def is_persisted_maintenance_identity(
    base_release: object, current_release: object
) -> bool:
    return bool(
        isinstance(base_release, dict)
        and isinstance(current_release, dict)
        and isinstance(base_release.get("maintenance_revision"), dict)
        and base_release.get("version") == current_release.get("version")
    )


def compare_artifacts_to_base(
    base_ref: str, relative_paths: set[str]
) -> None:
    for relative_path in sorted(relative_paths):
        path = Path(relative_path)
        target = ROOT / path
        if path.is_absolute() or ".." in path.parts or not target.is_file():
            continue
        try:
            base_artifact = git_file_bytes(base_ref, path.as_posix())
        except subprocess.CalledProcessError as exc:
            fail(
                f"cannot load preserved aggregate {relative_path!r} from "
                f"base {base_ref!r}: {exc}"
            )
            continue
        if target.read_bytes() != base_artifact:
            fail(
                "maintenance changed a declared preserved aggregate artifact: "
                f"{relative_path}"
            )


if current_maybe_therefore_parts(
    "Maybe a competing explanation remains plausible. Therefore the record keeps a measurable test open."
) is None or any(
    current_maybe_therefore_parts(value) is not None
    for value in (
        None,
        {},
        "",
        "Maybe Therefore the competing clause is empty.",
        "Therefore the order is reversed. Maybe uncertainty remains.",
        "Maybe uncertainty remains without a consequence clause.",
        "Maybe same short clause. Therefore same short clause.",
        "Maybe one. Therefore two.",
    )
):
    fail("current Maybe / Therefore validator self-test failed")

_aggregate_self_test_release = {"release_iso": "2026-08-25", "version": "8.3.1"}
_aggregate_self_test_legacy = {
    "artifacts/THE_RECORD_CURRENT_UPDATE_PACK_2026-08-25.zip",
    "artifacts/THE_RECORD_CURRENT_UPDATE_PACK_2026-08-25.zip.sha256",
}
_aggregate_self_test_versioned = {
    "artifacts/THE_RECORD_CURRENT_UPDATE_PACK_2026-08-25_v8.3.1.zip",
    "artifacts/THE_RECORD_CURRENT_UPDATE_PACK_2026-08-25_v8.3.1.zip.sha256",
}
if (
    aggregate_inventory(_aggregate_self_test_legacy, _aggregate_self_test_release)
    != _aggregate_self_test_legacy
    or aggregate_inventory(
        _aggregate_self_test_legacy | _aggregate_self_test_versioned,
        _aggregate_self_test_release,
    )
    != _aggregate_self_test_versioned
):
    fail("release aggregate-inventory validator self-test failed")
if (
    not is_persisted_maintenance_identity(
        {"version": "8.3.1", "maintenance_revision": {"remediation_kind": "test"}},
        {"version": "8.3.1", "maintenance_revision": {"remediation_kind": "test"}},
    )
    or is_persisted_maintenance_identity(
        {"version": "8.3.1", "maintenance_revision": {"remediation_kind": "test"}},
        {"version": "8.3.2", "maintenance_revision": {"remediation_kind": "test"}},
    )
    or is_persisted_maintenance_identity(
        {"version": "8.3.1"},
        {"version": "8.3.1", "maintenance_revision": {"remediation_kind": "test"}},
    )
):
    fail("persisted maintenance-identity validator self-test failed")


def normalized_heading(value: object) -> str:
    return normalized_text(re.split(r"(?<=[.!?])\s", str(value or ""), maxsplit=1)[0])


def normalized_url(value: object) -> str:
    parsed = urlparse(str(value or "").strip())
    if not parsed.scheme or not parsed.netloc:
        return ""
    query = urlencode(
        sorted(
            (key, item)
            for key, item in parse_qsl(parsed.query, keep_blank_values=True)
            if not key.casefold().startswith("utm_")
        )
    )
    return urlunparse(
        (
            parsed.scheme.casefold(),
            parsed.netloc.casefold().removeprefix("www."),
            parsed.path.rstrip("/") or "/",
            "",
            query,
            "",
        )
    )


def formal_identifiers(value: object) -> set[str]:
    text = str(value or "")
    patterns = (
        r"\bExecutive\s+Order\s+(?:No\.?\s*)?\d+[A-Z0-9.\-]*",
        r"\bEO[-\s]?\d{3,}[A-Z0-9.\-]*",
        r"\bH\.R\.\s*\d+[A-Z0-9.\-]*",
        r"\bS\.\s*\d+[A-Z0-9.\-]*",
        r"\b(?:SCOTUS|Docket)\s+(?:No\.?\s*)?\d+[A-Z0-9.\-]*",
        r"\bProclamation\s+(?:No\.?\s*)?\d+[A-Z0-9.\-]*",
    )
    return {
        normalized_text(match.group(0))
        for pattern in patterns
        for match in re.finditer(pattern, text, re.IGNORECASE)
    }


hero = SITE / "assets/brand/the-record-hero.png"
if not hero.exists():
    fail("missing assets/brand/the-record-hero.png")
elif not hero.read_bytes().startswith(b"\x89PNG\r\n\x1a\n"):
    fail("the-record-hero.png is not a PNG")

mark = SITE / "assets/brand/the-record-mark.svg"
if not mark.exists():
    fail("missing assets/brand/the-record-mark.svg")
elif "<svg" not in mark.read_text(encoding="utf-8"):
    fail("the-record-mark.svg is not an SVG")

for route in CURRENT_ROUTES:
    if not (SITE / route).is_file():
        fail(f"missing current route {route}")

html_files = sorted(SITE.rglob("*.html"))
for page in html_files:
    text = page.read_text(encoding="utf-8")
    soup = BeautifulSoup(text, "html.parser")
    if not soup.title or not soup.title.get_text(strip=True):
        fail(f"{page}: missing title")
    for anchor in soup.find_all("a", href=True):
        href = anchor["href"].split("#", 1)[0].split("?", 1)[0]
        if not href or re.match(r"^(https?:|mailto:|tel:|/)", href):
            continue
        target = (page.parent / href).resolve()
        if href.endswith("/"):
            target = target / "index.html"
        if not target.exists():
            fail(f"{page.relative_to(SITE)} -> missing {href}")

for route in CURRENT_ROUTES:
    page = SITE / route
    if not page.exists():
        continue
    text = page.read_text(encoding="utf-8")
    soup = BeautifulSoup(text, "html.parser")
    nav = soup.select_one(".primary-nav")
    if not nav:
        fail(f"{route}: missing primary navigation")
    else:
        labels = [anchor.get_text(" ", strip=True) for anchor in nav.find_all("a")]
        if "Weekly" not in labels:
            fail(f"{route}: Weekly is not a top-level navigation item")
        if "Agencies" not in labels:
            fail(f"{route}: Agencies is not a top-level navigation item")
        if "The Archive" not in labels:
            fail(f"{route}: The Archive is not a top-level navigation item")
        if "Quality" not in labels:
            fail(f"{route}: Quality is not a top-level navigation item")
        if "Institutions" in labels:
            fail(f"{route}: stale Institutions navigation label")
    if "assets/brand/the-record-mark.svg" not in text:
        fail(f"{route}: missing The Record brand mark")
    for model in CURRENT_AI:
        if model not in text:
            fail(f"{route}: missing current AI disclosure {model}")
    for model in DEPRECATED_AI:
        if model in text:
            fail(f"{route}: deprecated AI disclosure {model}")
    if RELEASE_HUMAN not in text:
        fail(f"{route}: missing {RELEASE_HUMAN} currentness marker")

entries_path = SITE / "data/current_entries.json"
ledger_path = SITE / "data/source_ledger.json"
legacy_canonical_path = SITE / "data/legacy_entries.json"
metrics_path = SITE / "data/archive_metrics.json"
registry_path = SITE / "data/archive_registry.json"
federated_path = SITE / "data/federated_records.json"
legacy_revisions_path = SITE / "data/legacy_revisions.json"
entries = json.loads(entries_path.read_text(encoding="utf-8"))
ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
legacy_canonical = json.loads(legacy_canonical_path.read_text(encoding="utf-8"))
archive_metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
archive_registry = json.loads(registry_path.read_text(encoding="utf-8"))
federated_records = json.loads(federated_path.read_text(encoding="utf-8"))
legacy_revisions = json.loads(legacy_revisions_path.read_text(encoding="utf-8"))
active_legacy = [
    entry for entry in legacy_canonical if entry.get("review_status") != "superseded"
]
superseded_legacy = [
    entry for entry in legacy_canonical if entry.get("review_status") == "superseded"
]
ids = {entry["id"] for entry in entries}
if len(ids) != len(entries):
    fail("duplicate entry IDs")
if not NEW_ENTRY_IDS <= ids:
    fail(f"release metadata names missing entries: {sorted(NEW_ENTRY_IDS - ids)}")

release_id_lists: dict[str, list[str]] = {}
for field in ("new_entry_ids", "added_entry_ids", "refreshed_entry_ids"):
    values = RELEASE.get(field, [])
    if not isinstance(values, list) or any(
        not isinstance(entry_id, str) or not entry_id.strip() for entry_id in values
    ):
        fail(f"release {field} must be a list of nonempty strings")
        release_id_lists[field] = []
    else:
        release_id_lists[field] = values
        if len(set(values)) != len(values):
            fail(f"release {field} contains duplicates")
added_ids = set(release_id_lists["added_entry_ids"])
refreshed_ids = set(release_id_lists["refreshed_entry_ids"])
if added_ids & refreshed_ids:
    fail(f"release added/refreshed IDs overlap: {sorted(added_ids & refreshed_ids)}")
if NEW_ENTRY_IDS != added_ids | refreshed_ids:
    fail("release new_entry_ids must equal the union of added and refreshed IDs")

base_ref = os.environ.get("CURRENT_REMEDIATION_BASE_REF", "").strip()
base_release: dict | None = None
base_entries: list[dict] | None = None
base_repository_paths: set[str] = set()
if base_ref and not re.fullmatch(r"0+", base_ref):
    try:
        loaded_base_release = git_json(base_ref, "data/release.json")
        loaded_base_entries = git_json(base_ref, "data/current_entries.json")
        tree_result = subprocess.run(
            ["git", "ls-tree", "-r", "--name-only", base_ref, "--", "artifacts"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        base_repository_paths = set(tree_result.stdout.splitlines())
    except (subprocess.CalledProcessError, json.JSONDecodeError) as exc:
        fail(f"cannot load current-remediation base {base_ref!r}: {exc}")
    else:
        if not isinstance(loaded_base_release, dict):
            fail(f"current-remediation base {base_ref!r} has invalid release metadata")
        else:
            base_release = loaded_base_release
        if not isinstance(loaded_base_entries, list) or any(
            not isinstance(entry, dict) or not entry.get("id")
            for entry in loaded_base_entries
        ):
            fail(f"current-remediation base {base_ref!r} has invalid canonical entries")
        else:
            base_entries = loaded_base_entries

maintenance = RELEASE.get("maintenance_revision")
base_maintenance = (
    base_release.get("maintenance_revision")
    if isinstance(base_release, dict)
    else None
)
persisted_maintenance_identity = is_persisted_maintenance_identity(
    base_release, RELEASE
)

if base_release is not None and base_entries is not None:
    same_release_identity = base_release.get("version") == RELEASE.get("version")
    if same_release_identity:
        if RELEASE != base_release:
            fail("release metadata changed without a new release identity")
        if entries != base_entries:
            fail("current entries changed without a new release identity")
    else:
        if RELEASE.get("previous_version") != base_release.get("version"):
            fail("previous_version must equal the base release version")
        if RELEASE.get("previous_checked_at") != base_release.get("checked_at"):
            fail("previous_checked_at must equal the base checked_at")

        # A regular editorial release must account exactly for every canonical
        # current-entry change. If it cannot, the release needs an enumerated
        # maintenance transition and its narrower field-level contract.
        if maintenance is None:
            base_by_id = {str(entry["id"]): entry for entry in base_entries}
            current_by_id = {str(entry["id"]): entry for entry in entries}
            if len(base_by_id) != len(base_entries):
                fail(f"current-release base {base_ref!r} has duplicate entry IDs")
            else:
                actual_added_ids = set(current_by_id) - set(base_by_id)
                actual_removed_ids = set(base_by_id) - set(current_by_id)
                actual_refreshed_ids = {
                    entry_id
                    for entry_id in set(base_by_id) & set(current_by_id)
                    if base_by_id[entry_id] != current_by_id[entry_id]
                }
                if actual_removed_ids:
                    fail(
                        "regular current release removes canonical entry IDs without "
                        f"a maintenance contract: {sorted(actual_removed_ids)}"
                    )
                if actual_added_ids != added_ids:
                    fail(
                        "release added_entry_ids differ from the base-ref current-entry "
                        f"diff: metadata={sorted(added_ids)}, "
                        f"diff={sorted(actual_added_ids)}"
                    )
                if actual_refreshed_ids != refreshed_ids:
                    fail(
                        "release refreshed_entry_ids differ from the base-ref "
                        "current-entry diff; unaccounted field changes require an "
                        "enumerated maintenance contract: "
                        f"metadata={sorted(refreshed_ids)}, "
                        f"diff={sorted(actual_refreshed_ids)}"
                    )

# A maintenance identity remains in release.json after publication. For later
# docs-only, feed-only, or other unrelated changes, pin that release and its
# current canonical layer exactly instead of replaying its one-time diff.
if persisted_maintenance_identity:
    pinned_paths = base_maintenance.get("preserved_aggregate_artifacts", [])
    if isinstance(pinned_paths, list) and all(
        isinstance(path, str) and path.strip() for path in pinned_paths
    ):
        published_inventory = aggregate_inventory(base_repository_paths, base_release)
        compare_artifacts_to_base(
            base_ref, set(pinned_paths) | published_inventory
        )

remediated_ids: set[str] = set()
review_status_materialized_ids: set[str] = set()
preserved_aggregate_artifacts: list[str] = []
remediation_kind: str | None = None
if maintenance is not None and not isinstance(maintenance, dict):
    fail("release maintenance_revision must be an object")
elif isinstance(maintenance, dict):
    raw_kind = maintenance.get("remediation_kind")
    if not isinstance(raw_kind, str) or not raw_kind.strip():
        fail("maintenance remediation_kind must be a nonempty string")
    elif raw_kind not in ALLOWED_MAINTENANCE_KINDS:
        fail(f"unsupported maintenance remediation_kind {raw_kind!r}")
    else:
        remediation_kind = raw_kind

    if maintenance.get("recorded_at") != RELEASE_ISO:
        fail("maintenance recorded_at must equal release_iso")
    if maintenance.get("base_editorial_version") != RELEASE.get("previous_version"):
        fail("maintenance base_editorial_version must equal previous_version")
    if not str(maintenance.get("publication_acceptance_authority") or "").strip():
        fail("maintenance publication_acceptance_authority must be recorded")
    if not str(maintenance.get("artifact_identity_rule") or "").strip():
        fail("maintenance artifact_identity_rule must be recorded")

    raw_preserved_artifacts = maintenance.get("preserved_aggregate_artifacts", [])
    if not isinstance(raw_preserved_artifacts, list) or any(
        not isinstance(path, str) or not path.strip()
        for path in raw_preserved_artifacts
    ):
        fail(
            "maintenance preserved_aggregate_artifacts must be a list of "
            "nonempty relative paths"
        )
    else:
        preserved_aggregate_artifacts = raw_preserved_artifacts
        if len(set(preserved_aggregate_artifacts)) != len(
            preserved_aggregate_artifacts
        ):
            fail("maintenance preserved_aggregate_artifacts contains duplicates")
        for relative_path in preserved_aggregate_artifacts:
            path = Path(relative_path)
            if (
                path.is_absolute()
                or ".." in path.parts
                or not path.parts
                or path.parts[0] != "artifacts"
            ):
                fail(
                    "maintenance preserved aggregate path must stay under artifacts/: "
                    f"{relative_path!r}"
                )
            elif not (ROOT / path).is_file():
                fail(f"missing preserved aggregate artifact {relative_path}")
        if not preserved_aggregate_artifacts:
            fail("maintenance requires preserved aggregate artifact paths")

    raw_remediated_ids = maintenance.get("remediated_entry_ids", [])
    if not isinstance(raw_remediated_ids, list) or any(
        not isinstance(entry_id, str) or not entry_id.strip()
        for entry_id in raw_remediated_ids
    ):
        fail("maintenance remediated_entry_ids must be a list of nonempty strings")
    else:
        remediated_ids = set(raw_remediated_ids)
        if len(remediated_ids) != len(raw_remediated_ids):
            fail("maintenance remediated_entry_ids contains duplicates")
        if not remediated_ids <= ids:
            fail(
                "maintenance metadata names missing current entries: "
                f"{sorted(remediated_ids - ids)}"
            )
        editorial_change_ids = NEW_ENTRY_IDS | added_ids | refreshed_ids
        if remediated_ids & editorial_change_ids:
            fail(
                "maintenance remediation IDs must remain separate from editorial change IDs: "
                f"{sorted(remediated_ids & editorial_change_ids)}"
            )
        if not remediated_ids:
            fail("current Maybe / Therefore backfill requires remediated_entry_ids")

    raw_materialized_ids = maintenance.get("review_status_materialized_entry_ids", [])
    if not isinstance(raw_materialized_ids, list) or any(
        not isinstance(entry_id, str) or not entry_id.strip()
        for entry_id in raw_materialized_ids
    ):
        fail(
            "maintenance review_status_materialized_entry_ids must be a list "
            "of nonempty strings"
        )
    else:
        review_status_materialized_ids = set(raw_materialized_ids)
        if len(review_status_materialized_ids) != len(raw_materialized_ids):
            fail("maintenance review_status_materialized_entry_ids contains duplicates")
        if not review_status_materialized_ids <= ids:
            fail(
                "maintenance review-status metadata names missing current entries: "
                f"{sorted(review_status_materialized_ids - ids)}"
            )
        if review_status_materialized_ids != ids:
            fail(
                "current Maybe / Therefore backfill must materialize review status "
                "for every current entry"
            )

    is_new_transition = bool(
        remediation_kind in ALLOWED_MAINTENANCE_KINDS
        and base_release is not None
        and base_entries is not None
        and not persisted_maintenance_identity
    )
    if is_new_transition:
        base_version = base_release.get("version")
        if RELEASE.get("version") == base_version:
            fail("maintenance transition must increment the release version")
        if RELEASE.get("previous_version") != base_version:
            fail("maintenance previous_version must equal the base release version")
        if RELEASE.get("previous_checked_at") != base_release.get("checked_at"):
            fail("maintenance previous_checked_at must equal the base checked_at")
        if maintenance.get("base_editorial_version") != base_version:
            fail("maintenance base_editorial_version must equal the base release version")

        carried_keys = (
            set(base_release) | set(RELEASE)
        ) - BASE_EDITORIAL_CARRY_EXCEPTIONS
        changed_carried_fields = sorted(
            key
            for key in carried_keys
            if base_release.get(key) != RELEASE.get(key)
        )
        if changed_carried_fields:
            fail(
                "maintenance changed base editorial release fields: "
                f"{changed_carried_fields}"
            )

        expected_preserved = aggregate_inventory(base_repository_paths, base_release)
        if not expected_preserved:
            fail("base release has no discoverable aggregate artifact inventory")
        if set(preserved_aggregate_artifacts) != expected_preserved:
            fail(
                "maintenance preserved_aggregate_artifacts differs from the complete "
                "base-release aggregate inventory: "
                f"metadata={sorted(preserved_aggregate_artifacts)}, "
                f"base={sorted(expected_preserved)}"
            )
        compare_artifacts_to_base(base_ref, expected_preserved)

        base_by_id = {str(entry["id"]): entry for entry in base_entries}
        current_by_id = {str(entry["id"]): entry for entry in entries}
        if len(base_by_id) != len(base_entries):
            fail(f"current-remediation base {base_ref!r} has duplicate entry IDs")
        elif set(base_by_id) != set(current_by_id):
            fail(
                "current-remediation release changes the canonical current-entry "
                "inventory"
            )
        else:
            maybe_changed_ids = {
                entry_id
                for entry_id in current_by_id
                if base_by_id[entry_id].get("maybe_therefore")
                != current_by_id[entry_id].get("maybe_therefore")
            }
            if maybe_changed_ids != remediated_ids:
                fail(
                    "maintenance remediated_entry_ids differ from the base-ref "
                    "Maybe / Therefore diff: "
                    f"metadata={sorted(remediated_ids)}, "
                    f"diff={sorted(maybe_changed_ids)}"
                )

            review_status_changed_ids = {
                entry_id
                for entry_id in current_by_id
                if base_by_id[entry_id].get("review_status")
                != current_by_id[entry_id].get("review_status")
            }
            if review_status_changed_ids != review_status_materialized_ids:
                fail(
                    "maintenance review_status_materialized_entry_ids differ "
                    "from the base-ref review-status diff: "
                    f"metadata={sorted(review_status_materialized_ids)}, "
                    f"diff={sorted(review_status_changed_ids)}"
                )

            forbidden_changes: list[str] = []
            for entry_id in sorted(current_by_id):
                base_core = {
                    key: value
                    for key, value in base_by_id[entry_id].items()
                    if key not in {"maybe_therefore", "review_status"}
                }
                current_core = {
                    key: value
                    for key, value in current_by_id[entry_id].items()
                    if key not in {"maybe_therefore", "review_status"}
                }
                if base_core != current_core:
                    forbidden_changes.append(entry_id)
            if forbidden_changes:
                fail(
                    "current Maybe / Therefore maintenance changed canonical "
                    "fields outside maybe_therefore and review_status: "
                    f"{forbidden_changes}"
                )
expected_entry_packs = {entry["pack_path"] for entry in entries}
if len(expected_entry_packs) != len(entries):
    fail("duplicate per-entry pack paths")
actual_entry_packs = {
    path.relative_to(SITE).as_posix()
    for path in (SITE / "artifacts/entries").glob("*.zip")
}
if actual_entry_packs != expected_entry_packs:
    fail(
        "per-entry ZIP inventory differs from canonical entries: "
        f"missing {sorted(expected_entry_packs - actual_entry_packs)}, "
        f"orphaned {sorted(actual_entry_packs - expected_entry_packs)}"
    )
title_dates = {(entry["date"], re.sub(r"\W+", " ", entry["title"].lower()).strip()) for entry in entries}
if len(title_dates) != len(entries):
    fail("duplicate normalized date/title pairs")

# Every active pair is checked on every validation run. This intentionally does
# not depend on release.added_entry_ids: a later edit or legacy backfill can
# create a collision between records that were already published. Candidate
# pairs may remain separate only after an explicit lifecycle/false-positive
# adjudication. A same-event update must be consolidated instead of leaving both
# rows active.
allowed_dedupe_decisions = {"same_event_update", "distinct_lifecycle_stage", "false_positive"}
dedupe_resolutions: dict[frozenset[str], dict] = {}
for resolution in RELEASE.get("dedupe_resolutions", []):
    if not isinstance(resolution, dict):
        fail("release dedupe_resolutions rows must be objects")
        continue
    entry_id = str(resolution.get("entry_id") or "")
    target_id = str(resolution.get("target_id") or "")
    decision = str(resolution.get("decision") or "")
    if not entry_id or not target_id or decision not in allowed_dedupe_decisions:
        fail(f"malformed dedupe resolution for {entry_id or '<missing entry>'}")
        continue
    if not str(resolution.get("notes") or "").strip():
        fail(f"dedupe resolution {entry_id}/{target_id} requires notes")
    key = frozenset((entry_id, target_id))
    if key in dedupe_resolutions:
        fail(f"duplicate dedupe resolution for {sorted(key)}")
    dedupe_resolutions[key] = resolution


def require_duplicate_resolution(entry_id: str, target_id: str, signal: str) -> None:
    resolution = dedupe_resolutions.get(frozenset((entry_id, target_id)))
    if not resolution:
        fail(f"{entry_id}: duplicate candidate with {target_id} ({signal}) lacks an explicit resolution")
    elif resolution.get("decision") == "same_event_update":
        fail(
            f"{entry_id}: same_event_update resolution with {target_id} must consolidate or "
            "suppress one active row before publication"
        )


def current_source_urls(entry: dict) -> set[str]:
    return {
        normalized_url(ledger[source_id].get("url"))
        for source_id in entry.get("sources", [])
        if source_id in ledger and normalized_url(ledger[source_id].get("url"))
    }


def current_official_urls(entry: dict) -> set[str]:
    return {
        normalized_url(ledger[source_id].get("url"))
        for source_id in entry.get("sources", [])
        if source_id in ledger
        and any(token in str(ledger[source_id].get("type") or "").casefold() for token in ("official", "primary"))
        and normalized_url(ledger[source_id].get("url"))
    }


def legacy_source_urls(entry: dict) -> set[str]:
    return {
        normalized_url(source if isinstance(source, str) else source.get("url"))
        for source in entry.get("src", [])
        if normalized_url(source if isinstance(source, str) else source.get("url"))
    }


def entry_similarity(left: str, right: str) -> float:
    if not left or not right:
        return 0.0
    return SequenceMatcher(None, normalized_text(left), normalized_text(right)).ratio()


current_dedupe_data: dict[str, dict[str, object]] = {}
for entry in entries:
    text = " ".join([entry.get("title", ""), *entry.get("facts", [])])
    current_dedupe_data[entry["id"]] = {
        "date": date.fromisoformat(entry["date"]),
        "identifiers": formal_identifiers(text),
        "official_urls": current_official_urls(entry),
        "text": text,
        "title": normalized_text(entry.get("title")),
        "urls": current_source_urls(entry),
    }

legacy_dedupe_data: dict[str, dict[str, object]] = {}
for entry in active_legacy:
    text = f'{entry.get("text", "")} {entry.get("sig", "")}'
    legacy_dedupe_data[entry["legacy_id"]] = {
        "date": date.fromisoformat(entry["sort"]),
        "heading": normalized_heading(entry.get("text")),
        "identifiers": formal_identifiers(text),
        "text": text,
        "urls": legacy_source_urls(entry),
    }

# Current-to-current: inspect every unordered pair exactly once.
for left_index, left in enumerate(entries):
    left_data = current_dedupe_data[left["id"]]
    for right in entries[left_index + 1 :]:
        right_data = current_dedupe_data[right["id"]]
        shared_urls = left_data["urls"] & right_data["urls"]
        signals: list[str] = []
        if left_data["title"] and left_data["title"] == right_data["title"]:
            signals.append("exact normalized title across dates")
        shared_formal = left_data["identifiers"] & right_data["identifiers"]
        if shared_formal:
            signals.append(f"shared formal identifier {sorted(shared_formal)}")
        shared_official = (
            (left_data["official_urls"] & right_data["urls"])
            | (right_data["official_urls"] & left_data["urls"])
        )
        if shared_official:
            signals.append("shared primary/official canonical URL")
        if (
            shared_urls
            and abs((left_data["date"] - right_data["date"]).days) <= 1
            and entry_similarity(left_data["text"], right_data["text"]) >= 0.45
        ):
            signals.append("shared source, overlapping date, and similar facts")
        if signals:
            require_duplicate_resolution(left["id"], right["id"], "; ".join(signals))

# Current-to-legacy: inspect every current row, regardless of scope, against
# every active legacy row. Tombstones are excluded because they are redirects,
# not runtime records.
for current_entry in entries:
    current_data = current_dedupe_data[current_entry["id"]]
    for legacy in active_legacy:
        legacy_data = legacy_dedupe_data[legacy["legacy_id"]]
        shared_urls = current_data["urls"] & legacy_data["urls"]
        signals = []
        if current_data["title"] and current_data["title"] == legacy_data["heading"]:
            signals.append("exact normalized heading across canonical layers")
        shared_formal = current_data["identifiers"] & legacy_data["identifiers"]
        if shared_formal:
            signals.append(f"shared formal identifier across runtime layers {sorted(shared_formal)}")
        if current_data["official_urls"] & legacy_data["urls"]:
            signals.append("shared primary/official URL across runtime layers")
        if (
            shared_urls
            and abs((current_data["date"] - legacy_data["date"]).days) <= 1
            and entry_similarity(current_data["text"], legacy_data["text"]) >= 0.45
        ):
            signals.append("shared source, overlapping date, and similar facts across runtime layers")
        if signals:
            require_duplicate_resolution(
                current_entry["id"], legacy["legacy_id"], "; ".join(signals)
            )
urls = [source["url"] for source in ledger.values()]
if len(urls) != len(set(urls)):
    fail("duplicate URLs in source ledger")
normalized_ledger_urls = [normalized_url(url) for url in urls]
if any(not url for url in normalized_ledger_urls) or len(normalized_ledger_urls) != len(set(normalized_ledger_urls)):
    fail("duplicate or invalid normalized URLs in source ledger")
for entry in entries:
    pack = SITE / entry["pack_path"]
    if not pack.exists():
        fail(f'missing pack {entry["pack_path"]}')
    elif not zipfile.is_zipfile(pack):
        fail(f'invalid ZIP pack {entry["pack_path"]}')
    else:
        try:
            with zipfile.ZipFile(pack) as archive:
                member_names = set(archive.namelist())
                for member_name in ("entry.json", "sources.json"):
                    if member_name not in member_names:
                        fail(f'{entry["id"]}: pack is missing {member_name}')
                if "entry.json" in member_names:
                    packed_entry = json.loads(archive.read("entry.json").decode("utf-8"))
                    if packed_entry != entry:
                        fail(f'{entry["id"]}: pack entry.json differs from canonical entry')
                if "sources.json" in member_names:
                    packed_sources = json.loads(archive.read("sources.json").decode("utf-8"))
                    if all(source_id in ledger for source_id in entry.get("sources", [])):
                        expected_sources = {
                            source_id: ledger[source_id] for source_id in entry["sources"]
                        }
                        if packed_sources != expected_sources:
                            fail(
                                f'{entry["id"]}: pack sources.json differs from canonical '
                                "source-ledger subset"
                            )
        except (KeyError, UnicodeDecodeError, json.JSONDecodeError, zipfile.BadZipFile) as exc:
            fail(f'{entry["id"]}: cannot inspect canonical pack payload: {exc}')
    for key in ("facts", "significance", "goalpost", "sources", "institutions"):
        if not entry.get(key):
            fail(f'{entry["id"]}: empty {key}')
    if entry.get("review_status") not in CURRENT_PUBLISHABLE_REVIEW_STATES:
        fail(
            f'{entry["id"]}: review_status must explicitly be '
            "current-standard-reviewed or corrected"
        )
    if current_maybe_therefore_parts(entry.get("maybe_therefore")) is None:
        fail(
            f'{entry["id"]}: maybe_therefore requires substantive, distinct '
            "Maybe and Therefore clauses"
        )
    for source_id in entry["sources"]:
        if source_id not in ledger:
            fail(f'{entry["id"]}: unknown source {source_id}')
    for correction in entry.get("corrections", []):
        if not correction.get("timestamp") or not correction.get("note"):
            fail(f'{entry["id"]}: malformed correction record')
    if entry["id"] in NEW_ENTRY_IDS and not (RELEASE["cutoff_start"] <= entry["date"] <= RELEASE_ISO):
        fail(f'{entry["id"]}: new-entry date falls outside the release cutoff')

with (SITE / "data/source_ledger.csv").open(encoding="utf-8", newline="") as handle:
    csv_ids = {row["source_id"] for row in csv.DictReader(handle)}
if csv_ids != set(ledger):
    fail("CSV and JSON source-ledger IDs differ")

weekly_ids = {entry["id"] for entry in entries if WEEK_START <= entry["date"] <= WEEK_END}
weekly_soup = BeautifulSoup((SITE / "weekly/index.html").read_text(encoding="utf-8"), "html.parser")
rendered_weekly_ids = {card.get("id") for card in weekly_soup.select("[data-week-card]")}
if rendered_weekly_ids != weekly_ids:
    fail(f"weekly route IDs differ: expected {sorted(weekly_ids)}, found {sorted(rendered_weekly_ids)}")
if not weekly_soup.select("[data-week-filter]"):
    fail("weekly route has no scope controls")

agency_soup = BeautifulSoup((SITE / "agencies/index.html").read_text(encoding="utf-8"), "html.parser")
rendered_agencies = {card.find("h3").get_text(strip=True) for card in agency_soup.select(".institution-card")}
expected_agencies = {name for entry in entries for name in entry["institutions"]}
if rendered_agencies != expected_agencies:
    fail("Agencies route does not map every current institution")
alias_text = (SITE / "institutions/index.html").read_text(encoding="utf-8")
if not any(path in alias_text for path in ("../agencies/index.html", "/the-record/agencies/index.html")):
    fail("institutions compatibility route does not resolve to Agencies")

legacy_text = (SITE / "the-record.html").read_text(encoding="utf-8")
bridge_path = SITE / "current_layer_bridge.js"
if not bridge_path.exists():
    fail("missing generated current_layer_bridge.js")
else:
    bridge_text = bridge_path.read_text(encoding="utf-8")
    national_ids = {entry["id"] for entry in entries if entry["scope"] == "national"}
    missing_bridge_ids = sorted(entry_id for entry_id in national_ids if entry_id not in bridge_text)
    if missing_bridge_ids:
        fail(f"archive bridge is missing national entries: {missing_bridge_ids}")
    if "window.CURRENT_LAYER_META=" not in bridge_text or RELEASE["checked_at"] not in bridge_text:
        fail("archive bridge is missing current release metadata")
if not any(
    marker in legacy_text
    for marker in ('src="current_layer_bridge.js"', 'src="/the-record/current_layer_bridge.js"')
):
    fail("historical archive does not load current_layer_bridge.js")
if "Array.isArray(window.CURRENT_LAYER_BRIDGE)" not in legacy_text:
    fail("historical archive is missing its stable live-layer hook")
if "const CURRENT_LAYER_BRIDGE=[" in legacy_text:
    fail("historical archive still embeds the generated current layer")
if "assets/brand/the-record-mark.svg" not in legacy_text:
    fail("historical archive is missing The Record brand mark")
if 'id="timelineOrder"' not in legacy_text or "let timelineOrder='desc'" not in legacy_text:
    fail("historical archive timeline does not default to newest first")
if "timelineOrder==='desc'?b.localeCompare(a):a.localeCompare(b)" not in legacy_text:
    fail("historical archive year groups do not honor timeline order")
if "function toggleTimelineOrder()" not in legacy_text:
    fail("historical archive is missing its timeline order control")
if 'data-view="feed"' not in legacy_text or 'id="feedView"' not in legacy_text:
    fail("historical archive is missing its first-class Truth Social feed view")
if 'id="tsChecked"' not in legacy_text:
    fail("historical archive does not display when the Truth Social feed was checked")
if "window.TruthFeed.open()" not in legacy_text or "feed:'feed'" not in legacy_text:
    fail("historical archive does not activate or deep-link the Truth Social feed")
if not any(
    marker in legacy_text
    for marker in ('src="assets/truth-feed.js"', 'src="/the-record/assets/truth-feed.js"')
) or not any(
    marker in legacy_text
    for marker in ('href="assets/truth-feed.css"', 'href="/the-record/assets/truth-feed.css"')
):
    fail("historical archive is missing modular Truth Social assets")
if "connect-src 'self' https://ix.cnn.io" not in legacy_text:
    fail("historical archive CSP does not allow its declared live Truth Social mirror")
if "String(s??'')" not in legacy_text:
    fail("historical archive escaping is not null-safe")
if "typeof s==='string'?{url:s}:s" not in legacy_text:
    fail("historical archive renderer does not normalize legacy URL-string sources")
if "e.current_id||e.legacy_id||eid" not in legacy_text:
    fail("historical archive does not use stable current/legacy record IDs for permalinks")
if "e.mt?`<div class=\"emt\"" not in legacy_text:
    fail("historical archive does not render the Maybe / Therefore layer")
if "CANONICAL_LEGACY_ENTRIES.filter(e=>e.review_status!=='superseded')" not in legacy_text:
    fail("historical archive does not exclude superseded tombstones from runtime search and counts")
if "SUPERSEDED_REDIRECTS" not in legacy_text or "Retired duplicate permalink" not in legacy_text:
    fail("historical archive does not preserve retired IDs as redirecting tombstones")
legacy_entries_match = re.search(
    r'<script[^>]*id="dataEntries"[^>]*>(?P<data>.*?)</script>',
    legacy_text,
    re.DOTALL,
)
if not legacy_entries_match:
    fail("historical archive is missing its embedded entry data")
else:
    try:
        legacy_entries = json.loads(legacy_entries_match.group("data"))
    except json.JSONDecodeError as exc:
        fail(f"historical archive entry data is invalid JSON: {exc}")
    else:
        if legacy_entries != legacy_canonical:
            fail("historical archive embedded entries differ from canonical legacy JSON")
        unsupported_sources = []
        for entry_index, entry in enumerate(legacy_entries):
            for source_index, source in enumerate(entry.get("src") or []):
                if isinstance(source, str):
                    continue
                if isinstance(source, dict) and any(
                    source.get(field) for field in ("url", "t", "title", "name")
                ):
                    continue
                unsupported_sources.append(f"{entry_index}:{source_index}")
        if unsupported_sources:
            fail(
                "historical archive has unsupported source shapes: "
                + ", ".join(unsupported_sources[:10])
            )

docs_text = (SITE / "docs/the-record.html").read_text(encoding="utf-8")
if 'id="compatibilitySnapshotNotice"' not in docs_text:
    fail("docs archive is not labeled as a compatibility snapshot")
if "CANONICAL_LEGACY_ENTRIES.filter(e=>e.review_status!=='superseded')" not in docs_text:
    fail("docs compatibility archive does not exclude superseded rows from rendering")
docs_entries_match = re.search(
    r'<script[^>]*id="dataEntries"[^>]*>(?P<data>.*?)</script>', docs_text, re.DOTALL
)
if not docs_entries_match:
    fail("docs archive is missing its embedded canonical legacy data")
else:
    try:
        if json.loads(docs_entries_match.group("data")) != legacy_canonical:
            fail("docs archive embedded entries differ from canonical legacy JSON")
    except json.JSONDecodeError as exc:
        fail(f"docs archive entry data is invalid JSON: {exc}")

try:
    entries_array_text = (SITE / "entries_array.js").read_text(encoding="utf-8").strip()
    entries_array_match = re.fullmatch(r"const\s+E\s*=\s*(\[.*\])\s*;?", entries_array_text, re.DOTALL)
    # entries_array.js is a legacy runtime derivative and must contain active
    # records only. The canonical JSON and embedded archive payloads above retain
    # every tombstone for custody and stable retired permalinks.
    if not entries_array_match or json.loads(entries_array_match.group(1)) != active_legacy:
        fail("entries_array.js differs from the active-only canonical legacy view")
except json.JSONDecodeError as exc:
    fail(f"entries_array.js contains invalid JSON: {exc}")

legacy_by_id = {entry.get("legacy_id"): entry for entry in legacy_canonical}
revision_fields = {
    (revision.get("legacy_id"), change.get("field"))
    for revision in legacy_revisions
    if isinstance(revision, dict)
    for change in revision.get("changes", [])
    if isinstance(change, dict)
}
for tombstone in superseded_legacy:
    legacy_id = tombstone.get("legacy_id")
    target_id = tombstone.get("superseded_by")
    target = legacy_by_id.get(target_id)
    if not target or target.get("review_status") == "superseded" or target_id == legacy_id:
        fail(f"{legacy_id}: tombstone must redirect directly to one active canonical legacy ID")
    if not str(tombstone.get("superseded_reason") or "").strip():
        fail(f"{legacy_id}: tombstone lacks superseded_reason")
    for field in ("review_status", "superseded_by", "superseded_reason"):
        if (legacy_id, field) not in revision_fields:
            fail(f"{legacy_id}: tombstone field {field} is missing from the append-only revision ledger")

# Recompute the headline totals instead of trusting generated display strings.
national_entries = [entry for entry in entries if entry.get("scope") == "national"]
legacy_urls = {
    (source if isinstance(source, str) else source.get("url", "")).strip()
    for entry in active_legacy
    for source in (entry.get("src") or [])
    if (source if isinstance(source, str) else source.get("url", "")).strip()
}
national_urls = {
    str(ledger[source_id].get("url") or "").strip()
    for entry in national_entries
    for source_id in entry.get("sources", [])
    if source_id in ledger and str(ledger[source_id].get("url") or "").strip()
}
expected_totals = {
    "canonical_legacy_rows": len(legacy_canonical),
    "canonical_legacy_entries": len(active_legacy),
    "active_legacy_entries": len(active_legacy),
    "superseded_legacy_tombstones": len(superseded_legacy),
    "bridged_national_entries": len(national_entries),
    "full_archive_runtime_entries": len(active_legacy) + len(national_entries),
    "current_layer_entries": len(entries),
    "legacy_source_references": sum(len(entry.get("src") or []) for entry in active_legacy),
    "current_source_references": sum(len(entry.get("sources") or []) for entry in entries),
    "full_archive_runtime_source_references": (
        sum(len(entry.get("src") or []) for entry in active_legacy)
        + sum(len(entry.get("sources") or []) for entry in national_entries)
    ),
    "full_archive_runtime_unique_urls": len(legacy_urls | national_urls),
}
for metric, expected in expected_totals.items():
    if archive_metrics.get("totals", {}).get(metric) != expected:
        fail(f"archive metric {metric} is stale: expected {expected}")

review_states = Counter(str(entry.get("review_status") or "missing") for entry in active_legacy)
if archive_metrics.get("legacy", {}).get("review_states") != dict(sorted(review_states.items())):
    fail("archive legacy review-state totals are stale")
maybe_count = sum(bool(str(entry.get("mt") or "").strip()) for entry in active_legacy)
layer_metrics = archive_metrics.get("legacy", {}).get("interpretive_layers", {})
if layer_metrics.get("maybe_therefore_present") != maybe_count:
    fail("archive Maybe / Therefore present count is stale")
if layer_metrics.get("maybe_therefore_missing") != len(active_legacy) - maybe_count:
    fail("archive Maybe / Therefore backlog count is stale")
current_review_states = Counter(
    str(entry.get("review_status") or "missing") for entry in entries
)
current_metrics = archive_metrics.get("current", {})
if current_metrics.get("review_states") != dict(sorted(current_review_states.items())):
    fail("archive current-layer review-state totals are stale")
current_reviewed = sum(
    entry.get("review_status") in CURRENT_PUBLISHABLE_REVIEW_STATES
    for entry in entries
)
if current_metrics.get("current_standard_reviewed") != current_reviewed:
    fail("archive current-standard-reviewed count is stale")
if current_metrics.get("current_standard_pending") != len(entries) - current_reviewed:
    fail("archive current-standard review backlog is stale")
if archive_metrics.get("federated", {}).get("records") != len(federated_records):
    fail("archive federated-record count is stale")

quality_text = (SITE / "quality/index.html").read_text(encoding="utf-8")
for value in (
    f'{expected_totals["full_archive_runtime_entries"]:,}',
    f'{expected_totals["full_archive_runtime_source_references"]:,}',
    f'{expected_totals["full_archive_runtime_unique_urls"]:,}',
    f'{len(active_legacy) - maybe_count:,}',
    f'{len(superseded_legacy):,}',
):
    if value not in quality_text:
        fail(f"quality page is missing generated metric {value}")
if "Separate legacy derivatives" not in quality_text:
    fail("quality page does not disclose separate frozen legacy derivatives")

archive_page_text = (SITE / "archive/index.html").read_text(encoding="utf-8")
archive_page_visible_text = BeautifulSoup(archive_page_text, "html.parser").get_text(" ", strip=True)
archives = archive_registry.get("archives", [])
archive_ids = [str(archive.get("archive_id") or "") for archive in archives]
if any(not archive_id for archive_id in archive_ids) or len(archive_ids) != len(set(archive_ids)):
    fail("archive registry archive_id values must be nonempty and unique")
metric_ids = [
    str(measurement.get("metric_id") or "")
    for archive in archives
    for measurement in archive.get("measurements", [])
]
if any(not metric_id for metric_id in metric_ids) or len(metric_ids) != len(set(metric_ids)):
    fail("archive registry metric_id values must be nonempty and globally unique")
canonical_archive_urls: dict[str, str] = {}
for archive in archives:
    archive_id = str(archive.get("archive_id") or "")
    url = normalized_url(archive.get("homepage_url"))
    if not url:
        fail(f"archive registry {archive_id} has no valid canonical homepage URL")
    elif url in canonical_archive_urls:
        fail(
            f"archive registry canonical homepage URL collision: {archive_id} and "
            f"{canonical_archive_urls[url]}"
        )
    canonical_archive_urls[url] = archive_id
for archive in archives:
    if archive.get("name") not in archive_page_text:
        fail(f"Archive Network page is missing {archive.get('name')}")
    for url_field in ("homepage_url", "browse_url", "about_url"):
        url = str(archive.get(url_field) or "")
        if "utm_" in url:
            fail(f"archive registry {archive.get('archive_id')} retains tracking parameters")
    for measurement in archive.get("measurements", []):
        if measurement.get("value") is None:
            continue
        for required_text in (
            f'{measurement.get("value"):,}',
            str(measurement.get("as_reported_label") or ""),
            str(measurement.get("scope") or ""),
            str(measurement.get("observed_at") or ""),
        ):
            if required_text and required_text not in archive_page_visible_text:
                fail(
                    f"Archive Network page omits measurement detail for "
                    f"{measurement.get('metric_id')}: {required_text}"
                )
if "Maybe / Therefore" not in archive_page_text or "duplicate/lifecycle decision" not in archive_page_text:
    fail("Archive Network does not disclose the full reasoning and duplicate gate")
if "Staged research data" not in archive_page_text or "not presented as a finding" not in archive_page_text:
    fail("Archive Network does not withhold substantive prose for unauthorized staged records")
week_helper = re.search(r"function openPastWeekTimeline\(\)\{(?P<body>.*?)\n\}", legacy_text, re.DOTALL)
if not week_helper:
    fail("historical archive is missing the home-to-timeline helper")
else:
    helper_body = week_helper.group("body")
    if "pastWeekOnly=true" not in helper_body or "switchView('timeline')" not in helper_body:
        fail("home past-week controls do not activate the visible timeline")
if "href=\"#e-'+permalinkSort" in legacy_text:
    fail("home past-week links still use the invalid e-prefixed permalink")
if "href=\"#'+permalinkSort+'_'+idx+'\"" not in legacy_text:
    fail("home past-week links do not use timeline permalink IDs")
week_button = re.search(
    r"document\.getElementById\('weekBtnFull'\).*?addEventListener\('click',\(\)=>\{(?P<body>.*?)\n\}\);",
    legacy_text,
    re.DOTALL,
)
if not week_button or "openPastWeekTimeline()" not in week_button.group("body"):
    fail("home full-week button does not switch to the timeline")
if "ChatGPT 5.4 Extended Thinking" in legacy_text:
    fail("legacy archive still exposes deprecated current-maintenance AI credit")
if "Written by Claude (Anthropic, Opus 4)" not in legacy_text:
    fail("legacy AI Opinion authorship was not preserved")

truth_script = SITE / "assets/truth-feed.js"
truth_styles = SITE / "assets/truth-feed.css"
truth_seed_path = SITE / "data/truth_social_seed.json"
truth_meta_path = SITE / "data/truth_social_feed_meta.json"
if not truth_script.exists() or not truth_styles.exists():
    fail("missing Truth Social feed script or stylesheet")
if not truth_seed_path.exists() or not truth_meta_path.exists():
    fail("missing Truth Social fallback data or metadata")
else:
    try:
        truth_seed = json.loads(truth_seed_path.read_text(encoding="utf-8"))
        truth_meta = json.loads(truth_meta_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"Truth Social fallback JSON is invalid: {exc}")
    else:
        if not isinstance(truth_seed, list) or len(truth_seed) < 500:
            fail("Truth Social fallback must retain at least 500 recent posts")
        else:
            truth_ids = [str(post.get("id", "")) for post in truth_seed]
            if any(not post_id for post_id in truth_ids) or len(truth_ids) != len(set(truth_ids)):
                fail("Truth Social fallback has missing or duplicate IDs")
            truth_dates = [str(post.get("created_at", "")) for post in truth_seed]
            if truth_dates != sorted(truth_dates, reverse=True):
                fail("Truth Social fallback is not newest-first")
            if truth_meta.get("latest_post_id") != truth_ids[0]:
                fail("Truth Social metadata latest-post ID differs from fallback")
            if truth_meta.get("fallback_post_count") != len(truth_seed):
                fail("Truth Social metadata fallback count differs from data")
            source_post_count = truth_meta.get("source_post_count")
            if not isinstance(source_post_count, int) or source_post_count < len(truth_seed):
                fail("Truth Social metadata source count is smaller than the fallback")
            try:
                latest_seed_at = datetime.fromisoformat(truth_dates[0].replace("Z", "+00:00"))
                earliest_seed_at = datetime.fromisoformat(truth_dates[-1].replace("Z", "+00:00"))
                latest_meta_at = datetime.fromisoformat(
                    str(truth_meta.get("latest_post_at_utc", "")).replace("Z", "+00:00")
                )
                earliest_meta_at = datetime.fromisoformat(
                    str(truth_meta.get("fallback_earliest_post_at_utc", "")).replace("Z", "+00:00")
                )
            except (TypeError, ValueError):
                fail("Truth Social metadata has invalid endpoint timestamps")
            else:
                if latest_seed_at != latest_meta_at or earliest_seed_at != earliest_meta_at:
                    fail("Truth Social metadata endpoint timestamps differ from fallback")
            try:
                feed_checked_at = datetime.fromisoformat(
                    str(truth_meta.get("checked_at_utc", "")).replace("Z", "+00:00")
                )
            except (TypeError, ValueError):
                fail("Truth Social metadata has an invalid checked-at timestamp")
            else:
                feed_checked_eastern = feed_checked_at.astimezone(ZoneInfo("America/New_York"))
                if feed_checked_eastern.date().isoformat() < RELEASE_ISO:
                    fail("Truth Social fallback was checked before the current editorial release")
            for index, post in enumerate(truth_seed):
                post_url = urlparse(str(post.get("url", "")))
                if (
                    post_url.scheme != "https"
                    or post_url.hostname != "truthsocial.com"
                    or not re.fullmatch(r"/@realDonaldTrump/\d+/?", post_url.path)
                ):
                    fail(f"Truth Social fallback row {index} has an invalid post URL")
                    break
                media = post.get("media", [])
                if not isinstance(media, list) or any(
                    urlparse(str(url)).scheme != "https"
                    or urlparse(str(url)).hostname != "static-assets-1.truthsocial.com"
                    for url in media
                ):
                    fail(f"Truth Social fallback row {index} has invalid media")
                    break

provenance = SITE / "AI_PROVENANCE.md"
if not provenance.exists():
    fail("missing AI_PROVENANCE.md")
else:
    provenance_text = provenance.read_text(encoding="utf-8")
    for model in (*CURRENT_AI, "Claude (Anthropic, Opus 4)"):
        if model not in provenance_text:
            fail(f"AI provenance missing {model}")

for checksum_file in sorted((SITE / "artifacts").rglob("*.sha256")):
    parts = checksum_file.read_text(encoding="utf-8").strip().split()
    if len(parts) != 2:
        fail(f"malformed checksum file {checksum_file.relative_to(SITE)}")
        continue
    target = checksum_file.parent / parts[1]
    if not target.exists() or sha256(target) != parts[0]:
        fail(f"checksum mismatch {checksum_file.relative_to(SITE)}")

sums_path = SITE / "artifacts/SHA256SUMS.txt"
for required_artifact in (
    NATIONAL_PACK_NAME,
    COMPLETE_PACK_NAME,
    RUN_RECEIPT_NAME,
    IN6_CURRENT_BRIEF_NAME,
):
    if not (SITE / "artifacts" / required_artifact).is_file():
        fail(f"missing current release artifact {required_artifact}")
for line in sums_path.read_text(encoding="utf-8").splitlines():
    expected, relative = line.split(maxsplit=1)
    target = sums_path.parent / relative.strip()
    if not target.exists() or sha256(target) != expected:
        fail(f"SHA256SUMS mismatch {relative.strip()}")

# Prevent accidental credential publication.
secret_patterns = [
    r"github_pat_[A-Za-z0-9_]+",
    r"ghp_[A-Za-z0-9]+",
    r"BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY",
]
for path in SITE.rglob("*"):
    if path.is_file() and path.suffix.lower() in {".html", ".js", ".css", ".json", ".md", ".txt", ".csv", ".py", ".yml", ".yaml"}:
        text = path.read_text(encoding="utf-8", errors="ignore")
        for pattern in secret_patterns:
            if re.search(pattern, text):
                fail(f"{path}: possible secret")

if ERRORS:
    print("FAIL")
    print("\n".join(f"- {error}" for error in ERRORS))
    sys.exit(1)
print(
    f"PASS: {len(html_files)} HTML files, {len(entries)} current entries, "
    f"{len(weekly_ids)} weekly records, {len(rendered_agencies)} agencies/institutions, "
    f"Truth Social live/fallback feed, all internal links, packs, checksums, AI disclosures, and credential scans passed."
)
