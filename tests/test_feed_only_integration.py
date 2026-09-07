"""Exercise the real package and page builders without mutating the checkout."""
import copy
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import build_current_pages as pages
import package_current_release as packages
from editorial_state import artifact_names, digest


class FeedOnlyIntegration(unittest.TestCase):
    def test_feed_release_builds_only_receipt_and_manifest_and_resolves_pages(self):
        current = json.loads((ROOT / "data/release.json").read_text())
        candidate = copy.deepcopy(current)
        names = artifact_names(current)
        if current.get("artifact_mode") == "feed-only":
            snapshot = current["editorial_snapshot"]
        else:
            snapshot = {"version": current["version"]}
            for key in ("national_pack", "complete_pack", "national_brief", "in6_brief"):
                path = ROOT / "artifacts" / names[key]
                snapshot[key] = {"path": path.relative_to(ROOT).as_posix(), "sha256": digest(path.read_bytes())}
        candidate.update(version=current["version"] + "-feed-test", artifact_mode="feed-only", editorial_snapshot=snapshot,
                         new_entry_ids=[], added_entry_ids=[], refreshed_entry_ids=[], corrections=[])
        candidate.pop("engineering_revision", None)
        candidate.pop("maintenance_revision", None)
        resolved = artifact_names(candidate)
        with patch.multiple(packages, RELEASE=candidate, VERSION=candidate["version"], NEW_ENTRY_IDS=set(), RUN_RECEIPT_NAME=resolved["receipt"]):
            outputs = packages.build_outputs()
        receipt = ROOT / "artifacts" / resolved["receipt"]
        self.assertEqual(set(outputs), {receipt, ROOT / "artifacts/SHA256SUMS.txt"})
        self.assertIn(b"Reused editorial snapshot", outputs[receipt])
        def virtual_sha(path):
            return digest(outputs[path] if path in outputs else path.read_bytes())
        with patch.multiple(pages, RELEASE=candidate, VERSION=candidate["version"], ARTIFACT_NAMES=resolved,
                            NATIONAL_PACK_NAME=resolved["national_pack"], COMPLETE_PACK_NAME=resolved["complete_pack"],
                            IN6_CURRENT_BRIEF_NAME=resolved["in6_brief"], NEW_ENTRY_IDS=set(), MAINTENANCE=None), patch.object(pages, "sha", virtual_sha):
            rendered = pages.build_pages()
        self.assertEqual(len(rendered), 12)
        downloads = rendered[ROOT / "downloads/index.html"]
        self.assertIn("Editorial snapshot v" + snapshot["version"], downloads)
        self.assertIn(resolved["receipt"], downloads)
        self.assertIn(resolved["complete_pack"], downloads)
