# The Record — July 18, 2026 release overlay

Version: `8.0.0-rc1`

This repository package supplies a new navigable front door and current-release layer for The Record while preserving the complete legacy applications.

## Included

- Five current national entries
- Four current IN-6 entries
- Direct per-entry downloads
- National and IN-6 update packages
- Source ledger in CSV and JSON
- Agencies-and-institutions map
- Methodology, corrections, AI disclosure, and count-reconciliation finding
- Static link and schema validation

## Merge rule

Overlay the contents of `site/` onto the existing `the-record` repository **without deleting** `the-record.html`, `entries_array.js`, `THE-RECORD-COMPLETE.pdf`, or `docs/`. The new root `index.html` becomes the front door; the historical application remains preserved.

## Validation

```bash
python scripts/validate.py
```

## Evidence boundary

This release updates the current layer through 2026-07-18 12:00 PM EDT. It does not independently revalidate every historical entry in the long-form archive.
