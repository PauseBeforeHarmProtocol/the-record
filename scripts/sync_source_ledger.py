from __future__ import annotations

import argparse
import csv
import io
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
JSON_PATH = ROOT / "data/source_ledger.json"
CSV_PATH = ROOT / "data/source_ledger.csv"
FIELDS = ("source_id", "name", "publisher", "date", "type", "url")


def expected_csv() -> str:
    ledger = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=FIELDS, lineterminator="\n")
    writer.writeheader()
    for source_id, source in ledger.items():
        writer.writerow({"source_id": source_id, **source})
    return buffer.getvalue()


def main() -> int:
    parser = argparse.ArgumentParser(description="Synchronize the flat source ledger with its canonical JSON.")
    parser.add_argument("--check", action="store_true", help="fail if the CSV differs from canonical JSON")
    args = parser.parse_args()
    expected = expected_csv()
    if args.check:
        if not CSV_PATH.exists() or CSV_PATH.read_text(encoding="utf-8") != expected:
            print("data/source_ledger.csv is stale")
            return 1
        print("Verified source-ledger CSV.")
        return 0
    CSV_PATH.write_text(expected, encoding="utf-8")
    print("Built source-ledger CSV.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
