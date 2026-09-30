# The Record — Maintenance Run Receipt

- Release: 10.106.0
- Checked: 2026-09-29 11:57 PM EDT
- Editorial window: 2026-09-29 5:56 PM EDT through 2026-09-29 11:57 PM EDT
- Current layer: 315 records backed by 907 source-ledger records
- Full archive runtime: 5,042 records; 7,604 source references; 6,210 distinct stored URLs
- Legacy custody: 4,742 stored rows; 4,731 active; 11 duplicate tombstones excluded from totals
- Truth Social source: 36,570 posts; 1,000 retained in the validated local fallback
- Newest Truth Social post: 2026-09-29 8:11:21 PM EDT
- Truth Social fallback checked: 2026-09-29 11:58:44 PM EDT
- Added: 4 national records
- Materially refreshed: 2 national records

## Added or materially refreshed records

- `NAT-2026-09-29-005` — Treasury finalizes automatic establishment of Trump Accounts
- `NAT-2026-09-29-006` — DHS finalizes higher EB-5 immigrant-investor fees
- `NAT-2026-09-29-007` — Energy Department solicits exchange of up to 40 million reserve barrels
- `NAT-2026-09-29-008` — Appeals court declines to stay sanctions in Trump IRS settlement case
- `NAT-2026-09-03-003` — Treasury implements and codifies Cuba sanctions as embassy warns of infrastructure-linked illness
- `NAT-2026-09-29-004` — Trump and technology executives sign voluntary AI safety accord

## Withheld candidates

- Truth Social fallback: One image-only post was added. All three referenced image assets returned HTTP 403 with text/html rather than image content. No inaccessible-media claim was used, and the post remains feed-only.
- Trump TV review: The dated video library exposed new September 29 listings, including a long America.gov replay, routine remarks and short clips. Only page metadata was accessible; direct YouTube retrieval was blocked, no complete footage, captions or transcript boundary was reviewed, and no qualifying new item was located in the material reviewed.
- Boasberg contempt-probe appellate argument: The material reviewed described oral argument rather than an appellate decision, stay, remand or changed operative order.
- Iran statements and campaign appearances: The reviewed rhetoric and travel did not establish a new signed, ordered, implemented or adjudicated national action.
- White House press-access extension request: The filing sought continuation of an injunction but no new court ruling had issued by cutoff.
- External archive measurements: Trump Archive remained at 14,384 items, including 11,906 Truth Social posts and 1,836 speeches/transcripts. Immigration Policy Tracking remained at 1,796 and UndoTrump at 1,264. Record47's prior verified values were preserved because its current API was unavailable or inconsistent. Unlike units remain separate.
- Legacy-quality queue: No newly inspected record-specific evidence resolved the existing LEG-003757 or LEG-003957 source mismatches or the disclosed duplicate-candidate queue. No historical correction was made; existing warnings remain visible.

## Trump TV monitoring

- Checked: 2026-09-30 12:01:41 AM EDT
- Inspection state: partial_metadata_followup
- Current official stream link: https://www.youtube.com/watch?v=A4gNgHfZ-v4
- Last successful complete broadcast review: none; coverage boundary unknown

Rechecked the official Trump TV page, live hub, dated video library and remarks index. Stream ID A4gNgHfZ-v4 and live-hub/replay ID qyJL5gKhajE remained discoverable. The library added September 29 metadata for the America.gov replay, a Vance fireside chat, Trump remarks, a Super Intelligence clip, an America.gov short and a Presidents Cup clip. Direct YouTube access was blocked by an automated-traffic page; only titles, durations, dates and IDs were inspected, no complete footage, captions or transcript was retrieved, and no broadcast boundary was advanced. The America.gov and Super Intelligence material duplicated already catalogued events. No qualifying new item was located in the material reviewed.

Sources and material actually inspected:

- https://www.whitehouse.gov/trumptv/
- https://www.whitehouse.gov/live/
- https://www.whitehouse.gov/videos/
- https://www.whitehouse.gov/remarks/
- https://www.whitehouse.gov/presidential-actions/
- https://www.youtube.com/watch?v=qyJL5gKhajE
- Page metadata exposed YouTube video ID A4gNgHfZ-v4. Footage was not retrieved and interface text was not treated as proof of continuous status. (https://www.whitehouse.gov/trumptv/)
- The hub and library exposed video ID qyJL5gKhajE as an 8:38:21 America.gov replay. Direct retrieval was blocked, and the listing was deduplicated from the already catalogued America.gov action. (https://www.whitehouse.gov/live/)
- Metadata listed the America.gov replay, a Vance fireside chat, Trump remarks, a Super Intelligence clip, an America.gov short and a Presidents Cup clip. Complete footage and captions were not retrieved. (https://www.whitehouse.gov/videos/)
- The newest accessible transcript listing remained September 28; no September 29 complete transcript was retrieved. (https://www.whitehouse.gov/remarks/)
- The signed pest-control and Super Intelligence orders were inspected as primary written instruments rather than as broadcast transcripts. (https://www.whitehouse.gov/presidential-actions/)

Access gaps and recheck requirements:

- No complete Trump TV recording, captions or transcript was retrieved; direct YouTube access returned an automated-traffic block and no minute-by-minute or continuous coverage is claimed.
- Broadcast coverage boundary remains unknown; later checks must revisit inaccessible material and rediscover current official stream and clip IDs.
- Exact broadcast and upload times were not verified.
- Remarks and presidential-action listings are supplementary sources, not assumed complete transcript feeds.
- No verified channel budget, contract, staffing allocation or shared funding with the separate government-paid advertising contract was located.

## Verification

Current front-door pages, canonical datasets, archive bridge, individual evidence packs, versioned aggregate packs, source ledgers, and checksums are generated deterministically. Earlier date-only base aggregates remain byte-frozen and separately addressable; every new same-day aggregate is version-keyed. Candidate publication requires the repository validator and GitHub Actions to pass, followed by acceptance from the publication authority named above.

## Review traceability

- Current entries with content-bound claim-level receipts: 190 / 315
- Prior review-state labels are distinct from claim-level review receipt coverage.
- Stored post inspection-state records: 1394. Acquisition is not inspection.
- Per-post text/media states: data/truth_social_reviews.json; deferred follow-ups: data/research_queue.json.
- Actual acceptance results are recorded by scripts/accept_release.py and retained as a CI artifact; this generated receipt is not a test attestation.
