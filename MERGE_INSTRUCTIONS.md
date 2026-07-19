# Merge instructions

1. Review draft branch `agent/the-record-july-18-currentization` against `main`.
2. Preserve `the-record.html`, `entries_array.js`, `THE-RECORD-COMPLETE.pdf`, `docs/`, and all July 18 artifacts.
3. Confirm the generated front door is current: `python scripts/build_current_pages.py --check`.
4. Confirm the legacy Past Week bridge is current: `python scripts/build_legacy_bridge.py --check`.
5. Confirm deterministic release packages: `python scripts/package_current_release.py --check`.
6. Run `python scripts/validate.py` and `node --check assets/site.js`.
7. Review Home, Weekly, Agencies, National, Downloads, and the preserved archive on desktop and phone.
8. Keep the pull request in draft until editorial review is complete; do not auto-merge it.

Checked source window: 2026-07-19 08:15 AM EDT.
