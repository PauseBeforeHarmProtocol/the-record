# The Record — Maintenance Run Receipt

- Release: 10.145.0
- Checked: 2026-10-14 12:01 AM EDT
- Editorial window: 2026-10-13 5:56 PM EDT through 2026-10-14 12:01 AM EDT
- Current layer: 385 records backed by 1184 source-ledger records
- Full archive runtime: 5,112 records; 7,884 source references; 6,487 distinct stored URLs
- Legacy custody: 4,742 stored rows; 4,731 active; 11 duplicate tombstones excluded from totals
- Truth Social source: 36,862 posts; 1,000 retained in the validated local fallback
- Newest Truth Social post: 2026-10-13 11:17:40 PM EDT
- Truth Social fallback checked: 2026-10-14 12:02:33 AM EDT
- Added: 3 national records
- Materially refreshed: 1 national record

## Added or materially refreshed records

- `NAT-2026-10-13-008` — Treasury agencies impose $1.21 billion Bank of America enforcement package
- `NAT-2026-10-13-009` — Trump signs pardons for two Alaska diesel mechanics at rally
- `NAT-2026-10-13-010` — Justice Department defers Sue Mi Terry prosecution for one year
- `NAT-2026-09-18-007` — Press-access ban remains enjoined while DOJ probes television-pool response

## Withheld candidates

- Eleven newer Truth Social posts: Text and four still images were reviewed; representative frames from three videos were inspected while full motion, audio and captions remain pending. Campaign promotion, unsupported claims, rally media and rhetoric did not independently establish another qualifying federal action.
- Trump TV and official video-library recheck: The stream ID remained unchanged and the library added an October 13 departure-gaggle item. Only page metadata was retrieved; footage, audio and captions were not reviewed, and no qualifying new item was located in the material reviewed.
- Nicaragua charge d'affaires recall: The diplomatic protest was announced, but no broader legal, financial or operational consequence meeting the archive threshold was established by cutoff.
- Kimberly Guilfoyle resignation: Personnel departure and reported allegations did not include confirmed investigative findings or a material administration action.
- Taiwan Alaska LNG purchase claim: The claimed 30 percent purchase lacked independently verified binding terms and could not be distinguished from the existing 2025 letter of intent.

## Truth Social inspection

- New retained posts: 11
- Current retained inspection states: {"media_status": {"not_applicable": 816, "not_recorded": 19, "pending": 483, "reviewed": 125, "unavailable": 244}, "text_status": {"not_recorded": 147, "pending": 969, "reviewed": 571}}

Eleven posts were newer than the prior snapshot. All text and four still images were reviewed; representative frames from three videos were inspected while full motion, audio and captions remain pending. No additional independently verified action met the publication threshold.

## Trump TV monitoring

- Checked: 2026-10-14 12:01 AM EDT
- Inspection state: partial_metadata_recheck
- Current official stream link: https://www.youtube.com/watch?v=A4gNgHfZ-v4
- Last successful complete broadcast review: none; coverage boundary unknown

Official Trump TV, live, video-library, remarks and news pages were rechecked. The linked stream remained A4gNgHfZ-v4, and fallback error text was not treated as proof of an outage. The library newly led with an October 13 departure-gaggle item (10:05). Only page metadata was retrieved; footage, audio and captions were not reviewed. No qualifying new item located in the material reviewed.

Sources and material actually inspected:

- https://www.whitehouse.gov/trumptv/
- https://www.whitehouse.gov/live/
- https://www.whitehouse.gov/videos/
- https://www.whitehouse.gov/remarks/
- https://www.whitehouse.gov/news/
- Official page linked the unchanged A4gNgHfZ-v4 stream. No footage, audio or captions were retrieved; fallback text was not treated as proof of an outage. (https://www.whitehouse.gov/trumptv/)
- The hub linked the same Trump TV stream. Current live/replay state and audiovisual content were not independently reviewed. (https://www.whitehouse.gov/live/)
- The library newly led with 'President Trump Gaggles with Press Upon Departure' dated October 13 and showing a 10:05 duration. Metadata was inspected; footage, audio, captions and exact upload time were not retrieved. (https://www.whitehouse.gov/videos/)
- The index still listed October 9 science-summit remarks as newest and was not treated as a complete Trump TV transcript feed. (https://www.whitehouse.gov/remarks/)
- The news index led with an October 10 manufacturing research post and supplied no new Trump TV transcript or broadcast finding. (https://www.whitehouse.gov/news/)

Access gaps and recheck requirements:

- Broadcast footage, audio and captions were not retrieved, so no claim is made that every broadcast minute was reviewed.
- Current live/replay state was not independently verified; fallback text alone does not establish an outage.
- No complete transcript feed, channel budget, contract, staffing record or editorial-control record was available in the inspected official pages.

## Verification

Current front-door pages, canonical datasets, archive bridge, individual evidence packs, versioned aggregate packs, source ledgers, and checksums are generated deterministically. Earlier date-only base aggregates remain byte-frozen and separately addressable; every new same-day aggregate is version-keyed. Candidate publication requires the repository validator and GitHub Actions to pass, followed by acceptance from the publication authority named above.

## Review traceability

- Current entries with content-bound claim-level receipts: 262 / 385
- Prior review-state labels are distinct from claim-level review receipt coverage.
- Stored post inspection-state records: 1687. Acquisition is not inspection.
- Per-post text/media states: data/truth_social_reviews.json; deferred follow-ups: data/research_queue.json.
- Actual acceptance results are recorded by scripts/accept_release.py and retained as a CI artifact; this generated receipt is not a test attestation.
