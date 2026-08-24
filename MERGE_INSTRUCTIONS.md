# Merge instructions

1. Review the maintenance branch against `main`.
2. Preserve `the-record.html`, `entries_array.js`, `THE-RECORD-COMPLETE.pdf`, `docs/`, and all July 18 artifacts.
3. Confirm the source ledgers agree: `python scripts/sync_source_ledger.py --check`.
4. Confirm the generated front door is current: `python scripts/build_current_pages.py --check`.
5. Confirm the full archive consumes the generated live layer: `python scripts/build_legacy_bridge.py --check`.
6. Confirm deterministic release packages: `python scripts/package_current_release.py --check`.
7. Run `python scripts/validate.py` and `node --check assets/site.js`.
8. Review Home, Weekly, Agencies, Latest, Downloads, and the full archive on desktop and phone.
9. Merge only after local validation and GitHub Actions pass; otherwise leave the pull request open with the blocker.

Scheduled currentizations update `current_layer_bridge.js`; that generated asset feeds qualifying national entries into the complete archive while leaving the 14 MB historical application stable. The landing page remains a curated front door, not a replacement archive.

Checked source window: August 17 through 2026-08-24 10:43 AM EDT.
