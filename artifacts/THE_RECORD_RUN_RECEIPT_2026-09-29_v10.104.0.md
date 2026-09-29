# The Record — Maintenance Run Receipt

- Release: 10.104.0
- Checked: 2026-09-29 11:56 AM EDT
- Editorial window: 2026-09-29 5:58 AM EDT through 2026-09-29 11:56 AM EDT
- Current layer: 308 records backed by 889 source-ledger records
- Full archive runtime: 5,035 records; 7,586 source references; 6,192 distinct stored URLs
- Legacy custody: 4,742 stored rows; 4,731 active; 11 duplicate tombstones excluded from totals
- Truth Social source: 36,566 posts; 1,000 retained in the validated local fallback
- Newest Truth Social post: 2026-09-29 11:54:42 AM EDT
- Truth Social fallback checked: 2026-09-29 11:57:09 AM EDT
- Added: 1 national record
- Materially refreshed: 3 national records

## Added or materially refreshed records

- `NAT-2026-09-29-001` — Trump orders America.gov service portal and administration launches initial site
- `NAT-2026-08-22-001` — Targeted U.S. bans on Canadian imports take effect after reciprocal tariffs
- `NAT-2026-09-24-002` — Government-paid Trump ads top $1.4 million estimate as oversight expands
- `NAT-2026-08-17-001` — Trump rejects Iran proposal after Hormuz campaign and mediated talks

## Withheld candidates

- Jack Smith Senate testimony: Competing congressional testimony and allegations produced no new administration action, adjudicated finding or operative legal change.
- Supreme Court docket preview: No grant, stay, merits ruling or other operative court action existed by cutoff.
- Iran mediation and AI competition statements: No agreement, implementing instrument, force change or independently verified policy outcome was announced; rhetoric alone did not pass the threshold.
- Truth Social fallback: Two posts were added. One contained routine promotional text and a video; one was image-only. Both media assets returned HTTP 403, no inaccessible-media claim was used and neither established an independently verified qualifying action.
- Trump TV review: The official live hub displayed the America.gov announcement and a new official video ID, while the dated library and remarks index still ended September 28. Only metadata was inspected; no complete footage or transcript boundary was reviewed. The signed order and independent reporting, not the broadcast alone, support the America.gov record.
- External archive measurements: Trump Archive remained at 14,384 items, including 11,906 Truth Social posts and 1,836 speeches/transcripts. Immigration Policy Tracking remained at 1,796 and UndoTrump at 1,264. Record47's prior verified values were preserved because its current API was unavailable or inconsistent. Unlike units remain separate.
- Legacy-quality queue: No newly inspected record-specific evidence resolved the existing LEG-003757 or LEG-003957 source mismatches or the disclosed duplicate-candidate queue. No historical correction was made; existing warnings remain visible.

## Trump TV monitoring

- Checked: 2026-09-29 12:00:00 PM EDT
- Inspection state: partial_metadata_followup
- Current official stream link: https://www.youtube.com/watch?v=A4gNgHfZ-v4
- Last successful complete broadcast review: none; coverage boundary unknown

Rechecked the official Trump TV page, live hub, dated video library, remarks and news indexes. Trump TV stream ID A4gNgHfZ-v4 remained discoverable. The live hub displayed 'Announcement on America.gov' as on air with official embedded video ID qyJL5gKhajE. The dated library and remarks index still ended with September 28 material, while the news index exposed the signed America.gov order and fact sheet. Only page titles, dates, live-interface status and video IDs were inspected; no complete footage, captions or transcript was retrieved. The order and independent reporting, not the broadcast alone, support the new record. No other qualifying new item was located in the accessible material reviewed, and no complete broadcast boundary was advanced.

Sources and material actually inspected:

- https://www.whitehouse.gov/trumptv/
- https://www.whitehouse.gov/live/
- https://www.whitehouse.gov/videos/
- https://www.whitehouse.gov/remarks/
- https://www.whitehouse.gov/news/
- https://www.youtube.com/watch?v=qyJL5gKhajE
- Page metadata exposed YouTube video ID A4gNgHfZ-v4. Interface or fallback text was not treated as proof of offline status; footage was not retrieved. (https://www.whitehouse.gov/trumptv/)
- The hub displayed 'Announcement on America.gov' with embedded video ID qyJL5gKhajE. The interface status is recorded as observed metadata, not a claim of continuous monitoring. (https://www.whitehouse.gov/live/)
- The newest accessible library listings remained September 28 items; no September 29 archive page was located. (https://www.whitehouse.gov/videos/)
- The newest accessible listing remained a September 28 video page; no complete transcript was retrieved. (https://www.whitehouse.gov/remarks/)
- The index exposed the signed America.gov order and fact sheet, which were reviewed as primary records rather than as a transcript feed. (https://www.whitehouse.gov/news/)

Access gaps and recheck requirements:

- No complete Trump TV recording, captions or transcript was retrieved; no minute-by-minute or continuous broadcast coverage is claimed.
- Broadcast coverage boundary remains unknown; later checks must revisit inaccessible material and rediscover current official stream and clip IDs.
- Exact broadcast and upload times were not verified.
- Remarks and news listings are supplementary sources, not assumed complete transcript feeds.
- No verified channel budget, contract, staffing allocation or shared funding with separate government-paid advertisements was located.

## Verification

Current front-door pages, canonical datasets, archive bridge, individual evidence packs, versioned aggregate packs, source ledgers, and checksums are generated deterministically. Earlier date-only base aggregates remain byte-frozen and separately addressable; every new same-day aggregate is version-keyed. Candidate publication requires the repository validator and GitHub Actions to pass, followed by acceptance from the publication authority named above.

## Review traceability

- Current entries with content-bound claim-level receipts: 182 / 308
- Prior review-state labels are distinct from claim-level review receipt coverage.
- Stored post inspection-state records: 1390. Acquisition is not inspection.
- Per-post text/media states: data/truth_social_reviews.json; deferred follow-ups: data/research_queue.json.
- Actual acceptance results are recorded by scripts/accept_release.py and retained as a CI artifact; this generated receipt is not a test attestation.
