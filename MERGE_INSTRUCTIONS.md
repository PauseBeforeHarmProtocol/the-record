# Merge instructions

1. Review branch `agent/the-record-july-18-currentization` against `main`.
2. Preserve `the-record.html`, `entries_array.js`, `THE-RECORD-COMPLETE.pdf`, `docs/`, and all July 18 artifacts.
3. Confirm the source ledgers agree: `python scripts/sync_source_ledger.py --check`.
4. Confirm the generated front door is current: `python scripts/build_current_pages.py --check`.
5. Confirm deterministic release packages: `python scripts/package_current_release.py --check`.
6. Run `python scripts/validate.py` and `node --check assets/site.js`.
7. Review Home, Weekly, Agencies, National, Downloads, and the preserved archive on desktop and phone.
8. Merge only after local validation and GitHub Actions pass; otherwise leave the pull request open with the blocker.

Scheduled currentizations leave the 14 MB `the-record.html` legacy archive immutable. The generated National and Weekly routes are the live current layer.

Checked source window: August 17 through 2026-08-24 10:43 AM EDT.
