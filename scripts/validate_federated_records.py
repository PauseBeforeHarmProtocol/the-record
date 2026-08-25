#!/usr/bin/env python3
"""Validate federated external-archive records without trusting upstream prose.

The JSON Schema supplies the portable shape contract. This script adds semantic
rules JSON Schema cannot express cleanly: deterministic fingerprints, origin
uniqueness, independently derived collision signals, claim/source linkage,
non-additive counting, and lifecycle graph integrity. It intentionally uses
only the standard library; if ``jsonschema`` is installed, full Draft 2020-12
validation runs as an additional check.
"""

from __future__ import annotations

import argparse
import calendar
import copy
import difflib
import hashlib
import json
import re
import sys
import unicodedata
from collections import defaultdict, deque
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, unquote, urlencode, urlparse, urlunparse


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA = ROOT / "data" / "federated_records.json"
DEFAULT_SCHEMA = ROOT / "schemas" / "federated_record.schema.json"
DEFAULT_REGISTRY = ROOT / "data" / "archive_registry.json"
DEFAULT_CURRENT_DATA = ROOT / "data" / "current_entries.json"
DEFAULT_LEGACY_DATA = ROOT / "data" / "legacy_entries.json"

STATUS_VALUES = {
    "research_lead",
    "source_reviewed",
    "interpretive_draft",
    "editor_reviewed",
    "published",
    "superseded",
}
NON_LEAD_STATUSES = STATUS_VALUES - {"research_lead"}
LIFECYCLE_RELATIONSHIPS = {
    "same_action_lifecycle",
    "previous_stage",
    "next_stage",
    "supersedes",
    "superseded_by",
}
RECIPROCAL_LIFECYCLE_RELATIONSHIP = {
    "same_action_lifecycle": "same_action_lifecycle",
    "previous_stage": "next_stage",
    "next_stage": "previous_stage",
    "supersedes": "superseded_by",
    "superseded_by": "supersedes",
}
DATE_RE = re.compile(r"^[0-9]{4}(?:-(?:0[1-9]|1[0-2])(?:-(?:0[1-9]|[12][0-9]|3[01]))?)?$")
HASH_RE = re.compile(r"^sha256:[a-f0-9]{64}$")
RECORD_ID_RE = re.compile(r"^FED-[A-Z0-9][A-Z0-9._-]{2,}$")
EXECUTIVE_ORDER_RE = re.compile(
    r"(?<![a-z0-9])(?:executive[\W_]*order|e[\W_]*o)"
    r"(?:[\W_]*(?:no|number))?[\W_]*0*(\d{3,6})(?!\d)",
    re.IGNORECASE,
)
SCOTUS_APPLICATION_RE = re.compile(
    r"(?<![a-z0-9])(\d{2})[\W_]*([ao])[\W_]*0*(\d{1,5})(?![a-z0-9])",
    re.IGNORECASE,
)
SCOTUS_DOCKET_RE = re.compile(r"(?<!\d)(\d{2})\s*[-\u2013\u2014]\s*0*(\d{1,6})(?!\d)")
TRACKING_QUERY_KEYS = {
    "fbclid",
    "gclid",
    "mc_cid",
    "mc_eid",
    "ref",
    "source",
}


class Report:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def error(self, location: str, message: str) -> None:
        self.errors.append(f"{location}: {message}")

    def warn(self, location: str, message: str) -> None:
        self.warnings.append(f"{location}: {message}")


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"missing file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON in {path}: {exc}") from exc


def normalize_component(value: str) -> str:
    value = unicodedata.normalize("NFKC", value).casefold()
    value = re.sub(r"[^\w]+", " ", value, flags=re.UNICODE)
    return " ".join(value.split())


def normalize_formal_identifier(value: str) -> str:
    """Normalize an official identifier independently of editor fingerprints."""

    value = unicodedata.normalize("NFKC", value).casefold()
    return re.sub(r"[^a-z0-9]+", "", value)


def contains_scotus_context(value: str) -> bool:
    normalized = normalize_component(value)
    return any(
        marker in normalized
        for marker in (
            "scotus",
            "supreme court",
            "supremecourt gov",
            "docket",
            "case no",
            "case number",
        )
    )


def extract_formal_identifiers_from_text(value: Any, *, scotus_context: bool = False) -> set[str]:
    """Extract narrowly recognizable official identifiers from untrusted prose.

    The editor's fingerprint basis remains useful, but it is not authoritative.
    This extractor deliberately recognizes the common spelling and punctuation
    variants of executive orders and Supreme Court docket numbers wherever they
    appear in record prose or source metadata.
    """

    if not isinstance(value, str) or not value.strip():
        return set()
    text = unicodedata.normalize("NFKC", unquote(value))
    identifiers = {f"eo:{int(match.group(1))}" for match in EXECUTIVE_ORDER_RE.finditer(text)}
    identifiers.update(
        f"scotus:{match.group(1)}{match.group(2).casefold()}{int(match.group(3))}"
        for match in SCOTUS_APPLICATION_RE.finditer(text)
    )
    if scotus_context or contains_scotus_context(text):
        identifiers.update(
            f"scotus:{match.group(1)}-{int(match.group(2))}"
            for match in SCOTUS_DOCKET_RE.finditer(text)
        )
    return identifiers


def extract_formal_identifiers_from_url(value: Any) -> set[str]:
    """Extract recognized identifiers from a URL without mistaking date paths for dockets."""

    if not isinstance(value, str) or not value.strip():
        return set()
    identifiers = extract_formal_identifiers_from_text(value)
    try:
        parsed = urlparse(value)
    except ValueError:
        return identifiers
    hostname = (parsed.hostname or "").casefold()
    if hostname == "supremecourt.gov" or hostname.endswith(".supremecourt.gov"):
        components = [
            unquote(component)
            for component in re.split(r"[/&=?#]", parsed.path + "?" + parsed.query)
            if component
        ]
        for component in components:
            application = re.fullmatch(r"(\d{2})[\W_]*([ao])[\W_]*0*(\d{1,5})(?:\.[a-z0-9]+)?", component, re.I)
            if application:
                identifiers.add(
                    f"scotus:{application.group(1)}{application.group(2).casefold()}{int(application.group(3))}"
                )
                continue
            docket = re.fullmatch(r"(\d{2})[-\u2013\u2014]0*(\d{1,6})(?:\.[a-z0-9]+)?", component, re.I)
            if docket:
                identifiers.add(f"scotus:{docket.group(1)}-{int(docket.group(2))}")
    return identifiers


def normalize_evidence_url(value: str) -> str:
    """Canonicalize a direct-evidence URL while retaining identity-bearing query data."""

    parsed = urlparse(value)
    try:
        hostname = (parsed.hostname or "").casefold()
        port = parsed.port
    except ValueError:
        return value.strip()
    if port and not (parsed.scheme.casefold() == "https" and port == 443):
        hostname = f"{hostname}:{port}"
    path = re.sub(r"/{2,}", "/", unquote(parsed.path or "/"))
    if path != "/":
        path = path.rstrip("/")
    query = urlencode(
        sorted(
            (key, item)
            for key, item in parse_qsl(parsed.query, keep_blank_values=True)
            if not key.casefold().startswith("utm_") and key.casefold() not in TRACKING_QUERY_KEYS
        ),
        doseq=True,
    )
    return urlunparse((parsed.scheme.casefold(), hostname, path, "", query, ""))


def record_date_interval(record: dict[str, Any]) -> tuple[date, date] | None:
    """Return the inclusive uncertainty interval represented by a record date."""

    value = record.get("event_date")
    if not isinstance(value, str) or not DATE_RE.fullmatch(value):
        return None
    try:
        if len(value) == 4:
            year = int(value)
            return date(year, 1, 1), date(year, 12, 31)
        if len(value) == 7:
            year, month = (int(part) for part in value.split("-"))
            return date(year, month, 1), date(year, month, calendar.monthrange(year, month)[1])
        exact = date.fromisoformat(value)
    except ValueError:
        return None
    if record.get("date_precision") == "approximate":
        return exact - timedelta(days=31), exact + timedelta(days=31)
    return exact, exact


def intervals_overlap(left: tuple[date, date] | None, right: tuple[date, date] | None) -> bool:
    return bool(left and right and left[0] <= right[1] and right[0] <= left[1])


def normalized_claim_text(record: dict[str, Any]) -> str:
    claims = (record.get("facts") or {}).get("claims") or []
    return normalize_component(
        " ".join(
            str(claim.get("text", ""))
            for claim in claims
            if isinstance(claim, dict) and str(claim.get("text", "")).strip()
        )
    )


def text_similarity(left: str, right: str) -> float:
    """Combine sequence and token similarity without an external dependency."""

    if not left or not right:
        return 0.0
    left_tokens = set(left.split())
    right_tokens = set(right.split())
    union = left_tokens | right_tokens
    jaccard = len(left_tokens & right_tokens) / len(union) if union else 0.0
    sequence = difflib.SequenceMatcher(None, left, right, autojunk=False).ratio()
    return max(jaccard, sequence)


def direct_evidence_urls(record: dict[str, Any]) -> set[str]:
    """Return normalized underlying evidence URLs, never archive metadata URLs."""

    return {
        normalize_evidence_url(str(source.get("url")))
        for source in record.get("sources") or []
        if isinstance(source, dict)
        and source.get("source_type") != "external_archive_metadata"
        and valid_https_url(source.get("url"))
    }


def formal_identifiers(record: dict[str, Any]) -> set[str]:
    """Return declared plus independently derived canonical formal identifiers."""

    identifiers: set[str] = set()
    basis = ((record.get("deduplication") or {}).get("fingerprint_basis") or {})
    for item in basis.get("formal_identifiers") or []:
        value = str(item)
        normalized = normalize_formal_identifier(value)
        if normalized:
            identifiers.add(f"declared:{normalized}")
        identifiers.update(extract_formal_identifiers_from_text(value))

    identifiers.update(extract_formal_identifiers_from_text(record.get("title")))
    facts = record.get("facts") or {}
    for claim in facts.get("claims") or []:
        if isinstance(claim, dict):
            identifiers.update(extract_formal_identifiers_from_text(claim.get("text")))

    for source in record.get("sources") or []:
        if not isinstance(source, dict):
            continue
        source_context = " ".join(
            str(source.get(field, ""))
            for field in ("source_id", "title", "publisher")
        )
        scotus_context = contains_scotus_context(source_context) or contains_scotus_context(
            str(source.get("url", ""))
        )
        for field in ("source_id", "title", "publisher"):
            identifiers.update(
                extract_formal_identifiers_from_text(
                    source.get(field),
                    scotus_context=scotus_context,
                )
            )
        identifiers.update(extract_formal_identifiers_from_url(source.get("url")))
        identifiers.update(extract_formal_identifiers_from_url(source.get("archived_url")))
    return identifiers


def has_reciprocal_lifecycle_link(left: dict[str, Any], right: dict[str, Any]) -> bool:
    """Return true only for an explicit, reciprocal previous/next stage link."""

    left_id = str(left.get("record_id"))
    right_id = str(right.get("record_id"))
    left_lifecycle = left.get("lifecycle") or {}
    right_lifecycle = right.get("lifecycle") or {}
    left_previous = {str(item) for item in left_lifecycle.get("previous_record_ids") or []}
    left_next = {str(item) for item in left_lifecycle.get("next_record_ids") or []}
    right_previous = {str(item) for item in right_lifecycle.get("previous_record_ids") or []}
    right_next = {str(item) for item in right_lifecycle.get("next_record_ids") or []}
    return (right_id in left_next and left_id in right_previous) or (
        right_id in left_previous and left_id in right_next
    )


def find_directed_cycle(graph: dict[str, set[str]]) -> list[str] | None:
    """Return one deterministic directed cycle, including its repeated start."""

    state: dict[str, int] = {node: 0 for node in graph}
    path: list[str] = []
    positions: dict[str, int] = {}

    def visit(node: str) -> list[str] | None:
        state[node] = 1
        positions[node] = len(path)
        path.append(node)
        for neighbor in sorted(graph.get(node, set())):
            if state.get(neighbor, 0) == 0:
                found = visit(neighbor)
                if found:
                    return found
            elif state.get(neighbor) == 1:
                return path[positions[neighbor] :] + [neighbor]
        path.pop()
        positions.pop(node, None)
        state[node] = 2
        return None

    for node in sorted(graph):
        if state[node] == 0:
            found = visit(node)
            if found:
                return found
    return None


def sha256_key(material: str) -> str:
    return "sha256:" + hashlib.sha256(material.encode("utf-8")).hexdigest()


def expected_fingerprint_keys(record: dict[str, Any]) -> tuple[str, str]:
    dedupe = record.get("deduplication") or {}
    basis = dedupe.get("fingerprint_basis") or {}
    lifecycle = record.get("lifecycle") or {}
    actor = normalize_component(str(basis.get("primary_actor", "")))
    subject = normalize_component(str(basis.get("normalized_subject", "")))
    formal = sorted(
        normalize_component(str(item))
        for item in basis.get("formal_identifiers", [])
        if str(item).strip()
    )
    family_material = "\x1f".join(
        ["federated-record-v1", f"actor={actor}", f"subject={subject}", f"formal={','.join(formal)}"]
    )
    family_key = sha256_key(family_material)
    dedupe_material = "\x1f".join(
        [
            family_key,
            f"stage={normalize_component(str(lifecycle.get('stage', '')))}",
            f"date={basis.get('event_date', '')}",
        ]
    )
    return family_key, sha256_key(dedupe_material)


def valid_https_url(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    try:
        parsed = urlparse(value)
        hostname = parsed.hostname
        parsed.port
    except ValueError:
        return False
    return parsed.scheme == "https" and bool(hostname)


def valid_datetime(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return "T" in value


def require_fields(report: Report, location: str, value: Any, fields: set[str]) -> dict[str, Any]:
    if not isinstance(value, dict):
        report.error(location, "must be an object")
        return {}
    missing = sorted(fields - set(value))
    if missing:
        report.error(location, f"missing required fields: {', '.join(missing)}")
    return value


def validate_schema_with_optional_library(records: Any, schema: Any, report: Report) -> str:
    try:
        import jsonschema  # type: ignore
    except ImportError:
        return "not installed; semantic validator still ran"

    try:
        validator_class = jsonschema.validators.validator_for(schema)
        validator_class.check_schema(schema)
        validator = validator_class(schema, format_checker=jsonschema.FormatChecker())
        for error in sorted(validator.iter_errors(records), key=lambda item: list(item.absolute_path)):
            path = "$" + "".join(f"[{part}]" if isinstance(part, int) else f".{part}" for part in error.absolute_path)
            report.error(path, f"schema: {error.message}")
    except Exception as exc:  # pragma: no cover - defensive around optional dependency
        report.error("schema", f"could not execute Draft 2020-12 validation: {exc}")
        return "failed"
    return "executed"


def validate_record_shape(
    record: Any,
    index: int,
    allowed_archives: set[str],
    report: Report,
) -> dict[str, Any]:
    location = f"records[{index}]"
    required = {
        "record_id",
        "status",
        "title",
        "event_date",
        "date_precision",
        "deduplication",
        "origins",
        "counting",
        "lifecycle",
        "crosslinks",
        "facts",
        "sources",
        "significance",
        "goalpost_response",
        "maybe_therefore",
        "evidence",
        "provenance",
        "consequences",
        "revisions",
        "tags",
        "institutions",
    }
    record = require_fields(report, location, record, required)
    if not record:
        return {}

    record_id = record.get("record_id")
    record_location = str(record_id) if isinstance(record_id, str) and record_id else location
    if not isinstance(record_id, str) or not RECORD_ID_RE.fullmatch(record_id):
        report.error(record_location, "record_id must match FED-[A-Z0-9._-]+")

    status = record.get("status")
    if status not in STATUS_VALUES:
        report.error(record_location, f"invalid status {status!r}")

    event_date = record.get("event_date")
    if not isinstance(event_date, str) or not DATE_RE.fullmatch(event_date):
        report.error(record_location, "event_date must be YYYY, YYYY-MM, or YYYY-MM-DD")
    precision = record.get("date_precision")
    expected_lengths = {"year": 4, "month": 7, "day": 10}
    if precision in expected_lengths and isinstance(event_date, str) and len(event_date) != expected_lengths[precision]:
        report.error(record_location, f"date_precision {precision!r} conflicts with event_date {event_date!r}")

    origins = record.get("origins")
    if not isinstance(origins, list) or not origins:
        report.error(record_location, "origins must contain at least one upstream record")
        origins = []
    local_origin_keys: set[str] = set()
    for origin_index, origin_value in enumerate(origins):
        origin_location = f"{record_location}.origins[{origin_index}]"
        origin = require_fields(
            report,
            origin_location,
            origin_value,
            {
                "archive_id",
                "external_id",
                "origin_key",
                "external_url",
                "external_record_unit",
                "unit_scope",
                "origin_role",
                "retrieved_at",
                "content_use",
            },
        )
        archive_id = origin.get("archive_id")
        external_id = origin.get("external_id")
        expected_origin_key = f"{archive_id}:{external_id}"
        if archive_id not in allowed_archives:
            report.error(origin_location, f"archive_id {archive_id!r} is absent from archive_registry.json")
        if not isinstance(external_id, str) or not external_id.strip():
            report.error(origin_location, "external_id must be a non-empty string")
        if origin.get("origin_key") != expected_origin_key:
            report.error(origin_location, f"origin_key must equal {expected_origin_key!r}")
        if expected_origin_key in local_origin_keys:
            report.error(origin_location, "duplicate archive_id + external_id inside one record")
        local_origin_keys.add(expected_origin_key)
        if not valid_https_url(origin.get("external_url")):
            report.error(origin_location, "external_url must be an HTTPS URL")
        if not valid_datetime(origin.get("retrieved_at")):
            report.error(origin_location, "retrieved_at must be an ISO 8601 date-time")

    dedupe = require_fields(
        report,
        f"{record_location}.deduplication",
        record.get("deduplication"),
        {
            "fingerprint_version",
            "dedupe_key",
            "event_family_key",
            "fingerprint_basis",
            "origin_aliases",
            "duplicate_review",
        },
    )
    if dedupe.get("fingerprint_version") != "federated-record-v1":
        report.error(record_location, "unsupported fingerprint_version")
    basis = require_fields(
        report,
        f"{record_location}.deduplication.fingerprint_basis",
        dedupe.get("fingerprint_basis"),
        {"event_date", "primary_actor", "normalized_subject", "formal_identifiers"},
    )
    if basis.get("event_date") != event_date:
        report.error(record_location, "fingerprint event_date must equal record event_date")
    aliases = dedupe.get("origin_aliases")
    if not isinstance(aliases, list) or set(aliases) != local_origin_keys or len(aliases) != len(local_origin_keys):
        report.error(record_location, "origin_aliases must exactly match the unique origin_key set")
    family_key = dedupe.get("event_family_key")
    dedupe_key = dedupe.get("dedupe_key")
    if not isinstance(family_key, str) or not HASH_RE.fullmatch(family_key):
        report.error(record_location, "event_family_key must be sha256:<64 lowercase hex>")
    if not isinstance(dedupe_key, str) or not HASH_RE.fullmatch(dedupe_key):
        report.error(record_location, "dedupe_key must be sha256:<64 lowercase hex>")
    try:
        expected_family, expected_dedupe = expected_fingerprint_keys(record)
    except Exception as exc:
        report.error(record_location, f"could not calculate fingerprint: {exc}")
    else:
        if family_key != expected_family:
            report.error(record_location, f"event_family_key is not deterministic; expected {expected_family}")
        if dedupe_key != expected_dedupe:
            report.error(record_location, f"dedupe_key is not deterministic; expected {expected_dedupe}")

    lifecycle = require_fields(
        report,
        f"{record_location}.lifecycle",
        record.get("lifecycle"),
        {"stage", "stage_date", "previous_record_ids", "next_record_ids"},
    )
    if lifecycle.get("stage_date") != event_date:
        report.error(record_location, "lifecycle.stage_date must equal event_date")

    counting = require_fields(
        report,
        f"{record_location}.counting",
        record.get("counting"),
        {
            "upstream_record_unit",
            "comparability_group",
            "additive_across_archives",
            "count_disposition",
            "canonical_the_record_entry_id",
            "rule",
        },
    )
    if counting.get("additive_across_archives") is not False:
        report.error(record_location, "additive_across_archives must be false")
    expected_rule = (
        "Preserve upstream units separately; count a published canonical event once in The Record, "
        "never once per contributing archive."
    )
    if counting.get("rule") != expected_rule:
        report.error(record_location, "counting.rule does not preserve the canonical non-additive rule")

    facts = require_fields(report, f"{record_location}.facts", record.get("facts"), {"claims", "scope_note"})
    claims = facts.get("claims")
    if not isinstance(claims, list):
        report.error(record_location, "facts.claims must be an array")
        claims = []
    claim_ids: set[str] = set()
    claim_refs: dict[str, set[str]] = {}
    for claim_index, claim_value in enumerate(claims):
        claim_location = f"{record_location}.facts.claims[{claim_index}]"
        claim = require_fields(report, claim_location, claim_value, {"claim_id", "text", "claim_status", "source_refs"})
        claim_id = claim.get("claim_id")
        if not isinstance(claim_id, str) or not claim_id:
            report.error(claim_location, "claim_id must be non-empty")
            continue
        if claim_id in claim_ids:
            report.error(claim_location, f"duplicate claim_id {claim_id!r}")
        claim_ids.add(claim_id)
        refs = claim.get("source_refs")
        if not isinstance(refs, list) or not refs:
            report.error(claim_location, "every fact claim requires at least one source_ref")
            refs = []
        claim_refs[claim_id] = set(str(ref) for ref in refs)

    sources = record.get("sources")
    if not isinstance(sources, list):
        report.error(record_location, "sources must be an array")
        sources = []
    source_ids: set[str] = set()
    source_by_id: dict[str, dict[str, Any]] = {}
    for source_index, source_value in enumerate(sources):
        source_location = f"{record_location}.sources[{source_index}]"
        source = require_fields(
            report,
            source_location,
            source_value,
            {"source_id", "title", "publisher", "url", "source_type", "publication_date", "accessed_at", "supports_claim_ids"},
        )
        source_id = source.get("source_id")
        if not isinstance(source_id, str) or not source_id:
            report.error(source_location, "source_id must be non-empty")
            continue
        if source_id in source_ids:
            report.error(source_location, f"duplicate source_id {source_id!r}")
        source_ids.add(source_id)
        source_by_id[source_id] = source
        if not valid_https_url(source.get("url")):
            report.error(source_location, "url must be an HTTPS URL")
        if not valid_datetime(source.get("accessed_at")):
            report.error(source_location, "accessed_at must be an ISO 8601 date-time")
        supported = source.get("supports_claim_ids")
        if not isinstance(supported, list):
            report.error(source_location, "supports_claim_ids must be an array")
            supported = []
        unknown_supported = set(str(item) for item in supported) - claim_ids
        if unknown_supported:
            report.error(source_location, f"supports unknown claims: {sorted(unknown_supported)}")

    for claim_id, refs in claim_refs.items():
        unknown_refs = refs - source_ids
        if unknown_refs:
            report.error(record_location, f"claim {claim_id} references unknown sources: {sorted(unknown_refs)}")
        direct_refs = [
            ref
            for ref in refs & source_ids
            if source_by_id[ref].get("source_type") != "external_archive_metadata"
        ]
        if status in NON_LEAD_STATUSES and not direct_refs:
            report.error(
                record_location,
                f"claim {claim_id} relies only on external archive metadata; inspect and cite an underlying source",
            )
        for ref in refs & source_ids:
            if claim_id not in set(source_by_id[ref].get("supports_claim_ids") or []):
                report.error(record_location, f"source {ref} does not declare support for claim {claim_id}")

    def validate_claim_basis(field_name: str, value: Any) -> None:
        if not isinstance(value, dict):
            return
        basis_ids = set(str(item) for item in value.get("basis_claim_ids", []))
        unknown = basis_ids - claim_ids
        if unknown:
            report.error(record_location, f"{field_name} references unknown fact claims: {sorted(unknown)}")

    validate_claim_basis("significance", record.get("significance"))
    validate_claim_basis("maybe_therefore", record.get("maybe_therefore"))

    goalpost = record.get("goalpost_response")
    if isinstance(goalpost, dict):
        response_refs = set(str(item) for item in goalpost.get("source_refs", []))
        unknown = response_refs - source_ids
        if unknown:
            report.error(record_location, f"goalpost_response references unknown sources: {sorted(unknown)}")
        if goalpost.get("response_kind") != "no_response_identified" and not response_refs:
            report.error(record_location, "a documented goalpost or response requires at least one source_ref")

    consequences = record.get("consequences")
    if not isinstance(consequences, list):
        report.error(record_location, "consequences must be an array")
        consequences = []
    for consequence_index, consequence in enumerate(consequences):
        consequence_location = f"{record_location}.consequences[{consequence_index}]"
        if not isinstance(consequence, dict):
            report.error(consequence_location, "must be an object")
            continue
        unknown = set(str(item) for item in consequence.get("source_refs", [])) - source_ids
        if unknown:
            report.error(consequence_location, f"references unknown sources: {sorted(unknown)}")

    evidence = require_fields(
        report,
        f"{record_location}.evidence",
        record.get("evidence"),
        {"tier", "confidence", "evidence_state", "human_reviewed", "reviewer", "reviewed_at", "limitations"},
    )
    provenance = require_fields(
        report,
        f"{record_location}.provenance",
        record.get("provenance"),
        {
            "created_at",
            "created_by",
            "last_modified_at",
            "source_level_review_completed",
            "external_archive_assertions_are_not_fact_sources",
            "publication_authorized",
            "copyright_boundary",
            "transformations",
        },
    )
    if not isinstance(evidence.get("human_reviewed"), bool):
        report.error(record_location, "evidence.human_reviewed must be a boolean")
    if provenance.get("external_archive_assertions_are_not_fact_sources") is not True:
        report.error(record_location, "external archive assertions must not be treated as fact sources")

    duplicate_review = require_fields(
        report,
        f"{record_location}.deduplication.duplicate_review",
        dedupe.get("duplicate_review"),
        {"state", "checked_at", "reviewer", "notes"},
    )
    revisions = record.get("revisions")
    if not isinstance(revisions, list):
        report.error(record_location, "revisions must be an array")
        revisions = []

    if status == "research_lead":
        if counting.get("count_disposition") != "not_counted_research_lead":
            report.error(record_location, "research leads must not enter any published total")
        if counting.get("canonical_the_record_entry_id") is not None:
            report.error(record_location, "research lead cannot claim a canonical The Record entry")
        if evidence.get("human_reviewed") is not False or evidence.get("evidence_state") != "lead_only":
            report.error(record_location, "research lead evidence must remain unreviewed and lead_only")
        if provenance.get("source_level_review_completed") is not False:
            report.error(record_location, "research lead cannot claim source-level review")
        if provenance.get("publication_authorized") is not False:
            report.error(record_location, "research lead cannot be publication-authorized")
    elif status in NON_LEAD_STATUSES:
        if not claims:
            report.error(record_location, "status beyond research_lead requires at least one sourced fact claim")
        if not sources:
            report.error(record_location, "status beyond research_lead requires source-level evidence")
        for field_name in ("significance", "goalpost_response", "maybe_therefore"):
            value = record.get(field_name)
            if not isinstance(value, dict) or not str(value.get("text", "")).strip():
                report.error(record_location, f"status beyond research_lead requires a complete {field_name} layer")
        maybe = record.get("maybe_therefore")
        if isinstance(maybe, dict):
            maybe_text = str(maybe.get("text", ""))
            if not re.search(r"\bmaybe\b", maybe_text, re.IGNORECASE) or not re.search(
                r"\btherefore\b", maybe_text, re.IGNORECASE
            ):
                report.error(record_location, "maybe_therefore.text requires explicit Maybe and Therefore clauses")
            if re.search(r"\bmaybe\s+therefore\b", maybe_text, re.IGNORECASE):
                report.error(record_location, "maybe_therefore.text must not collapse the clauses into 'Maybe therefore'")
            if maybe.get("editorial_not_fact") is not True:
                report.error(record_location, "maybe_therefore must be explicitly labeled editorial_not_fact")
            if not maybe.get("would_change_if"):
                report.error(record_location, "maybe_therefore must state what evidence would change the inference")
        if not evidence.get("reviewer") or not valid_datetime(evidence.get("reviewed_at")):
            report.error(record_location, "status beyond research_lead requires a dated source-review attribution")
        if status in {"editor_reviewed", "published"} and evidence.get("human_reviewed") is not True:
            report.error(record_location, f"{status} status requires dated human evidence review")
        if provenance.get("source_level_review_completed") is not True:
            report.error(record_location, "status beyond research_lead requires completed source-level review")
        if duplicate_review.get("state") not in {"clear", "merged_external_origins"}:
            report.error(record_location, "reviewed or published record requires cleared duplicate review")
        if not valid_datetime(duplicate_review.get("checked_at")) or not duplicate_review.get("reviewer"):
            report.error(record_location, "duplicate review requires reviewer and checked_at")
        if len(origins) > 1 and duplicate_review.get("state") != "merged_external_origins":
            report.error(record_location, "multiple same-event origins require merged_external_origins review state")
        if not revisions:
            report.error(record_location, "status beyond research_lead requires append-only revision history")

    if status in {"source_reviewed", "interpretive_draft", "editor_reviewed"}:
        if counting.get("count_disposition") != "not_counted_unpublished":
            report.error(record_location, "unpublished reviewed records must remain outside public totals")
        if provenance.get("publication_authorized") is not False:
            report.error(record_location, "unpublished reviewed records cannot be publication-authorized")
    elif status == "published":
        if counting.get("count_disposition") not in {"crosswalk_only_no_new_count", "canonical_new_record_count_once"}:
            report.error(record_location, "published record needs an explicit once-only count disposition")
        if not counting.get("canonical_the_record_entry_id"):
            report.error(record_location, "published record requires canonical_the_record_entry_id")
        if provenance.get("publication_authorized") is not True:
            report.error(record_location, "published record requires publication authorization")
    elif status == "superseded":
        if counting.get("count_disposition") != "not_counted_superseded":
            report.error(record_location, "superseded record must be removed from current totals")
        if provenance.get("publication_authorized") is not False:
            report.error(record_location, "superseded record cannot remain publication-authorized")

    crosslinks = record.get("crosslinks")
    if not isinstance(crosslinks, list):
        report.error(record_location, "crosslinks must be an array")
        crosslinks = []
    seen_links: set[tuple[str, str]] = set()
    lifecycle_link_targets: dict[str, str] = {}
    for link_index, link in enumerate(crosslinks):
        link_location = f"{record_location}.crosslinks[{link_index}]"
        if not isinstance(link, dict):
            report.error(link_location, "must be an object")
            continue
        target = link.get("target_record_id")
        relationship = link.get("relationship")
        if target == record_id:
            report.error(link_location, "record cannot crosslink to itself")
        pair = (str(target), str(relationship))
        if pair in seen_links:
            report.error(link_location, "duplicate crosslink")
        seen_links.add(pair)
        if relationship in LIFECYCLE_RELATIONSHIPS:
            target_key = str(target)
            previous_relationship = lifecycle_link_targets.get(target_key)
            if previous_relationship is not None and previous_relationship != relationship:
                report.error(
                    link_location,
                    f"lifecycle target {target_key!r} already uses relationship "
                    f"{previous_relationship!r}; one target cannot have conflicting lifecycle links",
                )
            lifecycle_link_targets[target_key] = str(relationship)

    return record


def validate_collection(
    records: Any,
    allowed_archives: set[str],
    canonical_entry_ids: set[str] | None = None,
    publishable_canonical_ids: set[str] | None = None,
) -> Report:
    report = Report()
    if not isinstance(records, list):
        report.error("$", "federated_records.json must contain an array")
        return report

    valid_records: list[dict[str, Any]] = []
    for index, raw in enumerate(records):
        record = validate_record_shape(raw, index, allowed_archives, report)
        if record:
            valid_records.append(record)

    by_id: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_origin: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_dedupe: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_family: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_canonical_target: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in valid_records:
        by_id[str(record.get("record_id"))].append(record)
        for origin in record.get("origins") or []:
            if isinstance(origin, dict):
                by_origin[str(origin.get("origin_key"))].append(record)
        dedupe = record.get("deduplication") or {}
        by_dedupe[str(dedupe.get("dedupe_key"))].append(record)
        by_family[str(dedupe.get("event_family_key"))].append(record)

        canonical_id_value = (record.get("counting") or {}).get("canonical_the_record_entry_id")
        if canonical_id_value:
            canonical_id = str(canonical_id_value)
            by_canonical_target[canonical_id].append(record)
            if canonical_entry_ids is not None and canonical_id not in canonical_entry_ids:
                report.error(
                    str(record.get("record_id")),
                    f"canonical_the_record_entry_id {canonical_id!r} does not exist in current or legacy canonical data",
                )
            if (
                record.get("status") == "published"
                and publishable_canonical_ids is not None
                and canonical_id not in publishable_canonical_ids
            ):
                report.error(
                    str(record.get("record_id")),
                    f"published crosswalk target {canonical_id!r} has not completed The Record's current evidence and Maybe / Therefore standard",
                )

    for record_id, owners in by_id.items():
        if len(owners) > 1:
            report.error(record_id, f"record_id appears {len(owners)} times")

    def enforce_duplicate_groups(groups: dict[str, list[dict[str, Any]]], kind: str) -> None:
        for key, owners in groups.items():
            unique_ids = sorted({str(owner.get("record_id")) for owner in owners})
            if len(unique_ids) <= 1:
                continue
            non_leads = [owner for owner in owners if owner.get("status") != "research_lead"]
            message = f"duplicate {kind} {key!r} across records {unique_ids}"
            if non_leads:
                report.error("collection", message + "; merge origins or resolve before review/publication")
            else:
                report.warn("collection", message + "; research leads remain blocked from publication")

    enforce_duplicate_groups(by_origin, "origin archive+external ID")
    enforce_duplicate_groups(by_dedupe, "dedupe key")
    enforce_duplicate_groups(by_canonical_target, "canonical The Record target")

    id_map = {record_id: owners[0] for record_id, owners in by_id.items() if len(owners) == 1}

    # Do not trust editor-supplied actor/subject strings or hashes as the only
    # duplicate barrier. Derive additional collision signals from the evidence
    # and prose actually present in each record. A reviewed collision may remain
    # separate only when it is a reciprocal stage in the same event family.
    collision_features: dict[str, dict[str, Any]] = {}
    for record_id, record in id_map.items():
        collision_features[record_id] = {
            "urls": direct_evidence_urls(record),
            "formal": formal_identifiers(record),
            "title": normalize_component(str(record.get("title", ""))),
            "facts": normalized_claim_text(record),
            "interval": record_date_interval(record),
        }

    record_ids = sorted(id_map)
    for left_index, left_id in enumerate(record_ids):
        left = id_map[left_id]
        left_features = collision_features[left_id]
        for right_id in record_ids[left_index + 1 :]:
            right = id_map[right_id]
            right_features = collision_features[right_id]
            shared_urls = sorted(left_features["urls"] & right_features["urls"])
            shared_formal = sorted(left_features["formal"] & right_features["formal"])
            overlap = intervals_overlap(left_features["interval"], right_features["interval"])
            title_score = text_similarity(left_features["title"], right_features["title"])
            fact_score = text_similarity(left_features["facts"], right_features["facts"])
            signals: list[str] = []
            if shared_urls:
                sample = shared_urls[0]
                signals.append(
                    f"shared normalized direct evidence URL {sample!r}"
                    + (f" (+{len(shared_urls) - 1} more)" if len(shared_urls) > 1 else "")
                )
            if shared_formal:
                signals.append(f"shared declared or independently derived formal identifier(s) {shared_formal}")
            if overlap and left_features["title"] and left_features["title"] == right_features["title"]:
                signals.append("identical normalized title in overlapping date intervals")
            elif overlap and title_score >= 0.92:
                signals.append(f"near-identical title ({title_score:.3f}) in overlapping date intervals")
            if (
                overlap
                and len(left_features["facts"]) >= 40
                and len(right_features["facts"]) >= 40
                and left_features["facts"] == right_features["facts"]
            ):
                signals.append("identical normalized fact text in overlapping date intervals")
            elif (
                overlap
                and len(left_features["facts"]) >= 40
                and len(right_features["facts"]) >= 40
                and fact_score >= 0.92
            ):
                signals.append(f"near-identical fact text ({fact_score:.3f}) in overlapping date intervals")
            if overlap and title_score >= 0.78 and fact_score >= 0.78:
                signals.append(
                    f"combined title/fact similarity ({title_score:.3f}/{fact_score:.3f}) "
                    "in overlapping date intervals"
                )
            if not signals:
                continue

            left_family = str((left.get("deduplication") or {}).get("event_family_key"))
            right_family = str((right.get("deduplication") or {}).get("event_family_key"))
            valid_stage_exception = left_family == right_family and has_reciprocal_lifecycle_link(left, right)
            if valid_stage_exception:
                continue
            message = (
                f"dynamic collision across {left_id!r} and {right_id!r}: "
                + "; ".join(signals)
                + "; merge, supersede, or establish a reciprocal same-family lifecycle stage"
            )
            if left.get("status") == "research_lead" and right.get("status") == "research_lead":
                report.warn("collection", message + "; research leads remain blocked from publication")
            else:
                report.error("collection", message)

    lifecycle_graph: dict[str, set[str]] = {record_id: set() for record_id in id_map}
    for record in valid_records:
        record_id = str(record.get("record_id"))
        family = str((record.get("deduplication") or {}).get("event_family_key"))
        dedupe_key = str((record.get("deduplication") or {}).get("dedupe_key"))
        lifecycle = record.get("lifecycle") or {}
        previous_ids = [str(item) for item in lifecycle.get("previous_record_ids") or []]
        next_ids = [str(item) for item in lifecycle.get("next_record_ids") or []]
        current_interval = record_date_interval(record)
        for link in record.get("crosslinks") or []:
            if not isinstance(link, dict):
                continue
            target_id = str(link.get("target_record_id"))
            relation = link.get("relationship")
            target = id_map.get(target_id)
            if target is None:
                report.error(record_id, f"crosslink target {target_id!r} does not exist")
                continue
            target_dedupe = str((target.get("deduplication") or {}).get("dedupe_key"))
            target_family = str((target.get("deduplication") or {}).get("event_family_key"))
            if relation == "same_event_alias" and target_dedupe != dedupe_key:
                report.error(record_id, "same_event_alias must point to an identical dedupe_key research lead")
            if relation not in LIFECYCLE_RELATIONSHIPS:
                continue
            if target_family != family:
                report.error(record_id, f"{relation} must point within the same event_family_key")

            expected_reciprocal = RECIPROCAL_LIFECYCLE_RELATIONSHIP[str(relation)]
            reciprocal_relations = {
                str(target_link.get("relationship"))
                for target_link in target.get("crosslinks") or []
                if isinstance(target_link, dict)
                and str(target_link.get("target_record_id")) == record_id
            }
            if expected_reciprocal not in reciprocal_relations:
                report.error(
                    record_id,
                    f"{relation} crosslink to {target_id!r} is not reciprocated by "
                    f"{expected_reciprocal!r}",
                )

            if relation == "previous_stage" and target_id not in set(previous_ids):
                report.error(
                    record_id,
                    f"previous_stage crosslink to {target_id!r} must also appear in previous_record_ids",
                )
            elif relation == "next_stage" and target_id not in set(next_ids):
                report.error(
                    record_id,
                    f"next_stage crosslink to {target_id!r} must also appear in next_record_ids",
                )

            target_interval = record_date_interval(target)
            earlier: tuple[str, tuple[date, date] | None]
            later: tuple[str, tuple[date, date] | None]
            if relation in {"previous_stage", "supersedes"}:
                earlier = (target_id, target_interval)
                later = (record_id, current_interval)
                lifecycle_graph.setdefault(target_id, set()).add(record_id)
            elif relation in {"next_stage", "superseded_by"}:
                earlier = (record_id, current_interval)
                later = (target_id, target_interval)
                lifecycle_graph.setdefault(record_id, set()).add(target_id)
            else:
                earlier = ("", None)
                later = ("", None)
            if earlier[1] and later[1] and earlier[1][0] > later[1][1]:
                report.error(
                    record_id,
                    f"{relation} crosslink to {target_id!r} has reversed chronology: "
                    f"earlier record {earlier[0]!r} spans "
                    f"{earlier[1][0].isoformat()}..{earlier[1][1].isoformat()}, while later "
                    f"record {later[0]!r} spans {later[1][0].isoformat()}..{later[1][1].isoformat()}",
                )

        if len(previous_ids) != len(set(previous_ids)):
            report.error(record_id, "previous_record_ids contains a duplicate")
        if len(next_ids) != len(set(next_ids)):
            report.error(record_id, "next_record_ids contains a duplicate")
        if record_id in set(previous_ids) | set(next_ids):
            report.error(record_id, "lifecycle record cannot point to itself")
        for previous_id in previous_ids:
            previous = id_map.get(previous_id)
            if previous is None:
                report.error(record_id, f"previous lifecycle record {previous_id!r} does not exist")
                continue
            previous_family = str((previous.get("deduplication") or {}).get("event_family_key"))
            if previous_family != family:
                report.error(record_id, f"previous lifecycle record {previous_id!r} must stay within the same event_family_key")
            previous_interval = record_date_interval(previous)
            if previous_interval and current_interval and previous_interval[0] > current_interval[1]:
                report.error(
                    record_id,
                    f"previous lifecycle record {previous_id!r} has reversed chronology: "
                    f"{previous_interval[0].isoformat()}..{previous_interval[1].isoformat()} follows "
                    f"{current_interval[0].isoformat()}..{current_interval[1].isoformat()}",
                )
            if record_id not in set((previous.get("lifecycle") or {}).get("next_record_ids") or []):
                report.error(record_id, f"previous_record_ids link to {previous_id!r} is not reciprocal")
            lifecycle_graph.setdefault(previous_id, set()).add(record_id)
        for next_id in next_ids:
            next_record = id_map.get(next_id)
            if next_record is None:
                report.error(record_id, f"next lifecycle record {next_id!r} does not exist")
                continue
            next_family = str((next_record.get("deduplication") or {}).get("event_family_key"))
            if next_family != family:
                report.error(record_id, f"next lifecycle record {next_id!r} must stay within the same event_family_key")
            next_interval = record_date_interval(next_record)
            if current_interval and next_interval and current_interval[0] > next_interval[1]:
                report.error(
                    record_id,
                    f"next lifecycle record {next_id!r} has reversed chronology: "
                    f"{current_interval[0].isoformat()}..{current_interval[1].isoformat()} follows "
                    f"{next_interval[0].isoformat()}..{next_interval[1].isoformat()}",
                )
            if record_id not in set((next_record.get("lifecycle") or {}).get("previous_record_ids") or []):
                report.error(record_id, f"next_record_ids link to {next_id!r} is not reciprocal")
            lifecycle_graph.setdefault(record_id, set()).add(next_id)

    directed_cycle = find_directed_cycle(lifecycle_graph)
    if directed_cycle:
        report.error("collection", f"directed previous/next lifecycle cycle detected: {' -> '.join(directed_cycle)}")

    for family_key, family_records in by_family.items():
        unique_family = {str(record.get("record_id")): record for record in family_records}
        if len(unique_family) <= 1:
            continue
        family_ids = set(unique_family)
        graph: dict[str, set[str]] = {record_id: set() for record_id in family_ids}
        for record_id, record in unique_family.items():
            lifecycle = record.get("lifecycle") or {}
            for target in (lifecycle.get("previous_record_ids") or []) + (lifecycle.get("next_record_ids") or []):
                target = str(target)
                if target in family_ids:
                    graph[record_id].add(target)
                    graph[target].add(record_id)
            for link in record.get("crosslinks") or []:
                if isinstance(link, dict) and link.get("relationship") in LIFECYCLE_RELATIONSHIPS:
                    target = str(link.get("target_record_id"))
                    if target in family_ids:
                        graph[record_id].add(target)
                        graph[target].add(record_id)
        start = next(iter(family_ids))
        visited = {start}
        queue = deque([start])
        while queue:
            current = queue.popleft()
            for neighbor in graph[current] - visited:
                visited.add(neighbor)
                queue.append(neighbor)
        if visited != family_ids:
            message = (
                f"event family {family_key!r} has unlinked lifecycle stages; "
                f"connected={sorted(visited)}, missing={sorted(family_ids - visited)}"
            )
            if any(record.get("status") != "research_lead" for record in unique_family.values()):
                report.error("collection", message)
            else:
                report.warn("collection", message + "; leads cannot advance until linked")

    return report


def make_self_test_record(
    record_id: str,
    *,
    status: str = "research_lead",
    external_id: str = "example-1",
    event_date: str = "2026-08-25",
    stage: str = "announcement",
    actor: str = "Example Administration",
    subject: str = "example policy action used only by validator self test",
) -> dict[str, Any]:
    now = "2026-08-25T13:15:51Z"
    origin_key = f"record47:{external_id}"
    record: dict[str, Any] = {
        "record_id": record_id,
        "status": status,
        "title": "Validator self-test record",
        "event_date": event_date,
        "date_precision": "day",
        "deduplication": {
            "fingerprint_version": "federated-record-v1",
            "dedupe_key": "sha256:" + "0" * 64,
            "event_family_key": "sha256:" + "0" * 64,
            "fingerprint_basis": {
                "event_date": event_date,
                "primary_actor": actor,
                "normalized_subject": subject,
                "formal_identifiers": ["SELF-TEST-1"],
            },
            "origin_aliases": [origin_key],
            "duplicate_review": {
                "state": "unreviewed" if status == "research_lead" else "clear",
                "checked_at": None if status == "research_lead" else now,
                "reviewer": None if status == "research_lead" else "Self Test",
                "notes": "Synthetic validator fixture; never publish.",
            },
        },
        "origins": [
            {
                "archive_id": "record47",
                "external_id": external_id,
                "origin_key": origin_key,
                "external_url": f"https://record47.org/entry/{external_id}",
                "external_record_unit": "executive_conduct_entry",
                "unit_scope": "synthetic self test",
                "external_record_status": None,
                "origin_role": "discovery_lead",
                "retrieved_at": now,
                "payload_sha256": None,
                "content_use": "metadata_and_links_only",
                "attribution": "Synthetic self test",
            }
        ],
        "counting": {
            "upstream_record_unit": "executive_conduct_entry",
            "comparability_group": "structured_executive_conduct",
            "additive_across_archives": False,
            "count_disposition": "not_counted_research_lead" if status == "research_lead" else "not_counted_unpublished",
            "canonical_the_record_entry_id": None,
            "rule": "Preserve upstream units separately; count a published canonical event once in The Record, never once per contributing archive.",
        },
        "lifecycle": {
            "stage": stage,
            "stage_date": event_date,
            "previous_record_ids": [],
            "next_record_ids": [],
        },
        "crosslinks": [],
        "facts": {"claims": [], "scope_note": "Synthetic self test."},
        "sources": [],
        "significance": None,
        "goalpost_response": None,
        "maybe_therefore": None,
        "evidence": {
            "tier": "D_research_lead" if status == "research_lead" else "B_primary_or_two_independent",
            "confidence": "unresolved" if status == "research_lead" else "high",
            "evidence_state": "lead_only" if status == "research_lead" else "source_reviewed",
            "human_reviewed": status != "research_lead",
            "reviewer": None if status == "research_lead" else "Self Test",
            "reviewed_at": None if status == "research_lead" else now,
            "limitations": ["Synthetic fixture."],
        },
        "provenance": {
            "created_at": now,
            "created_by": "Self Test",
            "last_modified_at": now,
            "source_level_review_completed": status != "research_lead",
            "external_archive_assertions_are_not_fact_sources": True,
            "publication_authorized": False,
            "copyright_boundary": "Synthetic fixture contains no upstream prose.",
            "transformations": [],
        },
        "consequences": [],
        "revisions": [],
        "tags": ["self-test"],
        "institutions": ["Example Institution"],
    }
    family_key, dedupe_key = expected_fingerprint_keys(record)
    record["deduplication"]["event_family_key"] = family_key
    record["deduplication"]["dedupe_key"] = dedupe_key
    if status != "research_lead":
        claim_id = f"{record_id}-F1"
        record["facts"]["claims"] = [
            {
                "claim_id": claim_id,
                "text": "A synthetic action occurred for validator testing.",
                "claim_status": "documented",
                "source_refs": ["SELF-S1"],
            }
        ]
        record["sources"] = [
            {
                "source_id": "SELF-S1",
                "title": "Synthetic primary record",
                "publisher": "Self Test",
                "url": "https://example.com/self-test",
                "archived_url": None,
                "source_type": "primary_agency_record",
                "publication_date": event_date,
                "accessed_at": now,
                "supports_claim_ids": [claim_id],
                "source_independence_group": "self-test",
                "evidence_locator": "synthetic",
                "notes": "Never publish.",
            }
        ]
        record["significance"] = {
            "text": "The fixture tests that interpretation remains distinct from fact.",
            "basis_claim_ids": [claim_id],
            "analysis_not_fact": True,
        }
        record["goalpost_response"] = {
            "text": "No real-world response exists because this is synthetic.",
            "response_kind": "no_response_identified",
            "source_refs": [],
        }
        record["maybe_therefore"] = {
            "text": "Maybe the synthetic fixture satisfies every documented premise. Therefore the validator should accept its complete structure.",
            "epistemic_status": "conditional_inference",
            "basis_claim_ids": [claim_id],
            "assumptions": ["The semantic rules are implemented as documented."],
            "would_change_if": ["A required semantic rule fails."],
            "confidence": "high",
            "editorial_not_fact": True,
        }
        record["revisions"] = [
            {
                "revision_id": f"{record_id}-R1",
                "timestamp": now,
                "actor": "Self Test",
                "kind": "created",
                "summary": "Created synthetic validator fixture.",
            }
        ]
    return record


def refresh_self_test_fingerprints(record: dict[str, Any]) -> None:
    """Refresh deterministic keys after a synthetic fixture is deliberately changed."""

    family_key, dedupe_key = expected_fingerprint_keys(record)
    record["deduplication"]["event_family_key"] = family_key
    record["deduplication"]["dedupe_key"] = dedupe_key


def run_self_test(allowed_archives: set[str], canonical_entry_ids: set[str]) -> bool:
    failures: list[str] = []

    lead = make_self_test_record("FED-SELF-LEAD")
    report = validate_collection([lead], allowed_archives)
    if report.errors:
        failures.append(f"valid lead rejected: {report.errors}")

    reviewed = make_self_test_record("FED-SELF-REVIEW", status="source_reviewed")
    report = validate_collection([reviewed], allowed_archives)
    if report.errors:
        failures.append(f"valid reviewed record rejected: {report.errors}")

    ai_draft = make_self_test_record("FED-SELF-AI-DRAFT", status="interpretive_draft")
    ai_draft["evidence"]["human_reviewed"] = False
    ai_draft["evidence"]["reviewer"] = "Synthetic AI source-review pass"
    report = validate_collection([ai_draft], allowed_archives)
    if report.errors:
        failures.append(f"valid AI-reviewed interpretive draft rejected: {report.errors}")

    missing_mt = copy.deepcopy(reviewed)
    missing_mt["maybe_therefore"] = None
    report = validate_collection([missing_mt], allowed_archives)
    if not any("maybe_therefore" in error for error in report.errors):
        failures.append("missing maybe_therefore was not blocked")

    collapsed_mt = copy.deepcopy(reviewed)
    collapsed_mt["maybe_therefore"]["text"] = "Maybe therefore this collapsed synthetic inference should fail."
    report = validate_collection([collapsed_mt], allowed_archives)
    if not any("collapse the clauses" in error for error in report.errors):
        failures.append("collapsed 'Maybe therefore' phrasing was not blocked")

    duplicate = copy.deepcopy(reviewed)
    duplicate["record_id"] = "FED-SELF-DUPLICATE"
    duplicate["facts"]["claims"][0]["claim_id"] = "FED-SELF-DUPLICATE-F1"
    duplicate["facts"]["claims"][0]["source_refs"] = ["SELF-S1"]
    duplicate["sources"][0]["supports_claim_ids"] = ["FED-SELF-DUPLICATE-F1"]
    duplicate["significance"]["basis_claim_ids"] = ["FED-SELF-DUPLICATE-F1"]
    duplicate["maybe_therefore"]["basis_claim_ids"] = ["FED-SELF-DUPLICATE-F1"]
    report = validate_collection([reviewed, duplicate], allowed_archives)
    if not any("duplicate origin" in error or "duplicate dedupe" in error for error in report.errors):
        failures.append("reviewed duplicate origin/dedupe key was not blocked")

    # Different editor-supplied actor, subject, formal identifier, origin, title,
    # and claim strings must not conceal reuse of the same underlying evidence.
    evidence_variant = make_self_test_record(
        "FED-SELF-EVIDENCE-COLLISION",
        status="source_reviewed",
        external_id="different-editor-key",
        actor="Different Actor Label",
        subject="different subject words selected by an editor",
    )
    evidence_variant["title"] = "Distinct title selected to evade a title collision"
    evidence_variant["facts"]["claims"][0]["text"] = "A differently worded synthetic claim exists."
    evidence_variant["deduplication"]["fingerprint_basis"]["formal_identifiers"] = ["OTHER-999"]
    refresh_self_test_fingerprints(evidence_variant)
    report = validate_collection([reviewed, evidence_variant], allowed_archives)
    if not any("shared normalized direct evidence URL" in error for error in report.errors):
        failures.append("different editor keys evaded a shared direct-evidence URL collision")

    prose_variant = make_self_test_record(
        "FED-SELF-PROSE-COLLISION",
        status="source_reviewed",
        external_id="different-prose-origin",
        actor="Another Actor Label",
        subject="another independently keyed subject",
    )
    prose_variant["deduplication"]["fingerprint_basis"]["formal_identifiers"] = ["OTHER-998"]
    prose_variant["sources"][0]["url"] = "https://example.com/different-self-test-source"
    refresh_self_test_fingerprints(prose_variant)
    report = validate_collection([reviewed, prose_variant], allowed_archives)
    if not any("normalized title" in error or "title/fact similarity" in error for error in report.errors):
        failures.append("overlapping-date title/fact similarity collision was not blocked")

    # This pair used to pass because every editor-controlled fingerprint field,
    # direct URL, title, and claim differs. The shared Executive Order is derived
    # independently from the actual prose and source metadata.
    eo_long = make_self_test_record(
        "FED-SELF-EO-LONG",
        status="source_reviewed",
        external_id="eo-long-form",
        actor="First Editor Actor",
        subject="first unrelated editor subject",
    )
    eo_long["title"] = "Synthetic safeguards announced under Executive Order No. 14110"
    eo_long["facts"]["claims"][0]["text"] = "A first synthetic safeguard was announced."
    eo_long["sources"][0]["source_id"] = "ALPHA-S1"
    eo_long["facts"]["claims"][0]["source_refs"] = ["ALPHA-S1"]
    eo_long["sources"][0]["supports_claim_ids"] = [eo_long["facts"]["claims"][0]["claim_id"]]
    eo_long["sources"][0]["title"] = "Executive Order 14110 source artifact"
    eo_long["sources"][0]["url"] = "https://example.com/alpha-artifact"
    eo_long["deduplication"]["fingerprint_basis"]["formal_identifiers"] = ["ALPHA-ACTION"]
    refresh_self_test_fingerprints(eo_long)

    eo_short = make_self_test_record(
        "FED-SELF-EO-SHORT",
        status="source_reviewed",
        external_id="eo-short-form",
        actor="Second Editor Actor",
        subject="second unrelated editor subject",
    )
    eo_short["title"] = "A differently described synthetic agency implementation"
    eo_short["facts"]["claims"][0]["text"] = "An agency later cited E.O. 14110 in a distinct sentence."
    eo_short["sources"][0]["source_id"] = "BETA-S1"
    eo_short["facts"]["claims"][0]["source_refs"] = ["BETA-S1"]
    eo_short["sources"][0]["supports_claim_ids"] = [eo_short["facts"]["claims"][0]["claim_id"]]
    eo_short["sources"][0]["title"] = "Differently labeled agency artifact"
    eo_short["sources"][0]["url"] = "https://example.com/beta-artifact"
    eo_short["deduplication"]["fingerprint_basis"]["formal_identifiers"] = ["BETA-ACTION"]
    refresh_self_test_fingerprints(eo_short)
    report = validate_collection([eo_long, eo_short], allowed_archives)
    if not any("eo:14110" in error and "independently derived" in error for error in report.errors):
        failures.append("EO/Executive Order variants evaded independently derived formal-ID collision")

    scotus_docket = copy.deepcopy(eo_long)
    scotus_docket["record_id"] = "FED-SELF-SCOTUS-DOCKET"
    scotus_docket["title"] = "Supreme Court docket No. 24-123 contains a synthetic filing"
    scotus_docket["facts"]["claims"][0]["claim_id"] = "FED-SELF-SCOTUS-DOCKET-F1"
    scotus_docket["facts"]["claims"][0]["source_refs"] = ["DOCKET-S1"]
    scotus_docket["sources"][0]["source_id"] = "DOCKET-S1"
    scotus_docket["sources"][0]["title"] = "First synthetic court artifact"
    scotus_docket["sources"][0]["publisher"] = "Independent Publisher"
    scotus_docket["sources"][0]["url"] = "https://example.com/court-alpha"
    scotus_docket["sources"][0]["supports_claim_ids"] = ["FED-SELF-SCOTUS-DOCKET-F1"]
    scotus_docket["significance"]["basis_claim_ids"] = ["FED-SELF-SCOTUS-DOCKET-F1"]
    scotus_docket["maybe_therefore"]["basis_claim_ids"] = ["FED-SELF-SCOTUS-DOCKET-F1"]
    scotus_docket["deduplication"]["fingerprint_basis"]["formal_identifiers"] = ["COURT-ALPHA"]
    refresh_self_test_fingerprints(scotus_docket)

    scotus_source = copy.deepcopy(eo_short)
    scotus_source["record_id"] = "FED-SELF-SCOTUS-SOURCE"
    scotus_source["facts"]["claims"][0]["claim_id"] = "FED-SELF-SCOTUS-SOURCE-F1"
    scotus_source["facts"]["claims"][0]["text"] = "A wholly different synthetic dispute was filed."
    scotus_source["facts"]["claims"][0]["source_refs"] = ["COURT-S1"]
    scotus_source["sources"][0]["source_id"] = "COURT-S1"
    scotus_source["sources"][0]["title"] = "Case No. 24\u20130123"
    scotus_source["sources"][0]["publisher"] = "Supreme Court of the United States"
    scotus_source["sources"][0]["url"] = "https://example.com/court-beta"
    scotus_source["sources"][0]["supports_claim_ids"] = ["FED-SELF-SCOTUS-SOURCE-F1"]
    scotus_source["significance"]["basis_claim_ids"] = ["FED-SELF-SCOTUS-SOURCE-F1"]
    scotus_source["maybe_therefore"]["basis_claim_ids"] = ["FED-SELF-SCOTUS-SOURCE-F1"]
    scotus_source["deduplication"]["fingerprint_basis"]["formal_identifiers"] = ["COURT-BETA"]
    refresh_self_test_fingerprints(scotus_source)
    report = validate_collection([scotus_docket, scotus_source], allowed_archives)
    if not any("scotus:24-123" in error and "independently derived" in error for error in report.errors):
        failures.append("SCOTUS docket punctuation/zero variants evaded derived formal-ID collision")

    if canonical_entry_ids:
        shared_target = sorted(canonical_entry_ids)[0]
        first_crosswalk = copy.deepcopy(reviewed)
        first_crosswalk["counting"]["canonical_the_record_entry_id"] = shared_target
        second_crosswalk = make_self_test_record(
            "FED-SELF-CANONICAL-DUPLICATE",
            status="source_reviewed",
            external_id="different-upstream-item",
            actor="Different Archive Label",
            subject="differently worded description of the same canonical event",
        )
        second_crosswalk["counting"]["canonical_the_record_entry_id"] = shared_target
        report = validate_collection(
            [first_crosswalk, second_crosswalk], allowed_archives, canonical_entry_ids
        )
        if not any("duplicate canonical The Record target" in error for error in report.errors):
            failures.append("duplicate canonical target across differently fingerprinted records was not blocked")

    lead_duplicate = copy.deepcopy(lead)
    lead_duplicate["record_id"] = "FED-SELF-LEAD2"
    report = validate_collection([lead, lead_duplicate], allowed_archives)
    if report.errors or not report.warnings:
        failures.append("duplicate research leads should warn without advancing")

    stage_one = make_self_test_record(
        "FED-SELF-STAGE1",
        status="source_reviewed",
        external_id="stage-1",
        event_date="2026-08-24",
        stage="announcement",
    )
    stage_two = make_self_test_record(
        "FED-SELF-STAGE2",
        status="source_reviewed",
        external_id="stage-2",
        event_date="2026-08-25",
        stage="implementation",
    )
    stage_one["lifecycle"]["next_record_ids"] = [stage_two["record_id"]]
    stage_two["lifecycle"]["previous_record_ids"] = [stage_one["record_id"]]
    stage_one["crosslinks"] = [
        {"target_record_id": stage_two["record_id"], "relationship": "next_stage", "note": "Synthetic link."}
    ]
    stage_two["crosslinks"] = [
        {"target_record_id": stage_one["record_id"], "relationship": "previous_stage", "note": "Synthetic link."}
    ]
    report = validate_collection([stage_one, stage_two], allowed_archives)
    if report.errors:
        failures.append(f"valid linked lifecycle rejected: {report.errors}")

    same_action_one = copy.deepcopy(stage_one)
    same_action_two = copy.deepcopy(stage_two)
    same_action_one["crosslinks"] = [
        {
            "target_record_id": same_action_two["record_id"],
            "relationship": "same_action_lifecycle",
            "note": "Synthetic symmetric link.",
        }
    ]
    same_action_two["crosslinks"] = [
        {
            "target_record_id": same_action_one["record_id"],
            "relationship": "same_action_lifecycle",
            "note": "Synthetic symmetric link.",
        }
    ]
    report = validate_collection([same_action_one, same_action_two], allowed_archives)
    if report.errors:
        failures.append(f"valid reciprocal same_action_lifecycle link rejected: {report.errors}")

    nonreciprocal_crosslink = copy.deepcopy(stage_two)
    nonreciprocal_crosslink["crosslinks"] = []
    report = validate_collection([stage_one, nonreciprocal_crosslink], allowed_archives)
    if not any("not reciprocated" in error for error in report.errors):
        failures.append("nonreciprocal next_stage crosslink was not blocked")

    ambiguous_crosslink = copy.deepcopy(stage_one)
    ambiguous_crosslink["crosslinks"].append(
        {
            "target_record_id": stage_two["record_id"],
            "relationship": "same_action_lifecycle",
            "note": "Synthetic conflicting link to the same target.",
        }
    )
    report = validate_collection([ambiguous_crosslink, stage_two], allowed_archives)
    if not any("conflicting lifecycle links" in error for error in report.errors):
        failures.append("multiple lifecycle relationships to one target were not blocked")

    wrong_direction_one = copy.deepcopy(stage_one)
    wrong_direction_two = copy.deepcopy(stage_two)
    wrong_direction_one["crosslinks"] = [
        {
            "target_record_id": wrong_direction_two["record_id"],
            "relationship": "previous_stage",
            "note": "Deliberately reversed synthetic direction.",
        }
    ]
    wrong_direction_two["crosslinks"] = [
        {
            "target_record_id": wrong_direction_one["record_id"],
            "relationship": "next_stage",
            "note": "Deliberately reversed synthetic direction.",
        }
    ]
    report = validate_collection([wrong_direction_one, wrong_direction_two], allowed_archives)
    if not any(
        "must also appear" in error or "reversed chronology" in error
        for error in report.errors
    ):
        failures.append("wrong-direction previous_stage/next_stage crosslinks were not blocked")

    # Lifecycle arrays alone form a valid earlier-to-later edge. These formerly
    # passing supersession crosslinks point the opposite way, creating a cycle
    # that is visible only when directed crosslinks participate in cycle checks.
    crosslink_cycle_one = copy.deepcopy(stage_one)
    crosslink_cycle_two = copy.deepcopy(stage_two)
    crosslink_cycle_one["crosslinks"] = [
        {
            "target_record_id": crosslink_cycle_two["record_id"],
            "relationship": "supersedes",
            "note": "Deliberately reversed synthetic supersession.",
        }
    ]
    crosslink_cycle_two["crosslinks"] = [
        {
            "target_record_id": crosslink_cycle_one["record_id"],
            "relationship": "superseded_by",
            "note": "Reciprocal but directionally wrong synthetic supersession.",
        }
    ]
    report = validate_collection([crosslink_cycle_one, crosslink_cycle_two], allowed_archives)
    if not any("lifecycle cycle detected" in error for error in report.errors):
        failures.append("directed supersession crosslink cycle was not blocked")

    cross_family_stage = copy.deepcopy(stage_two)
    cross_family_stage["deduplication"]["fingerprint_basis"]["primary_actor"] = "Different Lifecycle Actor"
    cross_family_stage["deduplication"]["fingerprint_basis"]["normalized_subject"] = (
        "different lifecycle family selected by an editor"
    )
    refresh_self_test_fingerprints(cross_family_stage)
    report = validate_collection([stage_one, cross_family_stage], allowed_archives)
    if not any("must stay within the same event_family_key" in error for error in report.errors):
        failures.append("cross-family previous/next lifecycle link was not blocked")

    reverse_previous = make_self_test_record(
        "FED-SELF-REVERSE-PREVIOUS",
        status="source_reviewed",
        external_id="reverse-previous",
        event_date="2026-08-25",
        stage="announcement",
    )
    reverse_next = make_self_test_record(
        "FED-SELF-REVERSE-NEXT",
        status="source_reviewed",
        external_id="reverse-next",
        event_date="2026-08-24",
        stage="implementation",
    )
    reverse_previous["lifecycle"]["next_record_ids"] = [reverse_next["record_id"]]
    reverse_next["lifecycle"]["previous_record_ids"] = [reverse_previous["record_id"]]
    report = validate_collection([reverse_previous, reverse_next], allowed_archives)
    if not any("reversed chronology" in error for error in report.errors):
        failures.append("reverse-chronology lifecycle link was not blocked")

    cycle_one = make_self_test_record(
        "FED-SELF-CYCLE1",
        status="source_reviewed",
        external_id="cycle-1",
        stage="announcement",
    )
    cycle_two = make_self_test_record(
        "FED-SELF-CYCLE2",
        status="source_reviewed",
        external_id="cycle-2",
        stage="implementation",
    )
    cycle_three = make_self_test_record(
        "FED-SELF-CYCLE3",
        status="source_reviewed",
        external_id="cycle-3",
        stage="enforcement",
    )
    cycle_one["lifecycle"].update(
        previous_record_ids=[cycle_three["record_id"]], next_record_ids=[cycle_two["record_id"]]
    )
    cycle_two["lifecycle"].update(
        previous_record_ids=[cycle_one["record_id"]], next_record_ids=[cycle_three["record_id"]]
    )
    cycle_three["lifecycle"].update(
        previous_record_ids=[cycle_two["record_id"]], next_record_ids=[cycle_one["record_id"]]
    )
    report = validate_collection([cycle_one, cycle_two, cycle_three], allowed_archives)
    if not any("lifecycle cycle detected" in error for error in report.errors):
        failures.append("directed previous/next lifecycle cycle was not blocked")

    broken_stage = copy.deepcopy(stage_two)
    broken_stage["lifecycle"]["previous_record_ids"] = []
    broken_stage["crosslinks"] = []
    report = validate_collection([stage_one, broken_stage], allowed_archives)
    if not report.errors:
        failures.append("unlinked lifecycle stage was not blocked")

    if canonical_entry_ids:
        published = make_self_test_record("FED-SELF-PUBLISHED", status="source_reviewed")
        published["status"] = "published"
        published["counting"]["count_disposition"] = "crosswalk_only_no_new_count"
        published["counting"]["canonical_the_record_entry_id"] = sorted(canonical_entry_ids)[0]
        published["provenance"]["publication_authorized"] = True
        report = validate_collection(
            [published], allowed_archives, canonical_entry_ids, canonical_entry_ids
        )
        if report.errors:
            failures.append(f"valid published canonical crosswalk rejected: {report.errors}")

        unreviewed_target = validate_collection(
            [published], allowed_archives, canonical_entry_ids, set()
        )
        if not unreviewed_target.errors:
            failures.append("published record targeting an unreviewed canonical entry was not blocked")

        unreviewed_publication = copy.deepcopy(published)
        unreviewed_publication["evidence"]["human_reviewed"] = False
        report = validate_collection([unreviewed_publication], allowed_archives, canonical_entry_ids)
        if not any("requires dated human evidence review" in error for error in report.errors):
            failures.append("published record without human review was not blocked")

        missing_canonical = copy.deepcopy(reviewed)
        missing_canonical["counting"]["canonical_the_record_entry_id"] = "LEG-999999"
        report = validate_collection([missing_canonical], allowed_archives, canonical_entry_ids)
        if not any("does not exist" in error for error in report.errors):
            failures.append("nonexistent canonical crosswalk target was not blocked")

    if failures:
        for failure in failures:
            print(f"SELF-TEST FAIL: {failure}", file=sys.stderr)
        return False
    print(
        "SELF-TEST PASS: interpretation, AI-draft/human-publication, independently derived "
        "EO/SCOTUS identifiers, origin, canonical-ID, reciprocal/directed crosslinks, family, "
        "chronology, and lifecycle-cycle gates enforced"
    )
    return True


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA)
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--current-data", type=Path, default=DEFAULT_CURRENT_DATA)
    parser.add_argument("--legacy-data", type=Path, default=DEFAULT_LEGACY_DATA)
    parser.add_argument("--self-test", action="store_true", help="Run synthetic positive and negative fixtures")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        records = load_json(args.data)
        schema = load_json(args.schema)
        registry = load_json(args.registry)
        current_entries = load_json(args.current_data)
        legacy_entries = load_json(args.legacy_data)
    except ValueError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1

    if not isinstance(schema, dict) or schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
        print("FAIL: federated_record.schema.json must declare JSON Schema Draft 2020-12", file=sys.stderr)
        return 1
    archives = registry.get("archives") if isinstance(registry, dict) else None
    if not isinstance(archives, list):
        print("FAIL: archive_registry.json has no archives array", file=sys.stderr)
        return 1
    allowed_archives = {
        str(item.get("archive_id"))
        for item in archives
        if isinstance(item, dict) and item.get("archive_id")
    }

    if not isinstance(current_entries, list) or not isinstance(legacy_entries, list):
        print("FAIL: current and legacy canonical data must each contain an array", file=sys.stderr)
        return 1
    canonical_entry_ids = {
        str(item.get("id"))
        for item in current_entries
        if isinstance(item, dict) and item.get("id")
    }
    canonical_entry_ids.update(
        str(item.get("legacy_id"))
        for item in legacy_entries
        if isinstance(item, dict) and item.get("legacy_id")
    )
    if not canonical_entry_ids:
        print("FAIL: no canonical The Record entry IDs were found", file=sys.stderr)
        return 1

    publishable_canonical_ids = {
        str(item.get("id"))
        for item in current_entries
        if isinstance(item, dict)
        and item.get("id")
        and item.get("maybe_therefore")
        and item.get("facts")
        and item.get("significance")
        and item.get("goalpost")
    }
    publishable_canonical_ids.update(
        str(item.get("legacy_id"))
        for item in legacy_entries
        if isinstance(item, dict)
        and item.get("legacy_id")
        and item.get("review_status") in {"current-standard-reviewed", "corrected"}
        and item.get("mt")
    )

    report = validate_collection(
        records,
        allowed_archives,
        canonical_entry_ids,
        publishable_canonical_ids,
    )
    schema_state = validate_schema_with_optional_library(records, schema, report)
    for warning in report.warnings:
        print(f"WARNING: {warning}")
    if report.errors:
        for error in report.errors:
            print(f"ERROR: {error}", file=sys.stderr)
        print(
            f"FAIL: {len(report.errors)} error(s), {len(report.warnings)} warning(s); "
            f"JSON Schema validation {schema_state}",
            file=sys.stderr,
        )
        return 1

    record_count = len(records) if isinstance(records, list) else 0
    print(
        f"PASS: {record_count} federated record(s), {len(report.warnings)} warning(s); "
        f"JSON Schema validation {schema_state}"
    )
    if record_count == 0:
        print("INFO: no external record has crossed the source, interpretation, license, and publication gates")
    if args.self_test and not run_self_test(allowed_archives, canonical_entry_ids):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
