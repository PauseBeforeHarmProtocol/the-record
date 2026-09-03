<p align="center">
  <img src="assets/brand/the-record-hero.png" alt="An illuminated evidence archive connecting sourced records across a living accountability timeline" width="100%">
</p>

<h1 align="center">The Record</h1>

<p align="center"><strong>Sources, reasoning, corrections, and review state made visible.</strong></p>

<p align="center">
  <a href="index.html">Open the current front door</a> ·
  <a href="the-record.html#home">Enter the full archive</a> ·
  <a href="weekly/index.html">Weekly record</a> ·
  <a href="national/index.html">National record</a> ·
  <a href="in6/index.html">IN-6</a> ·
  <a href="agencies/index.html">Agencies</a> ·
  <a href="quality/index.html">Quality</a> ·
  <a href="sources/index.html">Source ledger</a> ·
  <a href="archive/index.html">Archive Network</a> ·
  <a href="downloads/index.html">Downloads</a>
</p>

The Record pairs a concise, source-bound editorial front page with a full searchable chronological accountability archive. The archive remains the project’s primary research body, receives qualifying current national additions through a small generated live bridge, and includes a separate searchable Truth Social feed that does not treat raw posts as verified archive findings. Exact totals, review backlogs, retired duplicates, and coverage status below are generated from the same canonical data that powers the published archive.

---

<!-- GENERATED_ARCHIVE_METRICS_START -->
## Generated Scope and Quality Snapshot

Generated deterministically from canonical JSON for maintenance release **10.19.0**. Editorial news currentness was checked **2026-09-03 6:02 PM EDT**; QA inputs were updated **2026-09-03T22:02:32Z**.

| Measure | Exact count |
|---|---:|
| Canonical legacy rows stored | 4,742 |
| Active canonical legacy entries | 4,731 |
| Superseded duplicate tombstones (excluded from totals/search) | 11 |
| Current national entries bridged into the archive | 118 |
| Full archive entries rendered at runtime | 4,849 |
| Attached source references at runtime | 7,027 |
| Distinct stored source URLs at runtime | 5,639 |
| Current entries with Maybe / Therefore | 122 |
| Current entries awaiting Maybe / Therefore | 0 |
| Current entries explicitly reviewed or corrected | 122 |
| Current entries pending current-standard review | 0 |
| Legacy entries with Maybe / Therefore | 1,533 |
| Legacy entries awaiting Maybe / Therefore | 3,198 |
| Logged legacy revision records | 147 |
| Normalized external crosslinks | 1 |

Active legacy review states: **corrected: 7, in-review: 7, legacy-unreviewed: 4,717**. “Legacy-unreviewed” means not yet revalidated under the current standard; it does not mean false. Superseded rows remain available as stable audit redirects but do not count as active events. The canonical legacy layer and generated current bridge overlap; the generated metric detects **no inter-layer continuity gap**.

### The Six Eras

| Era | Active canonical legacy entries |
|---|---:|
| Formation | 352 |
| Campaign 1 | 526 |
| Term 1 | 1,638 |
| Post-presidency | 465 |
| Campaign 2 | 628 |
| Term 2 | 1,122 |

Counts from other archives are shown with their own units in the [Archive Network](archive/index.html#archive-network) and are never added to The Record’s totals. See the [Quality dashboard](quality/index.html) for definitions, source-health measures, duplicate candidates, and the remediation backlog.
<!-- GENERATED_ARCHIVE_METRICS_END -->

---

## What This Is

The Record is a single-file HTML application (listed as the-record.html in repo) whose dated coverage runs from his father Fred’s 1927 KKK-rally arrest into the current presidential term. It is a broad archive, not a claim of gap-free coverage: the generated Quality dashboard discloses coverage continuity status, source-health risks, and review backlog. Entries use a labeled reasoning format whose migration status is visible:

- **THE FACTS** — What happened, sourced to major news organizations, court filings, congressional records, and official government documents.
- **SIGNIFICANCE** — Why it matters in historical and political context.
- **GOALPOST** — The rhetorical defense used to normalize it, documented as observed talking points — not straw men.
- **MAYBE / THEREFORE** — The strongest plausible competing frame or uncertainty, followed by the evidence-bound consequence, falsifier, or remaining test. Older entries missing this layer remain in the measured remediation queue.

The current standard keeps editorial interpretation out of the fact layer, labels analysis, and exposes older records that still await revalidation against that standard.

## Entry Types

**Specific Event entries** document a particular event on a particular date with verifiable facts. **Context entries** (marked with a purple border) document broader patterns, periods, or systemic developments that span time ranges. Both types use the same labeled format once migrated under the current standard.

## Sourcing Standards

Every canonical legacy entry contains at least one stored source reference. Source presence is not the same as source sufficiency: the generated Quality dashboard separately measures direct links, low-specificity links, single-source records, review states, duplicate candidates, and revision progress. New and federated records must preserve source provenance and cannot advance from research lead to publication until their evidence and duplicate checks pass.

## Companion Documents

The repository preserves 34 dated companion DOCX documents. They are legacy derivatives, not part of the generated canonical totals, until their rebuild path is restored around stable record IDs:

- **6 era documents** — One per historical era
- **16 topic documents** — Courts, Democracy, Media, January 6, Epstein, Foreign Influence, DOGE, Policy, and more
- **5 AI opinion essays** — Clearly labeled AI-generated analysis on Trump, MAGA, the GOP, media, and democracy
- **7 reference documents** — Methodology, editorial approach, politicians, people mentioned, and internal audits

The preserved set was compiled into a master PDF (THE-RECORD-COMPLETE.pdf, ~2,900 pages). Its snapshot date and contents should not be treated as current parity with the live archive.

## AI Transparency

Current maintenance uses two AI systems:

- **ChatGPT 5.6 Sol Max** (OpenAI) — Independent auditing, analysis, code, and adversarial review
- **Claude Fable 5 Max (Cowork)** — Research organization, drafting support, code, and quality review

Phillip Linstrum is the acceptance authority for canonical publication. A canonical finding cannot be published until it has received the required editorial review and authorization. For auditability, the public machine-readable federation dataset may also expose clearly labeled AI-assisted research-draft JSON before review. Those staged fields are **unreviewed, unauthorized for canonical publication, uncounted, and not presented as findings**. The five April 2026 AI Opinion essays retain their original **Claude (Anthropic, Opus 4)** attribution; current model names are not silently substituted as authors. See [AI_PROVENANCE.md](AI_PROVENANCE.md). AI output is not a source.

## The Record Companion AI

Have questions? Ask **[The Record Companion AI](https://chatgpt.com/g/g-69d0fd0d49cc819184d7d0494471a3aa-the-record-companion-ai)** — a custom GPT based on a preserved master-document snapshot. It can help navigate that snapshot, but its answers are not archive findings and may not reflect the latest live records or corrections.

## The Pause Before Harm Protocol

This project operates under the **[Pause Before Harm Protocol](https://github.com/PauseBeforeHarmProtocol/pbhp)** (PBHP) — an open-source harm-reduction framework for AI and human decision-making.

PBHP asks: *“If I’m wrong, who pays first — and can they recover?”*

Applied to The Record, PBHP sets the current editorial standard:
- New or current-standard-reviewed entries identify who may bear the documented harms; legacy entries are being migrated to that standard
- Language must maintain “brutal clarity with zero contempt” — no mockery, no dehumanization
- The archive must be transparent about its own methods, limitations, and potential biases

## Technical Details

The historical application remains a portable HTML archive (~14 MB). On the published site, a small generated JavaScript bridge supplies the current national layer without rewriting the historical application on every six-hour run.

**Architecture:**
- `data/legacy_entries.json` — the only canonical editable legacy timeline dataset
- root `the-record.html` and `docs/the-record.html` — generated custody representations containing active rows and retained tombstones
- `entries_array.js` — generated active-only compatibility view; superseded tombstones are deliberately excluded to prevent downstream double-counting
- `data/archive_metrics.json` — deterministic totals, evidence-health measures, reasoning-layer completeness, duplicate candidates, and coverage status
- `data/archive_registry.json` — scope-aware registry for independent archives and their fundamentally different units
- `data/federated_records.json` — normalized external crosslinks; raw staged drafts may be public for auditability, but are explicitly unreviewed, publication-unauthorized, uncounted, and never treated as findings without review and deduplication
- `data/legacy_revisions.json` — append-only ledger for historical corrections and cleanups
- `data/current_entries.json` — structured current-layer national and IN-6 records
- `current_layer_bridge.js` — generated national entries and release metadata consumed by the full archive
- `data/truth_social_seed.json` — recent verified fallback for the live Truth Social feed
- `assets/truth-feed.js` — safe live-feed loader, search, year filters, and fallback behavior
- `scripts/update_truth_social_feed.py` — validates the public mirror and refreshes the local fallback
- `data/release.json` — the single release date, checked time, weekly window, and new-entry manifest used by every builder
- `scripts/sync_legacy_data.py` — schema, stable-ID, exact-duplicate, and generated-representation gate
- `scripts/apply_legacy_remediations.py` — idempotent append-only correction applier with expected-old-value guards
- `scripts/build_archive_metrics.py` / `scripts/sync_readme_metrics.py` — generate public totals and keep this README synchronized
- `scripts/validate_federated_records.py` — blocks duplicate promoted crosslinks and incomplete Maybe / Therefore records
- `EDITORIAL_AUTOMATION.md` — the no-padding publication threshold, correction rule, and six-hour maintenance workflow
- `tag_rules.js` — Automated topic classification rules
- `ai_essays.json` — AI-generated opinion content
- `politicians_all.json` / `pol_data_merged.json` — Politician profiles and cross-references
- `build_html.py` — Build pipeline that compiles everything into the single HTML file
- DOCX generators (Node.js) — 10 scripts that produce the 34 companion documents
- `gen_master_pdf.py` — Compiles all DOCX files into the master PDF

**Current front-door navigation:** Home, The Archive, Truth Social, Latest, Weekly, IN-6, Agencies, Quality, Method, Downloads

**Currentness:** generated from `data/release.json`. The release receipt records both published and withheld candidates.

**Full archive navigation:** Latest highlights, Home, Browse by Topic, Browse by Year, Full Timeline, Politicians, AI Opinion, Methodology, About, Search The Record

## Corrections & Contact

If you identify a factual error, missing source, misattribution, or unfair characterization, report it:

- **Email:** pausebeforeharmprotocol_pbhp@protonmail.com
- **Facebook:** [facebook.com/plinst](https://facebook.com/plinst)
- **PBHP:** [github.com/PauseBeforeHarmProtocol/pbhp](https://github.com/PauseBeforeHarmProtocol/pbhp)

## Support

This project is self-funded and independent.

**[Support The Record on GoFundMe](https://www.gofundme.com/f/building-the-record-accountability-ai)**

---

*Built by Phillip Linstrum with ChatGPT 5.6 Sol Max (OpenAI) & Claude Fable 5 Max (Cowork); legacy AI Opinion authorship remains attributed to Claude (Anthropic, Opus 4).*

*The goal is accuracy and completeness, not advocacy — though the archive makes no pretense of neutrality about whether accountability matters. It does. That is the premise. Everything else is evidence.*
