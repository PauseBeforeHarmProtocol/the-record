# The Record — Maintenance Run Receipt

- Release: 10.39.0
- Checked: 2026-09-09 6:00 AM EDT
- Editorial window: 2026-09-08 11:58 PM EDT through 2026-09-09 6:00 AM EDT
- Current layer: 164 records backed by 475 source-ledger records
- Full archive runtime: 4,891 records; 7,168 source references; 5,780 distinct stored URLs
- Legacy custody: 4,742 stored rows; 4,731 active; 11 duplicate tombstones excluded from totals
- Truth Social source: 36,204 posts; 1,000 retained in the validated local fallback
- Newest Truth Social post: 2026-09-08 10:25:12 PM EDT
- Truth Social fallback checked: 2026-09-09 6:01:13 AM EDT
- Added: 3 national records
- Materially refreshed: 1 national record

## Added or materially refreshed records

- `NAT-2026-09-06-001` — NTSB flight data indicates a late go-around attempt before fatal Miami cargo overrun
- `NAT-2026-09-08-010` — TSA launches ticketless gateside access for eligible trusted travelers at 13 airports
- `NAT-2026-09-08-011` — Judge dismisses Imran Ahmed's challenge to Trump immigration action on jurisdictional grounds
- `NAT-2026-08-17-001` — Trump widens the Hormuz war as U.S. forces strike Iranian military and oil targets

## Withheld candidates

- No new Truth Social posts: The validated fallback remains at 36,204 posts. The newest was published September 8 at 10:25:12 PM EDT; the source was checked September 9 at 6:01:13 AM EDT. No newer post required text or media review.
- Prior-window court and transportation omissions: The Ahmed ruling and NTSB preliminary briefing were published shortly before the prior 03:58:50Z boundary but were not available in that release's review. They are restored transparently under their actual September 8 and September 6 event dates rather than misdated as new actions.
- Hungary and Poland immigrant-visa processing: Reuters reported resumed processing based on four unnamed sources, and the State Department declined to comment. No public directive or second independent confirmation satisfied the archive's rule for a consequential unnamed-source claim.
- West Point, USPS OIG and ABA candidates: The complete West Point stipulation, public USPS OIG scope and adopted ABA council text were not available for direct inspection. Each remains queued, and none is converted into a final merits ruling, investigation finding or federal recognition decision.
- Bessent speech and Arlington memorial webpage: The Treasury secretary's policy advocacy did not announce a new instrument, and edits to a memorial webpage did not independently clear the materiality threshold.
- September 9 Federal Register documents: The DHS, NHTSA, USDA, DOE and CDC documents were scheduled for official publication after this run's 10:00:31Z evidence cutoff. They are queued for the next continuous window rather than pulled backward across the boundary.
- Legacy-quality batch: LEG-003957 still has a mismatched citation. Indexed and syndicated reporting narrowed the likely source, but the exact April 15 article was not fully inspectable, so no guarded historical correction or unsupported review upgrade was made.
- External archive measurements: Trump Archive advanced to 13,928 items, including 11,546 Truth Social posts and 1,753 speeches and transcripts. UndoTrump remained at 1,264 actions and IPTP at 1,790 policies. Record47 counts could not be freshly verified, so its prior scoped measurements and observation times were preserved. No external item was auto-promoted.

## Verification

Current front-door pages, canonical datasets, archive bridge, individual evidence packs, versioned aggregate packs, source ledgers, and checksums are generated deterministically. Earlier date-only base aggregates remain byte-frozen and separately addressable; every new same-day aggregate is version-keyed. Candidate publication requires the repository validator and GitHub Actions to pass, followed by acceptance from the publication authority named above.

## Review traceability

- Current entries with content-bound claim-level receipts: 22 / 164
- Prior review-state labels are distinct from claim-level review receipt coverage.
- Stored post inspection-state records: 1027. Acquisition is not inspection.
- Per-post text/media states: data/truth_social_reviews.json; deferred follow-ups: data/research_queue.json.
- Actual acceptance results are recorded by scripts/accept_release.py and retained as a CI artifact; this generated receipt is not a test attestation.
