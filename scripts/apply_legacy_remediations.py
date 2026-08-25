from __future__ import annotations

import argparse
import copy
import json
import re
import subprocess
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LEDGER = ROOT / "data/legacy_revisions.json"
DEFAULT_ENTRIES = ROOT / "data/legacy_entries.json"
MISSING = object()
MISSING_MARKER = {"$missing": True}
REVISION_ID_RE = re.compile(r"^LR-[0-9]{4}-[0-9]{2}-[0-9]{2}-[0-9]{3}$")
RECORD_CREATION_KIND = "record-creation"
BASE_PATH_MISSING = object()


class RemediationError(ValueError):
    """Raised when the ledger or canonical data violates a remediation guard."""


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise RemediationError(f"cannot read {path}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise RemediationError(f"invalid JSON in {path}: {exc}") from exc


def repository_relative_path(path: Path, option: str) -> str:
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError as exc:
        raise RemediationError(f"{option} requires {path} to be inside the repository") from exc


def load_base_json(path: Path, base_ref: str) -> Any:
    """Read one JSON path from a verified Git base, or return a missing sentinel."""
    relative_path = repository_relative_path(path, "--base-ref")
    lookup = subprocess.run(
        ["git", "ls-tree", "--full-tree", "-r", "--name-only", base_ref, "--", relative_path],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if lookup.returncode != 0:
        raise RemediationError(
            f"cannot inspect {base_ref!r} for {relative_path}: "
            f"{lookup.stderr.strip() or 'git ls-tree failed'}"
        )
    if relative_path not in lookup.stdout.splitlines():
        return BASE_PATH_MISSING
    base_blob = subprocess.run(
        ["git", "show", f"{base_ref}:{relative_path}"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if base_blob.returncode != 0:
        raise RemediationError(
            f"cannot read {base_ref}:{relative_path}: "
            f"{base_blob.stderr.strip() or 'git show failed'}"
        )
    try:
        return json.loads(base_blob.stdout)
    except json.JSONDecodeError as exc:
        raise RemediationError(f"{base_ref}:{relative_path} is invalid JSON: {exc}") from exc


def validate_base_prefix(
    current: list[dict[str, Any]], ledger_path: Path, base_ref: str
) -> tuple[int, bool]:
    """Verify that a locally available Git base contains an exact ledger prefix.

    This deliberately performs no fetch. CI checks out history before invoking it;
    ordinary filesystem-only use can omit ``--base-ref`` entirely.
    """
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._/-]*", base_ref):
        raise RemediationError(f"unsafe Git base ref: {base_ref!r}")
    if ".." in base_ref or "@{" in base_ref:
        raise RemediationError(f"unsafe Git base ref: {base_ref!r}")
    verify = subprocess.run(
        ["git", "rev-parse", "--verify", f"{base_ref}^{{commit}}"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if verify.returncode != 0:
        raise RemediationError(
            f"Git base ref {base_ref!r} is not available locally; refusing to skip prefix check"
        )

    relative_path = repository_relative_path(ledger_path, "--base-ref")
    base = load_base_json(ledger_path, base_ref)
    if base is BASE_PATH_MISSING:
        # The first commit that introduces the ledger has no prefix to preserve.
        return 0, False
    if not isinstance(base, list):
        raise RemediationError(f"base ledger {base_ref}:{relative_path} is not a JSON array")
    if len(current) < len(base) or current[: len(base)] != base:
        raise RemediationError(
            f"revision ledger rewrites or removes history from {base_ref}:{relative_path}; "
            "existing revisions must remain an exact prefix"
        )
    return len(base), True


def compact(value: Any, limit: int = 240) -> str:
    if value is MISSING:
        return "<missing>"
    rendered = json.dumps(value, ensure_ascii=False, sort_keys=True)
    if len(rendered) <= limit:
        return rendered
    return rendered[: limit - 1] + "…"


def validate_ledger(ledger: Any) -> list[dict[str, Any]]:
    if not isinstance(ledger, list) or not ledger:
        raise RemediationError("revision ledger must be a non-empty JSON array")

    revisions = ledger

    revision_ids: set[str] = set()
    legacy_ids_with_revisions: set[str] = set()
    record_creation_ids: set[str] = set()
    prior_replacements: dict[tuple[str, str], Any] = {}
    previous_recorded_at: date | None = None
    for revision_index, revision in enumerate(revisions):
        location = f"revisions[{revision_index}]"
        if not isinstance(revision, dict):
            raise RemediationError(f"{location} must be an object")

        revision_id = revision.get("revision_id")
        legacy_id = revision.get("legacy_id")
        changes = revision.get("changes")
        if not isinstance(revision_id, str) or not revision_id:
            raise RemediationError(f"{location}.revision_id must be a non-empty string")
        if not REVISION_ID_RE.fullmatch(revision_id):
            raise RemediationError(f"{location}.revision_id must match LR-YYYY-MM-DD-NNN")
        if revision_id in revision_ids:
            raise RemediationError(f"duplicate revision_id: {revision_id}")
        revision_ids.add(revision_id)
        try:
            recorded_at = date.fromisoformat(str(revision.get("recorded_at") or ""))
        except ValueError as exc:
            raise RemediationError(f"{revision_id}: recorded_at must be an ISO calendar date") from exc
        if previous_recorded_at and recorded_at < previous_recorded_at:
            raise RemediationError(f"{revision_id}: append-only ledger dates move backward")
        previous_recorded_at = recorded_at
        if not isinstance(legacy_id, str) or not legacy_id:
            raise RemediationError(f"{revision_id}: legacy_id must be a non-empty string")
        for field in ("kind", "summary"):
            if not isinstance(revision.get(field), str) or not revision[field].strip():
                raise RemediationError(f"{revision_id}: {field} must be a non-empty string")
        kind = revision["kind"]
        if kind == RECORD_CREATION_KIND:
            if legacy_id in record_creation_ids:
                raise RemediationError(f"{revision_id}: duplicate record-creation for {legacy_id}")
            if legacy_id in legacy_ids_with_revisions:
                raise RemediationError(
                    f"{revision_id}: record-creation must be the first revision for {legacy_id}"
                )
            record_creation_ids.add(legacy_id)
        provenance = revision.get("provenance")
        if not isinstance(provenance, list) or not provenance:
            raise RemediationError(f"{revision_id}: provenance must be a non-empty array")
        for provenance_index, item in enumerate(provenance):
            item_location = f"{revision_id}.provenance[{provenance_index}]"
            if not isinstance(item, dict):
                raise RemediationError(f"{item_location} must be an object")
            for field in ("type", "supports"):
                if not isinstance(item.get(field), str) or not item[field].strip():
                    raise RemediationError(f"{item_location}.{field} must be a non-empty string")
            if item.get("url") is not None:
                parsed = urlparse(str(item["url"]))
                if parsed.scheme != "https" or not parsed.netloc:
                    raise RemediationError(f"{item_location}.url must be an HTTPS URL")
        if not isinstance(changes, list) or not changes:
            raise RemediationError(f"{revision_id}: changes must be a non-empty array")

        fields_in_revision: set[str] = set()
        for change_index, change in enumerate(changes):
            change_location = f"{revision_id}.changes[{change_index}]"
            if not isinstance(change, dict):
                raise RemediationError(f"{change_location} must be an object")
            field = change.get("field")
            if not isinstance(field, str) or not field:
                raise RemediationError(f"{change_location}.field must be a non-empty string")
            if field == "legacy_id":
                raise RemediationError(f"{change_location}: legacy_id is immutable")
            if field in fields_in_revision:
                raise RemediationError(f"{revision_id}: duplicate field change for {field}")
            fields_in_revision.add(field)
            if "expected" not in change or "replacement" not in change:
                raise RemediationError(
                    f"{change_location} must declare expected and replacement values"
                )
            if change["expected"] == change["replacement"]:
                raise RemediationError(f"{change_location} does not change its value")
            if change["replacement"] == MISSING_MARKER:
                raise RemediationError(f"{change_location} cannot remove a canonical field")
            if kind == RECORD_CREATION_KIND and change["expected"] != MISSING_MARKER:
                raise RemediationError(
                    f"{change_location}: record-creation fields must start from the missing marker"
                )

            key = (legacy_id, field)
            if key in prior_replacements and change["expected"] != prior_replacements[key]:
                raise RemediationError(
                    f"{change_location} does not continue the append-only value chain for "
                    f"{legacy_id}.{field}; expected {compact(prior_replacements[key])}"
                )
            prior_replacements[key] = change["replacement"]

        legacy_ids_with_revisions.add(legacy_id)

    return revisions


def validate_entries(entries: Any) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    if not isinstance(entries, list):
        raise RemediationError("canonical legacy entries must be a JSON array")

    by_id: dict[str, dict[str, Any]] = {}
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            raise RemediationError(f"legacy entry at index {index} must be an object")
        legacy_id = entry.get("legacy_id")
        if not isinstance(legacy_id, str) or not legacy_id:
            raise RemediationError(f"legacy entry at index {index} has no stable legacy_id")
        if legacy_id in by_id:
            raise RemediationError(f"duplicate canonical legacy_id: {legacy_id}")
        by_id[legacy_id] = entry
    return entries, by_id


def validate_canonical_delta(
    base_entries: Any,
    current_entries: list[dict[str, Any]],
    appended_revisions: list[dict[str, Any]],
) -> tuple[int, int]:
    """Prove that the post-base canonical delta is fully ledger-derived.

    Stable IDs from the base may not disappear or change. Existing records are
    reconstructed by replaying only revisions appended after the preserved base
    ledger prefix. A new record must begin with a ``record-creation`` revision;
    its field changes use the missing marker and form an auditable initial
    snapshot. Exact comparison after replay catches unlogged field edits,
    additions, and removals.
    """
    _, base_by_id = validate_entries(base_entries)
    _, current_by_id = validate_entries(current_entries)

    removed_ids = sorted(set(base_by_id) - set(current_by_id))
    if removed_ids:
        raise RemediationError(
            "canonical legacy records were deleted or had stable IDs changed since the base: "
            + ", ".join(removed_ids[:20])
            + (" …" if len(removed_ids) > 20 else "")
        )

    replayed = copy.deepcopy(base_by_id)
    created_ids: set[str] = set()
    for revision in appended_revisions:
        revision_id = revision["revision_id"]
        legacy_id = revision["legacy_id"]
        kind = revision["kind"]

        if legacy_id not in replayed:
            if kind != RECORD_CREATION_KIND:
                raise RemediationError(
                    f"{revision_id}: {legacy_id} is not in the base canonical dataset; "
                    f"its first appended revision must use kind {RECORD_CREATION_KIND!r}"
                )
            replayed[legacy_id] = {"legacy_id": legacy_id}
            created_ids.add(legacy_id)
        elif kind == RECORD_CREATION_KIND:
            raise RemediationError(
                f"{revision_id}: record-creation cannot recreate existing canonical ID {legacy_id}"
            )

        candidate = replayed[legacy_id]
        for change in revision["changes"]:
            field = change["field"]
            expected = MISSING if change["expected"] == MISSING_MARKER else change["expected"]
            actual = candidate[field] if field in candidate else MISSING
            if actual != expected:
                raise RemediationError(
                    f"{revision_id}: base replay guard failed for {legacy_id}.{field}: "
                    f"expected {compact(expected)}, found {compact(actual)}"
                )
            candidate[field] = copy.deepcopy(change["replacement"])

    unlogged_records = sorted(set(current_by_id) - set(replayed))
    if unlogged_records:
        raise RemediationError(
            "canonical legacy record creation is not logged: "
            + ", ".join(unlogged_records[:20])
            + f"; add a {RECORD_CREATION_KIND!r} revision that snapshots every initial field"
        )

    unexpected_records = sorted(set(replayed) - set(current_by_id))
    if unexpected_records:
        raise RemediationError(
            "appended revisions create canonical records absent from the current dataset: "
            + ", ".join(unexpected_records[:20])
        )

    for legacy_id in sorted(current_by_id):
        expected_entry = replayed[legacy_id]
        current_entry = current_by_id[legacy_id]
        if expected_entry == current_entry:
            continue
        fields = sorted(set(expected_entry) | set(current_entry))
        changed_fields = [
            field
            for field in fields
            if expected_entry.get(field, MISSING) != current_entry.get(field, MISSING)
        ]
        raise RemediationError(
            f"{legacy_id}: canonical field change/addition/removal is not represented by "
            "revisions appended after the base ledger prefix: "
            + ", ".join(changed_fields[:20])
            + (" …" if len(changed_fields) > 20 else "")
        )

    return len(base_by_id), len(created_ids)


def grouped_changes(
    revisions: list[dict[str, Any]],
) -> dict[tuple[str, str], list[tuple[str, Any, Any]]]:
    grouped: dict[tuple[str, str], list[tuple[str, Any, Any]]] = defaultdict(list)
    for revision in revisions:
        for change in revision["changes"]:
            expected = MISSING if change["expected"] == MISSING_MARKER else change["expected"]
            grouped[(revision["legacy_id"], change["field"])].append(
                (revision["revision_id"], expected, change["replacement"])
            )
    return dict(grouped)


def apply_changes(
    by_id: dict[str, dict[str, Any]],
    groups: dict[tuple[str, str], list[tuple[str, Any, Any]]],
    *,
    check_only: bool,
) -> tuple[int, set[str], int]:
    changed_fields = 0
    changed_records: set[str] = set()
    already_current = 0

    for (legacy_id, field), operations in groups.items():
        if legacy_id not in by_id:
            raise RemediationError(f"ledger references missing canonical record {legacy_id}")
        entry = by_id[legacy_id]
        actual = entry[field] if field in entry else MISSING
        final_replacement = operations[-1][2]
        if actual == final_replacement:
            already_current += 1
            continue

        # The canonical value may already include any prefix of this field's
        # append-only chain (for example, all revisions preserved in the Git
        # base). Resume after the latest matching chain state, then guard and
        # apply only the remaining suffix.
        next_operation: int | None = 0 if actual == operations[0][1] else None
        for operation_index, (_, _, replacement) in enumerate(operations):
            if actual == replacement:
                next_operation = operation_index + 1
        if next_operation is None:
            states = [operations[0][1], *(operation[2] for operation in operations)]
            raise RemediationError(
                f"ledger guard failed for {legacy_id}.{field}: found {compact(actual)}, "
                f"which is not an expected chain state ({', '.join(compact(value, 80) for value in states)})"
            )

        candidate = actual
        for revision_id, expected, replacement in operations[next_operation:]:
            if candidate != expected:
                raise RemediationError(
                    f"{revision_id} guard failed for {legacy_id}.{field}: "
                    f"expected {compact(expected)}, found {compact(candidate)}"
                )
            candidate = replacement

        if candidate != final_replacement:
            raise RemediationError(
                f"internal error: {legacy_id}.{field} did not reach its final ledger value"
            )
        changed_fields += 1
        changed_records.add(legacy_id)
        if not check_only:
            entry[field] = candidate

    return changed_fields, changed_records, already_current


def order_is_current(entries: list[dict[str, Any]]) -> bool:
    # Python's sort is stable, so records sharing a sort date retain their
    # existing editorial order while corrected dates move to the right place.
    return entries == sorted(entries, key=lambda entry: entry["sort"])


def sort_entries(entries: list[dict[str, Any]]) -> None:
    entries.sort(key=lambda entry: entry["sort"])


def render_entries(entries: list[dict[str, Any]]) -> str:
    if not entries:
        return "[]\n"
    lines = [
        json.dumps(entry, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
        for entry in entries
    ]
    return "[\n" + ",\n".join(lines) + "\n]\n"


def write_entries(path: Path, entries: list[dict[str, Any]]) -> None:
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(render_entries(entries), encoding="utf-8")
    temporary.replace(path)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Apply the append-only legacy revision ledger to canonical legacy data with "
            "expected-old-value guards."
        )
    )
    parser.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER)
    parser.add_argument("--entries", type=Path, default=DEFAULT_ENTRIES)
    parser.add_argument(
        "--check",
        action="store_true",
        help="validate guards and fail if the canonical dataset has unapplied revisions",
    )
    parser.add_argument(
        "--base-ref",
        help=(
            "locally available Git commit/ref whose revision ledger must be an exact prefix "
            "and whose canonical legacy dataset, when present, must be reproducible solely "
            "from appended revisions; no network fetch is attempted"
        ),
    )
    args = parser.parse_args()

    try:
        revisions = validate_ledger(load_json(args.ledger))
        base_revision_count: int | None = None
        base_ledger_present = False
        if args.base_ref:
            base_revision_count, base_ledger_present = validate_base_prefix(
                revisions, args.ledger, args.base_ref
            )
        entries, by_id = validate_entries(load_json(args.entries))
        groups = grouped_changes(revisions)

        base_canonical_count: int | None = None
        base_created_count = 0
        if args.base_ref:
            base_entries = load_base_json(args.entries, args.base_ref)
            if base_entries is not BASE_PATH_MISSING:
                if not base_ledger_present:
                    raise RemediationError(
                        "the base contains canonical legacy data but no revision ledger; "
                        "cannot prove which canonical changes are newly appended"
                    )
                # Validate the prospective post-application dataset. This keeps
                # normal apply mode useful while making --check fail below when
                # valid appended revisions have not yet been applied.
                prospective_entries = copy.deepcopy(entries)
                _, prospective_by_id = validate_entries(prospective_entries)
                apply_changes(prospective_by_id, groups, check_only=False)
                base_canonical_count, base_created_count = validate_canonical_delta(
                    base_entries,
                    prospective_entries,
                    revisions[base_revision_count:],
                )

        changed_fields, changed_records, already_current = apply_changes(
            by_id, groups, check_only=args.check
        )
        order_current = order_is_current(entries)
        base_note = ""
        if base_revision_count is not None:
            base_note = (
                f" Preserved {base_revision_count} base revision(s) as an exact prefix."
            )
            if base_canonical_count is not None:
                base_note += (
                    f" Verified the ledger-derived delta from {base_canonical_count} base "
                    f"canonical record(s), including {base_created_count} logged creation(s)."
                )
            else:
                base_note += " The base predates the canonical legacy dataset."

        if args.check:
            if changed_fields or not order_current:
                order_note = " Canonical record order also needs a stable sort-date refresh." if not order_current else ""
                print(
                    f"Legacy remediation check failed: {changed_fields} field(s) across "
                    f"{len(changed_records)} record(s) have unapplied ledger values."
                    f"{order_note}"
                )
                return 1
            print(
                f"Verified {len(revisions)} legacy revision(s): all {already_current} guarded "
                "field value(s) are current."
                + base_note
            )
            return 0

        if not order_current:
            sort_entries(entries)

        if changed_fields or not order_current:
            write_entries(args.entries, entries)
            print(
                f"Applied {changed_fields} guarded field change(s) across "
                f"{len(changed_records)} legacy record(s); "
                f"stable sort-date refresh: {'yes' if not order_current else 'no'}."
                + base_note
            )
        else:
            print(
                f"No changes needed; {len(revisions)} legacy revision(s) and "
                f"{already_current} guarded field value(s) are already applied."
                + base_note
            )
        return 0
    except (OSError, RemediationError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
