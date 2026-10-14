# The Record — Maintenance Run Receipt

- Release: 10.146.0
- Checked: 2026-10-14 6:03 AM EDT
- Editorial window: 2026-10-14 12:01 AM EDT through 2026-10-14 6:03 AM EDT
- Current layer: 386 records backed by 1187 source-ledger records
- Full archive runtime: 5,113 records; 7,887 source references; 6,490 distinct stored URLs
- Legacy custody: 4,742 stored rows; 4,731 active; 11 duplicate tombstones excluded from totals
- Truth Social source: 36,888 posts; 1,000 retained in the validated local fallback
- Newest Truth Social post: 2026-10-14 2:19:28 AM EDT
- Truth Social fallback checked: 2026-10-14 6:04:12 AM EDT
- Added: 1 national record
- Materially refreshed: 2 national records

## Added or materially refreshed records

- `NAT-2026-10-13-011` — Reuters review measures political skew and avoided penalties in clemency for public officials
- `NAT-2026-09-15-003` — Federal noncitizen-voting push produces cases but no identified broad pattern
- `NAT-2026-10-13-010` — Justice Department defers Sue Mi Terry prosecution for one year

## Withheld candidates

- Twenty-six newer Truth Social posts: All text payloads were reviewed; full motion, audio and captions for 23 videos remain pending. The reviewable content was campaign commentary, unverified claims or a vague prospective Greenland announcement and did not independently establish another qualifying action.
- Greenland exploration announcement: Trump announced that exploration was getting ready to begin, but neither the post nor the Reuters report identified a project, operator, permit, funding, instrument, timetable or independently verified implementation.
- Trump TV and official video-library recheck: Official page and dated-library metadata were rechecked; footage, audio and captions were not retrieved, and no qualifying new item was located in the material reviewed.

## Truth Social inspection

- New retained posts: 26
- Current retained inspection states: {"media_status": {"not_applicable": 819, "not_recorded": 19, "pending": 506, "reviewed": 125, "unavailable": 244}, "text_status": {"not_recorded": 147, "pending": 969, "reviewed": 597}}

Twenty-six posts were newer than the prior snapshot. All text payloads were reviewed; representative frames from one 163.7-second video were inspected, while full motion, audio and captions for all 23 videos remain pending. The newest retained item was an RT pointer at 2:19:28 AM EDT. No additional independently verified action met the publication threshold.

## Trump TV monitoring

- Checked: 2026-10-14 6:09 AM EDT
- Inspection state: partial_metadata_recheck
- Current official stream link: https://www.youtube.com/watch?v=A4gNgHfZ-v4
- Last successful complete broadcast review: none; coverage boundary unknown

Official Trump TV, live, video-library, remarks and news pages were rechecked. The linked stream remained A4gNgHfZ-v4; fallback error text was not treated as proof of an outage. The dated library still led with three October 13 items: a departure gaggle, a 15-second press-secretary clip and a 14:26 press briefing. Only page metadata and stable White House item URLs were inspected; footage, audio and captions were not reviewed. No qualifying new item located in the material reviewed.

Sources and material actually inspected:

- https://www.whitehouse.gov/trumptv/
- https://www.whitehouse.gov/live/
- https://www.whitehouse.gov/videos/
- https://www.whitehouse.gov/remarks/
- https://www.whitehouse.gov/news/
- Official page linked the unchanged A4gNgHfZ-v4 stream. No footage, audio or captions were retrieved; fallback text was not treated as proof of an outage. (https://www.whitehouse.gov/trumptv/)
- The hub linked the same Trump TV stream. Current live/replay state and audiovisual content were not independently reviewed; page fallback text was not treated as proof of an outage. (https://www.whitehouse.gov/live/)
- The library still led with three October 13 items: the 10:05 departure gaggle, a 00:15 press-secretary clip and a 14:26 press briefing. Metadata and stable White House item pages were inspected; footage, audio, captions and exact upload times were not retrieved. (https://www.whitehouse.gov/videos/)
- The index still listed October 9 science-summit remarks as newest and was not treated as a complete Trump TV transcript feed. (https://www.whitehouse.gov/remarks/)
- The news index led with an October 10 manufacturing research post and supplied no new Trump TV transcript or broadcast finding. (https://www.whitehouse.gov/news/)

Access gaps and recheck requirements:

- Broadcast footage, audio and captions were not retrieved, so no claim is made that every broadcast minute was reviewed.
- Current live/replay state was not independently verified; fallback text alone does not establish an outage.
- No complete transcript feed, channel budget, contract, staffing record or editorial-control record was available in the inspected official pages.

## Verification

Current front-door pages, canonical datasets, archive bridge, individual evidence packs, versioned aggregate packs, source ledgers, and checksums are generated deterministically. Earlier date-only base aggregates remain byte-frozen and separately addressable; every new same-day aggregate is version-keyed. Candidate publication requires the repository validator and GitHub Actions to pass, followed by acceptance from the publication authority named above.

## Review traceability

- Current entries with content-bound claim-level receipts: 263 / 386
- Prior review-state labels are distinct from claim-level review receipt coverage.
- Stored post inspection-state records: 1713. Acquisition is not inspection.
- Per-post text/media states: data/truth_social_reviews.json; deferred follow-ups: data/research_queue.json.
- Actual acceptance results are recorded by scripts/accept_release.py and retained as a CI artifact; this generated receipt is not a test attestation.
