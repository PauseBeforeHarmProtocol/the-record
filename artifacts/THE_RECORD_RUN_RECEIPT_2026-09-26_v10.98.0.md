# The Record — Maintenance Run Receipt

- Release: 10.98.0
- Checked: 2026-09-26 5:57 PM EDT
- Editorial window: 2026-09-26 11:57 AM EDT through 2026-09-26 5:57 PM EDT
- Current layer: 295 records backed by 847 source-ledger records
- Full archive runtime: 5,022 records; 7,546 source references; 6,152 distinct stored URLs
- Legacy custody: 4,742 stored rows; 4,731 active; 11 duplicate tombstones excluded from totals
- Truth Social source: 36,497 posts; 1,000 retained in the validated local fallback
- Newest Truth Social post: 2026-09-26 5:47:27 PM EDT
- Truth Social fallback checked: 2026-09-26 5:58:56 PM EDT
- Added: 1 national record
- Materially refreshed: 0 national records

## Added or materially refreshed records

- `NAT-2026-09-26-001` — DOT announces Monday finalization of lower light-vehicle fuel-economy standards

## Withheld candidates

- Six non-CAFE Truth Social posts: The accessible material was campaign or ceremonial content, broad unverified claims, political coverage, or textless video. Four media assets could not be retrieved; no claim about inaccessible media was used and all six posts remain feed-only.
- Cuba and Venezuela negotiating rhetoric: No executed agreement, public operative terms or verified policy change located in the material reviewed.
- Trump TV follow-up: The official Trump TV and live pages still exposed the same stream ID and the latest dated video, remarks and release listings did not advance beyond the prior baseline. No complete recording, captions or transcript were retrieved, so no broadcast-minute coverage is claimed and no qualifying new item was located in the material reviewed.
- Legacy source mismatch LEG-003957: The retained NPR payments-system source does not resolve the CNN/IRS claim. No responsible record-specific correction was established; the warning remains visible.
- Earlier unresolved leads: Previously withheld candidates remain in data/research_queue.json; no unresolved instrument, corroboration or source gap was silently resolved.

## Trump TV monitoring

- Checked: 2026-09-26 5:57:30 PM EDT
- Inspection state: partial_metadata_followup
- Current official stream link: https://www.youtube.com/watch?v=A4gNgHfZ-v4
- Last successful complete broadcast review: none; coverage boundary unknown

Follow-up inspection of the official Trump TV page, White House live page, dated video library, remarks index and releases index. The Trump TV and live pages still exposed the same official YouTube stream ID. No newer dated video, remarks or release listing was found after the prior baseline in the material reviewed. No complete footage, captions or transcript were retrieved, no broadcast-minute coverage is claimed, and no qualifying new item was located in the material reviewed.

Sources and material actually inspected:

- https://www.whitehouse.gov/trumptv/
- https://www.whitehouse.gov/live/
- https://www.whitehouse.gov/videos/
- https://www.whitehouse.gov/remarks/
- https://www.whitehouse.gov/releases/
- Page source exposed YouTube video ID A4gNgHfZ-v4, unchanged from the baseline. The page's fallback error text was not treated as proof that the stream was offline. (https://www.whitehouse.gov/trumptv/)
- Newest displayed recordings remained the September 25 China-state-visit items already present at baseline; no newly dated recording was located. (https://www.whitehouse.gov/videos/)
- Newest displayed remarks remained dated September 22; the index was not assumed to be a complete transcript feed. (https://www.whitehouse.gov/remarks/)
- Newest displayed release remained dated September 25; the index was used only as a supplementary lead source. (https://www.whitehouse.gov/releases/)

Access gaps and recheck requirements:

- The official stream page and stable video ID were inspected, but no complete recording, captions or transcript was retrieved; no footage was watched and no minute-by-minute coverage is claimed.
- Broadcast coverage boundary remains unknown; later checks must revisit inaccessible material and discover current official video IDs.
- Remarks and releases are supplementary sources, not assumed complete transcript feeds.
- No verified channel budget, contract, staffing allocation or shared funding with the separately paid advertisement was located.

## Verification

Current front-door pages, canonical datasets, archive bridge, individual evidence packs, versioned aggregate packs, source ledgers, and checksums are generated deterministically. Earlier date-only base aggregates remain byte-frozen and separately addressable; every new same-day aggregate is version-keyed. Candidate publication requires the repository validator and GitHub Actions to pass, followed by acceptance from the publication authority named above.

## Review traceability

- Current entries with content-bound claim-level receipts: 169 / 295
- Prior review-state labels are distinct from claim-level review receipt coverage.
- Stored post inspection-state records: 1321. Acquisition is not inspection.
- Per-post text/media states: data/truth_social_reviews.json; deferred follow-ups: data/research_queue.json.
- Actual acceptance results are recorded by scripts/accept_release.py and retained as a CI artifact; this generated receipt is not a test attestation.
