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


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = "https://ix.cnn.io/data/truth-social/truth_archive.json"
DEFAULT_LIMIT = 1000
SEED_PATH = ROOT / "data/truth_social_seed.json"
META_PATH = ROOT / "data/truth_social_feed_meta.json"
EASTERN = ZoneInfo("America/New_York")


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
    SEED_PATH.write_text(json.dumps(seed, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    META_PATH.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Refresh The Record's verified recent Truth Social fallback.")
    parser.add_argument("--source", default=DEFAULT_SOURCE, help="public JSON archive URL")
    parser.add_argument("--input", type=Path, help="use an already-downloaded JSON archive instead of the network")
    parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT, help="number of recent posts retained locally")
    parser.add_argument("--checked-at", help="ISO-8601 check time; defaults to the current time")
    args = parser.parse_args()
    if args.limit < 100:
        parser.error("--limit must be at least 100")
    checked_at = parse_timestamp(args.checked_at) if args.checked_at else datetime.now(timezone.utc)
    try:
        rows = normalize(load_source(args.source, args.input))
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
