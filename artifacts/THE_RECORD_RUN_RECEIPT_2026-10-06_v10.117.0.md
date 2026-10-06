# The Record — Maintenance Run Receipt

- Release: 10.117.0
- Checked: 2026-10-06 12:04 PM EDT
- Editorial window: 2026-10-06 5:57 AM EDT through 2026-10-06 12:04 PM EDT
- Current layer: 347 records backed by 1049 source-ledger records
- Full archive runtime: 5,074 records; 7,746 source references; 6,352 distinct stored URLs
- Legacy custody: 4,742 stored rows; 4,731 active; 11 duplicate tombstones excluded from totals
- Truth Social source: 36,727 posts; 1,000 retained in the validated local fallback
- Newest Truth Social post: 2026-10-06 11:25:01 AM EDT
- Truth Social fallback checked: 2026-10-06 11:57:52 AM EDT
- Added: 3 national records
- Materially refreshed: 2 national records

## Added or materially refreshed records

- `NAT-2026-10-06-001` — August trade deficit widens despite tariff policy; year-to-date gap remains smaller
- `NAT-2026-09-24-002` — Trump announces private funding shift for government-paid advertising campaign
- `NAT-2026-09-15-010` — Paramount closes Warner Bros merger after DOJ’s antitrust nonchallenge
- `NAT-2026-10-05-006` — EEOC asks court to uphold secrecy over law-firm DEI inquiry records
- `NAT-2026-10-05-007` — DOJ reports forty denaturalization complaints; citizenship outcomes remain unresolved

## Withheld candidates

- Truth Social visa-overstay audit lead: New presidential post linked a report about a prior administration. The original OIG-26-38 PDF returned HTTP403 and report dating/scope were not fully verified. The post establishes publication only; no underlying audit finding is adopted.
- Seven newer text-only Truth Social posts: All seven texts inspected. Campaign and media criticism, foreign migration rhetoric, rally claims, a vague Midterm Surprise and a conditional Chicago-help statement supplied no verified new national action or operational order. The audit link remains a separate unresolved lead.
- Trump TV stream and previously listed recordings: Official pages and stable linked IDs rechecked. Newest listed library item remains the October5 gaggle; stream and newest-recording platform requests returned HTTP429. No footage, audio or captions reviewed; no qualifying new item located in the material reviewed.
- Legacy same-date-heading pair LEG-004656 / LEG-004657: Canonical texts inspected: different judges, institutions and legal instruments despite the generated same-date-heading flag. Original rulings and disputed source dates were not inspected; no merge or historical review-state upgrade performed.

## Truth Social inspection

- New retained posts: 7
- Current retained inspection states: {"media_status": {"not_applicable": 456, "not_recorded": 19, "pending": 216, "reviewed": 75, "unavailable": 234}, "text_status": {"not_recorded": 136, "pending": 419, "reviewed": 445}}

Seven posts newer than the prior validated snapshot were acquired and their complete retained text inspected. All seven are text-only, with no attached media. Newest post: October6 11:25:01AM EDT; feed checked October6 11:57:52AM EDT. Routine claims were not promoted; the inaccessible original visa-overstay audit remains queued. Current retained pending/unavailable states are separately counted; this is not a claim that every historic post was reviewed.

## Trump TV monitoring

- Checked: 2026-10-06 12:04 PM EDT
- Inspection state: partial_metadata_recheck
- Current official stream link: https://www.youtube.com/watch?v=A4gNgHfZ-v4
- Last successful complete broadcast review: none; coverage boundary unknown

Official Trump TV, live, videos, remarks and releases HTML and dated metadata inspected. Stream ID remains A4gNgHfZ-v4; newest library listing remains October5 departure gaggle kuYkk0TxYuM. These are repeated listings, not newly established actions. Both stream and newest-recording YouTube requests returned HTTP429. No footage, audio or captions reviewed and no live/replay state inferred from fallback error text. No qualifying new item located in the material reviewed; no new verified channel cost, contract, staffing/control, distribution, press-access or investigative finding located.

Sources and material actually inspected:

- https://www.whitehouse.gov/trumptv/
- https://www.whitehouse.gov/live/
- https://www.whitehouse.gov/videos/
- https://www.whitehouse.gov/remarks/
- https://www.whitehouse.gov/releases/
- Official HTML linked the unchanged A4gNgHfZ-v4 stream. Current YouTube request returned HTTP429; live/replay state and audiovisual content unverified. Fallback text does not prove an outage. (https://www.whitehouse.gov/trumptv/)
- Official live hub HTML and links inspected; it linked the same A4gNgHfZ-v4 ID. Platform state and audiovisual content were not reviewed. (https://www.whitehouse.gov/live/)
- Official dated listing still ends with October5 departure gaggle kuYkk0TxYuM; all12 listed video IDs match the prior inspection. Newest recording request returned HTTP429. Titles/durations/dates were read; footage, audio and captions were not retrieved or reviewed. Older uploads are repeat leads. (https://www.whitehouse.gov/videos/)
- Supplementary remarks index inspected; September 28 remains its newest listed event. It is not assumed to be a complete Trump TV transcript feed. (https://www.whitehouse.gov/remarks/)
- Official release index inspected. October 5 diesel action is already canonical; Nebraska promotion is not independent investment or policy-effectiveness verification. A release listing does not prove that a statement aired on Trump TV. (https://www.whitehouse.gov/releases/)

Access gaps and recheck requirements:

- No complete Trump TV stream recording, stream captions, audio or footage was reviewed; no continuous or minute-by-minute coverage is claimed.
- Individual third-party verbatim transcripts were inspected for three dated clips, but they do not establish coverage of the stream or unreviewed library recordings.
- English auto-caption track metadata was available for AVw2HnrbY44, but the timed-text retrieval returned an empty response; no caption review is claimed.
- White House JSON-LD uploadDate is a publication timestamp, not verified original event or broadcast time. Edited-clip original event dates remain unknown unless independently established.
- No verified channel budget, contract, staffing allocation, editorial-control arrangement or common funding with the separate government-paid advertisement was located.
- Prior inaccessible media and the unresolved original Trump TV trademark filing remain open for recheck.
- Current YouTube player metadata request returned HTTP 429; recheck platform state, recordings and accessible captions without advancing a broadcast coverage claim.
- No complete recording or new transcript was retrieved in this check. The last successful complete broadcast review boundary remains unknown; page metadata review does not close footage gaps.
- This check retried both the linked stream and newest library recording; each platform request returned HTTP429. Complete broadcast boundary remains unknown and is not advanced.

## Verification

Current front-door pages, canonical datasets, archive bridge, individual evidence packs, versioned aggregate packs, source ledgers, and checksums are generated deterministically. Earlier date-only base aggregates remain byte-frozen and separately addressable; every new same-day aggregate is version-keyed. Candidate publication requires the repository validator and GitHub Actions to pass, followed by acceptance from the publication authority named above.

## Review traceability

- Current entries with content-bound claim-level receipts: 224 / 347
- Prior review-state labels are distinct from claim-level review receipt coverage.
- Stored post inspection-state records: 1551. Acquisition is not inspection.
- Per-post text/media states: data/truth_social_reviews.json; deferred follow-ups: data/research_queue.json.
- Actual acceptance results are recorded by scripts/accept_release.py and retained as a CI artifact; this generated receipt is not a test attestation.
