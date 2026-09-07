"""Reject unverifiable review-state promotions and lost publication provenance."""
from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path

import jsonschema

from editorial_state import (ROOT, digest, entry_content_hash, load_state, matching_review,
                             parse_utc, post_content_hash, validate_snapshot, legacy_checked_at, validate_frozen_artifacts)


def git_json(ref: str, path: str, root: Path) -> object:
    return json.loads(subprocess.check_output(["git", "show", f"{ref}:{path}"], cwd=root, text=True))


def validate(root: Path = ROOT, base_ref: str | None = None) -> dict:
    state = load_state(root)
    schema = json.loads((root / "schemas/editorial_state.schema.json").read_text())
    jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker()).validate(state)
    entries = json.loads((root / "data/current_entries.json").read_text())
    ledger = json.loads((root / "data/source_ledger.json").read_text())
    release = json.loads((root / "data/release.json").read_text())
    by_id = {e["id"]: e for e in entries}
    previous_entries = {e["id"]: e for e in git_json(base_ref, "data/current_entries.json", root)} if base_ref else {}
    previous_ledger = git_json(base_ref, "data/source_ledger.json", root) if base_ref else {}
    def require(condition: bool, message: str) -> None:
        if not condition:
            raise ValueError(message)
    boundary = release["research_window"]
    start, end = parse_utc(boundary["from_utc"]), parse_utc(boundary["through_utc"])
    require(start <= end, "research window is reversed")
    require(boundary["precision"] in {"minute", "second"}, "missing research-window precision")
    require(end == parse_utc(legacy_checked_at(release["checked_at"])) or (
        boundary["precision"] == "second" and end.replace(second=0, microsecond=0) == parse_utc(legacy_checked_at(release["checked_at"]))),
        "research UTC cutoff differs from displayed checked_at")
    require(len({d["change_id"] for d in state["developments"]}) == len(state["developments"]), "duplicate development IDs")
    for change in state["developments"]:
        require(change["entry_id"] in by_id, "development targets missing entry")
        require(parse_utc(change["as_of_utc"]) <= end, "development lies after evidence cutoff")
        path = Path(change["provenance_path"])
        require(not path.is_absolute() and ".." not in path.parts, "unsafe provenance path")
        require(digest((root / path).read_bytes()) == change["provenance_sha256"], "development provenance changed")
    for entry_id in release["new_entry_ids"]:
        require(any(d["entry_id"] == entry_id and d["release_version"] == release["version"] for d in state["developments"]),
                "new/materially refreshed record needs a dated development entry")
    require(len({r["review_id"] for r in state["reviews"]}) == len(state["reviews"]), "duplicate review IDs")
    for review in state["reviews"]:
        require(review["entry_id"] in by_id, "review targets missing entry")
        reviewed = parse_utc(review["reviewed_at"])
        source_origins = {}
        for claim in review["claims"]:
            require(len({s["source_id"] for s in claim["supports"]}) == len(claim["supports"]), "same source repeated within one claim")
            for support in claim["supports"]:
                require(support["source_id"] in ledger, "review source is absent from source ledger")
                require(parse_utc(support["inspected_at"]) <= reviewed, "source inspection postdates review")
                old_origin = source_origins.setdefault(support["source_id"], support["origin_group"])
                require(old_origin == support["origin_group"], "one source cannot claim multiple independent origins")
            if claim["relies_on_unnamed_sources"]:
                require(len({s["document_sha256"] for s in claim["supports"]}) >= 2, "unnamed-source claim repeats the same document")
                require(len({s["origin_group"] for s in claim["supports"]}) >= 2,
                        "unnamed-source claim needs two independent origins, not syndication")
    mapped = 0
    for entry in entries:
        review = matching_review(entry, ledger, state)
        if not review:
            require(state["baseline"]["entry_hashes"].get(entry["id"]) == entry_content_hash(entry, ledger),
                    f'{entry["id"]}: changed/new content needs a content-bound claim-level review')
            if base_ref:
                require(entry["id"] in previous_entries and entry_content_hash(previous_entries[entry["id"]], previous_ledger) == entry_content_hash(entry, ledger),
                        "restoring migration-baseline content after a change still requires a new review")
            continue
        mapped += 1
        claims = review["claims"]
        require(sorted(c["fact_index"] for c in claims) == list(range(len(entry["facts"]))), "fact review coverage is incomplete or duplicated")
        for claim in claims:
            require(claim["fact_sha256"] == digest(entry["facts"][claim["fact_index"]].encode()), "reviewed fact hash is stale")
            require(all(s["source_id"] in entry["sources"] for s in claim["supports"]), "claim cites source not attached to entry")
        layers = review["reasoning_review"]
        require(sorted(r["field"] for r in layers) == ["goalpost", "maybe_therefore", "significance"], "reasoning-layer review coverage missing")
        for layer in layers:
            require(layer["text_sha256"] == digest(entry[layer["field"]].encode()), "reasoning-layer review is stale")
    if base_ref:
        validate_frozen_artifacts(base_ref, root)
        names = subprocess.check_output(["git", "ls-tree", "--name-only", base_ref, "data/editorial_state.json"], cwd=root, text=True)
        if names.strip():
            old = git_json(base_ref, "data/editorial_state.json", root)
            require(state["baseline"] == old["baseline"], "review migration baseline is immutable")
            for field, identity in (("developments", "change_id"), ("reviews", "review_id")):
                current = {r[identity]: r for r in state[field]}
                require(all(current.get(r[identity]) == r for r in old[field]), f"{field} is append-only")
        else:
            baseline = state["baseline"]
            original = git_json(baseline["commit"], "data/current_entries.json", root)
            sources = git_json(baseline["commit"], "data/source_ledger.json", root)
            require(baseline["entry_hashes"] == {e["id"]: entry_content_hash(e, sources) for e in original}, "migration baseline does not match original commit")
        previous = git_json(base_ref, "data/release.json", root)
        if previous["version"] != release["version"] and not release.get("engineering_revision"):
            expected = previous.get("research_window", {}).get("through_utc", legacy_checked_at(previous["checked_at"]))
            require(start == parse_utc(expected), "research window must start at previous coverage boundary")
    if release.get("engineering_revision") and base_ref:
        previous_release = git_json(base_ref, "data/release.json", root)
        prior_window = previous_release.get("research_window", {
            "from_utc": legacy_checked_at(previous_release["window_started_at"]),
            "through_utc": legacy_checked_at(previous_release["checked_at"]),
            "precision": "minute",
        })
        require(start == parse_utc(prior_window["from_utc"]) and end == parse_utc(prior_window["through_utc"])
                and boundary["precision"] == prior_window["precision"], "engineering release must preserve research window and precision")
        for path in ("data/current_entries.json", "data/source_ledger.json", "data/legacy_entries.json", "data/legacy_revisions.json"):
            require(git_json(base_ref, path, root) == json.loads((root / path).read_text()), "engineering release changes editorial content")
    queue = json.loads((root / "data/research_queue.json").read_text())
    require(len({c["candidate_id"] for c in queue}) == len(queue), "duplicate candidate IDs")
    for candidate in queue:
        require(candidate["status"] in {"pending", "blocked", "published", "withheld"}, "unknown candidate status")
        parse_utc(candidate["first_seen_at"])
        require(bool(candidate["reason"] and candidate["recheck_trigger"] and candidate["provenance"]), "candidate needs reason, provenance, and recheck trigger")
        if candidate.get("next_check_at"):
            parse_utc(candidate["next_check_at"])
        if candidate["status"] == "published":
            require(candidate.get("canonical_id") in by_id, "published candidate lacks canonical target")
    if base_ref:
        queue_exists = subprocess.check_output(["git", "ls-tree", "--name-only", base_ref, "data/research_queue.json"], cwd=root, text=True).strip()
        if queue_exists:
            old_queue = git_json(base_ref, "data/research_queue.json", root)
            current_queue = {c["candidate_id"]: c for c in queue}
            for old_candidate in old_queue:
                candidate = current_queue.get(old_candidate["candidate_id"])
                require(candidate is not None, "deferred candidates cannot silently disappear")
                if candidate != old_candidate:
                    require(candidate["first_seen_at"] == old_candidate["first_seen_at"], "candidate first-seen time is immutable")
                    require(old_candidate in candidate.get("revisions", []), "candidate change must retain its previous state in revisions")
    feed = json.loads((root / "data/truth_social_seed.json").read_text())
    feed_reviews = json.loads((root / "data/truth_social_reviews.json").read_text())
    require(len({(r["post_id"], r["content_sha256"]) for r in feed_reviews}) == len(feed_reviews), "duplicate post review versions")
    for r in feed_reviews:
        require(r["text_status"] in {"pending", "reviewed", "not_recorded"}, "invalid text review state")
        require(r["media_status"] in {"pending", "reviewed", "unavailable", "not_applicable", "not_recorded"}, "invalid media review state")
        if "reviewed" in (r["text_status"], r["media_status"]):
            require(bool(r.get("reviewer") and r.get("reviewed_at") and r.get("note")), "reviewed post needs reviewer, timestamp and note")
            parse_utc(r["reviewed_at"])
    if base_ref:
        previous_feed = git_json(base_ref, "data/truth_social_seed.json", root)
        old_hashes = {post_content_hash(p) for p in previous_feed}
        index = {(r["post_id"], r["content_sha256"]) for r in feed_reviews}
        require(all((p["id"], post_content_hash(p)) in index for p in feed if post_content_hash(p) not in old_hashes), "new/changed post has no explicit inspection state")
        old_reviews_exist = subprocess.check_output(["git", "ls-tree", "--name-only", base_ref, "data/truth_social_reviews.json"], cwd=root, text=True).strip()
        if old_reviews_exist:
            previous_reviews = git_json(base_ref, "data/truth_social_reviews.json", root)
            current_reviews = {(r["post_id"], r["content_sha256"]): r for r in feed_reviews}
            for old_review in previous_reviews:
                current = current_reviews.get((old_review["post_id"], old_review["content_sha256"]))
                require(current is not None, "post inspection history cannot be deleted")
                if current != old_review:
                    require(old_review in current.get("revisions", []), "post inspection changes must retain the previous state")
    validate_snapshot(release, root)
    return {"claim_mapped_entries": mapped, "prior_standard_entries": len(entries) - mapped,
            "development_records": len(state["developments"]), "deferred_candidates": len(queue)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-ref")
    args = parser.parse_args()
    try:
        print(json.dumps(validate(base_ref=args.base_ref), sort_keys=True))
    except (ValueError, KeyError, OSError, jsonschema.ValidationError, subprocess.CalledProcessError) as exc:
        print(f"FAIL: editorial-state contract: {exc}")
        return 1
    print("PASS: editorial-state, review coverage, windows, queue and snapshot contracts")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
