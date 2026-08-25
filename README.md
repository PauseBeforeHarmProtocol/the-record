<p align="center">
  <img src="assets/brand/the-record-hero.png" alt="An illuminated evidence archive connecting sourced records across a living accountability timeline" width="100%">
</p>

<h1 align="center">The Record</h1>

<p align="center"><strong>Every claim sourced. Every position documented. Every correction visible.</strong></p>

<p align="center">
  <a href="index.html">Open the current front door</a> ·
  <a href="the-record.html#home">Enter the full archive</a> ·
  <a href="weekly/index.html">Weekly record</a> ·
  <a href="national/index.html">National record</a> ·
  <a href="in6/index.html">IN-6</a> ·
  <a href="agencies/index.html">Agencies</a> ·
  <a href="sources/index.html">Source ledger</a> ·
  <a href="archive/index.html">Archive directory</a> ·
  <a href="downloads/index.html">Downloads</a>
</p>

The Record pairs a concise, source-bound editorial front page with the complete chronological accountability archive. The August 24 front door contains 19 national and four IN-6 records, including 13 national records added in the August 17–24 backfill, a working seven-day view, and an Agencies power map. The full archive remains the project’s primary research body, receives the same qualifying current national additions through a small generated live bridge, and includes a separate searchable Truth Social feed that does not treat raw posts as verified archive findings.

> **Integrity note:** Exact legacy totals are currently unreconciled across the README, repository description, and architecture notes. The current site discloses that conflict instead of presenting one disputed number as settled.

---

## What This Is

The Record is a single-file HTML application (listed as the-record.html in repo) that documents Donald Trump’s political career from his father Fred’s KKK arrest in 1927 through the present day. Every entry uses a three-layer format:

- **THE FACTS** — What happened, sourced to major news organizations, court filings, congressional records, and official government documents.
- **SIGNIFICANCE** — Why it matters in historical and political context.
- **GOALPOST** — The rhetorical defense used to normalize it, documented as observed talking points — not straw men.

The archive does not editorialize in the fact layer. It does not hide its analysis. It labels everything.

## The Six Eras

| Era | Period | Entries |
|-----|--------|--------|
| Formation | Pre-June 2015 | 352 |
| Campaign 1 | June 2015 – Jan 2017 | 528 |
| Term 1 | Jan 2017 – Jan 2021 | 1,640 |
| Post-Presidency | Jan 2021 – Nov 2022 | 462 |
| Campaign 2 | Nov 2022 – Jan 2025 | 622 |
| Term 2 | Jan 2025 – Present | 891 |

## Entry Types

**Specific Event entries** document a particular event on a particular date with verifiable facts. **Context entries** (marked with a purple border) document broader patterns, periods, or systemic developments that span time ranges. Both types use the three-layer format.

## Sourcing Standards

Every entry cites at least one source. Sources are drawn from major news organizations (AP, Reuters, NYT, Washington Post, CNN, BBC, NPR, NBC News, PBS, and others), court filings, congressional records, and official government documents. The archive tracks source diversity and maintains 100% real source coverage — no placeholder or synthetic citations.

## Companion Documents

The Record produces 34 companion DOCX documents:

- **6 era documents** — One per historical era
- **16 topic documents** — Courts, Democracy, Media, January 6, Epstein, Foreign Influence, DOGE, Policy, and more
- **5 AI opinion essays** — Clearly labeled AI-generated analysis on Trump, MAGA, the GOP, media, and democracy
- **7 reference documents** — Methodology, editorial approach, politicians, people mentioned, and internal audits

All 34 documents are compiled into a master PDF (THE-RECORD-COMPLETE.pdf, ~2,900 pages).

## AI Transparency

Current maintenance uses two AI systems:

- **ChatGPT 5.6 Sol Max** (OpenAI) — Independent auditing, analysis, code, and adversarial review
- **Claude Fable 5 Max (Cowork)** — Research organization, drafting support, code, and quality review

The editor (Phillip Linstrum) reviews, edits, and approves all AI-assisted content. The five April 2026 AI Opinion essays retain their original **Claude (Anthropic, Opus 4)** attribution; current model names are not silently substituted as authors. See [AI_PROVENANCE.md](AI_PROVENANCE.md). AI output is not a source, and the archive does not use it to fabricate events, invent sources, or publish unverified claims.

## The Record Companion AI

Have questions? Ask **[The Record Companion AI](https://chatgpt.com/g/g-69d0fd0d49cc819184d7d0494471a3aa-the-record-companion-ai)** — a custom GPT trained on the complete master document. It can answer questions about any entry, era, topic, sourcing, methodology, or the Pause Before Harm Protocol.

## The Pause Before Harm Protocol

This project operates under the **[Pause Before Harm Protocol](https://github.com/PauseBeforeHarmProtocol/pbhp)** (PBHP) — an open-source harm-reduction framework for AI and human decision-making.

PBHP asks: *“If I’m wrong, who pays first — and can they recover?”*

Applied to The Record, PBHP means:
- Every entry must name who is harmed by the documented events
- Language must maintain “brutal clarity with zero contempt” — no mockery, no dehumanization
- The archive must be transparent about its own methods, limitations, and potential biases

## Technical Details

The historical application remains a portable HTML archive (~14 MB). On the published site, a small generated JavaScript bridge supplies the current national layer without rewriting the historical application on every six-hour run.

**Architecture:**
- `entries_array.js` — preserved canonical legacy entries (exact total pending deterministic reconciliation)
- `data/current_entries.json` — 23 current-layer records: 19 national and four IN-6
- `current_layer_bridge.js` — generated national entries and release metadata consumed by the full archive
- `data/truth_social_seed.json` — recent verified fallback for the live Truth Social feed
- `assets/truth-feed.js` — safe live-feed loader, search, year filters, and fallback behavior
- `scripts/update_truth_social_feed.py` — validates the public mirror and refreshes the local fallback
- `data/release.json` — the single release date, checked time, weekly window, and new-entry manifest used by every builder
- `EDITORIAL_AUTOMATION.md` — the no-padding publication threshold, correction rule, and six-hour maintenance workflow
- `tag_rules.js` — Automated topic classification rules
- `ai_essays.json` — AI-generated opinion content
- `politicians_all.json` / `pol_data_merged.json` — Politician profiles and cross-references
- `build_html.py` — Build pipeline that compiles everything into the single HTML file
- DOCX generators (Node.js) — 10 scripts that produce the 34 companion documents
- `gen_master_pdf.py` — Compiles all DOCX files into the master PDF

**Current front-door navigation:** Home, The Archive, Truth Social, Latest, Weekly, IN-6, Agencies, Method, Downloads

**Currentness:** researched through August 24, 2026 at 10:43 AM EDT. The release receipt records both published and withheld candidates.

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
