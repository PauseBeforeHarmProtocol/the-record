from __future__ import annotations

import csv
import hashlib
import json
import re
import sys
import zipfile
from pathlib import Path

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


hero = SITE / "assets/brand/the-record-hero.png"
if not hero.exists():
    fail("missing assets/brand/the-record-hero.png")
elif not hero.read_bytes().startswith(b"\x89PNG\r\n\x1a\n"):
    fail("the-record-hero.png is not a PNG")

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
        if "Institutions" in labels:
            fail(f"{route}: stale Institutions navigation label")
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
entries = json.loads(entries_path.read_text(encoding="utf-8"))
ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
ids = {entry["id"] for entry in entries}
if len(ids) != len(entries):
    fail("duplicate entry IDs")
if not NEW_ENTRY_IDS <= ids:
    fail(f"release metadata names missing entries: {sorted(NEW_ENTRY_IDS - ids)}")
title_dates = {(entry["date"], re.sub(r"\W+", " ", entry["title"].lower()).strip()) for entry in entries}
if len(title_dates) != len(entries):
    fail("duplicate normalized date/title pairs")
urls = [source["url"] for source in ledger.values()]
if len(urls) != len(set(urls)):
    fail("duplicate URLs in source ledger")
for entry in entries:
    pack = SITE / entry["pack_path"]
    if not pack.exists():
        fail(f'missing pack {entry["pack_path"]}')
    elif not zipfile.is_zipfile(pack):
        fail(f'invalid ZIP pack {entry["pack_path"]}')
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
if "../agencies/index.html" not in alias_text:
    fail("institutions compatibility route does not resolve to Agencies")

legacy_text = (SITE / "the-record.html").read_text(encoding="utf-8")
if "CURRENT_LAYER_BRIDGE" not in legacy_text or "NAT-2026-07-19-001" not in legacy_text:
    fail("preserved legacy archive is missing its established current-layer bridge")
if "ChatGPT 5.4 Extended Thinking" in legacy_text:
    fail("legacy archive still exposes deprecated current-maintenance AI credit")
if "Written by Claude (Anthropic, Opus 4)" not in legacy_text:
    fail("legacy AI Opinion authorship was not preserved")

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
    f"all internal links, packs, checksums, AI disclosures, and credential scans passed."
)
