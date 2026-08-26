from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import textwrap
import zipfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CANONICAL = ROOT / "data/legacy_entries.json"
REVISIONS = ROOT / "data/legacy_revisions.json"
MANIFEST = ROOT / "data/legacy_restoration_manifest.json"

SOURCE_NAME = "The_Record_Source_2026-08-03_v13.zip"
SOURCE_SHA256 = "58b3543508d42d138f9079026158b2e63288603c93896d05d31f2f3b1a7635e2"
SOURCE_COMMIT = "ca80bae3a3f059d9ec4d5c9fc4a89545f52c6560"
SOURCE_HTML = "public/national.html"
SOURCE_RECORD_COUNT = 4_746
SOURCE_REFERENCE_COUNT = 6_697
RESTORED_SOURCE_REFERENCE_COUNT = 212
RESTORED_CANONICAL_REFERENCE_COUNT = 217
FIRST_RESTORED_ID = 4_648
RECORDED_AT = "2026-08-26"
MISSING_MARKER = {"$missing": True}

# Zero-based indices into the exact v13 #dataEntries array. These rows were
# published in v13, disappeared during the repository migration, and survived
# semantic comparison against both current canonical layers.
RESTORE_INDICES = (
    3930,
    3931,
    4249,
    4448,
    4619,
    4631,
    4632,
    4649,
    4654,
    4655,
    *range(4658, 4736),
    4737,
    4739,
    4740,
    4741,
    4743,
    4744,
    4745,
)

# These four v13 rows are deliberately not restored as active rows. Each is the
# same event as a richer record that already survives in the current runtime.
EXCLUDED_DUPLICATES = {
    4648: {
        "duplicate_of": "LEG-004635",
        "reason": "Same May 28 Carl Nichols mail-voting ruling; the surviving record is more complete and shares the NPR source URL.",
    },
    4736: {
        "duplicate_of": "NAT-2026-07-18-004",
        "reason": "Same Iran War Powers notice and identical Reuters source URL.",
    },
    4738: {
        "duplicate_of": "NAT-2026-07-18-003",
        "reason": "Same Bears Ears and Grand Staircase monument action with shared White House sources.",
    },
    4742: {
        "duplicate_of": "NAT-2026-07-19-001",
        "reason": "Same election-files address and release event with an identical Reuters source URL.",
    },
}

# Preserve each published source value in its creation revision, then apply
# explicit corrections for issues found during reconciliation. This keeps exact
# custody and the public record's corrected state simultaneously auditable.
SOURCE_CORRECTIONS = {
    4661: {
        "kind": "date-event-and-source-correction",
        "summary": "Correct Executive Order 14407's signing date and place it in the prior-memorandum lifecycle.",
        "reason": (
            "The White House text dates Executive Order 14407 to May 29, not June 2, and says it "
            "implements the December 5, 2025 presidential memorandum."
        ),
        "provenance": [
            {
                "type": "primary-source",
                "supports": "The signed order supplies its May 29 date, number, operative text, and predecessor memorandum.",
                "url": "https://www.whitehouse.gov/presidential-actions/2026/05/realigning-united-states-core-childhood-vaccine-recommendations-with-best-practices-from-peer-developed-countries/",
            }
        ],
        "changes": {
            "sort": "2026-05-29",
            "date": "May 29, 2026",
            "text": (
                "President Trump signed Executive Order 14407 on May 29, 2026, directing HHS, "
                "the CDC, and the Advisory Committee on Immunization Practices to review a January "
                "2026 assessment and realign the childhood and adolescent vaccine schedule with "
                "recommendations in peer countries. The order says vaccines already available remain "
                "covered without cost sharing by private insurance, Medicaid, CHIP, and the Vaccines "
                "for Children program. It implements a December 5, 2025 presidential memorandum and "
                "followed January HHS/CDC schedule changes; it was not the first presidential direction "
                "in this policy lifecycle."
            ),
            "sig": (
                "Moves prior White House direction into an executive order and steers the expert "
                "advisory process toward a narrower peer-country schedule. **Pattern-fit: executive "
                "direction of a scientific-advisory function.** Because insurance coverage and "
                "school-entry rules often track ACIP/CDC recommendations, later implementation can "
                "affect access beyond the schedule's advisory wording."
            ),
            "goal": (
                "\"This aligns the United States with peer developed nations, preserves vaccine "
                "access and coverage, and directs an evidence review rather than banning a vaccine.\""
            ),
            "mt": (
                "Maybe peer-country comparisons, preserved coverage, and a review mechanism make the "
                "order more limited than an immediate vaccine ban. Therefore the entry records the "
                "May 29 directive as one stage in a longer policy lifecycle because the president set "
                "the direction of a scientific advisory review whose recommendations affect access."
            ),
            "src": [
                {
                    "t": "White House — Executive Order 14407",
                    "url": "https://www.whitehouse.gov/presidential-actions/2026/05/realigning-united-states-core-childhood-vaccine-recommendations-with-best-practices-from-peer-developed-countries/",
                },
                {
                    "t": "U.S. News",
                    "url": "https://www.usnews.com/news/health-news/articles/2026-06-02/trump-signs-order-calling-for-fewer-childhood-vaccines",
                },
                {
                    "t": "CIDRAP",
                    "url": "https://www.cidrap.umn.edu/childhood-vaccines/trump-executive-order-directs-cdc-realign-childhood-vaccine-recommendations",
                },
            ],
        },
    },
    4672: {
        "kind": "lifecycle-consolidation",
        "summary": "Consolidate NSF's proposed ocean-observatory dismantling with its June 18 reversal.",
        "reason": (
            "The recovered June 5 row stopped at the announced dismantling; NSF reversed course on "
            "June 18, halted further removals, and said removed equipment would be redeployed."
        ),
        "provenance": [
            {
                "type": "primary-source",
                "supports": "The Ocean Observatories Initiative update records NSF's June 18 change in course.",
                "url": "https://oceanobservatories.org/2026/05/nsf-ooi-descoping-update-for-the-community/",
            },
            {
                "type": "independent-reporting",
                "supports": "Associated Press reporting corroborates the reversal and the stated operational steps.",
                "url": "https://apnews.com/article/7e00d19c0af8b15400d7621dcbaa2013",
            },
        ],
        "changes": {
            "date": "June 5–18, 2026",
            "text": (
                "The administration began dismantling the National Science Foundation's Ocean "
                "Observatories Initiative, with plans affecting more than 900 ocean sensors used to "
                "study circulation, ecosystems, climate, and extreme weather. After objections from "
                "scientists and lawmakers, NSF reversed course on June 18: it said it would stop "
                "removing or disabling equipment, redeploy instruments already removed after service, "
                "and convene an expert panel on the network's future."
            ),
            "sig": (
                "The initial dismantling threatened a major public scientific-data system; the reversal "
                "shows organized scientific and congressional scrutiny changing the implementation. "
                "**Pattern-fit: federal science infrastructure placed at risk, followed by a measurable "
                "institutional check.**"
            ),
            "goal": (
                "\"Reviewing an aging, expensive network was legitimate budget oversight, and NSF's "
                "reversal shows the process responded when the operational risks became clear.\""
            ),
            "mt": (
                "Maybe reviewing aging instruments and reprioritizing science budgets was legitimate, "
                "and the June 18 reversal is evidence that feedback worked. Therefore the record must "
                "preserve both stages: the attempted loss of more than 900 sensors and the later decision "
                "to keep the network operating and redeploy removed equipment."
            ),
            "src": [
                {
                    "t": "Democracy Now!",
                    "url": "https://www.democracynow.org/2026/6/5/headlines/trump_administration_scraps_ocean_sensors_that_track_climate_change_and_predict_storms",
                },
                {
                    "t": "Ocean Observatories Initiative — NSF update",
                    "url": "https://oceanobservatories.org/2026/05/nsf-ooi-descoping-update-for-the-community/",
                },
                {
                    "t": "Associated Press",
                    "url": "https://apnews.com/article/7e00d19c0af8b15400d7621dcbaa2013",
                },
            ],
        },
    },
    4688: {
        "kind": "maybe-therefore-layer",
        "summary": "Repair a malformed legacy Maybe / Therefore layer while preserving its consequence clause.",
        "reason": (
            "The published v13 layer began with a consequence statement rather than the required "
            "competing-frame Maybe clause."
        ),
        "provenance": [
            {
                "type": "internal-structure",
                "supports": "The source value contains a Therefore clause but no Maybe clause.",
            }
        ],
        "changes": {
            "mt": (
                "Maybe the distributed concert was ordinary expressive civic activity rather than "
                "a government action, and its lower-confrontation format was a legitimate organizing "
                "choice. Therefore it is logged as the window's principal organized opposition event, "
                "against the backdrop of the ongoing D.C. National Guard deployment."
            )
        },
    },
    4701: {
        "kind": "event-and-source-correction",
        "summary": "Correct the President's House ruling from removal to replacement and add direct reporting.",
        "reason": (
            "The Third Circuit allowed the National Park Service to replace the original exhibit; it "
            "did not authorize a categorical removal of all slavery history."
        ),
        "provenance": [
            {
                "type": "independent-reporting",
                "supports": "Reuters describes the ruling, the prior injunction, and the proposed replacement panels.",
                "url": "https://www.reuters.com/legal/government/trump-administration-may-alter-slavery-exhibit-philadelphia-site-court-says-2026-06-18/",
            },
            {
                "type": "independent-reporting",
                "supports": "Associated Press corroborates that the ruling permits replacement rather than erasure of every slavery reference.",
                "url": "https://apnews.com/article/6996253ba77a2a3ac1a5f6732576980b",
            },
        ],
        "changes": {
            "text": (
                "A unanimous Third Circuit panel overturned the preliminary injunction that had "
                "required the National Park Service to reinstall the original President's House panels "
                "in Philadelphia, allowing the administration to replace the exhibit. The original "
                "installation centered the nine people enslaved by George Washington at the site; the "
                "proposed replacement still discusses slavery but drew criticism from city officials and "
                "historians who said it sanitizes that history. The ruling addressed the government's "
                "authority and the city's claims; it did not find the original history false or finally "
                "resolve every related challenge."
            ),
            "sig": (
                "An appellate win permits replacement of a slavery-centered public-history exhibit, "
                "while the planned panels continue to mention slavery. **Pattern-fit: courts defining "
                "the executive's control over federal historical interpretation amid competing claims "
                "about accuracy and sanitization.**"
            ),
            "goal": (
                "\"The National Park Service controls the federal site, may revise its interpretation, "
                "and proposed panels still acknowledge slavery and add broader historical context.\""
            ),
            "mt": (
                "Maybe federal site management includes authority to revise exhibits, and the replacement "
                "panels still discuss slavery. Therefore the entry records the narrower consequence: the "
                "court allowed replacement of the original panels about nine enslaved people, not a "
                "categorical erasure of every reference to slavery."
            ),
            "src": [
                {
                    "t": "Reuters",
                    "url": "https://www.reuters.com/legal/government/trump-administration-may-alter-slavery-exhibit-philadelphia-site-court-says-2026-06-18/",
                },
                {
                    "t": "Associated Press",
                    "url": "https://apnews.com/article/6996253ba77a2a3ac1a5f6732576980b",
                },
                {
                    "t": "CBS News Philadelphia",
                    "url": "https://www.cbsnews.com/philadelphia/news/presidents-house-philadelphia-slavery-exhibits-court-ruling/",
                },
            ],
        },
    },
}

# A current canonical row encountered during reconciliation repeated the first
# reports too broadly. Later reporting and the responsible U.S. attorney's
# statement narrowed the investigation to the funding nonprofit, not Carroll as
# a named investigation subject. Correct the surviving row instead of importing
# the draft as a duplicate.
EXISTING_RECORD_CORRECTIONS = {
    "LEG-004634": {
        "kind": "event-and-source-correction",
        "summary": "Correct the reported Carroll investigation target and preserve the official denial.",
        "provenance": [
            {
                "type": "official-statement",
                "supports": "The U.S. Attorney for the Northern District of Illinois said the office had never opened a criminal investigation into E. Jean Carroll.",
                "url": "https://x.com/NDILnews/status/2060124784978010186",
            },
            {
                "type": "independent-reporting",
                "supports": "Associated Press reported that its source clarified the actual focus was the nonprofit that helped fund Carroll's case.",
                "url": "https://news.wttw.com/2026/05/28/justice-department-s-investigation-e-jean-carroll-who-accused-trump-assault-led-chicago",
            },
            {
                "type": "independent-reporting",
                "supports": "The Guardian separately reported that Carroll was not the subject and described the nonprofit-focused theories.",
                "url": "https://www.theguardian.com/us-news/2026/may/28/e-jean-carroll-doj-trump-reid-hoffman",
            },
        ],
        "replacements": {
            "review_status": "corrected",
            "sort": "2026-05-27",
            "date": "May 27–28, 2026",
            "text": (
                "On May 27 and 28, multiple outlets initially reported that the Justice Department "
                "had opened a perjury investigation into E. Jean Carroll based on her 2022 deposition "
                "about outside funding for the civil cases she won against Trump. U.S. Attorney Andrew "
                "Boutros then said the Northern District of Illinois had not opened and had never opened "
                "a criminal investigation into Carroll. Associated Press reported that its source later "
                "clarified the actual focus was American Future Republic, a nonprofit backed by Reid "
                "Hoffman that helped fund Carroll's litigation; other reporting described potential "
                "money-laundering, obstruction, and conspiracy theories involving the nonprofit. "
                "Carroll's deposition is related to the inquiry, but the public record does not support "
                "describing Carroll herself as its investigation target."
            ),
            "sig": (
                "DOJ scrutiny of the funding network behind litigation against the sitting president "
                "raises retaliation and chilling-effect concerns, while the official denial materially "
                "narrows who is publicly identified as the investigation subject. The entry records the "
                "conflicting initial reports, later source clarification, and official position without "
                "asserting criminal liability for Carroll or the nonprofit."
            ),
            "goal": (
                "\"Litigation-funding, money-laundering, obstruction, and truthful-testimony questions "
                "can be investigated independently of the civil verdicts, and the public correction "
                "shows Carroll herself was not made the investigation target.\""
            ),
            "mt": (
                "Maybe scrutiny of a litigation funder's financial conduct can be legitimate and is "
                "not the same as investigating the plaintiff it supported. Therefore the corrected "
                "entry preserves that distinction while recording the predictable chilling effect of "
                "federal scrutiny aimed at an organization that financed successful litigation against "
                "the sitting president."
            ),
            "src": [
                {
                    "t": "CNN — initial report",
                    "url": "https://www.cnn.com/2026/05/27/politics/exclusive-justice-department-launched-e-jean-carroll-investigation",
                },
                {
                    "t": "Reuters — initial report",
                    "url": "https://www.reuters.com/legal/government/doj-launches-criminal-probe-into-e-jean-carroll-source-says-2026-05-28/",
                },
                {
                    "t": "Washington Post — nonprofit focus",
                    "url": "https://www.washingtonpost.com/national-security/2026/05/28/doj-probes-reid-hoffmans-nonprofit-funding-e-jean-carrolls-legal-bills/",
                },
                {
                    "t": "Guardian — nonprofit focus",
                    "url": "https://www.theguardian.com/us-news/2026/may/28/e-jean-carroll-doj-trump-reid-hoffman",
                },
                {
                    "t": "Northern District of Illinois statement",
                    "url": "https://x.com/NDILnews/status/2060124784978010186",
                },
                {
                    "t": "Associated Press via WTTW — source clarification",
                    "url": "https://news.wttw.com/2026/05/28/justice-department-s-investigation-e-jean-carroll-who-accused-trump-assault-led-chicago",
                },
            ],
        },
    }
}


class RestorationError(ValueError):
    pass


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def record_sha256(value: dict[str, Any]) -> str:
    return sha256_bytes(canonical_bytes(value))


def source_record(entry: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in entry.items()
        if key not in {"legacy_id", "review_status"}
    }


def parse_source(path: Path) -> list[dict[str, Any]]:
    payload = path.read_bytes()
    actual_sha = sha256_bytes(payload)
    if actual_sha != SOURCE_SHA256:
        raise RestorationError(
            f"source SHA-256 mismatch: expected {SOURCE_SHA256}, found {actual_sha}"
        )
    with zipfile.ZipFile(path) as archive:
        try:
            html = archive.read(SOURCE_HTML).decode("utf-8")
        except KeyError as exc:
            raise RestorationError(f"source archive lacks {SOURCE_HTML}") from exc
    match = re.search(
        r'<script[^>]*id="dataEntries"[^>]*>(?P<data>.*?)</script>',
        html,
        re.DOTALL,
    )
    if match is None:
        raise RestorationError("source HTML lacks its dataEntries payload")
    entries = json.loads(match.group("data"))
    if not isinstance(entries, list) or any(not isinstance(row, dict) for row in entries):
        raise RestorationError("source dataEntries payload is not an object array")
    references = sum(len(row.get("src") or []) for row in entries)
    if len(entries) != SOURCE_RECORD_COUNT or references != SOURCE_REFERENCE_COUNT:
        raise RestorationError(
            "source corpus totals differ from the attested v13 package: "
            f"{len(entries)} rows / {references} references"
        )
    return entries


def restored_id(position: int) -> str:
    return f"LEG-{FIRST_RESTORED_ID + position:06d}"


def build_restored_records(source: list[dict[str, Any]]) -> list[dict[str, Any]]:
    records = []
    for position, source_index in enumerate(RESTORE_INDICES):
        row = dict(source[source_index])
        correction = SOURCE_CORRECTIONS.get(source_index)
        if correction is not None:
            row.update(correction["changes"])
        if not str(row.get("mt") or "").startswith("Maybe") or "Therefore" not in row["mt"]:
            raise RestorationError(f"restored source row {source_index} lacks Maybe / Therefore")
        if not isinstance(row.get("src"), list) or not row["src"]:
            raise RestorationError(f"v13 source row {source_index} lacks sources")
        records.append({
            "legacy_id": restored_id(position),
            "review_status": "legacy-unreviewed",
            **row,
        })
    reference_count = sum(len(row["src"]) for row in records)
    if len(records) != 95 or reference_count != RESTORED_CANONICAL_REFERENCE_COUNT:
        raise RestorationError(
            f"restoration selection drifted: {len(records)} rows / {reference_count} references"
        )
    return records


def creation_revision(
    position: int,
    source_index: int,
    source_row: dict[str, Any],
    record: dict[str, Any],
) -> dict[str, Any]:
    return {
        "revision_id": f"LR-{RECORDED_AT}-{position + 1:03d}",
        "recorded_at": RECORDED_AT,
        "legacy_id": record["legacy_id"],
        "kind": "record-creation",
        "summary": (
            "Restore a previously published timeline record lost during repository migration; "
            "preserve its exact v13 text, reasoning, and citations without current-standard promotion."
        ),
        "provenance": [
            {
                "type": "custody-recovery",
                "supports": (
                    f"Exact dataEntries row at zero-based index {source_index} in {SOURCE_NAME}; "
                    f"source commit {SOURCE_COMMIT}; source ZIP SHA-256 {SOURCE_SHA256}."
                ),
            },
            {
                "type": "source-citation-preservation",
                "supports": (
                    f"The row's {len(source_row['src'])} attached source reference(s) are preserved "
                    "from the published v13 corpus."
                ),
            },
        ],
        "changes": [
            {
                "field": field,
                "expected": MISSING_MARKER,
                "replacement": value,
            }
            for field, value in {
                "review_status": "legacy-unreviewed",
                **source_row,
            }.items()
        ],
    }


def correction_revision(
    revision_number: int,
    source_index: int,
    source_row: dict[str, Any],
    record: dict[str, Any],
) -> dict[str, Any]:
    correction = SOURCE_CORRECTIONS[source_index]
    return {
        "revision_id": f"LR-{RECORDED_AT}-{revision_number:03d}",
        "recorded_at": RECORDED_AT,
        "legacy_id": record["legacy_id"],
        "kind": correction["kind"],
        "summary": correction["summary"],
        "provenance": [
            {
                "type": "custody-recovery",
                "supports": (
                    f"The prior value is preserved at zero-based v13 source index {source_index}; "
                    f"source ZIP SHA-256 {SOURCE_SHA256}."
                ),
            },
            *correction["provenance"],
        ],
        "changes": [
            {
                "field": field,
                "expected": source_row[field],
                "replacement": replacement,
            }
            for field, replacement in correction["changes"].items()
        ],
    }


def apply_existing_record_corrections(
    canonical: list[dict[str, Any]],
    revisions: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    by_id = {str(row.get("legacy_id") or ""): row for row in canonical}
    manifest_rows = []
    first_revision_number = len(RESTORE_INDICES) + len(SOURCE_CORRECTIONS) + 1
    for offset, (legacy_id, correction) in enumerate(
        EXISTING_RECORD_CORRECTIONS.items()
    ):
        revision_id = f"LR-{RECORDED_AT}-{first_revision_number + offset:03d}"
        existing_revision = next(
            (row for row in revisions if row.get("revision_id") == revision_id),
            None,
        )
        current = by_id.get(legacy_id)
        if current is None:
            raise RestorationError(f"missing existing correction target {legacy_id}")
        before = copy.deepcopy(current)
        if existing_revision is not None:
            for change in existing_revision.get("changes", []):
                field = change["field"]
                if current.get(field, MISSING_MARKER) != change["replacement"]:
                    raise RestorationError(
                        f"persisted correction replacement drifted for {legacy_id}.{field}"
                    )
                before[field] = copy.deepcopy(change["expected"])
            revisions.remove(existing_revision)

        changes = []
        for field, replacement in correction["replacements"].items():
            expected = before.get(field, MISSING_MARKER)
            if expected == replacement:
                continue
            changes.append({
                "field": field,
                "expected": expected,
                "replacement": replacement,
            })
            current[field] = copy.deepcopy(replacement)
        if not changes:
            raise RestorationError(f"existing correction has no effective changes: {legacy_id}")
        revision = {
            "revision_id": revision_id,
            "recorded_at": RECORDED_AT,
            "legacy_id": legacy_id,
            "kind": correction["kind"],
            "summary": correction["summary"],
            "provenance": correction["provenance"],
            "changes": changes,
        }
        revisions.append(revision)
        manifest_rows.append({
            "legacy_id": legacy_id,
            "revision_id": revision_id,
            "before_record_sha256": record_sha256(before),
            "canonical_record_sha256": record_sha256(current),
            "fields": [change["field"] for change in changes],
            "summary": correction["summary"],
        })
    return manifest_rows


def build_manifest(
    source: list[dict[str, Any]],
    records: list[dict[str, Any]],
    existing_corrections: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "recorded_at": RECORDED_AT,
        "source": {
            "name": SOURCE_NAME,
            "sha256": SOURCE_SHA256,
            "source_commit": SOURCE_COMMIT,
            "html_member": SOURCE_HTML,
            "record_count": SOURCE_RECORD_COUNT,
            "source_reference_count": SOURCE_REFERENCE_COUNT,
            "index_convention": "zero-based JSON array index",
        },
        "restored_record_count": len(records),
        "restored_source_reference_count": sum(
            len(source[source_index]["src"]) for source_index in RESTORE_INDICES
        ),
        "restored_canonical_reference_count": sum(len(row["src"]) for row in records),
        "restored_records": [
            {
                "legacy_id": record["legacy_id"],
                "source_index": source_index,
                "source_record_sha256": record_sha256(source[source_index]),
                "canonical_record_sha256": record_sha256(source_record(record)),
            }
            for source_index, record in zip(RESTORE_INDICES, records, strict=True)
        ],
        "excluded_duplicate_count": len(EXCLUDED_DUPLICATES),
        "excluded_duplicates": [
            {
                "source_index": source_index,
                "source_record_sha256": record_sha256(source[source_index]),
                **details,
            }
            for source_index, details in EXCLUDED_DUPLICATES.items()
        ],
        "field_corrections": [
            {
                "source_index": source_index,
                "legacy_id": records[RESTORE_INDICES.index(source_index)]["legacy_id"],
                "kind": correction["kind"],
                "summary": correction["summary"],
                "reason": correction["reason"],
                "fields": list(correction["changes"]),
            }
            for source_index, correction in SOURCE_CORRECTIONS.items()
        ],
        "existing_record_corrections": existing_corrections,
        "custody_note": (
            "Only records absent from the current canonical corpus were considered. Four same-event "
            "duplicates were excluded; 75 v13/current differences already represented by current "
            "stable IDs were preserved in their newer corrected form and were not overwritten. Four "
            "recovered rows received separately logged corrections for date/lifecycle accuracy, "
            "source quality, or reasoning-layer structure."
        ),
    }


def render_canonical(entries: list[dict[str, Any]]) -> str:
    return "[\n" + ",\n".join(
        json.dumps(row, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
        for row in entries
    ) + "\n]\n"


def render_revisions(revisions: list[dict[str, Any]]) -> str:
    return "[\n" + ",\n".join(
        textwrap.indent(json.dumps(row, ensure_ascii=False, indent=2), "    ")
        for row in revisions
    ) + "\n]\n"


def validate_applied_state(
    canonical: list[dict[str, Any]],
    revisions: list[dict[str, Any]],
    manifest: dict[str, Any],
) -> None:
    by_id = {str(row.get("legacy_id") or ""): row for row in canonical}
    if len(by_id) != len(canonical):
        raise RestorationError("canonical legacy data has missing or duplicate IDs")
    revisions_by_id: dict[str, list[dict[str, Any]]] = {}
    for revision in revisions:
        revisions_by_id.setdefault(str(revision.get("legacy_id") or ""), []).append(revision)
    restored_rows = manifest.get("restored_records")
    if not isinstance(restored_rows, list) or len(restored_rows) != 95:
        raise RestorationError("restoration manifest must enumerate 95 restored records")
    for item in restored_rows:
        legacy_id = str(item.get("legacy_id") or "")
        canonical_row = by_id.get(legacy_id)
        if canonical_row is None:
            raise RestorationError(f"manifest names missing canonical record {legacy_id}")
        if record_sha256(source_record(canonical_row)) != item.get("canonical_record_sha256"):
            raise RestorationError(f"canonical restored row drifted from manifest: {legacy_id}")
        record_revisions = revisions_by_id.get(legacy_id, [])
        if not record_revisions or record_revisions[0].get("kind") != "record-creation":
            raise RestorationError(f"restored row lacks record-creation revision: {legacy_id}")
        replay = {"legacy_id": legacy_id}
        for revision in record_revisions:
            for change in revision.get("changes", []):
                field = change["field"]
                actual = replay.get(field, MISSING_MARKER)
                if actual != change.get("expected"):
                    raise RestorationError(f"revision replay guard drifted for {legacy_id}.{field}")
                replay[field] = change["replacement"]
        if replay != canonical_row:
            raise RestorationError(f"record-creation revision does not replay {legacy_id}")
    if manifest.get("excluded_duplicate_count") != 4:
        raise RestorationError("restoration manifest must enumerate four excluded duplicates")
    for item in manifest.get("existing_record_corrections", []):
        legacy_id = str(item.get("legacy_id") or "")
        revision_id = str(item.get("revision_id") or "")
        canonical_row = by_id.get(legacy_id)
        revision = next(
            (row for row in revisions if row.get("revision_id") == revision_id),
            None,
        )
        if canonical_row is None or revision is None:
            raise RestorationError(f"missing existing-record correction state for {legacy_id}")
        if record_sha256(canonical_row) != item.get("canonical_record_sha256"):
            raise RestorationError(f"corrected canonical record drifted: {legacy_id}")
        before = copy.deepcopy(canonical_row)
        for change in revision.get("changes", []):
            field = change["field"]
            if before.get(field, MISSING_MARKER) != change["replacement"]:
                raise RestorationError(f"correction replacement drifted for {legacy_id}.{field}")
            before[field] = copy.deepcopy(change["expected"])
        if record_sha256(before) != item.get("before_record_sha256"):
            raise RestorationError(f"correction prior-state hash drifted: {legacy_id}")


def apply(source_path: Path) -> None:
    source = parse_source(source_path)
    records = build_restored_records(source)
    canonical = json.loads(CANONICAL.read_text(encoding="utf-8"))
    revisions = json.loads(REVISIONS.read_text(encoding="utf-8"))
    ids = {str(row.get("legacy_id") or "") for row in canonical}
    restored_ids = {row["legacy_id"] for row in records}
    present = ids & restored_ids
    if present and present != restored_ids:
        raise RestorationError("partial v13 restoration detected; refusing to guess")
    if present == restored_ids:
        canonical = [row for row in canonical if row.get("legacy_id") not in restored_ids]
        revisions = [
            revision
            for revision in revisions
            if not (
                revision.get("recorded_at") == RECORDED_AT
                and revision.get("legacy_id") in restored_ids
            )
        ]
    canonical.extend(records)
    canonical.sort(key=lambda row: row["sort"])
    revisions.extend(
        creation_revision(position, source_index, source[source_index], record)
        for position, (source_index, record) in enumerate(
            zip(RESTORE_INDICES, records, strict=True)
        )
    )
    revisions.extend(
        correction_revision(
            len(RESTORE_INDICES) + offset,
            source_index,
            source[source_index],
            records[RESTORE_INDICES.index(source_index)],
        )
        for offset, source_index in enumerate(SOURCE_CORRECTIONS, start=1)
    )
    existing_corrections = apply_existing_record_corrections(canonical, revisions)
    canonical.sort(key=lambda row: row["sort"])
    manifest = build_manifest(source, records, existing_corrections)
    CANONICAL.write_text(render_canonical(canonical), encoding="utf-8")
    REVISIONS.write_text(render_revisions(revisions), encoding="utf-8")
    MANIFEST.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    validate_applied_state(canonical, revisions, manifest)
    print(
        f"Restored {len(records)} published legacy records with "
        f"{RESTORED_SOURCE_REFERENCE_COUNT} preserved source references and "
        f"{RESTORED_CANONICAL_REFERENCE_COUNT} after corrections; excluded four same-event duplicates."
    )


def check(source_path: Path | None) -> None:
    canonical = json.loads(CANONICAL.read_text(encoding="utf-8"))
    revisions = json.loads(REVISIONS.read_text(encoding="utf-8"))
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    validate_applied_state(canonical, revisions, manifest)
    if source_path is not None:
        source = parse_source(source_path)
        expected = build_manifest(
            source,
            build_restored_records(source),
            manifest.get("existing_record_corrections", []),
        )
        if manifest != expected:
            raise RestorationError("restoration manifest differs from the attested source package")
    print("Verified 95 restored v13 records, their creation ledger, and four duplicate exclusions.")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Restore the exact deduplicated legacy rows lost from The Record v13 corpus."
    )
    parser.add_argument("--source", type=Path, help=f"path to {SOURCE_NAME}")
    parser.add_argument("--apply", action="store_true", help="perform the one-time restoration")
    parser.add_argument("--check", action="store_true", help="verify the persisted restoration")
    args = parser.parse_args()
    if args.apply == args.check:
        parser.error("choose exactly one of --apply or --check")
    if args.apply and args.source is None:
        parser.error("--apply requires --source")
    try:
        if args.apply:
            apply(args.source)
        else:
            check(args.source)
        return 0
    except (OSError, json.JSONDecodeError, zipfile.BadZipFile, RestorationError) as exc:
        print(f"ERROR: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
