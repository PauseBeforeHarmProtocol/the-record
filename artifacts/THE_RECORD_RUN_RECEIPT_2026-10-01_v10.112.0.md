# The Record — Maintenance Run Receipt

- Release: 10.112.0
- Checked: 2026-10-01 6:00 PM EDT
- Editorial window: 2026-10-01 12:04 PM EDT through 2026-10-01 6:00 PM EDT
- Current layer: 333 records backed by 980 source-ledger records
- Full archive runtime: 5,060 records; 7,677 source references; 6,283 distinct stored URLs
- Legacy custody: 4,742 stored rows; 4,731 active; 11 duplicate tombstones excluded from totals
- Truth Social source: 36,617 posts; 1,000 retained in the validated local fallback
- Newest Truth Social post: 2026-10-01 5:30:06 PM EDT
- Truth Social fallback checked: 2026-10-01 6:00:42 PM EDT
- Added: 4 national records
- Materially refreshed: 1 national record

## Added or materially refreshed records

- `NAT-2026-10-01-002` — Court reinstates judicially appointed Seattle U.S. attorney
- `NAT-2026-10-01-003` — Treasury opens Iran rail and automotive sectors to sanctions and lists industrial networks
- `NAT-2026-10-01-004` — Treasury and IRS issue first rules for federal scholarship tax credit
- `NAT-2026-10-01-005` — Pentagon raises hostile-fire and imminent-danger pay
- `NAT-2026-09-15-003` — Federal noncitizen-voting push produces cases but no identified broad pattern

## Withheld candidates

- ICE internal traffic-stop guidance: The described memo was nonpublic and the consequential account rested on unnamed sources without a second independent confirmation or primary text.
- Iran ceasefire and retaliation statements: Presidential statements and campaign remarks did not identify a new strike order, ceasefire, agreement or other implemented action by the cutoff.
- Price and Iran nuclear Truth Social claims: The posts establish only that Trump made the claims; no independent evidence within the run established the broad causal or effectiveness assertions.
- Brian Meyers and Philip Aubart judicial announcements: The posts announced intended nominations but no formal Senate submission, hearing or confirmation; routine personnel announcements did not meet the threshold.
- Image and video Truth Social posts: Six media assets returned HTTP 403; the one accessible screenshot repeated an unverified claim about demonstrations in Iran and did not independently establish a qualifying action.
- Trump TV October 1 follow-up: The official channel and live-hub metadata exposed stable stream IDs and no October 1 library upload; complete footage, captions and transcripts were not retrieved, and no qualifying new item was located in the material reviewed.

## Trump TV monitoring

- Checked: 2026-10-01 6:14:00 PM EDT
- Inspection state: partial_metadata_followup
- Current official stream link: https://www.youtube.com/watch?v=A4gNgHfZ-v4
- Last successful complete broadcast review: none; coverage boundary unknown

The official Trump TV stream ID remained A4gNgHfZ-v4, while the White House live hub exposed event-stream ID 5fRpXOyalfc. The dated video library still ended with September 30 uploads; the remarks index ended September 28 and the only October 1 release was a general achievements post. Only page metadata, titles, dates, durations and IDs were inspected. Complete recordings, captions and transcripts were not retrieved; fallback error text was not used as proof that either stream was offline. No broadcast boundary was advanced, and no qualifying new item was located in the material reviewed.

Sources and material actually inspected:

- https://www.whitehouse.gov/trumptv/
- https://www.whitehouse.gov/live/
- https://www.whitehouse.gov/videos/
- https://www.whitehouse.gov/remarks/
- https://www.whitehouse.gov/releases/
- https://www.youtube.com/watch?v=A4gNgHfZ-v4
- https://www.youtube.com/watch?v=5fRpXOyalfc
- Page metadata exposed the unchanged Trump TV stream ID A4gNgHfZ-v4; footage and captions were not retrieved. (https://www.whitehouse.gov/trumptv/)
- Page source exposed event-stream ID 5fRpXOyalfc and Trump TV ID A4gNgHfZ-v4; footage was not retrieved and fallback text was not treated as a status finding. (https://www.whitehouse.gov/live/)
- The newest visible items remained September 30 uploads. Titles, dates and durations were inspected; no October 1 recording or complete captions were retrieved. (https://www.whitehouse.gov/videos/)
- The newest listed presidential remarks remained September 28; no newer complete transcript corresponding to a qualifying broadcast was retrieved. (https://www.whitehouse.gov/remarks/)
- The October 1 achievements release did not supply a complete Trump TV transcript or independently qualifying new action. (https://www.whitehouse.gov/releases/)

Access gaps and recheck requirements:

- No complete Trump TV or live-hub recording, captions or transcript was retrieved; no minute-by-minute or continuous coverage is claimed.
- Broadcast coverage boundary remains unknown and later checks must revisit inaccessible media.
- Exact broadcast and upload times were not verified.
- No verified channel budget, contract, staffing allocation or shared funding with the separate government-paid advertising contract was located.

## Verification

Current front-door pages, canonical datasets, archive bridge, individual evidence packs, versioned aggregate packs, source ledgers, and checksums are generated deterministically. Earlier date-only base aggregates remain byte-frozen and separately addressable; every new same-day aggregate is version-keyed. Candidate publication requires the repository validator and GitHub Actions to pass, followed by acceptance from the publication authority named above.

## Review traceability

- Current entries with content-bound claim-level receipts: 209 / 333
- Prior review-state labels are distinct from claim-level review receipt coverage.
- Stored post inspection-state records: 1441. Acquisition is not inspection.
- Per-post text/media states: data/truth_social_reviews.json; deferred follow-ups: data/research_queue.json.
- Actual acceptance results are recorded by scripts/accept_release.py and retained as a CI artifact; this generated receipt is not a test attestation.
