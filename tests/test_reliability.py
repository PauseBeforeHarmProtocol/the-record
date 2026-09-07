"""Regression tests for chronology, review binding, snapshots and fail-closed gates."""
from __future__ import annotations

import copy
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from editorial_state import (SNAPSHOT_FILES, activity_date, artifact_names, digest,
                             entry_content_hash, load_state, parse_utc, post_content_hash,
                             rolling_window, validate_snapshot, validate_frozen_artifacts, weekly_entries)
from accept_release import execute_steps, scan_text, zip_gate
from update_truth_social_feed import pending_reviews, format_eastern, parse_timestamp


class ChronologyTests(unittest.TestCase):
    def setUp(self):
        self.entries = [{"id": "NAT-2026-08-17-001", "date": "2026-08-17"}]
        self.release = {"research_window": {"through_utc": "2026-09-07T16:02:00Z"}}
        self.state = {"developments": [{"change_id": "fixture", "entry_id": self.entries[0]["id"], "as_of_utc": "2026-09-07T10:02:00Z"}]}

    def test_rolling_week_ends_at_coverage_not_future_calendar_days(self):
        self.assertEqual(rolling_window(self.release), ("2026-09-01", "2026-09-07"))

    def test_material_refresh_appears_without_redating_original_event(self):
        entry = next(e for e in self.entries if e["id"] == "NAT-2026-08-17-001")
        self.assertEqual(entry["date"], "2026-08-17")
        self.assertEqual(activity_date(entry, self.state), "2026-09-07")
        self.assertIn(entry, weekly_entries(self.entries, self.release, self.state))

    def test_recheck_alone_is_not_a_material_update(self):
        entry = {"id": "test", "date": "2026-01-01", "checked_at": "2026-09-07 12:02 PM EDT"}
        self.assertEqual(activity_date(entry, {"developments": []}), "2026-01-01")

    def test_week_has_unique_canonical_ids(self):
        rows = weekly_entries(self.entries, self.release, self.state)
        self.assertEqual(len(rows), len({e["id"] for e in rows}))
        self.assertGreater(len(rows), 0)

    def test_naive_timestamp_is_rejected(self):
        with self.assertRaises(ValueError):
            parse_utc("2026-09-07T16:02:20")

    def test_utc_midnight_is_previous_indianapolis_date(self):
        self.assertEqual(format_eastern(parse_timestamp("2026-09-07T02:35:49Z")), "2026-09-06 10:35:49 PM EDT")


class ReviewTests(unittest.TestCase):
    def test_fact_and_source_changes_invalidate_review_hash(self):
        entry = {"id": "x", "facts": ["Example"], "sources": ["a"], "checked_at": "old"}
        sources = {"a": {"url": "https://example.org/one"}}
        baseline = entry_content_hash(entry, sources)
        entry["checked_at"] = "new"
        self.assertEqual(baseline, entry_content_hash(entry, sources))
        entry["facts"][0] = "Changed"
        self.assertNotEqual(baseline, entry_content_hash(entry, sources))
        entry["facts"][0] = "Example"
        sources["a"]["url"] = "https://example.org/two"
        self.assertNotEqual(baseline, entry_content_hash(entry, sources))

    def test_engagement_does_not_invalidate_post_inspection(self):
        post = {"id": "1", "content": "Example", "media": [], "favourites_count": 1}
        baseline = post_content_hash(post)
        post["favourites_count"] = 99
        self.assertEqual(baseline, post_content_hash(post))
        post["media"] = ["https://example.org/image.jpg"]
        self.assertNotEqual(baseline, post_content_hash(post))

    def test_media_acquisition_never_implies_review(self):
        post = {"id": "1", "content": "", "media": ["https://example.org/image.jpg"]}
        records = pending_reviews([post], [])
        self.assertEqual(records[0]["media_status"], "pending")
        self.assertIsNone(records[0]["reviewed_at"])
        self.assertEqual(pending_reviews([post], records), records)


class AcceptanceTests(unittest.TestCase):
    def test_missing_jsonschema_cannot_pass(self):
        result = subprocess.run([sys.executable, "-S", "scripts/validate_federated_records.py"], cwd=ROOT, capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("jsonschema is required", result.stderr)

    def test_failure_marks_later_gates_not_run(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "receipt.json"
            result = execute_steps([("failure", [sys.executable, "-c", "raise SystemExit(2)"]),
                                    ("must-not-run", [sys.executable, "-c", "raise SystemExit(0)"])], {}, path, dict(os.environ))
            self.assertEqual(result, 1)
            receipt = json.loads(path.read_text())
            self.assertEqual([s["status"] for s in receipt["steps"]], ["failed", "not_run"])

    def test_invalid_base_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run([sys.executable, "scripts/accept_release.py", "--base-ref", "0" * 40,
                                     "--receipt", str(Path(directory) / "receipt.json")], cwd=ROOT, capture_output=True)
            self.assertNotEqual(result.returncode, 0)

    def test_credential_scan_redacts_matching_value(self):
        fake = "gh" + "p_" + "A" * 25
        with self.assertRaises(ValueError) as raised:
            scan_text(fake.encode(), "test fixture")
        self.assertNotIn(fake, str(raised.exception))

    def test_corrupt_zip_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.zip"
            path.write_bytes(b"not a zip")
            with self.assertRaises(zipfile.BadZipFile):
                zip_gate(path)

    def test_input_drift_cannot_pass(self):
        with tempfile.TemporaryDirectory() as directory, patch('accept_release.inventory_hash', return_value="changed"):
            output = Path(directory) / "receipt.json"
            self.assertEqual(execute_steps([], {"input_sha256": "original"}, output, dict(os.environ)), 1)
            self.assertEqual(json.loads(output.read_text())["steps"][-1]["status"], "failed")

    def test_rehash_does_not_authorize_rewriting_old_snapshot(self):
        with patch('editorial_state.subprocess.check_output', side_effect=["artifacts/old.zip\n", "artifacts/old.zip\n"]):
            with self.assertRaisesRegex(ValueError, "immutable historical artifact"):
                validate_frozen_artifacts("base")


class SnapshotTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        for name in SNAPSHOT_FILES:
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"{}\n")
        (self.root / "data/current_entries.json").write_text("[]\n")
        (self.root / "artifacts").mkdir()
        names = artifact_names({"release_iso": "2026-09-07", "version": "10.32.0"})
        snapshot = {"version": "10.32.0"}
        for key in ("national_pack", "complete_pack", "national_brief", "in6_brief"):
            path = self.root / "artifacts" / names[key]
            if key == "complete_pack":
                with zipfile.ZipFile(path, "w") as archive:
                    archive.writestr("data/release.json", json.dumps({"version": "10.32.0"}))
                    for name in SNAPSHOT_FILES:
                        archive.writestr(name, (self.root / name).read_bytes())
            else:
                path.write_bytes(b"frozen test artifact")
            snapshot[key] = {"path": path.relative_to(self.root).as_posix(), "sha256": digest(path.read_bytes())}
        self.release = {"artifact_mode": "feed-only", "release_iso": "2026-09-08", "version": "10.32.1",
                        "editorial_snapshot": snapshot, "new_entry_ids": [], "added_entry_ids": [], "refreshed_entry_ids": []}

    def tearDown(self):
        self.temp.cleanup()

    def test_next_day_and_consecutive_feed_release_reuses_same_snapshot(self):
        validate_snapshot(self.release, self.root)
        name = artifact_names(self.release)["complete_pack"]
        self.release.update(version="10.32.2", release_iso="2026-09-09")
        validate_snapshot(self.release, self.root)
        self.assertEqual(name, artifact_names(self.release)["complete_pack"])

    def test_changed_sources_or_legacy_data_are_not_feed_only(self):
        for name in ("data/source_ledger.json", "data/legacy_entries.json", "data/editorial_state.json"):
            path = self.root / name
            original = path.read_bytes()
            path.write_bytes(b'{"changed":true}\n')
            with self.assertRaises(ValueError):
                validate_snapshot(self.release, self.root)
            path.write_bytes(original)

    def test_tampered_or_missing_snapshot_rejected(self):
        path = self.root / self.release["editorial_snapshot"]["national_pack"]["path"]
        path.write_bytes(b"tampered")
        with self.assertRaises(ValueError):
            validate_snapshot(self.release, self.root)
        path.unlink()
        with self.assertRaises(OSError):
            validate_snapshot(self.release, self.root)

    def test_false_empty_change_declaration_rejected(self):
        self.release["refreshed_entry_ids"] = ["some-record"]
        with self.assertRaises(ValueError):
            validate_snapshot(self.release, self.root)


if __name__ == "__main__":
    unittest.main()
