from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "the-record.html"
START = "/* CURRENT_LAYER_BRIDGE_START */"
END = "/* CURRENT_LAYER_BRIDGE_END */"


def bridge_block() -> str:
    entries = json.loads((ROOT / "data/current_entries.json").read_text(encoding="utf-8"))
    ledger = json.loads((ROOT / "data/source_ledger.json").read_text(encoding="utf-8"))
    bridge = []
    for entry in sorted(
        (item for item in entries if item["scope"] == "national"),
        key=lambda item: (item["date"], item["id"]),
    ):
        bridge.append({
            "era": "term2",
            "sort": entry["date"],
            "date": entry["display_date"],
            "text": f'{entry["title"]}. ' + " ".join(entry["facts"]),
            "sig": entry["significance"],
            "goal": entry["goalpost"],
            "hi": 0,
            "gp": 1,
            "etype": "event",
            "dprec": "day",
            "src": [
                {"t": ledger[source_id]["name"], "url": ledger[source_id]["url"]}
                for source_id in entry["sources"]
            ],
            "current_id": entry["id"],
        })
    payload = json.dumps(bridge, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    return f'''{START}
// Generated from data/current_entries.json so the legacy Past Week control reaches the current national layer.
const CURRENT_LAYER_BRIDGE={payload};
E.push(...CURRENT_LAYER_BRIDGE);
{END}'''


def expected_text() -> str:
    text = TARGET.read_text(encoding="utf-8")
    start = text.index(START)
    end = text.index(END, start) + len(END)
    return text[:start] + bridge_block() + text[end:]


def main() -> int:
    parser = argparse.ArgumentParser(description="Bridge current national entries into the preserved single-file archive.")
    parser.add_argument("--check", action="store_true", help="fail if the embedded bridge is stale")
    args = parser.parse_args()
    current = TARGET.read_text(encoding="utf-8")
    expected = expected_text()
    if args.check:
        if current != expected:
            print("the-record.html current-layer bridge is stale")
            return 1
        print("Verified legacy current-layer bridge.")
        return 0
    TARGET.write_text(expected, encoding="utf-8")
    print("Built legacy current-layer bridge.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
