# The Record — Maintenance Run Receipt

- Release: 10.107.0
- Checked: 2026-09-30 6:00 AM EDT
- Editorial window: 2026-09-29 11:57 PM EDT through 2026-09-30 6:00 AM EDT
- Current layer: 318 records backed by 916 source-ledger records
- Full archive runtime: 5,045 records; 7,613 source references; 6,219 distinct stored URLs
- Legacy custody: 4,742 stored rows; 4,731 active; 11 duplicate tombstones excluded from totals
- Truth Social source: 36,570 posts; 1,000 retained in the validated local fallback
- Newest Truth Social post: 2026-09-29 8:11:21 PM EDT
- Truth Social fallback checked: 2026-09-30 6:01:41 AM EDT
- Added: 3 national records
- Materially refreshed: 1 national record

## Added or materially refreshed records

- `NAT-2026-09-29-009` — United States formally withdraws from European anti-corruption watchdog
- `NAT-2026-09-29-010` — EPA unions sue to restore terminated collective-bargaining agreement
- `NAT-2026-09-30-001` — U.S. military completes withdrawal from Iraq and ends coalition mission
- `NAT-2026-08-31-001` — Bureau of Prisons finalizes broader First Step Act time-credit eligibility

## Withheld candidates

- Truth Social fallback: The validated fallback remained at 36,570 posts. No post newer than September 29 at 8:11:21 PM EDT was located, and the newest image-only post remained inaccessible because its three referenced assets returned HTTP 403; it stays feed-only.
- Trump TV review: The official stream ID and September 29 video-library listings were unchanged. Only page metadata was accessible; direct YouTube retrieval remained blocked, no complete footage, captions or transcript boundary was reviewed, and no qualifying new item was located in the material reviewed.
- Boasberg contempt-probe appellate argument: The material reviewed described oral argument rather than an appellate decision, stay, remand or changed operative order.
- TSA checkpoint seating directive: Reporting described a nationwide instruction barring officers from sitting during routine identification checks. No primary directive or material security finding was located, and the workforce rule did not clear the archive's national-impact threshold in this run.
- White House press-access extension request: The filing sought continuation of an injunction but no new court ruling had issued by cutoff.
- Diesel-export and Korea investment deliberations: The reviewed reports described prospective decisions, internal deliberations or unnamed-source expectations. No signed instrument, final announcement or implemented action existed by cutoff.
- External archive measurements: Trump Archive remained at its prior verified 14,384 items, including 11,906 Truth Social posts and 1,836 speeches/transcripts, and UndoTrump remained at 1,264 actions. Immigration Policy Tracking exposed inconsistent 1,796 and 1,799 counts across its own pages, and Record47 remained unavailable or inconsistent; prior measurements were preserved. Unlike units remain separate.
- Legacy-quality queue: No newly inspected record-specific evidence resolved the existing LEG-003757 or LEG-003957 source mismatches or the disclosed duplicate-candidate queue. No historical correction was made; existing warnings remain visible.

## Trump TV monitoring

- Checked: 2026-09-30 6:06:30 AM EDT
- Inspection state: partial_metadata_followup
- Current official stream link: https://www.youtube.com/watch?v=A4gNgHfZ-v4
- Last successful complete broadcast review: none; coverage boundary unknown

Rechecked the official Trump TV page, live hub, dated video library and remarks index. Stream ID A4gNgHfZ-v4 remained discoverable, while the library still ended with the same September 29 America.gov replay, Vance fireside chat, Trump remarks, Super Intelligence clip, America.gov short and Presidents Cup clip. No September 30 video or newer remarks transcript appeared. Direct YouTube retrieval remained blocked; only titles, durations, dates and IDs were inspected, no complete footage, captions or transcript was retrieved, and no broadcast boundary was advanced. No qualifying new item was located in the material reviewed.

Sources and material actually inspected:

- https://www.whitehouse.gov/trumptv/
- https://www.whitehouse.gov/live/
- https://www.whitehouse.gov/videos/
- https://www.whitehouse.gov/remarks/
- https://www.youtube.com/watch?v=qyJL5gKhajE
- Page metadata exposed YouTube video ID A4gNgHfZ-v4. Footage was not retrieved and interface text was not treated as proof of continuous status. (https://www.whitehouse.gov/trumptv/)
- The hub linked the same Trump TV stream ID A4gNgHfZ-v4 and displayed fallback status text. The text was not treated as proof that the stream was offline, and direct footage was not retrieved. (https://www.whitehouse.gov/live/)
- The newest metadata remained the same September 29 America.gov replay, Vance fireside chat, Trump remarks, Super Intelligence clip, America.gov short and Presidents Cup clip. No September 30 listing appeared; complete footage and captions were not retrieved. (https://www.whitehouse.gov/videos/)
- The newest accessible remarks listing remained September 28; no September 29 or September 30 complete transcript was retrieved. (https://www.whitehouse.gov/remarks/)

Access gaps and recheck requirements:

- No complete Trump TV recording, captions or transcript was retrieved; direct YouTube access returned an automated-traffic block and no minute-by-minute or continuous coverage is claimed.
- Broadcast coverage boundary remains unknown; later checks must revisit inaccessible material and rediscover current official stream and clip IDs.
- Exact broadcast and upload times were not verified.
- Remarks and presidential-action listings are supplementary sources, not assumed complete transcript feeds.
- No verified channel budget, contract, staffing allocation or shared funding with the separate government-paid advertising contract was located.

## Verification

Current front-door pages, canonical datasets, archive bridge, individual evidence packs, versioned aggregate packs, source ledgers, and checksums are generated deterministically. Earlier date-only base aggregates remain byte-frozen and separately addressable; every new same-day aggregate is version-keyed. Candidate publication requires the repository validator and GitHub Actions to pass, followed by acceptance from the publication authority named above.

## Review traceability

- Current entries with content-bound claim-level receipts: 194 / 318
- Prior review-state labels are distinct from claim-level review receipt coverage.
- Stored post inspection-state records: 1394. Acquisition is not inspection.
- Per-post text/media states: data/truth_social_reviews.json; deferred follow-ups: data/research_queue.json.
- Actual acceptance results are recorded by scripts/accept_release.py and retained as a CI artifact; this generated receipt is not a test attestation.
