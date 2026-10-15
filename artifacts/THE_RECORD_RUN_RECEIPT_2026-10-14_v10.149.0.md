# The Record — Maintenance Run Receipt

- Release: 10.149.0
- Checked: 2026-10-14 11:56 PM EDT
- Editorial window: 2026-10-14 6:03 PM EDT through 2026-10-14 11:56 PM EDT
- Current layer: 395 records backed by 1213 source-ledger records
- Full archive runtime: 5,122 records; 7,914 source references; 6,516 distinct stored URLs
- Legacy custody: 4,742 stored rows; 4,731 active; 11 duplicate tombstones excluded from totals
- Truth Social source: 36,900 posts; 1,000 retained in the validated local fallback
- Newest Truth Social post: 2026-10-14 11:18:58 PM EDT
- Truth Social fallback checked: 2026-10-14 11:57:20 PM EDT
- Added: 2 national records
- Materially refreshed: 3 national records

## Added or materially refreshed records

- `NAT-2026-10-14-008` — GAO finds management gaps in CBP and ICE body-camera programs
- `NAT-2026-10-14-009` — Trump announces Pentagon weapons-testing 'super range' in Montana
- `NAT-2026-09-24-002` — Federal judge temporarily blocks taxpayer-funded Trump advertising campaign
- `NAT-2026-10-09-001` — U.S. sanctions the International Criminal Court as an institution
- `NAT-2026-10-12-001` — Federal agents execute search warrant at Rep. Ilhan Omar's home

## Withheld candidates

- Possible easing of Russian shadow-fleet sanctions: Reuters reported that the administration was considering delisting some vessels based on one unnamed official. No order, filed notice or second independent confirmation established a decision or implementation.
- Three newer Truth Social posts: The campaign-travel text and Caitlin Clark image supplied no government action. Representative frames from the rally video were inspected, but full motion, audio and captions remain pending; no claim from the sampled media was treated as evidence.
- Trump TV and official video-library recheck: The official pages retained stream ID A4gNgHfZ-v4 and added three October 14 clips. Only titles, dates, durations and stable video IDs were inspected; footage, audio, captions and complete transcripts were not retrieved, and the clips duplicated or supplied no independently qualifying action.
- D.C. National Guard appeal oral argument: The hearing did not itself alter the governing order; the existing record remains awaiting an appellate ruling.
- DHS final rule ending automatic EAD extensions: The October 14 final rule was discovered after the prior cutoff and outside this run's exact source window. Its quantified effects and 2025 interim-rule history remain a retrospective research lead for a dedicated source review rather than being padded into this release.

## Truth Social inspection

- New retained posts: 3
- Current retained inspection states: {"media_status": {"not_applicable": 829, "not_recorded": 19, "pending": 507, "reviewed": 126, "unavailable": 244}, "text_status": {"not_recorded": 147, "pending": 969, "reviewed": 609}}

Three posts were newer than the prior snapshot. Campaign-travel text and a Caitlin Clark sports image supplied no government action. Representative frames from the attached Montana-rally video were inspected, but full motion, audio and captions remain pending; no sampled-media claim was treated as independently verified.

## Trump TV monitoring

- Checked: 2026-10-15 12:02 AM EDT
- Inspection state: partial_metadata_recheck
- Current official stream link: https://www.youtube.com/watch?v=A4gNgHfZ-v4
- Last successful complete broadcast review: none; coverage boundary unknown

Official Trump TV, live, video-library, remarks and news pages were rechecked. The linked stream remained A4gNgHfZ-v4; fallback error text was not treated as proof of an outage. The dated library added three October 14 items: a Bullhead City press gaggle, a Golden Age of Science Summit clip and an America.Gov clip. Only page metadata, durations and stable video IDs were inspected; footage, audio, captions and complete transcripts were not retrieved. No qualifying new item located in the material reviewed.

Sources and material actually inspected:

- https://www.whitehouse.gov/trumptv/
- https://www.whitehouse.gov/live/
- https://www.whitehouse.gov/videos/
- https://www.whitehouse.gov/remarks/
- https://www.whitehouse.gov/news/
- Official page linked the unchanged A4gNgHfZ-v4 stream. No footage, audio or captions were retrieved; fallback text was not treated as proof of an outage. (https://www.whitehouse.gov/trumptv/)
- The hub linked the same Trump TV stream. Current live/replay state and audiovisual content were not independently reviewed. (https://www.whitehouse.gov/live/)
- The library led with three October 14 items. Titles, displayed dates, durations and stable YouTube IDs were inspected; footage, audio, captions and exact upload times were not retrieved. The Science Summit and America.Gov clips repeat already tracked subjects, and the press-gaggle metadata supplied no distinct action. (https://www.whitehouse.gov/videos/)
- The index was checked and was not treated as a complete Trump TV transcript feed. (https://www.whitehouse.gov/remarks/)
- The news index supplied no new Trump TV transcript or broadcast finding. (https://www.whitehouse.gov/news/)

Access gaps and recheck requirements:

- Broadcast footage, audio and captions were not retrieved, so no claim is made that every broadcast minute was reviewed.
- Current live/replay state was not independently verified; fallback text alone does not establish an outage.
- No complete transcript feed, channel budget, contract, staffing record or editorial-control record was available in the inspected official pages.

## Verification

Current front-door pages, canonical datasets, archive bridge, individual evidence packs, versioned aggregate packs, source ledgers, and checksums are generated deterministically. Earlier date-only base aggregates remain byte-frozen and separately addressable; every new same-day aggregate is version-keyed. Candidate publication requires the repository validator and GitHub Actions to pass, followed by acceptance from the publication authority named above.

## Review traceability

- Current entries with content-bound claim-level receipts: 272 / 395
- Prior review-state labels are distinct from claim-level review receipt coverage.
- Stored post inspection-state records: 1725. Acquisition is not inspection.
- Per-post text/media states: data/truth_social_reviews.json; deferred follow-ups: data/research_queue.json.
- Actual acceptance results are recorded by scripts/accept_release.py and retained as a CI artifact; this generated receipt is not a test attestation.
