from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

from editorial_state import post_content_hash


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = "https://ix.cnn.io/data/truth-social/truth_archive.json"
DEFAULT_LIMIT = 1000
SEED_PATH = ROOT / "data/truth_social_seed.json"
META_PATH = ROOT / "data/truth_social_feed_meta.json"
EASTERN = ZoneInfo("America/Indiana/Indianapolis")
REVIEWS_PATH = ROOT / "data/truth_social_reviews.json"


def pending_reviews(rows: list[dict], existing: list[dict]) -> list[dict]:
    result = list(existing)
    known = {(r["post_id"], r["content_sha256"]) for r in result}
    for post in rows:
        signature = post_content_hash(post)
        if (post["id"], signature) not in known:
            result.append({"post_id": post["id"], "content_sha256": signature,
                           "text_status": "pending", "media_status": "pending" if post["media"] else "not_applicable",
                           "reviewer": None, "reviewed_at": None,
                           "note": "Acquired as a research lead; source content and media have not been reviewed by this updater."})
            known.add((post["id"], signature))
    return result


def validate_local() -> None:
    raw = json.loads(SEED_PATH.read_text())
    rows = normalize(raw)
    metadata = json.loads(META_PATH.read_text())
    if rows != raw or len(rows) != metadata["fallback_post_count"]:
        raise ValueError("fallback normalization/count differs")
    if len(rows) < 500 or metadata["source_post_count"] < len(rows):
        raise ValueError("fallback/source count is invalid")
    for prefix, row in (("latest", rows[0]), ("fallback_earliest", rows[-1])):
        timestamp = parse_timestamp(row["created_at"])
        if timestamp != parse_timestamp(metadata[f"{prefix}_post_at_utc"]):
            raise ValueError("fallback endpoint differs from metadata")
    if metadata["latest_post_id"] != rows[0]["id"]:
        raise ValueError("latest post ID differs")
    if metadata["latest_post_at_eastern"] != format_eastern(parse_timestamp(rows[0]["created_at"])):
        raise ValueError("latest post local date/time differs")
    checked = parse_timestamp(metadata["checked_at_utc"])
    if metadata["checked_at_eastern"] != format_eastern(checked):
        raise ValueError("fallback check-time conversion differs")
    if checked < parse_timestamp(rows[0]["created_at"]):
        raise ValueError("latest post postdates the snapshot check")


def parse_timestamp(value: object) -> datetime:
    text = str(value or "").strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    parsed = datetime.fromisoformat(text)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def valid_https(value: object, *, host: str | None = None) -> bool:
    parsed = urlparse(str(value or ""))
    if parsed.scheme != "https" or not parsed.netloc:
        return False
    if host is None:
        return True
    return parsed.netloc == host and parsed.hostname == host


def optional_count(value: object) -> int | None:
    if value is None or value == "":
        return None
    return int(value)


def normalize(rows: object) -> list[dict]:
    if not isinstance(rows, list):
        raise ValueError("archive response is not a JSON array")
    seen: set[str] = set()
    normalized: list[tuple[datetime, dict]] = []
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise ValueError(f"row {index} is not an object")
        post_id = str(row.get("id") or "").strip()
        if not post_id or post_id in seen:
            raise ValueError(f"row {index} has a missing or duplicate ID")
        seen.add(post_id)
        created_at = str(row.get("created_at") or "").strip()
        timestamp = parse_timestamp(created_at)
        url = str(row.get("url") or "").strip()
        parsed_post_url = urlparse(url)
        if (
            not valid_https(url, host="truthsocial.com")
            or not re.fullmatch(r"/@realDonaldTrump/\d+/?", parsed_post_url.path)
        ):
            raise ValueError(f"row {index} has an invalid Truth Social URL")
        media = row.get("media") or []
        if not isinstance(media, list) or any(
            not valid_https(item, host="static-assets-1.truthsocial.com") for item in media
        ):
            raise ValueError(f"row {index} has malformed media URLs")
        normalized.append(
            (
                timestamp,
                {
                    "id": post_id,
                    "created_at": created_at,
                    "content": str(row.get("content") or ""),
                    "url": url,
                    "media": [str(item) for item in media],
                    "replies_count": optional_count(row.get("replies_count")),
                    "reblogs_count": optional_count(row.get("reblogs_count")),
                    "favourites_count": optional_count(row.get("favourites_count")),
                },
            )
        )
    normalized.sort(key=lambda item: item[0], reverse=True)
    return [row for _timestamp, row in normalized]


def load_source(source_url: str, input_path: Path | None) -> object:
    if input_path:
        return json.loads(input_path.read_text(encoding="utf-8"))
    request = urllib.request.Request(
        source_url,
        headers={"User-Agent": "The-Record-Truth-Social-Maintainer/1.0"},
    )
    with urllib.request.urlopen(request, timeout=90) as response:
        return json.load(response)


def format_eastern(timestamp: datetime) -> str:
    local = timestamp.astimezone(EASTERN)
    zone = local.tzname() or "ET"
    return local.strftime(f"%Y-%m-%d %-I:%M:%S %p {zone}")


def write_outputs(rows: list[dict], source_url: str, limit: int, checked_at: datetime) -> None:
    if len(rows) < limit:
        raise ValueError(f"source contains {len(rows)} posts, fewer than requested fallback size {limit}")
    seed = rows[:limit]
    if SEED_PATH.exists():
        previous = normalize(json.loads(SEED_PATH.read_text()))
        if parse_timestamp(seed[0]["created_at"]) < parse_timestamp(previous[0]["created_at"]):
            raise ValueError("upstream snapshot regressed; validated local snapshot preserved")
    latest_timestamp = parse_timestamp(seed[0]["created_at"])
    earliest_timestamp = parse_timestamp(seed[-1]["created_at"])
    metadata = {
        "source_name": "CNN-hosted public Trump Truth Social archive mirror",
        "source_url": source_url,
        "checked_at_utc": checked_at.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
        "checked_at_eastern": format_eastern(checked_at),
        "source_post_count": len(rows),
        "fallback_post_count": len(seed),
        "latest_post_id": seed[0]["id"],
        "latest_post_at_utc": latest_timestamp.isoformat().replace("+00:00", "Z"),
        "latest_post_at_eastern": format_eastern(latest_timestamp),
        "fallback_earliest_post_at_utc": earliest_timestamp.isoformat().replace("+00:00", "Z"),
        "scope_note": "Raw public posts are leads and primary records of publication, not independent verification of claims inside them.",
    }
    existing = json.loads(REVIEWS_PATH.read_text()) if REVIEWS_PATH.exists() else []
    reviews = pending_reviews(seed, existing)
    # Stage each payload before replacing its destination. The offline check
    # rejects any interrupted multi-file refresh before publication.
    for path, payload in ((SEED_PATH, seed), (META_PATH, metadata), (REVIEWS_PATH, reviews)):
        staged = path.with_suffix(path.suffix + ".tmp")
        staged.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        staged.replace(path)


def main() -> int:
    parser = argparse.ArgumentParser(description="Refresh The Record's verified recent Truth Social fallback.")
    parser.add_argument("--source", default=DEFAULT_SOURCE, help="public JSON archive URL")
    parser.add_argument("--input", type=Path, help="use an already-downloaded JSON archive instead of the network")
    parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT, help="number of recent posts retained locally")
    parser.add_argument("--checked-at", help="ISO-8601 check time; defaults to the current time")
    parser.add_argument("--check", action="store_true", help="validate retained snapshot offline; never refresh check time")
    args = parser.parse_args()
    if args.check:
        try:
            validate_local()
        except (OSError, ValueError, KeyError, IndexError) as exc:
            print(f"FAIL: {exc}", file=sys.stderr)
            return 1
        print("PASS: retained Truth Social fallback and Indianapolis timestamps")
        return 0
    if args.limit < 100:
        parser.error("--limit must be at least 100")
    try:
        rows = normalize(load_source(args.source, args.input))
        checked_at = parse_timestamp(args.checked_at) if args.checked_at else datetime.now(timezone.utc)
        write_outputs(rows, args.source, args.limit, checked_at)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    print(
        f"Updated {SEED_PATH.relative_to(ROOT)} with {args.limit} of {len(rows)} posts; "
        f"latest {rows[0]['created_at']} ({rows[0]['id']})."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
