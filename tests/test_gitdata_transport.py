"""Content-addressed connector transport and pre-publication failure checks."""
from __future__ import annotations

import base64
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from prepare_gitdata_publish import (CHUNK_BYTES, accepted_inventory, blob_bytes,
                                     build_plan, check_checkout, check_plan_tree, digest, git,
                                     load_plan)


class GitDataPlanTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name) / "checkout"
        self.root.mkdir()
        git(self.root, "init", "-q")
        git(self.root, "config", "user.name", "Fixture")
        git(self.root, "config", "user.email", "fixture@example.invalid")
        (self.root / "stable").mkdir()
        (self.root / "stable/keep.txt").write_text("unchanged\n")
        (self.root / "remove.txt").write_text("delete me\n")
        (self.root / "rename.txt").write_text("reuse this blob\n")
        git(self.root, "add", ".")
        git(self.root, "commit", "-qm", "base")
        self.base = git(self.root, "rev-parse", "HEAD").decode().strip()

    def tearDown(self):
        self.directory.cleanup()

    def modify(self):
        (self.root / "remove.txt").unlink()
        (self.root / "rename.txt").rename(self.root / "moved name.txt")
        (self.root / "new dir").mkdir()
        data = bytes(range(256)) * 800
        (self.root / "new dir/binary.zip").write_bytes(data)
        (self.root / "duplicate.bin").write_bytes(data)
        (self.root / "new dir/café.txt").write_text("non-ASCII name\n")
        (self.root / "run.sh").write_text("#!/bin/sh\nexit 0\n")
        (self.root / "run.sh").chmod(0o755)
        os.symlink("stable/keep.txt", self.root / "link")
        git(self.root, "add", "-A")
        git(self.root, "commit", "-qm", "target")

    def test_exact_tree_preserves_deletion_names_modes_and_subtrees(self):
        self.modify()
        plan = build_plan(self.root, self.base)
        stable = git(self.root, "rev-parse", f"{self.base}:stable").decode().strip()
        self.assertNotIn(stable, {row["sha"] for row in plan["trees"]})
        base_blob = git(self.root, "rev-parse", f"{self.base}:rename.txt").decode().strip()
        self.assertNotIn(base_blob, {row["sha"] for row in plan["blobs"]})
        duplicate = next(row for row in plan["blobs"] if "duplicate.bin" in row["paths"])
        self.assertEqual(set(duplicate["paths"]), {"duplicate.bin", "new dir/binary.zip"})
        available = set()
        for tree in plan["trees"]:
            for row in tree["entries"]:
                if row["type"] == "tree" and row["sha"] != stable:
                    self.assertIn(row["sha"], available)
            payload = b"".join(f"{row['mode']} {row['type']} {row['sha']}\t{row['path']}".encode() + b"\0"
                               for row in tree["entries"])
            rebuilt = subprocess.check_output(["git", "mktree", "-z"], cwd=self.root, input=payload).decode().strip()
            self.assertEqual(rebuilt, tree["sha"])
            available.add(rebuilt)
        self.assertEqual(plan["trees"][-1]["sha"], plan["target_tree"])
        rows = plan["trees"][-1]["entries"]
        self.assertNotIn("remove.txt", {row["path"] for row in rows})
        self.assertEqual(next(row for row in rows if row["path"] == "run.sh")["mode"], "100755")
        self.assertEqual(next(row for row in rows if row["path"] == "link")["mode"], "120000")

    def test_chunk_concatenation_round_trips_binary(self):
        self.modify()
        plan = build_plan(self.root, self.base)
        row = next(row for row in plan["blobs"] if "duplicate.bin" in row["paths"])
        data = blob_bytes(self.root, plan, row["sha"])
        encoded = "".join(base64.b64encode(data[i:i + CHUNK_BYTES]).decode()
                          for i in range(0, len(data), CHUNK_BYTES))
        self.assertEqual(base64.b64decode(encoded, validate=True), data)
        self.assertEqual(CHUNK_BYTES % 3, 0)

    def test_unchanged_tree_needs_no_upload(self):
        plan = build_plan(self.root, self.base)
        self.assertEqual(plan["blobs"], [])
        self.assertEqual(plan["trees"], [])

    def test_dirty_checkout_and_nonancestor_base_are_rejected(self):
        (self.root / "remove.txt").write_text("changed\n")
        with self.assertRaisesRegex(ValueError, "clean"):
            check_checkout(self.root, self.base)
        git(self.root, "checkout", "--", "remove.txt")
        self.modify()
        target = git(self.root, "rev-parse", "HEAD").decode().strip()
        with self.assertRaises(subprocess.CalledProcessError):
            build_plan(self.root, target, self.base)

    def test_plan_tampering_and_blob_outside_plan_are_rejected(self):
        plan = build_plan(self.root, self.base)
        plan["plan_sha256"] = digest(plan)
        path = Path(self.directory.name) / "plan.json"
        path.write_text(json.dumps(plan))
        self.assertEqual(load_plan(path)["target_tree"], plan["target_tree"])
        plan["target_tree"] = "0" * 40
        path.write_text(json.dumps(plan))
        with self.assertRaisesRegex(ValueError, "checksum"):
            load_plan(path)
        with self.assertRaisesRegex(ValueError, "not in"):
            blob_bytes(self.root, plan, "0" * 40)
        with self.assertRaisesRegex(ValueError, "immutable Git commit"):
            check_plan_tree(self.root, plan)

    def test_acceptance_inventory_drift_fails(self):
        result = hashlib.sha256()
        names = git(self.root, "ls-files", "-z")
        for name in sorted(set(names.split(b"\0")) - {b""}):
            result.update(name + b"\0" + (self.root / name.decode()).read_bytes())
        value = result.hexdigest()
        receipt = {"status": "passed", "base_commit": self.base,
                   "steps": [{"name": "input-stability", "status": "passed"}],
                   "input_sha256": value, "verified_input_sha256": value}
        path = Path(self.directory.name) / "receipt.json"
        path.write_text(json.dumps(receipt))
        self.assertEqual(accepted_inventory(self.root, path, self.base)["input_sha256"], value)
        (self.root / "remove.txt").write_text("changed\n")
        with self.assertRaisesRegex(ValueError, "accepted inventory"):
            accepted_inventory(self.root, path, self.base)
        receipt["steps"][0]["status"] = "not_run"
        path.write_text(json.dumps(receipt))
        with self.assertRaisesRegex(ValueError, "incomplete"):
            accepted_inventory(self.root, path, self.base)


class GitDataRuntimeTests(unittest.TestCase):
    def test_connector_failures_cannot_advance_branch(self):
        result = subprocess.run(["node", str(ROOT / "tests/fixtures/gitdata_runtime.js")],
                                cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("PASS: connector transport guard cases", result.stdout)


if __name__ == "__main__":
    unittest.main()
