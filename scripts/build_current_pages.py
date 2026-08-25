from __future__ import annotations

import argparse
import hashlib
import html
import json
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RELEASE = json.loads((ROOT / "data/release.json").read_text(encoding="utf-8"))
ARCHIVE_METRICS = json.loads((ROOT / "data/archive_metrics.json").read_text(encoding="utf-8"))
ARCHIVE_REGISTRY = json.loads((ROOT / "data/archive_registry.json").read_text(encoding="utf-8"))
FEDERATED_RECORDS = json.loads((ROOT / "data/federated_records.json").read_text(encoding="utf-8"))
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
SITE_ROOT = "/the-record/"


def esc(value: object, *, quote: bool = False) -> str:
    return html.escape(str(value), quote=quote)


def site_path(path: str = "") -> str:
    """Return a GitHub Pages project-absolute URL that survives nested routes."""
    return f"{SITE_ROOT}{path.lstrip('/')}"


def header(active: str) -> str:
    links = [
        ("home", "Home", site_path("index.html")),
        ("archive-live", "The Archive", site_path("the-record.html#home")),
        ("truth-feed", "Truth Social", site_path("the-record.html#feed")),
        ("national", "Latest", site_path("national/index.html")),
        ("weekly", "Weekly", site_path("weekly/index.html")),
        ("in6", "IN-6", site_path("in6/index.html")),
        ("agencies", "Agencies", site_path("agencies/index.html")),
        ("method", "Method", site_path("methodology/index.html")),
        ("quality", "Quality", site_path("quality/index.html")),
        ("downloads", "Downloads", site_path("downloads/index.html")),
    ]
    nav = "".join(
        f'<a href="{href}"{(" aria-current=\"page\"" if key == active else "")}>{label}</a>'
        for key, label, href in links
    )
    return f'''<a class="skip-link" href="#main">Skip to content</a>
<header class="site-header">
  <div class="header-inner">
    <a class="brand" href="{site_path('index.html')}"><img class="brand-mark" src="{site_path('assets/brand/the-record-mark.svg')}" width="48" height="48" alt=""><span><strong>THE RECORD</strong><span>Evidence · context · accountability</span></span></a>
    <button class="nav-toggle" type="button" aria-expanded="false" aria-controls="primary-nav">Menu</button>
    <nav class="primary-nav" id="primary-nav" aria-label="Primary">{nav}</nav>
    <span class="update-badge">Updated {RELEASE_DATE}</span>
  </div>
</header>'''


def footer() -> str:
    return f'''<footer class="site-footer"><div class="footer-inner">
  <section><h2>The Record</h2><p>A sourced accountability archive edited by Phillip Linstrum. This front page curates the latest verified developments; <a href="{site_path('the-record.html#home')}">the full searchable archive</a> holds the historical and current record, with review state and known gaps disclosed.</p></section>
  <section><h3>Project links</h3><p><a href="https://github.com/PauseBeforeHarmProtocol/the-record" target="_blank" rel="noopener">National source repository</a><br><a href="https://github.com/PauseBeforeHarmProtocol/the-record-in6" target="_blank" rel="noopener">IN-6 source repository</a><br><a href="https://github.com/PauseBeforeHarmProtocol/pbhp" target="_blank" rel="noopener">Pause Before Harm Protocol</a><br><a href="{site_path('methodology/index.html#ai-disclosure')}">AI provenance</a></p></section>
  <section><h3>Corrections</h3><p>Email <a href="mailto:pausebeforeharmprotocol_pbhp@protonmail.com">pausebeforeharmprotocol_pbhp@protonmail.com</a>. Include the entry ID, disputed text, and supporting source.</p></section>
</div><div class="footer-bottom">Release {VERSION} · editorial currentness checked {CHECKED_AT} · AI-assisted build with {AI_CREDIT}; review state is shown per record.</div></footer>
<div class="toast" role="status" aria-live="polite"></div>'''


def document(*, title: str, description: str, body: str, active: str, extra_head: str = "") -> str:
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="{esc(description, quote=True)}"><meta name="theme-color" content="#0b1320">{extra_head}<title>{esc(title)}</title><link rel="icon" href="{site_path('assets/brand/the-record-mark.svg')}" type="image/svg+xml"><link rel="stylesheet" href="{site_path('assets/styles.css')}"></head><body>
{header(active)}
<main id="main">{body}</main>
{footer()}
<script src="{site_path('assets/site.js')}"></script></body></html>
'''


def source_list(entry: dict, ledger: dict) -> str:
    return "\n".join(
        f'<li><a href="{esc(ledger[source_id]["url"], quote=True)}" target="_blank" rel="noopener">{esc(ledger[source_id]["name"])}</a><span>{esc(ledger[source_id]["type"])}</span></li>'
        for source_id in entry["sources"]
    )


def record_card(entry: dict, ledger: dict) -> str:
    searchable = " ".join([
        entry["title"], entry["dek"], entry.get("maybe_therefore", ""),
        *entry["tags"], *entry["institutions"], *entry["facts"]
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
    maybe_therefore = ""
    if entry.get("maybe_therefore"):
        maybe_therefore = f'<section class="layer layer--goalpost"><h3>Maybe / Therefore</h3><p>{esc(entry["maybe_therefore"])}</p></section>'
    return f'''<article class="record-card" id="{esc(entry["id"], quote=True)}" data-week-card data-scope="{esc(entry["scope"], quote=True)}" data-searchable="{esc(searchable, quote=True)}">
  <div class="record-card__head"><div><div class="eyebrow">{esc(entry["id"])} · {esc(entry["display_date"])}</div><h2>{esc(entry["title"])}</h2><p class="dek">{esc(entry["dek"])}</p></div><span class="status-pill">{esc(entry["evidence"])}</span></div>
  <div class="chips">{chips}</div>
  <div class="three-layer">
    <section class="layer layer--facts"><h3>The facts</h3><ul>{facts}</ul></section>
    <section class="layer layer--significance"><h3>Significance</h3><p>{esc(entry["significance"])}</p></section>
    <section class="layer layer--goalpost"><h3>Goalpost / response</h3><p>{esc(entry["goalpost"])}</p></section>
{maybe_therefore}
  </div>
{corrections}
  <details class="sources"><summary>Sources and verification notes</summary><ul>{source_list(entry, ledger)}</ul><p class="micro">Checked {esc(entry["checked_at"])}. Source type is shown because an official statement establishes what an institution says; it does not independently prove the institution’s interpretation.</p></details>
  <div class="card-actions"><a class="button button--primary" href="{site_path(esc(entry["pack_path"], quote=True))}" download>Download this entry</a><button class="button button--ghost copy-link" type="button" data-copy="#{esc(entry["id"], quote=True)}">Copy entry link</button></div>
</article>'''


def search_panel(label: str = "Filter records") -> str:
    return f'''<div class="search-panel"><label class="micro" for="record-search">{esc(label)}</label><input id="record-search" data-record-search type="search" placeholder="Search titles, agencies, institutions, or topics"><span class="search-count"></span></div>'''


def scoped_page(entries: list[dict], ledger: dict, scope: str) -> str:
    if scope == "national":
        title = "National current record"
        description = "A dated current-affairs layer for the full searchable Trump-accountability archive. This page covers the latest verified window; it does not imply that every legacy entry was re-audited today."
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
    cards = "\n".join(record_card(entry, ledger) for entry in selected)
    body = f'''<div class="container"><header class="page-head"><div class="eyebrow">Updated {RELEASE_DATE}</div><h1>{title}</h1><p>{description}</p><div class="button-row"><a class="button button--primary" href="{site_path('downloads/index.html')}">{download_text}</a><a class="button button--ghost" href="{site_path('the-record.html#timeline')}">Search the full archive</a></div></header>{search_panel()}<section class="record-list">{cards}</section></div>'''
    return document(title=f"{title} · The Record", description=description, body=body, active=scope)


def weekly_page(entries: list[dict], ledger: dict) -> str:
    weekly = sorted(
        (entry for entry in entries if WEEK_START <= entry["date"] <= WEEK_END),
        key=lambda entry: (entry["date"], entry["id"]),
        reverse=True,
    )
    national_count = sum(entry["scope"] == "national" for entry in weekly)
    in6_count = sum(entry["scope"] == "in6" for entry in weekly)
    cards = "\n".join(record_card(entry, ledger) for entry in weekly)
    body = f'''<div class="container"><header class="page-head"><div class="eyebrow">What happened this week</div><h1>{WEEK_LABEL}</h1><p>This is a reproducible seven-day view anchored to the {RELEASE_DATE} release—not a browser-clock guess. It includes {len(weekly)} records: {national_count} national and {in6_count} IN-6.</p><div class="scope-filter" aria-label="Filter weekly records"><button class="button button--primary" type="button" data-week-filter="all" aria-pressed="true">All {len(weekly)}</button><button class="button button--ghost" type="button" data-week-filter="national" aria-pressed="false">National {national_count}</button><button class="button button--ghost" type="button" data-week-filter="in6" aria-pressed="false">IN-6 {in6_count}</button></div></header>{search_panel("Search this week")}<div class="integrity-note"><h2>Currentness boundary</h2><p>The national current layer was researched through {CHECKED_AT}. This backfill covers qualifying developments beginning {CUTOFF_START} and added or materially refreshed {len(NEW_ENTRY_IDS)} national records. Per-entry evidence state and check times remain visible.</p></div><section class="record-list">{cards}</section></div>'''
    return document(title="Weekly record · The Record", description=f"The Record weekly accountability view for {WEEK_LABEL}.", body=body, active="weekly")


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
                f'<li><a href="{site_path(f"{entry["scope"]}/index.html#{esc(entry["id"], quote=True)}")}">{esc(entry["title"])}</a></li>'
                for entry in linked
            )
            ids = ", ".join(entry["id"] for entry in linked)
            searchable = f'{name} {category} ' + " ".join(entry["title"] for entry in linked)
            cards.append(f'''<article class="institution-card" data-searchable="{esc(searchable.lower(), quote=True)}"><div class="eyebrow">{len(linked)} linked record{"s" if len(linked) != 1 else ""}</div><h3>{esc(name)}</h3><ul>{links}</ul><p class="micro">Entry IDs: {esc(ids)}</p></article>''')
        sections.append(f'''<section class="agency-section"><div class="section-head"><div><div class="eyebrow">Accountability layer</div><h2>{esc(category)}</h2></div></div><div class="institution-grid">{"".join(cards)}</div></section>''')
    body = f'''<div class="container"><header class="page-head"><div class="eyebrow">Power map</div><h1>Agencies &amp; institutions</h1><p>Agencies are the missing middle between a headline and an accountable action. This map names the public body, links every current record attached to it, and keeps executive agencies separate from Congress, courts, and civic institutions.</p></header>{search_panel("Find an agency")}<div class="integrity-note"><h2>How to use this tab</h2><p>Start with the body that exercised power, then follow the linked record to its source and response layers. A body appearing here does not imply wrongdoing; it means the current record names that body’s authority, action, review role, or evidence.</p></div>{"".join(sections)}</div>'''
    return document(title="Agencies · The Record", description="A map of agencies and institutions named in The Record’s current accountability layer.", body=body, active="agencies")


def institutions_alias() -> str:
    body = f'''<div class="container"><header class="page-head"><div class="eyebrow">Route preserved</div><h1>Institutions moved to Agencies.</h1><p>The content is still here; it now has the top-level name and route requested for the public navigation.</p><div class="button-row"><a class="button button--primary" href="{site_path('agencies/index.html')}">Open Agencies</a></div></header></div>'''
    return document(
        title="Institutions moved to Agencies · The Record",
        description="Compatibility route for The Record agencies and institutions map.",
        body=body,
        active="agencies",
        extra_head=f'<meta http-equiv="refresh" content="0; url={site_path("agencies/index.html")}"><link rel="canonical" href="{site_path("agencies/index.html")}">',
    )


def sources_page(ledger: dict) -> str:
    rows = "".join(
        f'<tr><td><code>{esc(source_id)}</code></td><td><a href="{esc(source["url"], quote=True)}" target="_blank" rel="noopener">{esc(source["name"])}</a><span class="micro">{esc(source["publisher"])}</span></td><td>{esc(source["date"])}</td><td>{esc(source["type"])}</td></tr>'
        for source_id, source in ledger.items()
    )
    body = f'''<div class="container"><header class="page-head"><div class="eyebrow">Current-layer source ledger</div><h1>The current evidence ledger</h1><p>This table contains the structured sources used by the {len(json.loads((ROOT / "data/current_entries.json").read_text(encoding="utf-8")))} current-layer records. Legacy evidence health and independent archive discovery are disclosed separately so this page never implies that 4,000-plus historical entries have already been migrated to the stronger schema.</p><div class="button-row"><a class="button button--primary" href="{site_path('data/source_ledger.csv')}" download>Download CSV</a><a class="button button--ghost" href="{site_path('data/source_ledger.json')}" download>Download JSON</a><a class="button button--ghost" href="{site_path('quality/index.html')}">Legacy quality dashboard</a><a class="button button--ghost" href="{site_path('archive/index.html#archive-network')}">Archive Network</a></div></header><div class="integrity-note"><h2>Scope boundary</h2><p>{len(ledger)} ledger rows are maintained for the current layer; {ARCHIVE_METRICS["current"]["used_source_ledger_rows"]} are presently attached to entries. The historical archive contains {ARCHIVE_METRICS["totals"]["legacy_source_references"]:,} source references and is being migrated in controlled batches.</p></div><div class="table-wrap"><table><thead><tr><th>ID</th><th>Source</th><th>Date</th><th>Type</th></tr></thead><tbody>{rows}</tbody></table></div></div>'''
    return document(title="Current source ledger · The Record", description=f"Current-layer source ledger for The Record {RELEASE_DATE} release.", body=body, active="method")


def human_key(value: str) -> str:
    rendered = value.replace("_", " ").replace(" or ", " / ").strip().title()
    for before, after in (
        ("Api", "API"), ("Ai", "AI"), ("Qa", "QA"),
        ("Term Ii", "Term II"), ("Term I ", "Term I "),
        ("Url", "URL"), ("Id", "ID"),
    ):
        rendered = rendered.replace(before, after)
    return rendered


def quality_page() -> str:
    totals = ARCHIVE_METRICS["totals"]
    legacy = ARCHIVE_METRICS["legacy"]
    sources = legacy["sources"]
    current = ARCHIVE_METRICS["current"]
    coverage = ARCHIVE_METRICS["coverage"]
    interpretive = legacy["interpretive_layers"]
    remediation = ARCHIVE_METRICS["remediation"]
    federated = ARCHIVE_METRICS["federated"]
    completed_review = sum(
        legacy["review_states"].get(state, 0)
        for state in ("current-standard-reviewed", "corrected")
    )
    awaiting_review = legacy["entries"] - completed_review
    era_rows = "".join(
        f"<tr><td>{esc({'campaign1': 'Campaign 1', 'campaign2': 'Campaign 2', 'term1': 'Term 1', 'term2': 'Term 2', 'post1': 'Post-presidency', 'formation': 'Formation'}.get(era, human_key(era)))}</td><td>{count:,}</td><td>Legacy — not yet revalidated under the current standard</td></tr>"
        for era, count in legacy["eras"].items()
    )
    body = f'''<div class="container"><header class="page-head"><div class="eyebrow">Generated QA inputs updated {esc(ARCHIVE_METRICS["quality_inputs_updated_at"])}</div><h1>Archive quality dashboard</h1><p>Editorial news coverage remains checked through <strong>{esc(ARCHIVE_METRICS["editorial_checked_at"])}</strong>; archive-network measurements were checked through <strong>{esc(ARCHIVE_METRICS["external_registry_checked_at"])}</strong>, and legacy revisions are recorded through <strong>{esc(ARCHIVE_METRICS["legacy_revisions_through"])}</strong>. These totals are generated from canonical JSON. “Legacy-unreviewed” does not mean false; it means the record has not yet been revalidated under the stronger current-layer standard. Missing interpretive layers are measured as work to do, never silently invented.</p><div class="button-row"><a class="button button--primary" href="{site_path('data/archive_metrics.json')}" download>Download metrics JSON</a><a class="button button--ghost" href="{site_path('data/legacy_entries.json')}" download>Download canonical legacy JSON</a><a class="button button--ghost" href="{site_path('data/legacy_revisions.json')}" download>Download revision ledger</a><a class="button button--ghost" href="{site_path('data/federated_records.json')}" download>Download federation crosswalks</a><a class="button button--ghost" href="{site_path('archive/index.html#archive-network')}">Open Archive Network</a></div></header>
<section class="stats" aria-label="Generated archive totals"><div class="stat"><strong>{totals["full_archive_runtime_entries"]:,}</strong><span>active entries rendered in the full archive</span></div><div class="stat"><strong>{totals["full_archive_runtime_source_references"]:,}</strong><span>attached source references</span></div><div class="stat"><strong>{totals["full_archive_runtime_unique_urls"]:,}</strong><span>distinct source URLs</span></div><div class="stat"><strong>{awaiting_review:,}</strong><span>active legacy entries awaiting completed current-standard review</span></div><div class="stat"><strong>{interpretive["maybe_therefore_missing"]:,}</strong><span>active legacy entries awaiting Maybe / Therefore</span></div><div class="stat"><strong>{totals["superseded_legacy_tombstones"]:,}</strong><span>retired duplicate tombstones excluded from totals</span></div></section>
<div class="integrity-note"><h2>Known continuity gap</h2><p>The canonical legacy layer ends {esc(coverage["legacy_last_date"])} and the generated national bridge begins {esc(coverage["current_bridge_first_date"])}. The {coverage["uncovered_days_between_layers"]}-day period <strong>{esc(coverage["known_gap_label"])}</strong> remains disclosed and queued for backfill.</p></div>
<div class="section-head"><div><div class="eyebrow">Evidence health</div><h2>What the generated audit found</h2></div><p>Source presence and source sufficiency are different controls.</p></div><section class="method-grid">
<article class="method-card"><h2>{sources["entries_with_one_source"]:,} single-source entries</h2><p>{sources["entries_with_one_source_percent"]}% of legacy entries currently cite one source. A single direct primary record may be sufficient for a narrow formal fact; otherwise these records enter the remediation queue.</p></article>
<article class="method-card"><h2>{sources["entries_relying_only_on_low_specificity_sources"]:,} weak-link-only entries</h2><p>{sources["entries_relying_only_on_low_specificity_sources_percent"]}% currently rely only on publisher homepages, search results, or query-result pages rather than direct supporting documents.</p></article>
<article class="method-card"><h2>{sources["single_source_low_specificity_entries"]:,} first-priority records</h2><p>These entries combine a single citation with a low-specificity destination. They are the first automated remediation queue—not an allegation that every underlying event is wrong.</p></article>
<article class="method-card"><h2>{sources["unique_domains"]:,} legacy source domains</h2><p>{sources["unique_urls"]:,} unique URLs appear across {sources["references"]:,} legacy source references. Repeated links remain visible rather than inflated into “unique sources.”</p></article>
<article class="method-card"><h2>{legacy["duplicate_candidates"]["exact_text_groups"]} unresolved exact-text duplicate groups</h2><p>Confirmed duplicates are preserved as redirecting tombstones and removed from active totals. Candidate detection is automated; merging remains an editorial action because records can share wording while documenting different lifecycle stages.</p></article>
<article class="method-card"><h2>{current["entries"]} structured current records</h2><p>{current["entries_with_one_source"]} are presently single-source and {current["maybe_therefore_missing"]} still need a separately reviewed Maybe / Therefore field. New federated promotions cannot pass without it.</p></article>
<article class="method-card"><h2>{interpretive["maybe_therefore_present"]:,} Maybe / Therefore layers</h2><p>{interpretive["maybe_therefore_present_percent"]}% of the legacy body already contains the competing-frame layer. The remaining {interpretive["maybe_therefore_missing"]:,} entries are a measured editorial backlog; federation publication now requires this layer.</p></article>
<article class="method-card"><h2>{legacy["duplicate_candidates"]["same_date_heading_groups"]} same-date heading clusters</h2><p>Stable IDs, exact fingerprints, normalized date/title headings, origin IDs, canonical targets, and lifecycle relationships are checked before import. Candidates are linked for review rather than automatically copied or merged.</p></article>
<article class="method-card"><h2>{legacy["duplicate_candidates"]["repeated_heading_any_date_groups"]} repeated-heading review groups</h2><p>These cross-date candidates are queued for adjudication. Repeated headings can represent recurring posts or distinct lifecycle stages, so they are not silently deleted or excluded until a revision names the surviving record or records the distinct-stage decision.</p></article>
<article class="method-card"><h2>{remediation["legacy_revision_records"]:,} logged legacy revisions</h2><p>Every applied correction or mechanical cleanup is recorded in the append-only revision ledger and guarded by its expected prior value.</p></article>
<article class="method-card"><h2>{federated["records"]:,} normalized external crosslinks</h2><p>These are counted separately from canonical entries. No outside item becomes a finding until its evidence, full reasoning structure, provenance, and deduplication checks pass.</p></article>
</section>
<div class="section-head"><div><div class="eyebrow">Coverage by era</div><h2>Active canonical legacy body</h2></div><p><code>data/legacy_entries.json</code> stores {totals["canonical_legacy_rows"]:,} rows: {totals["active_legacy_entries"]:,} active records plus {totals["superseded_legacy_tombstones"]:,} retained tombstones. The era counts below include active records only.</p></div><div class="table-wrap"><table><thead><tr><th>Era</th><th>Entries</th><th>Review state</th></tr></thead><tbody>{era_rows}</tbody></table></div>
<div class="integrity-note"><h2>Definitions and limits</h2><p><strong>Source reference</strong> means one source object attached to one entry; repeated URLs count repeatedly. <strong>Distinct URL</strong> means a unique URL exactly as stored; redirects are not yet collapsed. <strong>Maybe / Therefore</strong> names the strongest plausible defense or uncertainty, then states the evidence-bound consequence, test, or remaining gap. Automated checks identify risk and inconsistency, while human review determines whether an entry is correct, sufficiently sourced, duplicated, corrected, or superseded.</p></div>
<div class="integrity-note"><h2>Separate legacy derivatives</h2><p>The Politicians detail index and companion DOCX/PDF files are frozen or separately generated legacy derivatives. They are not included in the canonical timeline totals and must not be presented as synchronized copies until rebuilt around stable record IDs.</p></div></div>'''
    return document(title="Archive quality · The Record", description="Generated totals, review states, source health, coverage gaps, and remediation progress for The Record.", body=body, active="quality")


def archive_registry_card(archive: dict) -> str:
    measurements = [measurement for measurement in archive.get("measurements", []) if measurement.get("value") is not None]
    metric_rows = "".join(
        f'<li><strong>{measurement["value"]:,} {esc(measurement["as_reported_label"])}</strong><br>'
        f'<span class="micro">Unit: {esc(human_key(measurement["unit"]))} · '
        f'Scope: {esc(measurement["scope"])} · Observed: {esc(measurement["observed_at"])}</span></li>'
        for measurement in measurements
    )
    if not metric_rows:
        metric_rows = '<li><strong>Exact entry total not exposed</strong></li>'
    features = [human_key(name) for name, enabled in archive.get("features", {}).items() if enabled is True]
    feature_text = " · ".join(features[:6])
    warning = ""
    warning_states = str(archive.get("last_check", {}).get("state", ""))
    if "warning" in warning_states or "unavailable" in warning_states:
        warning = f'<p class="micro"><strong>Upstream QA note:</strong> {esc(human_key(warning_states))}. The registry keeps upstream scope, date, and count flags visible rather than silently normalizing them.</p>'
    about_url = archive.get("about_url") or archive["homepage_url"]
    historical_note = archive.get("scope", {}).get("observed_historical_outliers", {}).get("note", "")
    stated_period = archive.get("scope", {}).get("stated_primary_period", {})
    period_text = "–".join(
        str(stated_period.get(key) or "") for key in ("start", "end")
    ).strip("–")
    return f'''<article class="route-card"><div class="eyebrow">{esc(human_key(archive["source_class"]))}</div><h3>{esc(archive["name"])}</h3><p>{esc(archive["self_description"])}</p><ul>{metric_rows}</ul><p class="micro"><strong>Archive unit:</strong> {esc(archive["scope"]["record_unit"])}<br><strong>Stated primary period:</strong> {esc(period_text or "not stated")}<br><strong>Best used for:</strong> {esc(feature_text)}{f'<br><strong>Coverage caveat:</strong> {esc(historical_note)}' if historical_note else ''}<br><strong>Registry check:</strong> {esc(archive.get("last_check", {}).get("checked_at", "not recorded"))}</p>{warning}<div class="card-actions"><a class="button button--primary" href="{esc(archive["browse_url"], quote=True)}" target="_blank" rel="noopener">Open source archive</a><a class="button button--ghost" href="{esc(about_url, quote=True)}" target="_blank" rel="noopener">Method / about</a></div></article>'''


def federated_record_card(record: dict) -> str:
    origins = "".join(
        f'<li><a href="{esc(origin["external_url"], quote=True)}" target="_blank" rel="noopener">{esc(human_key(origin["archive_id"]))} · {esc(origin["external_record_unit"])}</a></li>'
        for origin in record.get("origins", [])
    )
    sources = "".join(
        f'<li><a href="{esc(source["url"], quote=True)}" target="_blank" rel="noopener">{esc(source["title"])}</a><span>{esc(source["source_type"])}</span></li>'
        for source in record.get("sources", [])
    )
    canonical_id = record.get("counting", {}).get("canonical_the_record_entry_id")
    canonical_link = (
        f'<a class="button button--primary" href="{site_path(f"the-record.html#{esc(canonical_id, quote=True)}")}">Open canonical record</a>'
        if canonical_id
        else ""
    )
    maybe = record.get("maybe_therefore") or {}
    maybe_text = maybe.get("text") if isinstance(maybe, dict) else ""
    evidence = record.get("evidence") or {}
    provenance = record.get("provenance") or {}
    publicly_authorized = bool(
        record.get("status") == "published"
        and evidence.get("human_reviewed")
        and provenance.get("publication_authorized")
    )
    head = f'''<div class="record-card__head"><div><div class="eyebrow">{esc(record["record_id"])} · {esc(record["event_date"])}</div><h2>{esc(record["title"])}</h2><p class="micro"><strong>Count disposition:</strong> {esc(human_key(record.get("counting", {}).get("count_disposition", "unknown")))} · <strong>Evidence:</strong> {esc(human_key(evidence.get("evidence_state", "unknown")))} / {esc(human_key(evidence.get("confidence", "unknown")))} · <strong>Human reviewed:</strong> {"yes" if evidence.get("human_reviewed") else "no"}</p></div><span class="status-pill">{esc(human_key(record["status"]))}</span></div>'''
    if not publicly_authorized:
        return f'''<article class="record-card" id="{esc(record["record_id"], quote=True)}">{head}<div class="integrity-note"><h3>Staged research data—not a finding</h3><p>The raw normalized JSON is deliberately public for auditability and contains substantive draft Facts / Significance / Goalpost / Maybe / Therefore fields. Those fields are unreviewed, unauthorized for canonical publication, excluded from every canonical total, and not presented as a finding. This page exposes origin and workflow metadata without rendering the draft as accepted analysis.</p></div><section class="layer layer--facts"><h3>Federated origins</h3><ul>{origins}</ul></section><details class="sources"><summary>Inspected source list and provenance state</summary><ul>{sources}</ul><p class="micro">Created {esc(provenance.get("created_at", "not recorded"))} · last modified {esc(provenance.get("last_modified_at", "not recorded"))} · human reviewed: no · publication authorized: no · canonical count: excluded.</p></details><div class="card-actions">{canonical_link}<a class="button button--ghost" href="{site_path('data/federated_records.json')}" download>Inspect unreviewed draft JSON</a></div></article>'''

    claims = "".join(
        f'<li><strong>{esc(claim.get("claim_status", "unknown"))}:</strong> {esc(claim.get("text", ""))}</li>'
        for claim in (record.get("facts") or {}).get("claims", [])
    )
    limitations = "".join(f"<li>{esc(item)}</li>" for item in evidence.get("limitations", []))
    consequences = "".join(
        f'<li>{esc(item.get("text", ""))} <span class="micro">({esc(item.get("observation_state", "unknown"))}; causal confidence {esc(item.get("causal_confidence", "unknown"))})</span></li>'
        for item in record.get("consequences", [])
    )
    revisions = "".join(
        f'<li><strong>{esc(item.get("timestamp", ""))}</strong> — {esc(item.get("summary", ""))}</li>'
        for item in record.get("revisions", [])
    )
    return f'''<article class="record-card" id="{esc(record["record_id"], quote=True)}">{head}<div class="three-layer"><section class="layer layer--facts"><h3>The facts</h3><ul>{claims}</ul><p class="micro">{esc((record.get("facts") or {}).get("scope_note", ""))}</p></section><section class="layer layer--significance"><h3>Significance</h3><p>{esc((record.get("significance") or {}).get("text", ""))}</p></section><section class="layer layer--goalpost"><h3>Goalpost / response</h3><p>{esc((record.get("goalpost_response") or {}).get("text", ""))}</p></section><section class="layer layer--goalpost"><h3>Maybe / Therefore</h3><p>{esc(maybe_text)}</p></section></div><section class="layer layer--facts"><h3>Consequences</h3><ul>{consequences}</ul></section><details class="sources"><summary>Evidence, limitations, origins, provenance, and revisions</summary><h3>Underlying evidence</h3><ul>{sources}</ul><h3>Federated origins</h3><ul>{origins}</ul><h3>Limitations</h3><ul>{limitations}</ul><h3>Revision history</h3><ul>{revisions}</ul><p class="micro">Created {esc(provenance.get("created_at", "not recorded"))} · last modified {esc(provenance.get("last_modified_at", "not recorded"))} · publication authorized: yes.</p></details><div class="card-actions">{canonical_link}</div></article>'''


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def download_card(title: str, text: str, href: str, digest: str, label: str) -> str:
    return f'''<article class="download-card"><div class="eyebrow">Download</div><h3>{esc(title)}</h3><p>{esc(text)}</p><p class="micro">SHA-256: <code>{digest[:16]}…</code></p><a class="button button--primary" href="{esc(href, quote=True)}" download>{esc(label)}</a></article>'''


def downloads_page(entries: list[dict]) -> str:
    national_count = sum(entry["scope"] == "national" for entry in entries)
    in6_count = sum(entry["scope"] == "in6" for entry in entries)
    ledger_count = len(json.loads((ROOT / "data/source_ledger.json").read_text(encoding="utf-8")))
    featured = [
        (f"Complete {RELEASE_DATE} update", f"All {len(entries)} entry packs, the national brief, source ledgers, machine-readable data, and the run receipt.", site_path(f"artifacts/{COMPLETE_PACK_NAME}"), ROOT / "artifacts" / COMPLETE_PACK_NAME, "Download complete update"),
        ("National current brief", f"All {national_count} national entries, including {len(NEW_ENTRY_IDS)} records added in this pass, with individual packs and the source ledger.", site_path(f"artifacts/{NATIONAL_PACK_NAME}"), ROOT / "artifacts" / NATIONAL_PACK_NAME, "Download national pack"),
        ("IN-6 current brief", f"The {in6_count} IN-6 records remain preserved from the July 18 package; this run’s requested scope was the national Trump record.", site_path("artifacts/THE_RECORD_IN6_UPDATE_PACK_2026-07-18.zip"), ROOT / "artifacts/THE_RECORD_IN6_UPDATE_PACK_2026-07-18.zip", "Download IN-6 pack"),
        ("Current-entry data", f"All {len(entries)} dated entries in one JSON file for reuse in future builds or research tools.", site_path("data/current_entries.json"), ROOT / "data/current_entries.json", "Download entry JSON"),
        ("Source ledger CSV", f"A flat audit table of all {ledger_count} sources linked in this current layer.", site_path("data/source_ledger.csv"), ROOT / "data/source_ledger.csv", "Download source CSV"),
        ("Artifact checksums", "SHA-256 values for release artifacts, including every individual entry pack.", site_path("artifacts/SHA256SUMS.txt"), ROOT / "artifacts/SHA256SUMS.txt", "Download checksums"),
    ]
    featured_html = "".join(download_card(title, text, href, sha(path), label) for title, text, href, path, label in featured)
    individual_html = "".join(
        download_card(entry["title"], entry["dek"], site_path(entry["pack_path"]), sha(ROOT / entry["pack_path"]), "Download this entry")
        for entry in sorted(entries, key=lambda entry: (entry["date"], entry["id"]), reverse=True)
    )
    body = f'''<div class="container"><header class="page-head"><div class="eyebrow">Portable evidence</div><h1>Read it here. Download it here.</h1><p>Every major section and every individual update is available without hunting through a repository. Each entry pack contains readable Markdown, JSON, source data, and a checksum.</p></header><section class="download-grid">{featured_html}</section><div class="section-head"><div><div class="eyebrow">Individual records</div><h2>One entry, one direct download</h2></div><p>The same information block shown on the site is packaged for offline review and reuse.</p></div><section class="download-grid">{individual_html}</section><div class="integrity-note"><h2>Preserved July 18 packages</h2><p>The original candidate packages remain unchanged: <a href="{site_path('artifacts/THE_RECORD_JULY_18_UPDATE_PACK_2026-07-18.zip')}" download>complete July 18</a> · <a href="{site_path('artifacts/THE_RECORD_NATIONAL_UPDATE_PACK_2026-07-18.zip')}" download>national July 18</a> · <a href="{site_path('artifacts/THE_RECORD_IN6_UPDATE_PACK_2026-07-18.zip')}" download>IN-6 July 18</a>.</p></div></div>'''
    return document(title="Downloads · The Record", description=f"Download The Record {RELEASE_DATE} update and individual entries.", body=body, active="downloads")


def methodology_page(entries: list[dict]) -> str:
    totals = ARCHIVE_METRICS["totals"]
    legacy = ARCHIVE_METRICS["legacy"]
    coverage = ARCHIVE_METRICS["coverage"]
    body = f'''<div class="container"><header class="page-head"><div class="eyebrow">Methodology</div><h1>Facts are not analysis. Official claims are not independent verification.</h1><p>The Record’s value depends on keeping those categories visible, preserving corrections, and refusing to turn a large archive into an unreviewable claim of completeness.</p></header>
<section class="method-grid">
<article class="method-card"><h2>1. The three-layer entry</h2><p><strong>THE FACTS</strong> records the sourced event. <strong>SIGNIFICANCE</strong> states the editor’s contextual analysis. <strong>GOALPOST / RESPONSE</strong> records the strongest relevant defense, explanation, or shifting rhetorical frame without treating it as established fact.</p></article>
<article class="method-card"><h2>2. Source hierarchy</h2><p>Primary legal documents, official roll calls, bill text, and agency records are preferred for what an institution formally did. Independent reporting is used to corroborate, supply context, and identify disputes. Official press releases establish the speaker’s position—not the truth of every claim inside the release.</p></article>
<article class="method-card"><h2>3. Currentness</h2><p>Every release has a visible checked time. Relative words such as “today” are avoided inside durable entries. A current brief never implies that the entire historical archive was revalidated in the same pass.</p></article>
<article class="method-card"><h2>4. Corrections and reply</h2><p>Send the entry ID, disputed wording, and supporting documentation to the project address. Corrections identify what changed and when. A materially relevant response from an affected office or candidate is attached to the relevant entry rather than hidden in a separate page.</p></article>
<article class="method-card"><h2>5. Generated totals and review states</h2><p>The canonical file stores {totals["canonical_legacy_rows"]:,} legacy rows: {totals["active_legacy_entries"]:,} active records and {totals["superseded_legacy_tombstones"]:,} retained duplicate tombstones. The national bridge adds {totals["bridged_national_entries"]}, producing {totals["full_archive_runtime_entries"]:,} active records at runtime. Tombstones redirect old IDs but never enter search, source totals, or the event count. The same build counts {totals["full_archive_runtime_source_references"]:,} source references and {totals["full_archive_runtime_unique_urls"]:,} distinct stored URLs.</p></article>
<article class="method-card" id="ai-disclosure"><h2>6. AI disclosure &amp; provenance</h2><p>Current research organization, drafting support, code, and adversarial review use <strong>ChatGPT 5.6 Sol Max</strong> and <strong>Claude Fable 5 Max (Cowork)</strong>. Phillip Linstrum is the acceptance authority for canonical publication. AI output is not a source.</p><p>For auditability, the public federation JSON may expose substantive AI-assisted research drafts before review. Public accessibility does not make them published findings: staged drafts are labeled unreviewed, unauthorized for canonical publication, excluded from canonical totals, and not rendered as accepted analysis. The five April 2026 AI Opinion essays retain their original attribution to <strong>Claude (Anthropic, Opus 4)</strong>. This {RELEASE_DATE} pass updates the surrounding maintenance disclosure; it does not silently reassign or rewrite those essays’ authorship. See <a href="{site_path('AI_PROVENANCE.md')}">the provenance record</a>.</p></article>
</section>
<div class="integrity-note"><h2>Scope of this release</h2><p>This release contains {len(entries)} dated current-layer entries, including {len(NEW_ENTRY_IDS)} national records added or materially refreshed in the August 17–24 backfill. It does not certify the complete legacy archive, independently validate every historical source, or resolve all open IN-6 claims. The {coverage["uncovered_days_between_layers"]}-day continuity gap ({esc(coverage["known_gap_label"])}) remains disclosed pending backfill. See the <a href="{site_path('quality/index.html')}">generated quality dashboard</a>.</p></div>
<h2>Publication rules</h2><pre class="code-note">NO SOURCE → NO FACT CLAIM
OFFICIAL STATEMENT → WHAT THE INSTITUTION SAYS
INDEPENDENT REPORTING → CORROBORATION AND CONTEXT
ANALYSIS → LABELED
EXACT COUNT → GENERATED FROM CANONICAL DATA
CORRECTION → TIMESTAMPED AND PRESERVED</pre></div>'''
    return document(title="Methodology · The Record", description="Evidence, correction, currentness, and AI rules for The Record.", body=body, active="method")


def home_page(entries: list[dict], ledger: dict) -> str:
    national_count = sum(entry["scope"] == "national" for entry in entries)
    totals = ARCHIVE_METRICS["totals"]
    weekly = sorted(
        (entry for entry in entries if WEEK_START <= entry["date"] <= WEEK_END),
        key=lambda entry: (entry["date"], entry["id"]), reverse=True
    )
    weekly_links = "".join(
        f'<li><span class="chip">{"National" if entry["scope"] == "national" else "IN-6"}</span><a href="{site_path(entry["scope"] + "/index.html#" + esc(entry["id"], quote=True))}">{esc(entry["title"])}</a></li>'
        for entry in weekly[:5]
    )
    body = f'''<section class="hero"><div class="hero-inner"><div><div class="kicker">A living Trump accountability archive · updated {RELEASE_DATE}</div><h1>The full searchable archive, not just the latest headline.</h1><p>This page is the editorial front door: a concise view of newly verified developments. The full searchable archive currently renders {totals["full_archive_runtime_entries"]:,} active dated entries with {totals["full_archive_runtime_source_references"]:,} attached source references across years, topics, people, institutions, and the timeline; its known gaps and legacy review backlog remain disclosed.</p><div class="hero-actions"><a class="button button--primary" href="{site_path('the-record.html#home')}">Enter the full archive</a><a class="button button--secondary" href="{site_path('the-record.html#timeline')}">Search the timeline</a><a class="button button--ghost" href="{site_path('weekly/index.html')}">Latest seven days</a></div></div><aside class="hero-stamp"><div class="eyebrow">Archive state</div><strong>Current through {CHECKED_AT}</strong><p>{len(NEW_ENTRY_IDS)} national records were added or materially refreshed in this editorial release. The quality layer was maintained separately without implying a later news cutoff.</p></aside></div><figure class="hero-art"><img src="{site_path('assets/brand/the-record-hero.png')}" alt="An illuminated evidence archive connecting sourced records across a living accountability timeline" width="1672" height="941" fetchpriority="high" decoding="async"></figure></section>
<div class="container"><section class="stats" aria-label="Archive and release statistics"><div class="stat"><strong>{totals["full_archive_runtime_entries"]:,}</strong><span>generated full-archive entries</span></div><div class="stat"><strong>{totals["full_archive_runtime_unique_urls"]:,}</strong><span>distinct full-archive source URLs</span></div><div class="stat"><strong>{national_count}</strong><span>verified current national entries</span></div><div class="stat"><strong>{len(weekly)}</strong><span>records in this seven-day window</span></div></section>
<section class="archive-feature"><div class="archive-feature__copy"><div class="eyebrow">The research layer</div><h2>The archive is where the whole project lives.</h2><p>The landing page stays readable by showing a curated current layer. The archive brings historical entries, sources, topic folders, people, statistics, methodology, current additions, and Trump's raw Truth Social feed into one searchable application, while the quality dashboard discloses review backlogs and known gaps.</p><div class="button-row"><a class="button button--primary" href="{site_path('the-record.html#home')}">Browse the archive</a><a class="button button--ghost" href="{site_path('the-record.html#timeline')}">Open the full timeline</a><a class="button button--ghost" href="{site_path('archive/index.html#archive-network')}">Explore the Archive Network</a></div></div><div class="archive-paths" aria-label="Archive research paths"><a href="{site_path('the-record.html#topics')}"><strong>Topics</strong><span>Courts, democracy, immigration, media, foreign influence, and more</span></a><a href="{site_path('the-record.html#years')}"><strong>Years</strong><span>Move through covered dates from 1927 into the current term; see Quality for known gaps</span></a><a href="{site_path('the-record.html#politicians')}"><strong>People</strong><span>Find officeholders, advisers, opponents, and connected events</span></a><a href="{site_path('the-record.html#timeline')}"><strong>Search</strong><span>Query dates, names, agencies, events, and source-linked entries</span></a><a href="{site_path('the-record.html#feed')}"><strong>Truth Social</strong><span>Search the raw public posting record without turning every post into an archive finding</span></a><a href="{site_path('quality/index.html')}"><strong>Quality</strong><span>Inspect generated counts, source health, review status, and known coverage gaps</span></a></div></section>
<section class="weekly-highlight"><div><div class="eyebrow">What happened this week</div><h2>{len(weekly)} records · {WEEK_LABEL}</h2><p>A compact, fixed seven-day window. Use it for the latest signal; use the full searchable archive for the broader record, with known gaps and review state disclosed.</p><a class="button button--primary" href="{site_path('weekly/index.html')}">Open the weekly record</a></div><ul>{weekly_links}</ul></section>
<div class="section-head"><div><div class="eyebrow">Current layer</div><h2>Focused views for the newest material</h2></div><p>These pages summarize and package recent verified additions. They do not create a second count for records already bridged into the searchable archive.</p></div><section class="route-grid">
<article class="route-card"><div class="eyebrow">Latest</div><h3>National current record</h3><p>{national_count} sourced developments, each separated into facts, significance, and the administration’s response.</p><a class="button button--ghost" href="{site_path('national/index.html')}">Open latest national</a></article>
<article class="route-card"><div class="eyebrow">Weekly</div><h3>What happened this week</h3><p>{len(weekly)} current records in a stable {WEEK_LABEL} window, with scope filters and search.</p><a class="button button--ghost" href="{site_path('weekly/index.html')}">Open weekly</a></article>
<article class="route-card"><div class="eyebrow">Power map</div><h3>Agencies &amp; institutions</h3><p>See which public bodies acted, what authority they used, and every current record linked to them.</p><a class="button button--ghost" href="{site_path('agencies/index.html')}">Browse agencies</a></article>
<article class="route-card"><div class="eyebrow">District</div><h3>IN-6 representation audit</h3><p>House votes, appropriations activity, committee power, and verified election status for Indiana’s Sixth District.</p><a class="button button--ghost" href="{site_path('in6/index.html')}">Open IN-6</a></article>
<article class="route-card"><div class="eyebrow">Integrity</div><h3>Method &amp; AI provenance</h3><p>Read the evidence rules, correction process, exact current AI disclosure, and legacy essay provenance.</p><a class="button button--ghost" href="{site_path('methodology/index.html')}">Read the method</a></article>
<article class="route-card"><div class="eyebrow">Portable</div><h3>Downloads &amp; source ledger</h3><p>Download the current package or inspect every primary, official, and independent source in the current layer.</p><div class="card-actions"><a class="button button--ghost" href="{site_path('downloads/index.html')}">Downloads</a><a class="button button--ghost" href="{site_path('sources/index.html')}">Sources</a></div></article>
</section><div class="integrity-note"><h2>Generated count rule</h2><p>The public totals now come from <code>data/legacy_entries.json</code>, the national current bridge, and a deterministic metrics build. The <a href="{site_path('quality/index.html')}">quality dashboard</a> shows exactly what is counted, what remains legacy-unreviewed, and where the source and coverage risks are.</p></div></div>'''
    return document(title=f"The Record · Trump Accountability Archive", description=f"The Record is a living, searchable Trump accountability archive, current through {CHECKED_AT}.", body=body, active="home")


def archive_page() -> str:
    totals = ARCHIVE_METRICS["totals"]
    external_cards = "".join(archive_registry_card(archive) for archive in ARCHIVE_REGISTRY["archives"])
    adoption_cards = "".join(
        f'''<article class="method-card"><div class="eyebrow">Adopt from {esc(item["inspiration"])}</div><h2>{esc(human_key(item["feature"]))}</h2><p>{esc(item["recommendation"])}</p></article>'''
        for item in sorted(ARCHIVE_REGISTRY["recommended_feature_adoption"], key=lambda item: item["priority"])
    )
    visible_federated = [
        record for record in FEDERATED_RECORDS
        if record.get("status") not in {"research_lead", "superseded"}
    ]
    published_federated = [record for record in visible_federated if record.get("status") == "published"]
    staged_federated = [record for record in visible_federated if record.get("status") != "published"]
    if visible_federated:
        federation_results = "".join(federated_record_card(record) for record in visible_federated)
    else:
        federation_results = '<div class="integrity-note"><h2>No normalized crosslink has cleared publication yet</h2><p>The gate is operating as intended: directory discovery alone is insufficient. A record appears here only after source inspection, complete Maybe / Therefore reasoning, duplicate and lifecycle review, and editorial authorization.</p></div>'
    body = f'''<div class="container"><header class="page-head"><div class="eyebrow">One research home · different evidence units preserved</div><h1>The Archive Network</h1><p>The Record is the broad narrative accountability layer. Independent archives add raw statements, confirmed policy actions, immigration expertise, primary documents, contradictions, sequences, and revision history. The intake system connects those strengths and requires every canonically published promotion to meet The Record’s evidence and reasoning structure—including Maybe / Therefore—without pretending unlike record types can be added into one grand total.</p><div class="button-row"><a class="button button--primary" href="{site_path('the-record.html#home')}">Enter The Record</a><a class="button button--ghost" href="{site_path('data/archive_registry.json')}" download>Download registry JSON</a><a class="button button--ghost" href="{site_path('data/federated_records.json')}" download>Download normalized crosslinks</a><a class="button button--ghost" href="{site_path('quality/index.html')}">View generated QA totals</a></div></header>
<section class="stats" aria-label="The Record generated totals"><div class="stat"><strong>{totals["full_archive_runtime_entries"]:,}</strong><span>The Record entries at runtime</span></div><div class="stat"><strong>{totals["full_archive_runtime_source_references"]:,}</strong><span>attached source references</span></div><div class="stat"><strong>{totals["full_archive_runtime_unique_urls"]:,}</strong><span>distinct source URLs</span></div><div class="stat"><strong>{len(ARCHIVE_REGISTRY["archives"])}</strong><span>independent archives in the network registry</span></div><div class="stat"><strong>{len(staged_federated)}</strong><span>normalized crosslinks awaiting editor review</span></div><div class="stat"><strong>{len(published_federated)}</strong><span>published normalized crosslinks</span></div></section>
<section class="download-grid"><article class="download-card"><div class="eyebrow">Primary narrative archive · current {RELEASE_DATE}</div><h3>The Record</h3><p>{totals["active_legacy_entries"]:,} active canonical historical records plus {totals["bridged_national_entries"]} current national records, organized by date, topic, person, evidence, significance, and response. {totals["superseded_legacy_tombstones"]} retired duplicate IDs remain available only as audit redirects.</p><a class="button button--primary" href="{site_path('the-record.html#home')}">Open The Record</a><p class="micro"><a href="{site_path('the-record.html#timeline')}">Timeline</a> · <a href="{site_path('the-record.html#feed')}">Truth Social</a> · <a href="{site_path('quality/index.html')}">Quality dashboard</a></p></article>
<article class="download-card"><div class="eyebrow">Indiana 6th</div><h3>IN-6 representation audit</h3><p>The district archive covers votes, candidates, appropriations, district data, and representation accountability without inflating the national Trump-archive total.</p><a class="button button--primary" href="https://pausebeforeharmprotocol.github.io/the-record-in6/" target="_blank" rel="noopener">Open IN-6 archive</a></article>
</section>
<div class="section-head" id="archive-network"><div><div class="eyebrow">Federated discovery</div><h2>Independent Trump-related archives</h2></div><p>Counts are snapshots, always shown with their own unit and scope.</p></div><section class="route-grid">{external_cards}</section>
<div class="integrity-note"><h2>Federation and duplicate boundary</h2><p>External records enter a normalized research-lead queue, not the published count. Promotion requires a stable origin ID, source review, evidence and confidence states, facts, significance, goalpost / response, Maybe / Therefore, consequences, revision provenance, and a duplicate/lifecycle decision. Matching records are crosslinked to one canonical event rather than copied. Counts from different comparability groups are never summed.</p></div>
<div class="section-head"><div><div class="eyebrow">Normalized crosslinks</div><h2>External evidence brought into the full Record structure</h2></div><p>Status is explicit. Raw staged JSON is public for auditability, but its substantive fields remain unreviewed, unauthorized for canonical publication, uncounted, and not findings. Accepted links reuse an existing canonical ID when the underlying event is already present, so one event remains one count.</p></div>{federation_results}
<div class="section-head"><div><div class="eyebrow">Best ideas, combined carefully</div><h2>Capabilities being brought home</h2></div><p>Each feature keeps its own evidence and lifecycle controls.</p></div><section class="method-grid">{adoption_cards}</section>
<div class="integrity-note"><h2>Preservation rule</h2><p><code>data/legacy_entries.json</code> is now the canonical historical body. The root and <code>docs/</code> HTML custody representations retain active rows and superseded tombstones so retired permalinks keep working; the generated <code>entries_array.js</code> compatibility view contains active rows only so downstream consumers cannot double-count retired records. Companion DOCX/PDF files remain dated snapshots until their separate rebuild path is restored.</p></div></div>'''
    return document(title="Archive Network · The Record", description="The Record and a federated directory of independent Trump archives, with scope-aware counts and provenance.", body=body, active="archive")


def not_found_page() -> str:
    body = f'''<div class="container"><header class="page-head"><div class="eyebrow">404</div><h1>That record path does not exist.</h1><p>Return to the editorial front page or search the full archive.</p><div class="button-row"><a class="button button--primary" href="{site_path('index.html')}">Return home</a><a class="button button--ghost" href="{site_path('the-record.html#timeline')}">Search the archive</a></div></header></div>'''
    return document(title="Not found · The Record", description="Page not found.", body=body, active="")


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
        ROOT / "quality/index.html": quality_page(),
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
