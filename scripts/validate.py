from __future__ import annotations

import csv
import hashlib
import json
import re
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
RELEASE = json.loads((ROOT / "data/release.json").read_text(encoding="utf-8"))
RELEASE_ISO = RELEASE["release_iso"]
RELEASE_HUMAN = RELEASE["release_human"]
WEEK_START = RELEASE["week_start"]
WEEK_END = RELEASE["week_end"]
NEW_ENTRY_IDS = set(RELEASE["new_entry_ids"])
NATIONAL_PACK_NAME = f"THE_RECORD_NATIONAL_UPDATE_PACK_{RELEASE_ISO}.zip"
COMPLETE_PACK_NAME = f"THE_RECORD_CURRENT_UPDATE_PACK_{RELEASE_ISO}.zip"
RUN_RECEIPT_NAME = f"THE_RECORD_RUN_RECEIPT_{RELEASE_ISO}.md"


def fail(message: str) -> None:
    ERRORS.append(message)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalized_text(value: object) -> str:
    return re.sub(r"\W+", " ", str(value or "").casefold()).strip()


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
for required_artifact in (NATIONAL_PACK_NAME, COMPLETE_PACK_NAME, RUN_RECEIPT_NAME):
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
