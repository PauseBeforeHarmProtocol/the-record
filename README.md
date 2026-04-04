# The Record

**A chronological, sourced accountability archive of Donald Trump’s political career.**

4,371 entries. 5,396 sources. Six eras. 34 companion documents. One premise: accountability matters.

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
| Formation | Pre-June 2015 | 330 |
| Campaign 1 | June 2015 – Jan 2017 | 528 |
| Term 1 | Jan 2017 – Jan 2021 | 1,640 |
| Post-Presidency | Jan 2021 – Nov 2022 | 462 |
| Campaign 2 | Nov 2022 – Jan 2025 | 622 |
| Term 2 | Jan 2025 – Present | 789 |

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

The Record is built with two AI systems:

- **Claude** (Anthropic) — Entry drafting, code generation, quality assurance
- **ChatGPT 5.4 Extended Thinking** (OpenAI) — Independent auditing, analysis, companion AI

The editor (Phillip Linstrum) reviews, edits, and approves all AI-generated content. AI opinion essays are clearly separated from the factual timeline and explicitly labeled. The archive does not use AI to fabricate events, invent sources, or generate unverified claims.

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

The Record is a self-contained single-file HTML application (~11.5 MB). No server required — open the file in any modern browser.

**Architecture:**
- `entries_array.js` — 4,371 structured entries in JSON format
- `tag_rules.js` — Automated topic classification rules
- `ai_essays.json` — AI-generated opinion content
- `politicians_all.json` / `pol_data_merged.json` — Politician profiles and cross-references
- `build_html.py` — Build pipeline that compiles everything into the single HTML file
- DOCX generators (Node.js) — 10 scripts that produce the 34 companion documents
- `gen_master_pdf.py` — Compiles all DOCX files into the master PDF

**Navigation (9 tabs):** Home, Browse by Topic, Browse by Year, Full Timeline, Politicians, AI Opinion, Methodology, About, Search The Record

## Corrections & Contact

If you identify a factual error, missing source, misattribution, or unfair characterization, report it:

- **Email:** pausebeforeharmprotocol_pbhp@protonmail.com
- **Facebook:** [facebook.com/plinst](https://facebook.com/plinst)
- **PBHP:** [github.com/PauseBeforeHarmProtocol/pbhp](https://github.com/PauseBeforeHarmProtocol/pbhp)

## Support

This project is self-funded and independent.

**[Support The Record on GoFundMe](https://www.gofundme.com/f/building-the-record-accountability-ai)**

---

*Built by Phillip Linstrum with Claude (Anthropic) & ChatGPT 5.4 Extended Thinking (OpenAI)*

*The goal is accuracy and completeness, not advocacy — though the archive makes no pretense of neutrality about whether accountability matters. It does. That is the premise. Everything else is evidence.*
