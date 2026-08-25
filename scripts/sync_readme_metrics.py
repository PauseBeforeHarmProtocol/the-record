from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
METRICS = ROOT / "data/archive_metrics.json"
RELEASE = ROOT / "data/release.json"
START = "<!-- GENERATED_ARCHIVE_METRICS_START -->"
END = "<!-- GENERATED_ARCHIVE_METRICS_END -->"


ERA_LABELS = {
    "formation": "Formation",
    "campaign1": "Campaign 1",
    "term1": "Term 1",
    "post1": "Post-presidency",
    "campaign2": "Campaign 2",
    "term2": "Term 2",
}


def render_block() -> str:
    metrics = json.loads(METRICS.read_text(encoding="utf-8"))
    release = json.loads(RELEASE.read_text(encoding="utf-8"))
    totals = metrics["totals"]
    legacy = metrics["legacy"]
    layers = legacy["interpretive_layers"]
    coverage = metrics["coverage"]
    revisions = metrics["remediation"]["legacy_revision_records"]
    federated = metrics["federated"]["records"]
    era_rows = "\n".join(
        f"| {label} | {legacy['eras'].get(era, 0):,} |"
        for era, label in ERA_LABELS.items()
    )
    review_summary = ", ".join(
        f"{state}: {count:,}" for state, count in legacy["review_states"].items()
    )
    return f"""{START}
## Generated Scope and Quality Snapshot

Generated deterministically from canonical JSON for maintenance release **{release['version']}**. Editorial news currentness was checked **{metrics['editorial_checked_at']}**; QA inputs were updated **{metrics['quality_inputs_updated_at']}**.

| Measure | Exact count |
|---|---:|
| Canonical legacy rows stored | {totals['canonical_legacy_rows']:,} |
| Active canonical legacy entries | {totals['active_legacy_entries']:,} |
| Superseded duplicate tombstones (excluded from totals/search) | {totals['superseded_legacy_tombstones']:,} |
| Current national entries bridged into the archive | {totals['bridged_national_entries']:,} |
| Full archive entries rendered at runtime | {totals['full_archive_runtime_entries']:,} |
| Attached source references at runtime | {totals['full_archive_runtime_source_references']:,} |
| Distinct stored source URLs at runtime | {totals['full_archive_runtime_unique_urls']:,} |
| Legacy entries with Maybe / Therefore | {layers['maybe_therefore_present']:,} |
| Legacy entries awaiting Maybe / Therefore | {layers['maybe_therefore_missing']:,} |
| Logged legacy revision records | {revisions:,} |
| Normalized external crosslinks | {federated:,} |

Active legacy review states: **{review_summary}**. “Legacy-unreviewed” means not yet revalidated under the current standard; it does not mean false. Superseded rows remain available as stable audit redirects but do not count as active events. The known **{coverage['uncovered_days_between_layers']}-day** continuity gap is **{coverage['known_gap_label']}** and remains queued for backfill.

### The Six Eras

| Era | Active canonical legacy entries |
|---|---:|
{era_rows}

Counts from other archives are shown with their own units in the [Archive Network](archive/index.html#archive-network) and are never added to The Record’s totals. See the [Quality dashboard](quality/index.html) for definitions, source-health measures, duplicate candidates, and the remediation backlog.
{END}"""


def expected_readme() -> str:
    text = README.read_text(encoding="utf-8")
    if text.count(START) != 1 or text.count(END) != 1:
        raise ValueError("README must contain exactly one generated archive-metrics marker pair")
    before, rest = text.split(START, 1)
    _, after = rest.split(END, 1)
    return before + render_block() + after


def main() -> int:
    parser = argparse.ArgumentParser(description="Synchronize README archive totals from generated metrics.")
    parser.add_argument("--check", action="store_true", help="fail when README totals are stale")
    args = parser.parse_args()
    expected = expected_readme()
    current = README.read_text(encoding="utf-8")
    if args.check:
        if current != expected:
            print("README generated archive metrics are stale")
            return 1
        print("Verified README generated archive totals.")
        return 0
    README.write_text(expected, encoding="utf-8")
    print("Synchronized README generated archive totals.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
