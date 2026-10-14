# The Record — Maintenance Run Receipt

- Release: 10.147.0
- Checked: 2026-10-14 11:55 AM EDT
- Editorial window: 2026-10-14 6:03 AM EDT through 2026-10-14 11:55 AM EDT
- Current layer: 389 records backed by 1196 source-ledger records
- Full archive runtime: 5,116 records; 7,896 source references; 6,499 distinct stored URLs
- Legacy custody: 4,742 stored rows; 4,731 active; 11 duplicate tombstones excluded from totals
- Truth Social source: 36,893 posts; 1,000 retained in the validated local fallback
- Newest Truth Social post: 2026-10-14 7:53:09 AM EDT
- Truth Social fallback checked: 2026-10-14 11:57:12 AM EDT
- Added: 3 national records
- Materially refreshed: 2 national records

## Added or materially refreshed records

- `NAT-2026-10-14-001` — CMS removes Marketplace subsidies tied to 189,000 duplicate or deceased records
- `NAT-2026-10-14-002` — OCC reports all nine reviewed large banks had policies capable of influencing debanking
- `NAT-2026-10-14-003` — Social Security sets automatic 3.6% cost-of-living adjustment for 2027
- `NAT-2026-09-11-006` — BLS reports 0.6% September consumer-price rise and 3.7% annual inflation
- `NAT-2026-10-13-008` — Treasury agencies impose $1.21 billion Bank of America enforcement package

## Withheld candidates

- Five newer Truth Social link posts: All text payloads were reviewed. Four were commentary, polling or unverified accusation links; the Ohio submarine-facility link repeated NAT-2026-10-06-004 and supplied no new implementing instrument or measured outcome.
- D.C. National Guard appeal oral argument: The appellate hearing did not itself change the governing order or establish a new implemented action; the existing record remains awaiting a ruling.
- Press-access injunction follow-up: The same preliminary injunction was already incorporated into NAT-2026-09-18-007 in release 10.145.0; later wire coverage supplied no new order or compliance outcome.
- Election-interference scenario analysis: The analysis described prospective risks and possible tactics rather than a newly documented administration action, order, investigation or measured outcome.
- Trump TV and official video-library recheck: The official pages still led with October 13 metadata and the same stream ID; audiovisual content and complete transcripts were not retrieved, and no qualifying new item was located in the material reviewed.

## Truth Social inspection

- New retained posts: 5
- Current retained inspection states: {"media_status": {"not_applicable": 824, "not_recorded": 19, "pending": 506, "reviewed": 125, "unavailable": 244}, "text_status": {"not_recorded": 147, "pending": 969, "reviewed": 602}}

Five posts were newer than the prior snapshot. All five text payloads and linked headlines were reviewed; none had a media attachment. The newest retained item was a Just the News link at 7:53:09 AM EDT. The Ohio submarine link duplicated an existing record, and no additional independently verified action met the publication threshold.

## Trump TV monitoring

- Checked: 2026-10-14 12:07 PM EDT
- Inspection state: partial_metadata_recheck
- Current official stream link: https://www.youtube.com/watch?v=A4gNgHfZ-v4
- Last successful complete broadcast review: none; coverage boundary unknown

Official Trump TV, live, video-library, remarks and news pages were rechecked. The linked stream remained A4gNgHfZ-v4; fallback error text was not treated as proof of an outage. The dated library still led with the October 13 departure gaggle and press-secretary clip. Only page and stable-item metadata were inspected; footage, audio, captions and complete transcripts were not retrieved. No qualifying new item located in the material reviewed.

Sources and material actually inspected:

- https://www.whitehouse.gov/trumptv/
- https://www.whitehouse.gov/live/
- https://www.whitehouse.gov/videos/
- https://www.whitehouse.gov/remarks/
- https://www.whitehouse.gov/news/
- Official page linked the unchanged A4gNgHfZ-v4 stream. No footage, audio or captions were retrieved; fallback text was not treated as proof of an outage. (https://www.whitehouse.gov/trumptv/)
- The hub linked the same Trump TV stream. Current live/replay state and audiovisual content were not independently reviewed; page fallback text was not treated as proof of an outage. (https://www.whitehouse.gov/live/)
- The library still led with the October 13 departure gaggle and 15-second press-secretary clip. Metadata and the stable departure-gaggle item page were inspected; footage, audio, captions and exact upload times were not retrieved. (https://www.whitehouse.gov/videos/)
- The index still listed October 9 science-summit remarks as newest and was not treated as a complete Trump TV transcript feed. (https://www.whitehouse.gov/remarks/)
- The news index led with an October 10 manufacturing research post and supplied no new Trump TV transcript or broadcast finding. (https://www.whitehouse.gov/news/)

Access gaps and recheck requirements:

- Broadcast footage, audio and captions were not retrieved, so no claim is made that every broadcast minute was reviewed.
- Current live/replay state was not independently verified; fallback text alone does not establish an outage.
- No complete transcript feed, channel budget, contract, staffing record or editorial-control record was available in the inspected official pages.

## Verification

Current front-door pages, canonical datasets, archive bridge, individual evidence packs, versioned aggregate packs, source ledgers, and checksums are generated deterministically. Earlier date-only base aggregates remain byte-frozen and separately addressable; every new same-day aggregate is version-keyed. Candidate publication requires the repository validator and GitHub Actions to pass, followed by acceptance from the publication authority named above.

## Review traceability

- Current entries with content-bound claim-level receipts: 266 / 389
- Prior review-state labels are distinct from claim-level review receipt coverage.
- Stored post inspection-state records: 1718. Acquisition is not inspection.
- Per-post text/media states: data/truth_social_reviews.json; deferred follow-ups: data/research_queue.json.
- Actual acceptance results are recorded by scripts/accept_release.py and retained as a CI artifact; this generated receipt is not a test attestation.
