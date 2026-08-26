# Merge instructions

1. Review the maintenance branch against `main`.
2. Confirm historical edits were made in `data/legacy_entries.json`, not independently in `the-record.html`, `docs/the-record.html`, or `entries_array.js`. Preserve `THE-RECORD-COMPLETE.pdf`, companion documents, and historical release artifacts unless the pull request explicitly replaces them with regenerated, reviewed versions.
3. Run the deterministic acceptance sequence in this exact order:
   1. `python scripts/sync_source_ledger.py --check`
   2. `python scripts/apply_legacy_remediations.py --check`
   3. `python scripts/sync_legacy_data.py --check`
   4. `python scripts/build_archive_metrics.py --check`
   5. `python scripts/sync_readme_metrics.py --check`
   6. `python scripts/validate_federated_records.py --self-test`
   7. `python scripts/build_legacy_bridge.py --check`
   8. `python scripts/package_current_release.py --check`
   9. `python scripts/build_current_pages.py --check`
   10. `python scripts/validate.py`
4. Run `node --check assets/site.js` and `node --check assets/truth-feed.js`.
5. Confirm `data/archive_metrics.json` separately reports stored legacy rows, active entries, superseded tombstones, source references, unique URLs, ledger rows, current-layer entries, and published runtime entries. Confirm the displayed coverage boundary and any known gap agree with canonical data. Review the surfaced legacy duplicate-candidate queue; existing candidates remain open until adjudicated and are not silently deleted merely to make the count fall. Every confirmed duplicate must retain a revision-backed tombstone that redirects to one active record and is excluded from runtime counts and search.
6. Confirm every current canonical record carries an explicit `review_status` of `current-standard-reviewed` or `corrected`; Maybe / Therefore presence alone must not create or imply that state. Confirm federated archive records preserve their upstream units and observation times, do not sum unlike archive counts, and do not auto-promote external records into verified Record entries. Every promoted record must include facts, significance, goalpost/response, Maybe / Therefore, evidence/confidence, provenance, consequences, and revision state. Federated validation must reject collisions derived from origin IDs, canonical targets, direct evidence URLs, formal identifiers, normalized facts/titles, date intervals, family, chronology, and lifecycle cycles—not merely editor-entered hashes. A published crosswalk target must already meet the current evidence, Maybe / Therefore, and explicit review-state standard. If raw staged JSON is publicly downloadable for auditability, verify that the record and public copy call it unreviewed, unauthorized for canonical publication, uncounted, and not a finding; do not describe every publicly accessible AI-assisted field as human-approved.
7. Review Home, Weekly, Agencies, Latest, Sources, Method, Downloads, and the full archive on desktop and phone. Check at least one legacy stable ID, one bridged current ID, one source link, the Truth Social feed fallback, and the public count disclosure.
8. Review the complete diff. Generated legacy representations must agree with canonical JSON; do not resolve a generated-file conflict by editing only one representation.
9. Preserve earlier date-only aggregate paths byte-for-byte. When another release already exists for the date, confirm every new aggregate brief, pack, receipt, and checksum sidecar is keyed by both release date and release version. If `maintenance_revision.base_editorial_version` is set, ensure the receipt describes `new_entry_ids`, `added_entry_ids`, and `refreshed_entry_ids` as base-editorial carryforwards, not changes made by the maintenance.
10. Merge only after local validation, GitHub Actions, and Phillip Linstrum's final publication acceptance pass; otherwise leave the pull request open with the blocker.

Scheduled six-hour currentizations update `current_layer_bridge.js`; that generated asset feeds qualifying national entries into the full searchable archive while leaving the historical application body stable during ordinary current-only runs. Legacy remediation begins in `data/legacy_entries.json` and is propagated deterministically to every compatibility representation. The landing page remains a curated front door, not a replacement archive.

The checked source window is defined by `data/release.json`; do not maintain a competing timestamp in this file.
