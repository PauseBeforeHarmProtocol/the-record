# The Record — Maintenance Run Receipt

- Release: 10.135.0
- Checked: 2026-10-10 11:58 PM EDT
- Editorial window: 2026-10-10 6:02 PM EDT through 2026-10-10 11:58 PM EDT
- Current layer: 374 records backed by 1136 source-ledger records
- Full archive runtime: 5,101 records; 7,837 source references; 6,439 distinct stored URLs
- Legacy custody: 4,742 stored rows; 4,731 active; 11 duplicate tombstones excluded from totals
- Truth Social source: 36,787 posts; 1,000 retained in the validated local fallback
- Newest Truth Social post: 2026-10-10 10:02:46 PM EDT
- Truth Social fallback checked: 2026-10-11 12:00:13 AM EDT
- Added: 1 national record
- Materially refreshed: 1 national record

## Added or materially refreshed records

- `NAT-2026-10-01-007` — Federal Medicaid eligibility restriction takes effect for many legal immigrants
- `NAT-2026-09-18-007` — DOJ opens antitrust investigation into White House television pool

## Withheld candidates

- Five new Truth Social posts: The appointment post was routine personnel news and the approval-rating repost was political rhetoric. Three media-only posts could not be retrieved through the available review path; their empty text and access limitation were recorded, and no claim was inferred from unavailable media.
- Katie Bailey appointment: Trump's appointment of a White House legislative-affairs director was verified but remains routine personnel news without a material policy or institutional consequence at cutoff.
- Trump TV metadata recheck: The official library added a 5:37 departure-gaggle clip dated October 10 with video ID kPscOnPqVM4. Only title, date, duration and link metadata were accessible; footage, audio and captions were not retrieved, and a replay or clip is not itself a new government action.
- Trump calls for a new Ukrainian president: The statement materially sharpened rhetoric toward Volodymyr Zelenskyy but did not itself create a U.S. order, formal proposal, appropriation, diplomatic agreement or implemented action; the related diesel and Houthi developments are already preserved in existing canonical records.
- The State of American Manufacturing: The October 10 White House research post summarized and advocated for existing policy; no new signed, ordered or implemented action was identified in it.

## Truth Social inspection

- New retained posts: 5
- Current retained inspection states: {"media_status": {"not_applicable": 795, "not_recorded": 19, "pending": 464, "reviewed": 95, "unavailable": 239}, "text_status": {"not_recorded": 147, "pending": 969, "reviewed": 496}}

Five posts newer than the prior snapshot were inspected as research leads. The two nonempty texts were an approval-rating repost and a routine legislative-affairs appointment. Three media-only posts had empty text; their videos, plus the repost image, could not be retrieved through the available review path. No unavailable media claim was inferred or promoted.

## Trump TV monitoring

- Checked: 2026-10-10 11:58 PM EDT
- Inspection state: partial_metadata_recheck
- Current official stream link: https://www.youtube.com/watch?v=A4gNgHfZ-v4
- Last successful complete broadcast review: none; coverage boundary unknown

Official Trump TV, live, video-library, remarks, briefings and release pages were rechecked. The stream link remained A4gNgHfZ-v4; fallback error text was not treated as proof of an outage. The library added a 5:37 departure-gaggle clip dated October 10 and linked YouTube video ID kPscOnPqVM4. Only page metadata was reviewed; footage, audio and captions could not be retrieved. No qualifying new item located in the material reviewed, and no verified new channel cost, contract, staffing/control, distribution, press-access consequence, investigation or court/congressional finding was located.

Sources and material actually inspected:

- https://www.whitehouse.gov/trumptv/
- https://www.whitehouse.gov/live/
- https://www.whitehouse.gov/videos/
- https://www.whitehouse.gov/remarks/
- https://www.whitehouse.gov/briefings-statements/
- https://www.whitehouse.gov/releases/
- Official page linked the unchanged A4gNgHfZ-v4 stream. No footage, audio or captions were retrieved; fallback text was not treated as proof of an outage. (https://www.whitehouse.gov/trumptv/)
- The hub linked the same Trump TV stream. Current live/replay state and audiovisual content were not independently reviewed. (https://www.whitehouse.gov/live/)
- The library listed a new 5:37 departure-gaggle clip dated October 10 and linked YouTube ID kPscOnPqVM4. Title, date, duration and link metadata were inspected; footage, audio and captions could not be retrieved, so no claim is made about the clip's contents. (https://www.whitehouse.gov/videos/)
- The index still listed Michael Kratsios's October 9 science-summit remarks as newest and was not treated as a complete Trump TV transcript feed. (https://www.whitehouse.gov/remarks/)
- The index still ended with October 9 messages and a routine signed-bill notice; it supplied no new Trump TV transcript or qualifying broadcast finding. (https://www.whitehouse.gov/briefings-statements/)
- The index still ended with October 8 releases. A listing was not treated as proof that material aired on Trump TV. (https://www.whitehouse.gov/releases/)

Access gaps and recheck requirements:

- Footage, audio and captions were not retrieved, so no claim is made that every broadcast minute was reviewed.
- Current live/replay state was not independently verified; page fallback text alone does not establish an outage.
- No complete transcript feed, channel budget, contract, staffing record or editorial-control record was available in the inspected official pages.

## Verification

Current front-door pages, canonical datasets, archive bridge, individual evidence packs, versioned aggregate packs, source ledgers, and checksums are generated deterministically. Earlier date-only base aggregates remain byte-frozen and separately addressable; every new same-day aggregate is version-keyed. Candidate publication requires the repository validator and GitHub Actions to pass, followed by acceptance from the publication authority named above.

## Review traceability

- Current entries with content-bound claim-level receipts: 251 / 374
- Prior review-state labels are distinct from claim-level review receipt coverage.
- Stored post inspection-state records: 1612. Acquisition is not inspection.
- Per-post text/media states: data/truth_social_reviews.json; deferred follow-ups: data/research_queue.json.
- Actual acceptance results are recorded by scripts/accept_release.py and retained as a CI artifact; this generated receipt is not a test attestation.
