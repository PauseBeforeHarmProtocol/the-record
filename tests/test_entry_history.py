"""Lossless prior-entry history with an append-only shared history prefix."""
from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from editorial_state import (HISTORY_ENCODING, append_entry_history, canonical_bytes,
                             digest, reconstruct_history_entry, validate_entry_history)


class EntryHistoryTests(unittest.TestCase):
    def setUp(self):
        self.before = {
            "id": "NAT-fixture", "facts": ["Fact é—one"], "significance": "Unchanged",
            "optional_null": None, "version_history": [
                {"timestamp": "2026-10-30T12:00:00Z", "entry": {"id": "NAT-fixture", "facts": ["Earlier"]}},
            ],
        }

    def test_complete_source_object_round_trip_and_no_mutation(self):
        original = copy.deepcopy(self.before)
        history = append_entry_history(self.before, "2026-11-01T20:00:00Z", "10.208.0")
        self.assertEqual(self.before, original)
        self.assertEqual(history[:-1], original["version_history"])
        self.assertEqual(reconstruct_history_entry(history, 1), original)
        self.assertEqual(history[1]["entry_sha256"], digest(canonical_bytes(original)))
        self.assertNotIn("version_history", history[1]["entry"])
        history[1]["entry"]["facts"].append("Independent copy")
        self.assertEqual(self.before, original)

    def test_two_refreshes_reconstruct_both_full_versions(self):
        first = copy.deepcopy(self.before)
        first["version_history"] = append_entry_history(self.before, "2026-11-01T20:00:00Z", "10.208.0")
        first["facts"].append("Second fact")
        second = copy.deepcopy(first)
        second["version_history"] = append_entry_history(first, "2026-11-01T21:00:00Z", "10.209.0")
        second["facts"].append("Third fact")
        validate_entry_history(first, self.before)
        validate_entry_history(second, first)
        self.assertEqual(reconstruct_history_entry(second["version_history"], 1), self.before)
        self.assertEqual(reconstruct_history_entry(second["version_history"], 2), first)
        # New rows contain the factual object once, not a recursive history copy.
        self.assertNotIn("version_history", second["version_history"][2]["entry"])

    def test_absent_and_empty_history_are_distinct_and_lossless(self):
        for previous in ({"id": "x", "facts": []}, {"id": "x", "facts": [], "version_history": []}):
            history = append_entry_history(previous, "2026-11-01T20:00:00Z", "10.208.0")
            self.assertEqual(reconstruct_history_entry(history, 0), previous)
            validate_entry_history({**previous, "version_history": history}, previous)

    def test_snapshot_field_and_checksum_tampering_are_rejected(self):
        for field, value in (("entry_sha256", "0" * 64), ("entry", {"id": "NAT-fixture", "facts": ["Forged"]})):
            history = append_entry_history(self.before, "2026-11-01T20:00:00Z", "10.208.0")
            history[-1][field] = value
            with self.assertRaisesRegex(ValueError, "checksum"):
                validate_entry_history({**self.before, "version_history": history})

    def test_incomplete_forward_boolean_prefixes_and_unknown_encoding_fail(self):
        for key, value in (("version_history_prefix_length", 0), ("version_history_prefix_length", 2),
                           ("version_history_prefix_length", True), ("encoding", "unknown"),
                           ("version_history_was_present", False)):
            history = append_entry_history(self.before, "2026-11-01T20:00:00Z", "10.208.0")
            history[-1][key] = value
            with self.assertRaises(ValueError):
                validate_entry_history({**self.before, "version_history": history})

    def test_existing_prefix_cannot_be_changed_or_removed(self):
        history = append_entry_history(self.before, "2026-11-01T20:00:00Z", "10.208.0")
        for changed in (history[1:], [*copy.deepcopy(history)]):
            if len(changed) == len(history):
                changed[0]["entry"]["facts"] = ["Altered earlier row"]
            with self.assertRaisesRegex(ValueError, "append-only"):
                validate_entry_history({**self.before, "version_history": changed}, self.before)
        with self.assertRaisesRegex(ValueError, "removed"):
            validate_entry_history({"id": "x"}, {"id": "x", "version_history": []})

    def test_new_encoding_cannot_change_canonical_target(self):
        history = append_entry_history(self.before, "2026-11-01T20:00:00Z", "10.208.0")
        with self.assertRaisesRegex(ValueError, "different canonical"):
            validate_entry_history({"id": "other", "version_history": history})


if __name__ == "__main__":
    unittest.main()
