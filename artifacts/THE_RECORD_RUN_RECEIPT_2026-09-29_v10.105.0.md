# The Record — Maintenance Run Receipt

- Release: 10.105.0
- Checked: 2026-09-29 5:56 PM EDT
- Editorial window: 2026-09-29 11:56 AM EDT through 2026-09-29 5:56 PM EDT
- Current layer: 311 records backed by 899 source-ledger records
- Full archive runtime: 5,038 records; 7,596 source references; 6,202 distinct stored URLs
- Legacy custody: 4,742 stored rows; 4,731 active; 11 duplicate tombstones excluded from totals
- Truth Social source: 36,569 posts; 1,000 retained in the validated local fallback
- Newest Truth Social post: 2026-09-29 5:24:58 PM EDT
- Truth Social fallback checked: 2026-09-29 5:57:34 PM EDT
- Added: 3 national records
- Materially refreshed: 3 national records

## Added or materially refreshed records

- `NAT-2026-09-29-002` — Trump orders federal mosquito and tick reduction campaign in Washington
- `NAT-2026-09-29-003` — Trump orders executive branch to call artificial intelligence 'Super Intelligence'
- `NAT-2026-09-29-004` — Trump and technology executives sign voluntary AI safety accord
- `NAT-2026-09-23-004` — Supreme Court temporarily restores third-country removals pending appeal
- `NAT-2026-09-24-002` — DHS identifies $20 million contract behind government-paid Trump ads
- `NAT-2026-09-25-009` — GAO says Trump's $810 million pocket rescission violates spending law

## Withheld candidates

- Truth Social fallback: Three posts were added. Two were image-only and all three image assets returned HTTP 403; the text post linked an unverified Strait of Hormuz assertion. No inaccessible-media claim or independently unverified assertion was used, and all three remain feed-only.
- Trump TV review: The official Trump TV and live-hub video IDs were unchanged, while the dated video library and remarks index still ended with September 28 material. Only accessible page metadata was inspected; no complete footage, captions or transcript boundary was reviewed. No qualifying new item was located in the broadcast material reviewed.
- European diesel drawdown request: The reported White House request and voluntary export alternatives rested on unnamed sources; no public directive, final agreement or second independent confirmation was obtained.
- DOJ investigation staffing report: The reported departure remained source-dependent and did not establish a completed investigative disposition; a confirmed evolution belongs in the existing canonical investigation record.
- Campaign travel, Jack Smith testimony and Cuba rhetoric: The reviewed material did not establish a new operative administration action, adjudicated finding or implemented policy change.
- External archive measurements: Trump Archive remained at 14,384 items, including 11,906 Truth Social posts and 1,836 speeches/transcripts. Immigration Policy Tracking remained at 1,796 and UndoTrump at 1,264. Record47's prior verified values were preserved because its current API was unavailable or inconsistent. Unlike units remain separate.
- Legacy-quality queue: No newly inspected record-specific evidence resolved the existing LEG-003757 or LEG-003957 source mismatches or the disclosed duplicate-candidate queue. No historical correction was made; existing warnings remain visible.

## Trump TV monitoring

- Checked: 2026-09-29 6:03:00 PM EDT
- Inspection state: partial_metadata_followup
- Current official stream link: https://www.youtube.com/watch?v=A4gNgHfZ-v4
- Last successful complete broadcast review: none; coverage boundary unknown

Rechecked the official Trump TV page, live hub, dated video library, remarks and presidential-actions index. Trump TV stream ID A4gNgHfZ-v4 and live-hub embed qyJL5gKhajE remained discoverable. The dated video library and remarks index still ended with September 28 material. Only page titles, dates and video IDs were inspected; no complete footage, captions or transcript was retrieved, and no broadcast boundary was advanced. The two signed orders were reviewed from their official texts, not inferred from a broadcast. No qualifying new item was located in the accessible broadcast material reviewed.

Sources and material actually inspected:

- https://www.whitehouse.gov/trumptv/
- https://www.whitehouse.gov/live/
- https://www.whitehouse.gov/videos/
- https://www.whitehouse.gov/remarks/
- https://www.whitehouse.gov/presidential-actions/
- https://www.youtube.com/watch?v=qyJL5gKhajE
- Page metadata exposed YouTube video ID A4gNgHfZ-v4. Footage was not retrieved and interface text was not treated as proof of continuous status. (https://www.whitehouse.gov/trumptv/)
- The hub continued to expose embedded video ID qyJL5gKhajE. The observed listing is metadata, not a claim of continuous monitoring. (https://www.whitehouse.gov/live/)
- The newest accessible library listings remained September 28 items; no September 29 archive page was located. (https://www.whitehouse.gov/videos/)
- The newest accessible listing remained September 28; no complete transcript was retrieved. (https://www.whitehouse.gov/remarks/)
- The signed pest-control and Super Intelligence orders were inspected as primary written instruments rather than as broadcast transcripts. (https://www.whitehouse.gov/presidential-actions/)

Access gaps and recheck requirements:

- No complete Trump TV recording, captions or transcript was retrieved; no minute-by-minute or continuous broadcast coverage is claimed.
- Broadcast coverage boundary remains unknown; later checks must revisit inaccessible material and rediscover current official stream and clip IDs.
- Exact broadcast and upload times were not verified.
- Remarks and presidential-action listings are supplementary sources, not assumed complete transcript feeds.
- No verified channel budget, contract, staffing allocation or shared funding with the separate government-paid advertising contract was located.

## Verification

Current front-door pages, canonical datasets, archive bridge, individual evidence packs, versioned aggregate packs, source ledgers, and checksums are generated deterministically. Earlier date-only base aggregates remain byte-frozen and separately addressable; every new same-day aggregate is version-keyed. Candidate publication requires the repository validator and GitHub Actions to pass, followed by acceptance from the publication authority named above.

## Review traceability

- Current entries with content-bound claim-level receipts: 185 / 311
- Prior review-state labels are distinct from claim-level review receipt coverage.
- Stored post inspection-state records: 1393. Acquisition is not inspection.
- Per-post text/media states: data/truth_social_reviews.json; deferred follow-ups: data/research_queue.json.
- Actual acceptance results are recorded by scripts/accept_release.py and retained as a CI artifact; this generated receipt is not a test attestation.
