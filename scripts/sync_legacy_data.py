from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
CANONICAL = ROOT / "data/legacy_entries.json"
ROOT_ARCHIVE = ROOT / "the-record.html"
DOCS_ARCHIVE = ROOT / "docs/the-record.html"
ENTRIES_ARRAY = ROOT / "entries_array.js"

DATA_PATTERN = re.compile(
    r'(?P<open><script[^>]*id="dataEntries"[^>]*>)(?P<data>.*?)(?P<close></script>)',
    re.DOTALL,
)

ALLOWED_REVIEW_STATES = {
    "legacy-unreviewed",
    "in-review",
    "current-standard-reviewed",
    "needs-sourcing",
    "corrected",
    "superseded",
}
ALLOWED_ERAS = {"formation", "campaign1", "term1", "post1", "campaign2", "term2"}
ALLOWED_ENTRY_TYPES = {"event", "context"}
ALLOWED_DATE_PRECISION = {"day", "month", "year", "approx"}
LEGACY_ID_PATTERN = re.compile(r"LEG-\d{6,}")
REQUIRED_TEXT_FIELDS = ("legacy_id", "review_status", "era", "sort", "date", "text", "sig", "goal")


def extract_html_entries(path: Path) -> list[dict]:
    text = path.read_text(encoding="utf-8")
    matches = list(DATA_PATTERN.finditer(text))
    if len(matches) != 1:
        raise ValueError(
            f"{path.relative_to(ROOT)} must contain exactly one dataEntries block; found {len(matches)}"
        )
    match = matches[0]
    data = json.loads(match.group("data"))
    if not isinstance(data, list):
        raise ValueError(f"{path.relative_to(ROOT)} dataEntries is not an array")
    return data


def extract_entries_array(path: Path) -> list[dict]:
    text = path.read_text(encoding="utf-8").strip()
    match = re.fullmatch(r"const\s+E\s*=\s*(?P<data>\[.*\])\s*;?", text, re.DOTALL)
    if not match:
        raise ValueError("entries_array.js is not a plain const E JSON array")
    data = json.loads(match.group("data"))
    if not isinstance(data, list):
        raise ValueError("entries_array.js E value is not an array")
    return data


def with_stable_metadata(entries: list[dict]) -> list[dict]:
    width = max(6, len(str(len(entries))))
    normalized: list[dict] = []
    used_ids: set[str] = set()
    for index, source in enumerate(entries, start=1):
        entry = dict(source)
        legacy_id = str(entry.pop("legacy_id", "") or f"LEG-{index:0{width}d}")
        review_status = str(entry.pop("review_status", "") or "legacy-unreviewed")
        if legacy_id in used_ids:
            raise ValueError(f"duplicate legacy ID: {legacy_id}")
        if review_status not in ALLOWED_REVIEW_STATES:
            raise ValueError(f"{legacy_id}: unsupported review state {review_status}")
        used_ids.add(legacy_id)
        normalized.append({
            "legacy_id": legacy_id,
            "review_status": review_status,
            **entry,
        })
    return normalized


def validate_schema(entries: list[dict]) -> list[str]:
    """Validate the canonical legacy contract without rewriting historical prose.

    Exact record duplicates are blocked. Near-duplicate lifecycle records are
    reported by archive_metrics.json and remain an editorial adjudication task.
    """
    errors: list[str] = []
    seen_ids: set[str] = set()
    seen_core: dict[str, str] = {}
    previous_sort = ""
    superseded_targets: dict[str, str] = {}

    for index, entry in enumerate(entries, start=1):
        label = str(entry.get("legacy_id") or f"row {index}")
        for field in REQUIRED_TEXT_FIELDS:
            if not isinstance(entry.get(field), str) or not entry[field].strip():
                errors.append(f"{label}: missing or empty string field {field}")

        legacy_id = str(entry.get("legacy_id") or "")
        if not LEGACY_ID_PATTERN.fullmatch(legacy_id):
            errors.append(f"{label}: legacy_id must match LEG- followed by at least six digits")
        elif legacy_id in seen_ids:
            errors.append(f"{label}: duplicate stable ID")
        seen_ids.add(legacy_id)

        if entry.get("review_status") not in ALLOWED_REVIEW_STATES:
            errors.append(f"{label}: unsupported review state {entry.get('review_status')!r}")
        if entry.get("review_status") == "superseded":
            target = entry.get("superseded_by")
            reason = entry.get("superseded_reason")
            if not isinstance(target, str) or not LEGACY_ID_PATTERN.fullmatch(target):
                errors.append(f"{label}: superseded record requires a valid superseded_by LEG ID")
            else:
                superseded_targets[label] = target
            if not isinstance(reason, str) or not reason.strip():
                errors.append(f"{label}: superseded record requires superseded_reason")
        elif "superseded_by" in entry or "superseded_reason" in entry:
            errors.append(f"{label}: superseded metadata is allowed only when review_status is superseded")
        maybe_therefore = entry.get("mt")
        if maybe_therefore is not None and (
            not isinstance(maybe_therefore, str)
            or not maybe_therefore.startswith("Maybe")
            or "Therefore" not in maybe_therefore
        ):
            errors.append(f"{label}: mt must be a nonempty 'Maybe … Therefore …' layer")
        if entry.get("review_status") in {"in-review", "current-standard-reviewed", "corrected"} and not maybe_therefore:
            errors.append(f"{label}: promoted review state requires a Maybe / Therefore layer")
        if entry.get("era") not in ALLOWED_ERAS:
            errors.append(f"{label}: unsupported era {entry.get('era')!r}")
        if entry.get("etype") not in ALLOWED_ENTRY_TYPES:
            errors.append(f"{label}: unsupported entry type {entry.get('etype')!r}")
        if entry.get("dprec") not in ALLOWED_DATE_PRECISION:
            errors.append(f"{label}: unsupported date precision {entry.get('dprec')!r}")

        sort_value = str(entry.get("sort") or "")
        try:
            date.fromisoformat(sort_value)
        except ValueError:
            errors.append(f"{label}: sort must be an ISO calendar date")
        if previous_sort and sort_value < previous_sort:
            errors.append(f"{label}: sort order moves backward ({previous_sort} to {sort_value})")
        previous_sort = sort_value

        for flag in ("hi", "gp"):
            if entry.get(flag) not in (0, 1, False, True):
                errors.append(f"{label}: {flag} must be boolean-like 0/1")

        sources = entry.get("src")
        if not isinstance(sources, list) or not sources:
            errors.append(f"{label}: src must be a nonempty array")
        else:
            for source_index, source in enumerate(sources, start=1):
                if isinstance(source, str):
                    url = source.strip()
                    title = url
                elif isinstance(source, dict):
                    url = str(source.get("url") or "").strip()
                    title = str(source.get("t") or source.get("title") or source.get("name") or "").strip()
                else:
                    errors.append(f"{label}: source {source_index} has an unsupported shape")
                    continue
                parsed = urlparse(url)
                if parsed.scheme not in {"http", "https"} or not parsed.netloc:
                    errors.append(f"{label}: source {source_index} has an invalid URL")
                if not title:
                    errors.append(f"{label}: source {source_index} has no label")

        core = {key: value for key, value in entry.items() if key not in {"legacy_id", "review_status"}}
        fingerprint = json.dumps(core, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        if fingerprint in seen_core:
            errors.append(f"{label}: exact record duplicate of {seen_core[fingerprint]}")
        else:
            seen_core[fingerprint] = label

    for label, target in superseded_targets.items():
        if target == label:
            errors.append(f"{label}: superseded record cannot redirect to itself")
        elif target not in seen_ids:
            errors.append(f"{label}: superseded_by target {target} does not exist")
        elif target in superseded_targets:
            errors.append(
                f"{label}: superseded_by target {target} is also superseded; "
                "redirect directly to one active canonical record"
            )

    # Tombstones must terminate at one active record and may never form a
    # redirect cycle. The direct-target rule above keeps old permalinks stable
    # without creating redirect chains that can later change their meaning.
    for start in superseded_targets:
        visited: set[str] = set()
        cursor = start
        while cursor in superseded_targets:
            if cursor in visited:
                errors.append(f"{start}: superseded_by redirect cycle detected")
                break
            visited.add(cursor)
            cursor = superseded_targets[cursor]

    return errors


def entry_line(entry: dict) -> str:
    # Escaping the slash prevents an entry string from prematurely closing the
    # application/json script element when this payload is embedded in HTML.
    return json.dumps(entry, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")


def render_payload(entries: list[dict]) -> str:
    if not entries:
        return "[]"
    return "[\n" + ",\n".join(entry_line(entry) for entry in entries) + "\n]"


def render_canonical(entries: list[dict]) -> str:
    # One complete record per line keeps a large historical dataset diffable.
    return render_payload(entries) + "\n"


def render_entries_array(entries: list[dict]) -> str:
    # entries_array.js is an old runtime derivative, not a custody record. Keep
    # retired duplicate tombstones in the canonical JSON and both embedded HTML
    # payloads, but omit them here so older consumers cannot render or count a
    # superseded row as active.
    active_entries = [entry for entry in entries if entry.get("review_status") != "superseded"]
    return "const E=" + render_payload(active_entries) + ";\n"


def render_archive(path: Path, entries: list[dict]) -> str:
    text = path.read_text(encoding="utf-8")
    payload = render_payload(entries)
    rendered, replacements = DATA_PATTERN.subn(
        lambda match: match.group("open") + payload + match.group("close"),
        text,
        count=1,
    )
    if replacements != 1:
        raise ValueError(f"{path.relative_to(ROOT)} dataEntries replacement failed")
    return rendered


def canonical_entries() -> list[dict]:
    data = json.loads(CANONICAL.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("data/legacy_entries.json is not an array")
    normalized = with_stable_metadata(data)
    if normalized != data:
        raise ValueError("canonical legacy entries are missing stable metadata or have unstable key order")
    schema_errors = validate_schema(data)
    if schema_errors:
        preview = "\n".join(f"- {error}" for error in schema_errors[:30])
        remainder = len(schema_errors) - 30
        if remainder:
            preview += f"\n- …and {remainder} more"
        raise ValueError(f"canonical legacy schema validation failed:\n{preview}")
    return data


def bootstrap() -> None:
    if CANONICAL.exists():
        raise ValueError("canonical legacy data already exists; bootstrap is intentionally one-time")
    entries = with_stable_metadata(extract_html_entries(ROOT_ARCHIVE))
    CANONICAL.parent.mkdir(parents=True, exist_ok=True)
    CANONICAL.write_text(render_canonical(entries), encoding="utf-8")
    print(f"Bootstrapped {len(entries):,} canonical legacy entries from published root archive.")


def expected_files(entries: list[dict]) -> dict[Path, str]:
    return {
        CANONICAL: render_canonical(entries),
        # The archives retain the complete custody payload, including stable
        # redirect tombstones for retired duplicate permalinks.
        ROOT_ARCHIVE: render_archive(ROOT_ARCHIVE, entries),
        DOCS_ARCHIVE: render_archive(DOCS_ARCHIVE, entries),
        # The legacy JS derivative exposes active records only.
        ENTRIES_ARRAY: render_entries_array(entries),
    }


def validate_identity(entries: list[dict]) -> list[str]:
    errors: list[str] = []
    active_entries = [entry for entry in entries if entry.get("review_status") != "superseded"]
    # HTML embeds are custody representations and retain tombstones. The old JS
    # array is an active-only runtime derivative by design.
    for path, loader, expected in (
        (ROOT_ARCHIVE, extract_html_entries, entries),
        (DOCS_ARCHIVE, extract_html_entries, entries),
        (ENTRIES_ARRAY, extract_entries_array, active_entries),
    ):
        try:
            actual = loader(path)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            errors.append(f"{path.relative_to(ROOT)}: {exc}")
            continue
        if actual != expected:
            expected_ids = {entry["legacy_id"] for entry in expected}
            actual_ids = {entry.get("legacy_id") for entry in actual}
            errors.append(
                f"{path.relative_to(ROOT)} differs from its generated canonical view "
                f"({len(actual):,} records; missing IDs {len(expected_ids - actual_ids):,}; "
                f"extra IDs {len(actual_ids - expected_ids):,})"
            )
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Synchronize every legacy archive representation from one canonical JSON dataset."
    )
    parser.add_argument(
        "--bootstrap",
        action="store_true",
        help="one-time extraction of the published root archive into canonical JSON",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="fail if any generated legacy representation differs from canonical data",
    )
    args = parser.parse_args()

    try:
        if args.bootstrap:
            bootstrap()
        entries = canonical_entries()
        if args.check:
            errors = validate_identity(entries)
            if errors:
                print("Legacy data synchronization failed:")
                print("\n".join(f"- {error}" for error in errors))
                return 1
            print(f"Verified {len(entries):,} canonical legacy entries across all representations.")
            return 0

        for path, content in expected_files(entries).items():
            path.write_text(content, encoding="utf-8")
        print(f"Synchronized {len(entries):,} canonical legacy entries across all representations.")
        return 0
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
