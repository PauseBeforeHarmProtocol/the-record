from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter, defaultdict
from datetime import date, timedelta
from pathlib import Path
from urllib.parse import parse_qs, urlparse


ROOT = Path(__file__).resolve().parents[1]
LEGACY_PATH = ROOT / "data/legacy_entries.json"
CURRENT_PATH = ROOT / "data/current_entries.json"
LEDGER_PATH = ROOT / "data/source_ledger.json"
RELEASE_PATH = ROOT / "data/release.json"
OUTPUT_PATH = ROOT / "data/archive_metrics.json"
FEDERATED_PATH = ROOT / "data/federated_records.json"
REVISION_PATH = ROOT / "data/legacy_revisions.json"
REGISTRY_PATH = ROOT / "data/archive_registry.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_url(source: object) -> str:
    if isinstance(source, str):
        return source.strip()
    if isinstance(source, dict):
        return str(source.get("url") or "").strip()
    return ""


def source_domain(url: str) -> str:
    hostname = (urlparse(url).hostname or "").lower()
    return hostname.removeprefix("www.")


def low_specificity_reason(url: str) -> str | None:
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower().removeprefix("www.")
    path = parsed.path.rstrip("/").lower()
    query = parse_qs(parsed.query.lower())
    if not host:
        return "missing-url"
    if not path:
        return "publisher-homepage"
    search_hosts_and_paths = (
        ("apnews.com", "/search"),
        ("reuters.com", "/site-search"),
        ("congress.gov", "/search"),
        ("google.com", "/search"),
        ("courtlistener.com", "/search"),
    )
    if any(host.endswith(search_host) and path.startswith(search_path) for search_host, search_path in search_hosts_and_paths):
        return "search-results"
    if host.endswith("fec.gov") and path.startswith("/data/receipts"):
        return "query-results"
    if any(key in query for key in ("q", "query", "search")) and path.endswith("search"):
        return "search-results"
    return None


def normalized_heading(entry: dict) -> str:
    text = str(entry.get("text") or "")
    heading = re.split(r"(?<=[.!?])\s", text, maxsplit=1)[0]
    return re.sub(r"\W+", " ", heading.lower()).strip()


def pct(value: int, total: int) -> float:
    return round((value / total * 100) if total else 0.0, 1)


def human_date(value: date) -> str:
    return f"{value.strftime('%B')} {value.day}, {value.year}"


def legacy_metrics(entries: list[dict]) -> dict:
    source_counts: list[int] = []
    source_domains_per_entry: list[set[str]] = []
    all_urls: list[str] = []
    low_reason_counts: Counter[str] = Counter()
    entries_with_low = 0
    entries_low_only = 0
    single_low_only = 0
    repeated_within_entry = 0
    no_url_sources = 0

    for entry in entries:
        urls = [source_url(source) for source in (entry.get("src") or [])]
        source_counts.append(len(urls))
        all_urls.extend(url for url in urls if url)
        domains = {source_domain(url) for url in urls if source_domain(url)}
        source_domains_per_entry.append(domains)
        reasons = [low_specificity_reason(url) for url in urls]
        reasons = [reason for reason in reasons if reason]
        low_reason_counts.update(reasons)
        if reasons:
            entries_with_low += 1
        if urls and len(reasons) == len(urls):
            entries_low_only += 1
            if len(urls) == 1:
                single_low_only += 1
        if len([url for url in urls if url]) != len(set(url for url in urls if url)):
            repeated_within_entry += 1
        no_url_sources += sum(not url for url in urls)

    exact_text: dict[str, list[str]] = defaultdict(list)
    date_heading: dict[tuple[str, str], list[str]] = defaultdict(list)
    heading_any_date: dict[str, list[str]] = defaultdict(list)
    for entry in entries:
        legacy_id = entry["legacy_id"]
        exact_text[str(entry.get("text") or "").strip()].append(legacy_id)
        heading = normalized_heading(entry)
        date_heading[(str(entry.get("sort") or ""), heading)].append(legacy_id)
        heading_any_date[heading].append(legacy_id)

    exact_groups = [ids for text, ids in exact_text.items() if text and len(ids) > 1]
    heading_groups = [ids for (_, heading), ids in date_heading.items() if heading and len(ids) > 1]
    repeated_heading_groups = [
        ids for heading, ids in heading_any_date.items() if heading and len(ids) > 1
    ]
    review_states = Counter(str(entry.get("review_status") or "missing") for entry in entries)
    era_counts = Counter(str(entry.get("era") or "unknown") for entry in entries)
    date_precision = Counter(str(entry.get("dprec") or "missing") for entry in entries)
    entry_types = Counter(str(entry.get("etype") or "missing") for entry in entries)
    maybe_therefore_present = sum(bool(str(entry.get("mt") or "").strip()) for entry in entries)
    domain_counts = Counter(source_domain(url) for url in all_urls if source_domain(url))
    url_counts = Counter(all_urls)
    min_date = min(str(entry.get("sort") or "") for entry in entries)
    max_date = max(str(entry.get("sort") or "") for entry in entries)

    total = len(entries)
    single_source = sum(count == 1 for count in source_counts)
    single_domain = sum(len(domains) == 1 for domains in source_domains_per_entry)
    return {
        "entries": total,
        "coverage": {"first_sort_date": min_date, "last_sort_date": max_date},
        "entry_types": dict(sorted(entry_types.items())),
        "date_precision": dict(sorted(date_precision.items())),
        "eras": dict(sorted(era_counts.items())),
        "review_states": dict(sorted(review_states.items())),
        "sources": {
            "references": len(all_urls) + no_url_sources,
            "references_with_url": len(all_urls),
            "unique_urls": len(set(all_urls)),
            "unique_domains": len(domain_counts),
            "entries_with_one_source": single_source,
            "entries_with_one_source_percent": pct(single_source, total),
            "entries_with_one_domain": single_domain,
            "entries_with_one_domain_percent": pct(single_domain, total),
            "entries_with_low_specificity_source": entries_with_low,
            "entries_with_low_specificity_source_percent": pct(entries_with_low, total),
            "entries_relying_only_on_low_specificity_sources": entries_low_only,
            "entries_relying_only_on_low_specificity_sources_percent": pct(entries_low_only, total),
            "single_source_low_specificity_entries": single_low_only,
            "single_source_low_specificity_entries_percent": pct(single_low_only, total),
            "entries_repeating_a_url_internally": repeated_within_entry,
            "low_specificity_reasons": dict(sorted(low_reason_counts.items())),
            "most_used_domains": [
                {"domain": domain, "references": count}
                for domain, count in domain_counts.most_common(15)
            ],
            "urls_reused_by_ten_or_more_entries": sum(count >= 10 for count in url_counts.values()),
        },
        "duplicate_candidates": {
            "exact_text_groups": len(exact_groups),
            "exact_text_extra_rows": sum(len(ids) - 1 for ids in exact_groups),
            "exact_text_group_ids": exact_groups,
            "same_date_heading_groups": len(heading_groups),
            "same_date_heading_extra_rows": sum(len(ids) - 1 for ids in heading_groups),
            "same_date_heading_group_ids": heading_groups,
            "repeated_heading_any_date_groups": len(repeated_heading_groups),
            "repeated_heading_any_date_extra_rows": sum(
                len(ids) - 1 for ids in repeated_heading_groups
            ),
            "repeated_heading_any_date_group_ids": repeated_heading_groups,
        },
        "interpretive_layers": {
            "maybe_therefore_present": maybe_therefore_present,
            "maybe_therefore_present_percent": pct(maybe_therefore_present, total),
            "maybe_therefore_missing": total - maybe_therefore_present,
            "maybe_therefore_missing_percent": pct(total - maybe_therefore_present, total),
        },
    }


def current_metrics(entries: list[dict], ledger: dict) -> dict:
    used_source_ids = [source_id for entry in entries for source_id in entry.get("sources", [])]
    national = [entry for entry in entries if entry.get("scope") == "national"]
    in6 = [entry for entry in entries if entry.get("scope") == "in6"]
    national_source_ids = [
        source_id for entry in national for source_id in entry.get("sources", [])
    ]
    publisher_counts = Counter(
        str(ledger[source_id].get("publisher") or "Unknown")
        for source_id in used_source_ids
        if source_id in ledger
    )
    single_source = sum(len(entry.get("sources", [])) == 1 for entry in entries)
    national_single_source = sum(len(entry.get("sources", [])) == 1 for entry in national)
    maybe_therefore_present = sum(bool(str(entry.get("maybe_therefore") or "").strip()) for entry in entries)
    review_states = Counter(str(entry.get("review_status") or "missing") for entry in entries)
    current_standard_reviewed = sum(
        entry.get("review_status") in {"current-standard-reviewed", "corrected"}
        for entry in entries
    )
    return {
        "entries": len(entries),
        "national_entries": len(national),
        "in6_entries": len(in6),
        "source_references": len(used_source_ids),
        "national_source_references": len(national_source_ids),
        "source_ledger_rows": len(ledger),
        "used_source_ledger_rows": len(set(used_source_ids)),
        "unused_source_ledger_rows": len(set(ledger) - set(used_source_ids)),
        "entries_with_one_source": single_source,
        "entries_with_one_source_percent": pct(single_source, len(entries)),
        "national_entries_with_one_source": national_single_source,
        "national_entries_with_one_source_percent": pct(national_single_source, len(national)),
        "maybe_therefore_present": maybe_therefore_present,
        "maybe_therefore_missing": len(entries) - maybe_therefore_present,
        "review_states": dict(sorted(review_states.items())),
        "current_standard_reviewed": current_standard_reviewed,
        "current_standard_pending": len(entries) - current_standard_reviewed,
        "most_used_publishers": [
            {"publisher": publisher, "references": count}
            for publisher, count in publisher_counts.most_common(10)
        ],
    }


def build_metrics() -> dict:
    legacy_rows = json.loads(LEGACY_PATH.read_text(encoding="utf-8"))
    active_legacy = [
        entry for entry in legacy_rows if entry.get("review_status") != "superseded"
    ]
    superseded_legacy = [
        entry for entry in legacy_rows if entry.get("review_status") == "superseded"
    ]
    current = json.loads(CURRENT_PATH.read_text(encoding="utf-8"))
    ledger = json.loads(LEDGER_PATH.read_text(encoding="utf-8"))
    release = json.loads(RELEASE_PATH.read_text(encoding="utf-8"))
    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    legacy_result = legacy_metrics(active_legacy)
    current_result = current_metrics(current, ledger)
    national_current = current_result["national_entries"]
    national_source_references = current_result["national_source_references"]
    legacy_urls = {
        source_url(source)
        for entry in active_legacy
        for source in (entry.get("src") or [])
        if source_url(source)
    }
    national_current_urls = {
        str(ledger[source_id].get("url") or "").strip()
        for entry in current
        if entry.get("scope") == "national"
        for source_id in entry.get("sources", [])
        if source_id in ledger and str(ledger[source_id].get("url") or "").strip()
    }
    legacy_last = date.fromisoformat(legacy_result["coverage"]["last_sort_date"])
    bridge_first_text = min(
        entry["date"] for entry in current if entry.get("scope") == "national"
    )
    bridge_first = date.fromisoformat(bridge_first_text)
    gap_first = legacy_last + timedelta(days=1)
    gap_last = bridge_first - timedelta(days=1)
    gap_label = (
        f"{human_date(gap_first)}–{human_date(gap_last)}"
        if gap_first <= gap_last
        else "none"
    )
    federated = json.loads(FEDERATED_PATH.read_text(encoding="utf-8")) if FEDERATED_PATH.exists() else []
    revisions = json.loads(REVISION_PATH.read_text(encoding="utf-8")) if REVISION_PATH.exists() else []
    if not isinstance(federated, list):
        raise ValueError("data/federated_records.json must be an array")
    if not isinstance(revisions, list):
        raise ValueError("data/legacy_revisions.json must be an array")
    federated_states = Counter(str(record.get("status") or "missing") for record in federated)
    federation_modified = max(
        (
            str(record.get("provenance", {}).get("last_modified_at") or "")
            for record in federated
        ),
        default="",
    )
    registry_checked = str(registry.get("checked_at") or "")
    quality_inputs_updated_at = max(
        (value for value in (registry_checked, federation_modified) if value),
        default=release["checked_at"],
    )
    legacy_revisions_through = max(
        (str(revision.get("recorded_at") or "") for revision in revisions),
        default="",
    )
    return {
        "schema_version": 3,
        "editorial_checked_at": release["checked_at"],
        "quality_inputs_updated_at": quality_inputs_updated_at,
        "external_registry_checked_at": registry_checked,
        "federation_last_modified_at": federation_modified,
        "legacy_revisions_through": legacy_revisions_through,
        "release_version": release["version"],
        "canonical_files": {
            "legacy": "data/legacy_entries.json",
            "current": "data/current_entries.json",
            "source_ledger": "data/source_ledger.json",
            "federated": "data/federated_records.json",
            "legacy_revisions": "data/legacy_revisions.json",
            "archive_registry": "data/archive_registry.json",
        },
        "canonical_sha256": {
            "legacy": sha256(LEGACY_PATH),
            "current": sha256(CURRENT_PATH),
            "source_ledger": sha256(LEDGER_PATH),
            "federated": sha256(FEDERATED_PATH),
            "legacy_revisions": sha256(REVISION_PATH),
            "archive_registry": sha256(REGISTRY_PATH),
        },
        "totals": {
            "canonical_legacy_rows": len(legacy_rows),
            "canonical_legacy_entries": len(active_legacy),
            "active_legacy_entries": len(active_legacy),
            "superseded_legacy_tombstones": len(superseded_legacy),
            "bridged_national_entries": national_current,
            "full_archive_runtime_entries": len(active_legacy) + national_current,
            "current_layer_entries": len(current),
            "legacy_source_references": legacy_result["sources"]["references"],
            "current_source_references": current_result["source_references"],
            "full_archive_runtime_source_references": (
                legacy_result["sources"]["references"] + national_source_references
            ),
            "full_archive_runtime_unique_urls": len(legacy_urls | national_current_urls),
        },
        "coverage": {
            "legacy_last_date": legacy_result["coverage"]["last_sort_date"],
            "current_bridge_first_date": bridge_first_text,
            "uncovered_days_between_layers": max(0, (bridge_first - legacy_last).days - 1),
            "known_gap_label": gap_label,
            "known_gap_status": (
                "disclosed; backfill required" if gap_first <= gap_last else "no gap"
            ),
        },
        "legacy": legacy_result,
        "current": current_result,
        "federated": {
            "records": len(federated),
            "states": dict(sorted(federated_states.items())),
            "counting_rule": "Federated crosslinks are not added to The Record entry totals unless promoted as a distinct canonical event after deduplication and editorial review.",
        },
        "remediation": {
            "legacy_revision_records": len(revisions),
            "superseded_tombstones": [
                {
                    "legacy_id": entry["legacy_id"],
                    "superseded_by": entry["superseded_by"],
                    "reason": entry["superseded_reason"],
                }
                for entry in superseded_legacy
            ],
        },
        "definitions": {
            "source_reference": "One source object attached to one entry; repeated URLs count repeatedly.",
            "unique_url": "A distinct normalized-as-stored source URL; redirects are not yet collapsed.",
            "low_specificity": "A publisher homepage, search-results page, or query-results page rather than a direct supporting document.",
            "review_state": "Editorial QA status; legacy-unreviewed does not mean false, only not revalidated under the current standard.",
            "maybe_therefore": "A labeled competing-frame layer that states the strongest plausible defense or uncertainty before the record's evidence-bound consequence or test. Missing legacy layers remain a visible remediation backlog and are never silently generated as fact.",
            "deduplication": "Superseded rows remain as permalink tombstones but are excluded from totals and search. New canonical and federated records are checked across layers using formal IDs, direct-source URLs, normalized titles and facts, date intervals, canonical targets, and lifecycle relationships before promotion.",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build deterministic archive totals and evidence-health metrics.")
    parser.add_argument("--check", action="store_true", help="fail when committed metrics are stale")
    args = parser.parse_args()
    expected = json.dumps(build_metrics(), ensure_ascii=False, indent=2) + "\n"
    if args.check:
        current = OUTPUT_PATH.read_text(encoding="utf-8") if OUTPUT_PATH.exists() else ""
        if current != expected:
            print("data/archive_metrics.json is stale")
            return 1
        print("Verified generated archive totals and evidence-health metrics.")
        return 0
    OUTPUT_PATH.write_text(expected, encoding="utf-8")
    print("Built deterministic archive totals and evidence-health metrics.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
