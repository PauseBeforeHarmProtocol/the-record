# The Record — Maintenance Run Receipt

- Release: 10.177.0
- Checked: 2026-10-23 6:01 PM EDT
- Editorial window: 2026-10-23 11:59 AM EDT through 2026-10-23 6:01 PM EDT
- Current layer: 441 records backed by 1382 source-ledger records
- Full archive runtime: 5,168 records; 8,079 source references; 6,680 distinct stored URLs
- Legacy custody: 4,742 stored rows; 4,731 active; 11 duplicate tombstones excluded from totals
- Truth Social source: 37,227 posts; 1,000 retained in the validated local fallback
- Newest Truth Social post: 2026-10-23 5:49:02 PM EDT
- Truth Social fallback checked: 2026-10-23 6:01:02 PM EDT
- Added: 0 national records
- Materially refreshed: 4 national records

## Added or materially refreshed records

- `NAT-2026-09-05-001` — U.S.-mediated Ukraine talks advance to a dated localized Oleshky pause
- `NAT-2026-09-10-005` — Fifth Circuit rejects constitutional bond-hearing right as Supreme Court reviews statutory dispute
- `NAT-2026-10-09-003` — First Russian diesel cargo under Treasury license departs for New York
- `NAT-2026-08-22-001` — Trump signs narrower revision to Canadian 50% tariff product scope

## Withheld candidates

- Pentagon Confucius Institutes designation report: A late wire report lacked a located primary directive and enough operational detail for source-level claim mapping.
- Minnesota immigration evidence-withholding allegation: The report concerned a prior-window September pause and primary court filings were not retrieved in this run.
- Truth Social posts and Florida rally stream: Routine rhetoric, campaign material, commentary and an image-only National Mall post did not independently establish a qualifying action.
- Trump TV material: No qualifying new item was located in the accessible official metadata; footage and captions were unavailable.
- Legacy California National Guard remediation: Deferred under the ordinary-maintenance historical-body stability rule after the authenticated connector rejected the regenerated large HTML blobs above its 16 MiB request ceiling.

## Truth Social inspection

- New retained posts: 6
- Current retained inspection states: {}

Six posts were newer than the prior validated snapshot. Text, linked-page metadata and the newest image-only post were reviewed; none independently met the publication threshold.

## Trump TV monitoring

- Checked: 2026-10-23 6:01 PM EDT
- Inspection state: partial_metadata_recheck
- Current official stream link: https://www.youtube.com/watch?v=A4gNgHfZ-v4
- Last successful complete broadcast review: none; coverage boundary unknown

Official Trump TV, live, dated video-library, remarks and releases pages were rechecked. Stream A4gNgHfZ-v4 and the three October 22 library listings were unchanged; no October 23 listing was present. Footage, audio and captions were unavailable. No qualifying new item located in the material reviewed.

Sources and material actually inspected:

- https://www.whitehouse.gov/trumptv/
- https://www.whitehouse.gov/live/
- https://www.whitehouse.gov/videos/
- https://www.whitehouse.gov/remarks/
- https://www.whitehouse.gov/releases/
- Official page linked unchanged stream A4gNgHfZ-v4. Fallback text was not treated as proof of an outage. (https://www.whitehouse.gov/trumptv/)
- The hub presented the official channel and fallback text; footage and captions were not retrieved. (https://www.whitehouse.gov/live/)
- The latest three listings remained the October 22 departure gaggle, Fraud Whistleblower Incentive Program clip and October 21 Joint Base Andrews gaggle replay; the fraud clip was already covered by NAT-2026-10-20-002. (https://www.whitehouse.gov/videos/)
- No new complete Trump TV transcript was supplied; the index was not treated as a complete transcript feed. (https://www.whitehouse.gov/remarks/)
- The Florida release was used as a lead only; no broadcast footage or separate qualifying government action was inferred. (https://www.whitehouse.gov/releases/)

Access gaps and recheck requirements:

- Broadcast footage, audio and captions were not retrieved, so no claim is made that every broadcast minute was reviewed.
- Current live/replay state was not independently verified; fallback error text alone does not establish an outage.
- No complete transcript feed, channel budget, contract, staffing record or editorial-control record was available in the inspected official pages.

## Verification

Current front-door pages, canonical datasets, archive bridge, individual evidence packs, versioned aggregate packs, source ledgers, and checksums are generated deterministically. Earlier date-only base aggregates remain byte-frozen and separately addressable; every new same-day aggregate is version-keyed. Candidate publication requires the repository validator and GitHub Actions to pass, followed by acceptance from the publication authority named above.

## Review traceability

- Current entries with content-bound claim-level receipts: 319 / 441
- Prior review-state labels are distinct from claim-level review receipt coverage.
- Stored post inspection-state records: 2054. Acquisition is not inspection.
- Per-post text/media states: data/truth_social_reviews.json; deferred follow-ups: data/research_queue.json.
- Actual acceptance results are recorded by scripts/accept_release.py and retained as a CI artifact; this generated receipt is not a test attestation.
