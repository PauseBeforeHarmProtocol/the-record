from __future__ import annotations

import argparse
import hashlib
import html
import json
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RELEASE = json.loads((ROOT / "data/release.json").read_text(encoding="utf-8"))
VERSION = RELEASE["version"]
RELEASE_ISO = RELEASE["release_iso"]
RELEASE_DATE = RELEASE["release_human"]
CHECKED_AT = RELEASE["checked_at"]
WEEK_START = RELEASE["week_start"]
WEEK_END = RELEASE["week_end"]
WEEK_LABEL = RELEASE["week_label"]
CUTOFF_START = RELEASE["cutoff_start"]
NEW_ENTRY_IDS = set(RELEASE["new_entry_ids"])
AI_CREDIT = RELEASE["ai_credit"]
NATIONAL_PACK_NAME = f"THE_RECORD_NATIONAL_UPDATE_PACK_{RELEASE_ISO}.zip"
COMPLETE_PACK_NAME = f"THE_RECORD_CURRENT_UPDATE_PACK_{RELEASE_ISO}.zip"


def esc(value: object, *, quote: bool = False) -> str:
    return html.escape(str(value), quote=quote)


def header(active: str, prefix: str) -> str:
    links = [
        ("home", "Home", f"{prefix}index.html"),
        ("archive-live", "The Archive", f"{prefix}the-record.html#home"),
        ("national", "Latest", f"{prefix}national/index.html"),
        ("weekly", "Weekly", f"{prefix}weekly/index.html"),
        ("in6", "IN-6", f"{prefix}in6/index.html"),
        ("agencies", "Agencies", f"{prefix}agencies/index.html"),
        ("method", "Method", f"{prefix}methodology/index.html"),
        ("downloads", "Downloads", f"{prefix}downloads/index.html"),
    ]
    nav = "".join(
        f'<a href="{href}"{(" aria-current=\"page\"" if key == active else "")}>{label}</a>'
        for key, label, href in links
    )
    return f'''<a class="skip-link" href="#main">Skip to content</a>
<header class="site-header">
  <div class="header-inner">
    <a class="brand" href="{prefix}index.html"><img class="brand-mark" src="{prefix}assets/brand/the-record-mark.svg" width="48" height="48" alt=""><span><strong>THE RECORD</strong><span>Evidence · context · accountability</span></span></a>
    <button class="nav-toggle" type="button" aria-expanded="false" aria-controls="primary-nav">Menu</button>
    <nav class="primary-nav" id="primary-nav" aria-label="Primary">{nav}</nav>
    <span class="update-badge">Updated {RELEASE_DATE}</span>
  </div>
</header>'''


def footer(prefix: str) -> str:
    return f'''<footer class="site-footer"><div class="footer-inner">
  <section><h2>The Record</h2><p>A sourced accountability archive edited by Phillip Linstrum. This front page curates the latest verified developments; <a href="{prefix}the-record.html#home">the full searchable archive</a> holds the complete historical record.</p></section>
  <section><h3>Project links</h3><p><a href="https://github.com/PauseBeforeHarmProtocol/the-record" target="_blank" rel="noopener">National source repository</a><br><a href="https://github.com/PauseBeforeHarmProtocol/the-record-in6" target="_blank" rel="noopener">IN-6 source repository</a><br><a href="https://github.com/PauseBeforeHarmProtocol/pbhp" target="_blank" rel="noopener">Pause Before Harm Protocol</a><br><a href="{prefix}methodology/index.html#ai-disclosure">AI provenance</a></p></section>
  <section><h3>Corrections</h3><p>Email <a href="mailto:pausebeforeharmprotocol_pbhp@protonmail.com">pausebeforeharmprotocol_pbhp@protonmail.com</a>. Include the entry ID, disputed text, and supporting source.</p></section>
</div><div class="footer-bottom">Release {VERSION} · checked {CHECKED_AT} · built with {AI_CREDIT}, editor-reviewed.</div></footer>
<div class="toast" role="status" aria-live="polite"></div>'''


def document(*, title: str, description: str, body: str, active: str, prefix: str, extra_head: str = "") -> str:
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="{esc(description, quote=True)}"><meta name="theme-color" content="#0b1320">{extra_head}<title>{esc(title)}</title><link rel="icon" href="{prefix}assets/brand/the-record-mark.svg" type="image/svg+xml"><link rel="stylesheet" href="{prefix}assets/styles.css"></head><body>
{header(active, prefix)}
<main id="main">{body}</main>
{footer(prefix)}
<script src="{prefix}assets/site.js"></script></body></html>
'''


def source_list(entry: dict, ledger: dict) -> str:
    return "\n".join(
        f'<li><a href="{esc(ledger[source_id]["url"], quote=True)}" target="_blank" rel="noopener">{esc(ledger[source_id]["name"])}</a><span>{esc(ledger[source_id]["type"])}</span></li>'
        for source_id in entry["sources"]
    )


def record_card(entry: dict, ledger: dict, prefix: str) -> str:
    searchable = " ".join([
        entry["title"], entry["dek"], *entry["tags"], *entry["institutions"], *entry["facts"]
    ]).lower()
    facts = "".join(f"<li>{esc(fact)}</li>" for fact in entry["facts"])
    chips = "".join(f'<span class="chip">{esc(tag)}</span>' for tag in entry["tags"])
    corrections = ""
    if entry.get("corrections"):
        correction_items = "".join(
            f'<li><strong>{esc(item["timestamp"])}</strong> — {esc(item["note"])}</li>'
            for item in entry["corrections"]
        )
        corrections = f'<div class="integrity-note"><h3>Corrections</h3><ul>{correction_items}</ul></div>'
    return f'''<article class="record-card" id="{esc(entry["id"], quote=True)}" data-week-card data-scope="{esc(entry["scope"], quote=True)}" data-searchable="{esc(searchable, quote=True)}">
  <div class="record-card__head"><div><div class="eyebrow">{esc(entry["id"])} · {esc(entry["display_date"])}</div><h2>{esc(entry["title"])}</h2><p class="dek">{esc(entry["dek"])}</p></div><span class="status-pill">{esc(entry["evidence"])}</span></div>
  <div class="chips">{chips}</div>
  <div class="three-layer">
    <section class="layer layer--facts"><h3>The facts</h3><ul>{facts}</ul></section>
    <section class="layer layer--significance"><h3>Significance</h3><p>{esc(entry["significance"])}</p></section>
    <section class="layer layer--goalpost"><h3>Goalpost / response</h3><p>{esc(entry["goalpost"])}</p></section>
  </div>
{corrections}
  <details class="sources"><summary>Sources and verification notes</summary><ul>{source_list(entry, ledger)}</ul><p class="micro">Checked {esc(entry["checked_at"])}. Source type is shown because an official statement establishes what an institution says; it does not independently prove the institution’s interpretation.</p></details>
  <div class="card-actions"><a class="button button--primary" href="{prefix}{esc(entry["pack_path"], quote=True)}" download>Download this entry</a><button class="button button--ghost copy-link" type="button" data-copy="#{esc(entry["id"], quote=True)}">Copy entry link</button></div>
</article>'''


def search_panel(label: str = "Filter records") -> str:
    return f'''<div class="search-panel"><label class="micro" for="record-search">{esc(label)}</label><input id="record-search" data-record-search type="search" placeholder="Search titles, agencies, institutions, or topics"><span class="search-count"></span></div>'''


def scoped_page(entries: list[dict], ledger: dict, scope: str) -> str:
    if scope == "national":
        title = "National current record"
        description = "A dated current-affairs layer for the complete Trump-accountability archive. This page covers the latest verified window; it does not imply that every legacy entry was re-audited today."
        download_text = "Download national section"
    else:
        title = "IN-6 representation audit"
        description = "Current representation, votes, appropriations, and election records for Indiana’s Sixth Congressional District."
        download_text = "Download IN-6 section"
    selected = sorted(
        (entry for entry in entries if entry["scope"] == scope),
        key=lambda entry: (entry["date"], entry["id"]),
        reverse=True,
    )
    cards = "\n".join(record_card(entry, ledger, "../") for entry in selected)
    body = f'''<div class="container"><header class="page-head"><div class="eyebrow">Updated {RELEASE_DATE}</div><h1>{title}</h1><p>{description}</p><div class="button-row"><a class="button button--primary" href="../downloads/index.html">{download_text}</a><a class="button button--ghost" href="../the-record.html#timeline">Search the full archive</a></div></header>{search_panel()}<section class="record-list">{cards}</section></div>'''
    return document(title=f"{title} · The Record", description=description, body=body, active=scope, prefix="../")


def weekly_page(entries: list[dict], ledger: dict) -> str:
    weekly = sorted(
        (entry for entry in entries if WEEK_START <= entry["date"] <= WEEK_END),
        key=lambda entry: (entry["date"], entry["id"]),
        reverse=True,
    )
    national_count = sum(entry["scope"] == "national" for entry in weekly)
    in6_count = sum(entry["scope"] == "in6" for entry in weekly)
    cards = "\n".join(record_card(entry, ledger, "../") for entry in weekly)
    body = f'''<div class="container"><header class="page-head"><div class="eyebrow">What happened this week</div><h1>{WEEK_LABEL}</h1><p>This is a reproducible seven-day view anchored to the {RELEASE_DATE} release—not a browser-clock guess. It includes {len(weekly)} records: {national_count} national and {in6_count} IN-6.</p><div class="scope-filter" aria-label="Filter weekly records"><button class="button button--primary" type="button" data-week-filter="all" aria-pressed="true">All {len(weekly)}</button><button class="button button--ghost" type="button" data-week-filter="national" aria-pressed="false">National {national_count}</button><button class="button button--ghost" type="button" data-week-filter="in6" aria-pressed="false">IN-6 {in6_count}</button></div></header>{search_panel("Search this week")}<div class="integrity-note"><h2>Currentness boundary</h2><p>The national current layer was researched through {CHECKED_AT}. This backfill covers qualifying developments beginning {CUTOFF_START} and added or materially refreshed {len(NEW_ENTRY_IDS)} national records. Per-entry evidence state and check times remain visible.</p></div><section class="record-list">{cards}</section></div>'''
    return document(title="Weekly record · The Record", description=f"The Record weekly accountability view for {WEEK_LABEL}.", body=body, active="weekly", prefix="../")


def agency_category(name: str) -> str:
    executive = (
        "The White House", "Department", "Bureau", "Office of the National Cyber Director",
        "Office of the Director of National Intelligence", "Federal Bureau", "Central Intelligence",
        "DHS/CISA", "NSA", "Treasury", "U.S. Fish and Wildlife Service"
    )
    legislative = (
        "Congress", "U.S. House", "U.S. Senate", "House ", "Office of the Clerk", "Federal courts"
    )
    if name.startswith(executive):
        return "Executive departments & agencies"
    if name.startswith(legislative):
        return "Congress, courts & oversight"
    return "State, local & civic institutions"


def agencies_page(entries: list[dict]) -> str:
    mapped: dict[str, list[dict]] = defaultdict(list)
    for entry in entries:
        for institution in entry["institutions"]:
            mapped[institution].append(entry)
    grouped: dict[str, list[tuple[str, list[dict]]]] = defaultdict(list)
    for name, linked in mapped.items():
        grouped[agency_category(name)].append((name, linked))
    category_order = [
        "Executive departments & agencies",
        "Congress, courts & oversight",
        "State, local & civic institutions",
    ]
    sections = []
    for category in category_order:
        cards = []
        for name, linked in sorted(grouped[category], key=lambda item: (-len(item[1]), item[0])):
            links = "".join(
                f'<li><a href="../{entry["scope"]}/index.html#{esc(entry["id"], quote=True)}">{esc(entry["title"])}</a></li>'
                for entry in linked
            )
            ids = ", ".join(entry["id"] for entry in linked)
            searchable = f'{name} {category} ' + " ".join(entry["title"] for entry in linked)
            cards.append(f'''<article class="institution-card" data-searchable="{esc(searchable.lower(), quote=True)}"><div class="eyebrow">{len(linked)} linked record{"s" if len(linked) != 1 else ""}</div><h3>{esc(name)}</h3><ul>{links}</ul><p class="micro">Entry IDs: {esc(ids)}</p></article>''')
        sections.append(f'''<section class="agency-section"><div class="section-head"><div><div class="eyebrow">Accountability layer</div><h2>{esc(category)}</h2></div></div><div class="institution-grid">{"".join(cards)}</div></section>''')
    body = f'''<div class="container"><header class="page-head"><div class="eyebrow">Power map</div><h1>Agencies &amp; institutions</h1><p>Agencies are the missing middle between a headline and an accountable action. This map names the public body, links every current record attached to it, and keeps executive agencies separate from Congress, courts, and civic institutions.</p></header>{search_panel("Find an agency")}<div class="integrity-note"><h2>How to use this tab</h2><p>Start with the body that exercised power, then follow the linked record to its source and response layers. A body appearing here does not imply wrongdoing; it means the current record names that body’s authority, action, review role, or evidence.</p></div>{"".join(sections)}</div>'''
    return document(title="Agencies · The Record", description="A map of agencies and institutions named in The Record’s current accountability layer.", body=body, active="agencies", prefix="../")


def institutions_alias() -> str:
    body = '''<div class="container"><header class="page-head"><div class="eyebrow">Route preserved</div><h1>Institutions moved to Agencies.</h1><p>The content is still here; it now has the top-level name and route requested for the public navigation.</p><div class="button-row"><a class="button button--primary" href="../agencies/index.html">Open Agencies</a></div></header></div>'''
    return document(
        title="Institutions moved to Agencies · The Record",
        description="Compatibility route for The Record agencies and institutions map.",
        body=body,
        active="agencies",
        prefix="../",
        extra_head='<meta http-equiv="refresh" content="0; url=../agencies/index.html"><link rel="canonical" href="../agencies/index.html">',
    )


def sources_page(ledger: dict) -> str:
    rows = "".join(
        f'<tr><td><code>{esc(source_id)}</code></td><td><a href="{esc(source["url"], quote=True)}" target="_blank" rel="noopener">{esc(source["name"])}</a><span class="micro">{esc(source["publisher"])}</span></td><td>{esc(source["date"])}</td><td>{esc(source["type"])}</td></tr>'
        for source_id, source in ledger.items()
    )
    body = f'''<div class="container"><header class="page-head"><div class="eyebrow">Source ledger</div><h1>Every linked source in one place</h1><p>The ledger records source type because an official page and independent reporting answer different questions. Download the CSV or JSON for audit and reuse.</p><div class="button-row"><a class="button button--primary" href="../data/source_ledger.csv" download>Download CSV</a><a class="button button--ghost" href="../data/source_ledger.json" download>Download JSON</a></div></header><div class="table-wrap"><table><thead><tr><th>ID</th><th>Source</th><th>Date</th><th>Type</th></tr></thead><tbody>{rows}</tbody></table></div></div>'''
    return document(title="Source ledger · The Record", description=f"Source ledger for The Record {RELEASE_DATE} release.", body=body, active="method", prefix="../")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def download_card(title: str, text: str, href: str, digest: str, label: str) -> str:
    return f'''<article class="download-card"><div class="eyebrow">Download</div><h3>{esc(title)}</h3><p>{esc(text)}</p><p class="micro">SHA-256: <code>{digest[:16]}…</code></p><a class="button button--primary" href="{esc(href, quote=True)}" download>{esc(label)}</a></article>'''


def downloads_page(entries: list[dict]) -> str:
    national_count = sum(entry["scope"] == "national" for entry in entries)
    in6_count = sum(entry["scope"] == "in6" for entry in entries)
    ledger_count = len(json.loads((ROOT / "data/source_ledger.json").read_text(encoding="utf-8")))
    featured = [
        (f"Complete {RELEASE_DATE} update", f"All {len(entries)} entry packs, the national brief, source ledgers, machine-readable data, and the run receipt.", f"../artifacts/{COMPLETE_PACK_NAME}", ROOT / "artifacts" / COMPLETE_PACK_NAME, "Download complete update"),
        ("National current brief", f"All {national_count} national entries, including {len(NEW_ENTRY_IDS)} records added in this pass, with individual packs and the source ledger.", f"../artifacts/{NATIONAL_PACK_NAME}", ROOT / "artifacts" / NATIONAL_PACK_NAME, "Download national pack"),
        ("IN-6 current brief", f"The {in6_count} IN-6 records remain preserved from the July 18 package; this run’s requested scope was the national Trump record.", "../artifacts/THE_RECORD_IN6_UPDATE_PACK_2026-07-18.zip", ROOT / "artifacts/THE_RECORD_IN6_UPDATE_PACK_2026-07-18.zip", "Download IN-6 pack"),
        ("Current-entry data", f"All {len(entries)} dated entries in one JSON file for reuse in future builds or research tools.", "../data/current_entries.json", ROOT / "data/current_entries.json", "Download entry JSON"),
        ("Source ledger CSV", f"A flat audit table of all {ledger_count} sources linked in this current layer.", "../data/source_ledger.csv", ROOT / "data/source_ledger.csv", "Download source CSV"),
        ("Artifact checksums", "SHA-256 values for release artifacts, including every individual entry pack.", "../artifacts/SHA256SUMS.txt", ROOT / "artifacts/SHA256SUMS.txt", "Download checksums"),
    ]
    featured_html = "".join(download_card(title, text, href, sha(path), label) for title, text, href, path, label in featured)
    individual_html = "".join(
        download_card(entry["title"], entry["dek"], f'../{entry["pack_path"]}', sha(ROOT / entry["pack_path"]), "Download this entry")
        for entry in sorted(entries, key=lambda entry: (entry["date"], entry["id"]), reverse=True)
    )
    body = f'''<div class="container"><header class="page-head"><div class="eyebrow">Portable evidence</div><h1>Read it here. Download it here.</h1><p>Every major section and every individual update is available without hunting through a repository. Each entry pack contains readable Markdown, JSON, source data, and a checksum.</p></header><section class="download-grid">{featured_html}</section><div class="section-head"><div><div class="eyebrow">Individual records</div><h2>One entry, one direct download</h2></div><p>The same information block shown on the site is packaged for offline review and reuse.</p></div><section class="download-grid">{individual_html}</section><div class="integrity-note"><h2>Preserved July 18 packages</h2><p>The original candidate packages remain unchanged: <a href="../artifacts/THE_RECORD_JULY_18_UPDATE_PACK_2026-07-18.zip" download>complete July 18</a> · <a href="../artifacts/THE_RECORD_NATIONAL_UPDATE_PACK_2026-07-18.zip" download>national July 18</a> · <a href="../artifacts/THE_RECORD_IN6_UPDATE_PACK_2026-07-18.zip" download>IN-6 July 18</a>.</p></div></div>'''
    return document(title="Downloads · The Record", description=f"Download The Record {RELEASE_DATE} update and individual entries.", body=body, active="downloads", prefix="../")


def methodology_page(entries: list[dict]) -> str:
    body = f'''<div class="container"><header class="page-head"><div class="eyebrow">Methodology</div><h1>Facts are not analysis. Official claims are not independent verification.</h1><p>The Record’s value depends on keeping those categories visible, preserving corrections, and refusing to turn a large archive into an unreviewable claim of completeness.</p></header>
<section class="method-grid">
<article class="method-card"><h2>1. The three-layer entry</h2><p><strong>THE FACTS</strong> records the sourced event. <strong>SIGNIFICANCE</strong> states the editor’s contextual analysis. <strong>GOALPOST / RESPONSE</strong> records the strongest relevant defense, explanation, or shifting rhetorical frame without treating it as established fact.</p></article>
<article class="method-card"><h2>2. Source hierarchy</h2><p>Primary legal documents, official roll calls, bill text, and agency records are preferred for what an institution formally did. Independent reporting is used to corroborate, supply context, and identify disputes. Official press releases establish the speaker’s position—not the truth of every claim inside the release.</p></article>
<article class="method-card"><h2>3. Currentness</h2><p>Every release has a visible checked time. Relative words such as “today” are avoided inside durable entries. A current brief never implies that the entire historical archive was revalidated in the same pass.</p></article>
<article class="method-card"><h2>4. Corrections and reply</h2><p>Send the entry ID, disputed wording, and supporting documentation to the project address. Corrections identify what changed and when. A materially relevant response from an affected office or candidate is attached to the relevant entry rather than hidden in a separate page.</p></article>
<article class="method-card"><h2>5. Count reconciliation</h2><p>The repository currently exposes conflicting entry and source totals. Exact totals are withheld until one deterministic build step counts canonical records and source objects. The integrity rule is simple: the build—not promotional copy—sets the number.</p></article>
<article class="method-card" id="ai-disclosure"><h2>6. AI disclosure &amp; provenance</h2><p>Current research organization, drafting support, code, and adversarial review use <strong>ChatGPT 5.6 Sol Max</strong> and <strong>Claude Fable 5 Max (Cowork)</strong>. Phillip Linstrum remains the editor and acceptance authority. AI output is not a source.</p><p>The five April 2026 AI Opinion essays retain their original attribution to <strong>Claude (Anthropic, Opus 4)</strong>. This {RELEASE_DATE} pass updates the surrounding maintenance disclosure; it does not silently reassign or rewrite those essays’ authorship. See <a href="../AI_PROVENANCE.md">the provenance record</a>.</p></article>
</section>
<div class="integrity-note"><h2>Scope of this release</h2><p>This release contains {len(entries)} dated current-layer entries, including {len(NEW_ENTRY_IDS)} national records added or materially refreshed in the August 17–24 backfill. It does not certify the complete legacy archive, independently validate every historical source, or resolve all open IN-6 claims.</p></div>
<h2>Publication rules</h2><pre class="code-note">NO SOURCE → NO FACT CLAIM
OFFICIAL STATEMENT → WHAT THE INSTITUTION SAYS
INDEPENDENT REPORTING → CORROBORATION AND CONTEXT
ANALYSIS → LABELED
EXACT COUNT → GENERATED FROM CANONICAL DATA
CORRECTION → TIMESTAMPED AND PRESERVED</pre></div>'''
    return document(title="Methodology · The Record", description="Evidence, correction, currentness, and AI rules for The Record.", body=body, active="method", prefix="../")


def home_page(entries: list[dict], ledger: dict) -> str:
    national_count = sum(entry["scope"] == "national" for entry in entries)
    weekly = sorted(
        (entry for entry in entries if WEEK_START <= entry["date"] <= WEEK_END),
        key=lambda entry: (entry["date"], entry["id"]), reverse=True
    )
    weekly_links = "".join(
        f'<li><span class="chip">{"National" if entry["scope"] == "national" else "IN-6"}</span><a href="{entry["scope"]}/index.html#{esc(entry["id"], quote=True)}">{esc(entry["title"])}</a></li>'
        for entry in weekly[:5]
    )
    body = f'''<section class="hero"><div class="hero-inner"><div><div class="kicker">A living Trump accountability archive · updated {RELEASE_DATE}</div><h1>The full record, not just the latest headline.</h1><p>This page is the editorial front door: a concise view of newly verified developments. The complete archive holds the rest—4,000+ dated entries, their sources, and research paths across years, topics, people, institutions, and the full timeline.</p><div class="hero-actions"><a class="button button--primary" href="the-record.html#home">Enter the full archive</a><a class="button button--secondary" href="the-record.html#timeline">Search the timeline</a><a class="button button--ghost" href="weekly/index.html">Latest seven days</a></div></div><aside class="hero-stamp"><div class="eyebrow">Archive state</div><strong>Current through {CHECKED_AT}</strong><p>{len(NEW_ENTRY_IDS)} national records were added or materially refreshed in this release. Those records now feed the complete archive as well as the latest-updates pages.</p></aside></div><figure class="hero-art"><img src="assets/brand/the-record-hero.png" alt="An illuminated evidence archive connecting sourced records across a living accountability timeline" width="1672" height="941" fetchpriority="high" decoding="async"></figure></section>
<div class="container"><section class="stats" aria-label="Archive and release statistics"><div class="stat"><strong>4,000+</strong><span>full-archive entries</span></div><div class="stat"><strong>{national_count}</strong><span>verified current national entries</span></div><div class="stat"><strong>{len(weekly)}</strong><span>records in this seven-day window</span></div><div class="stat"><strong>{len(ledger)}</strong><span>sources in the current ledger</span></div></section>
<section class="archive-feature"><div class="archive-feature__copy"><div class="eyebrow">The research layer</div><h2>The archive is where the whole project lives.</h2><p>The landing page will stay readable by showing a curated current layer. The archive carries the complete body of information: historical entries, sources, topic folders, people, statistics, methodology, and current additions in one searchable application.</p><div class="button-row"><a class="button button--primary" href="the-record.html#home">Browse the archive</a><a class="button button--ghost" href="the-record.html#timeline">Open the full timeline</a></div></div><div class="archive-paths" aria-label="Archive research paths"><a href="the-record.html#topics"><strong>Topics</strong><span>Courts, democracy, immigration, media, foreign influence, and more</span></a><a href="the-record.html#years"><strong>Years</strong><span>Move through the record chronologically, from 1927 to the present</span></a><a href="the-record.html#politicians"><strong>People</strong><span>Find officeholders, advisers, opponents, and connected events</span></a><a href="the-record.html#timeline"><strong>Search</strong><span>Query dates, names, agencies, events, and source-linked entries</span></a></div></section>
<section class="weekly-highlight"><div><div class="eyebrow">What happened this week</div><h2>{len(weekly)} records · {WEEK_LABEL}</h2><p>A compact, fixed seven-day window. Use it for the latest signal; use the archive for the complete record.</p><a class="button button--primary" href="weekly/index.html">Open the weekly record</a></div><ul>{weekly_links}</ul></section>
<div class="section-head"><div><div class="eyebrow">Current layer</div><h2>Focused views for the newest material</h2></div><p>These pages summarize and package recent verified additions. They do not duplicate the complete historical archive.</p></div><section class="route-grid">
<article class="route-card"><div class="eyebrow">Latest</div><h3>National current record</h3><p>{national_count} sourced developments, each separated into facts, significance, and the administration’s response.</p><a class="button button--ghost" href="national/index.html">Open latest national</a></article>
<article class="route-card"><div class="eyebrow">Weekly</div><h3>What happened this week</h3><p>{len(weekly)} current records in a stable {WEEK_LABEL} window, with scope filters and search.</p><a class="button button--ghost" href="weekly/index.html">Open weekly</a></article>
<article class="route-card"><div class="eyebrow">Power map</div><h3>Agencies &amp; institutions</h3><p>See which public bodies acted, what authority they used, and every current record linked to them.</p><a class="button button--ghost" href="agencies/index.html">Browse agencies</a></article>
<article class="route-card"><div class="eyebrow">District</div><h3>IN-6 representation audit</h3><p>House votes, appropriations activity, committee power, and verified election status for Indiana’s Sixth District.</p><a class="button button--ghost" href="in6/index.html">Open IN-6</a></article>
<article class="route-card"><div class="eyebrow">Integrity</div><h3>Method &amp; AI provenance</h3><p>Read the evidence rules, correction process, exact current AI disclosure, and legacy essay provenance.</p><a class="button button--ghost" href="methodology/index.html">Read the method</a></article>
<article class="route-card"><div class="eyebrow">Portable</div><h3>Downloads &amp; source ledger</h3><p>Download the current package or inspect every primary, official, and independent source in the current layer.</p><div class="card-actions"><a class="button button--ghost" href="downloads/index.html">Downloads</a><a class="button button--ghost" href="sources/index.html">Sources</a></div></article>
</section><div class="integrity-note"><h2>Count note</h2><p>Legacy project files still contain conflicting exact totals. Until the historical source arrays generate one reconciled count, this site uses the accurate public description <strong>4,000+ entries and 5,000+ sources</strong> rather than presenting false precision.</p></div></div>'''
    return document(title=f"The Record · Trump Accountability Archive", description=f"The Record is a living, searchable Trump accountability archive, current through {CHECKED_AT}.", body=body, active="home", prefix="")


def archive_page() -> str:
    body = f'''<div class="container"><header class="page-head"><div class="eyebrow">The research layer</div><h1>Open the complete archives</h1><p>The landing page highlights current developments. The national archive is the living, searchable body of the project and receives every qualifying current national addition; the IN-6 archive remains the complete district research application.</p></header><section class="download-grid">
<article class="download-card"><div class="eyebrow">Primary archive · current {RELEASE_DATE}</div><h3>Trump Accountability Archive</h3><p>Search the full historical timeline, browse by topic, year, or person, inspect sources, and read the methodology and companion analysis. The latest verified national entries are included in the same application.</p><a class="button button--primary" href="../the-record.html#home">Enter the full archive</a><p class="micro"><a href="../the-record.html#timeline">Open timeline directly</a> · <a href="https://github.com/PauseBeforeHarmProtocol/the-record" target="_blank" rel="noopener">Source repository</a></p></article>
<article class="download-card"><div class="eyebrow">Indiana 6th</div><h3>Complete IN-6 representation audit</h3><p>Open the established district archive for the full timeline, candidate comparison, topic views, district data, methodology, and historical analysis.</p><a class="button button--primary" href="https://pausebeforeharmprotocol.github.io/the-record-in6/" target="_blank" rel="noopener">Open IN-6 archive</a><p class="micro"><a href="https://github.com/PauseBeforeHarmProtocol/the-record-in6" target="_blank" rel="noopener">Source repository</a></p></article>
<article class="download-card"><div class="eyebrow">Latest layer</div><h3>What belongs on the landing site</h3><p>The smaller National and Weekly pages make new material easy to scan, verify, and download. They are curated views into the same project, not substitutes for the archive.</p><a class="button button--ghost" href="../national/index.html">See latest verified entries</a></article>
</section><div class="integrity-note"><h2>Preservation and maintenance rule</h2><p>Keep <code>the-record.html</code>, <code>entries_array.js</code>, companion documents, the complete PDF, and <code>docs/</code>. Scheduled updates refresh the archive’s small generated current layer while leaving its historical application and source body stable.</p></div></div>'''
    return document(title="Complete archives · The Record", description="Links to the complete national and IN-6 archives.", body=body, active="archive", prefix="../")


def not_found_page() -> str:
    body = '''<div class="container"><header class="page-head"><div class="eyebrow">404</div><h1>That record path does not exist.</h1><p>Return to the editorial front page or search the full archive.</p><div class="button-row"><a class="button button--primary" href="index.html">Return home</a><a class="button button--ghost" href="the-record.html#timeline">Search the archive</a></div></header></div>'''
    return document(title="Not found · The Record", description="Page not found.", body=body, active="", prefix="")


def build_pages() -> dict[Path, str]:
    entries = json.loads((ROOT / "data/current_entries.json").read_text(encoding="utf-8"))
    ledger = json.loads((ROOT / "data/source_ledger.json").read_text(encoding="utf-8"))
    return {
        ROOT / "index.html": home_page(entries, ledger),
        ROOT / "weekly/index.html": weekly_page(entries, ledger),
        ROOT / "national/index.html": scoped_page(entries, ledger, "national"),
        ROOT / "in6/index.html": scoped_page(entries, ledger, "in6"),
        ROOT / "agencies/index.html": agencies_page(entries),
        ROOT / "institutions/index.html": institutions_alias(),
        ROOT / "sources/index.html": sources_page(ledger),
        ROOT / "downloads/index.html": downloads_page(entries),
        ROOT / "methodology/index.html": methodology_page(entries),
        ROOT / "archive/index.html": archive_page(),
        ROOT / "404.html": not_found_page(),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build The Record current static front door from canonical data.")
    parser.add_argument("--check", action="store_true", help="fail if generated pages differ from committed pages")
    args = parser.parse_args()
    pages = build_pages()
    mismatches = []
    for path, content in pages.items():
        if args.check:
            if not path.exists() or path.read_text(encoding="utf-8") != content:
                mismatches.append(path.relative_to(ROOT).as_posix())
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
    if mismatches:
        print("Generated pages are stale:")
        print("\n".join(f"- {path}" for path in mismatches))
        return 1
    print(f"{'Verified' if args.check else 'Built'} {len(pages)} current pages.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
