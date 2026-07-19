# The Record — July 19, 2026 currentization

Version: `8.0.1-rc1`

Publication status: **review candidate, not a tagged production release**

## Included

- Six current national entries, including the July 16–17 election-security disclosure reviewed on July 19
- Four current IN-6 entries
- A fixed, searchable, scope-filterable `weekly/` route for July 13–19
- A top-level `agencies/` route with every current institution mapped to its records
- A preserved `institutions/` compatibility route
- Exact current AI maintenance disclosure for ChatGPT 5.6 Sol Max and Claude Fable 5 Max (Cowork)
- Preserved Claude (Anthropic, Opus 4) authorship for the five April 2026 AI Opinion essays
- Direct per-entry downloads, July 19 national and complete packages, source ledgers, and checksums
- A current-layer bridge that makes the preserved single-file archive’s Past Week control reach the latest national records
- Deterministic page and package builders plus expanded repository validation

## Preserved

- `the-record.html`
- `entries_array.js`
- `THE-RECORD-COMPLETE.pdf`
- `docs/` and all companion documents
- All July 18 candidate packages and receipts
- Existing Git history and release history

## Validation

```bash
python scripts/build_current_pages.py --check
python scripts/build_legacy_bridge.py --check
python scripts/package_current_release.py --check
python scripts/validate.py
node --check assets/site.js
```

## Evidence boundary

Official White House, Justice Department, House, and IN-6 publication channels were checked through `2026-07-19 08:15 AM EDT`. This pass added one source-bound national record. It does not independently revalidate every historical entry in the long-form archive.
