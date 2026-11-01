"""Run small compatibility repairs against the real preserved archive functions."""
from __future__ import annotations

import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ArchiveCompatibilityTests(unittest.TestCase):
    def test_stable_id_search_complete_date_labels_and_unchanged_records(self):
        result = subprocess.run(
            ["node", str(ROOT / "tests/fixtures/archive_compat.js"), str(ROOT)],
            cwd=ROOT, capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("PASS: archive stable-ID search and complete date labels", result.stdout)

    def test_old_and_current_permalinks_render_only_the_target_page(self):
        result = subprocess.run(
            ["node", str(ROOT / "tests/fixtures/archive_compat.js"), str(ROOT), "permalinks"],
            cwd=ROOT, capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("PASS: bounded real-archive permalinks", result.stdout)


if __name__ == "__main__":
    unittest.main()
