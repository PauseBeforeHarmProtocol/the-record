from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "the-record.html"
DOCS_ARCHIVE = ROOT / "docs/the-record.html"
BRIDGE = ROOT / "current_layer_bridge.js"


class SmokeFailure(AssertionError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SmokeFailure(message)


def embedded_json(html: str, element_id: str) -> object:
    match = re.search(
        rf'<script[^>]*id="{re.escape(element_id)}"[^>]*>(?P<data>.*?)</script>',
        html,
        re.DOTALL,
    )
    if match is None:
        raise SmokeFailure(f"missing embedded JSON element {element_id}")
    return json.loads(match.group("data"))


def bridge_payload(script: str, variable: str, next_variable: str | None) -> object:
    end = rf";\nwindow\.{re.escape(next_variable)}=" if next_variable else r";\s*$"
    match = re.search(
        rf"window\.{re.escape(variable)}=(?P<data>.*?){end}",
        script,
        re.DOTALL,
    )
    if match is None:
        raise SmokeFailure(f"missing generated bridge variable {variable}")
    return json.loads(match.group("data"))


def check_inline_javascript(path: Path, html: str) -> int:
    checked = 0
    scripts = re.finditer(
        r"<script(?P<attrs>[^>]*)>(?P<body>.*?)</script>",
        html,
        re.DOTALL | re.IGNORECASE,
    )
    for index, script in enumerate(scripts, start=1):
        attrs = script.group("attrs")
        if re.search(r"\bsrc\s*=", attrs, re.IGNORECASE) or re.search(
            r"\btype\s*=\s*['\"]application/json['\"]", attrs, re.IGNORECASE
        ):
            continue
        source = script.group("body")
        if not source.strip():
            continue
        result = subprocess.run(
            ["node", "--check", "-"],
            input=source,
            text=True,
            capture_output=True,
            check=False,
        )
        require(
            result.returncode == 0,
            f"{path.relative_to(ROOT)} inline script {index} has invalid JavaScript: "
            f"{result.stderr.strip()}",
        )
        checked += 1
    return checked


def main() -> int:
    try:
        archive_text = ARCHIVE.read_text(encoding="utf-8")
        docs_text = DOCS_ARCHIVE.read_text(encoding="utf-8")
        bridge_text = BRIDGE.read_text(encoding="utf-8")
        canonical = json.loads((ROOT / "data/legacy_entries.json").read_text(encoding="utf-8"))
        current = json.loads((ROOT / "data/current_entries.json").read_text(encoding="utf-8"))
        release = json.loads((ROOT / "data/release.json").read_text(encoding="utf-8"))
        manifest = json.loads(
            (ROOT / "data/legacy_restoration_manifest.json").read_text(encoding="utf-8")
        )

        require('src="current_layer_bridge.js"' in archive_text, "archive bridge URL is not relative")
        require('src="/the-record/current_layer_bridge.js"' not in archive_text, "archive bridge URL is root-specific")
        require('id="currentLayerLoadWarning"' in archive_text, "archive lacks bridge failure warning")
        require("CURRENT_LAYER_BRIDGE_STATUS_START" in archive_text, "archive lacks bridge status check")
        require(
            "new URL('../the-record.html',window.location.href)" in docs_text
            and "target.hash=window.location.hash" in docs_text,
            "docs compatibility page does not redirect deep links to the live archive",
        )

        embedded = embedded_json(archive_text, "dataEntries")
        require(embedded == canonical, "archive embedded payload differs from canonical legacy JSON")
        meta = bridge_payload(bridge_text, "CURRENT_LAYER_META", "CURRENT_LAYER_BRIDGE")
        bridged = bridge_payload(bridge_text, "CURRENT_LAYER_BRIDGE", None)
        require(meta.get("version") == release["version"], "bridge release version is stale")
        require(meta.get("checked_at") == release["checked_at"], "bridge checked-at value is stale")

        active_legacy = [row for row in canonical if row.get("review_status") != "superseded"]
        national = [row for row in current if row.get("scope") == "national"]
        require(
            {row.get("current_id") for row in bridged} == {row["id"] for row in national},
            "bridge does not contain exactly the national current layer",
        )
        expected_latest = max(
            [row["sort"] for row in active_legacy] + [row["date"] for row in national]
        )
        rendered_latest = max(
            [row["sort"] for row in active_legacy] + [row["sort"] for row in bridged]
        )
        require(rendered_latest == expected_latest, "combined timeline does not reach the latest record")
        require(rendered_latest > "2026-05-29", "combined timeline still stops at May 29")
        after_may_29 = sum(row["sort"] > "2026-05-29" for row in active_legacy) + sum(
            row["sort"] > "2026-05-29" for row in bridged
        )
        require(after_may_29 >= 100, "post-May-29 timeline recovery is unexpectedly small")
        require(
            len(active_legacy) + len(bridged) == meta.get("runtime_entry_count"),
            "bridge runtime total differs from canonical layers",
        )

        restored = manifest.get("restored_records", [])
        excluded = manifest.get("excluded_duplicates", [])
        require(len(restored) == 95, "restoration manifest does not contain 95 records")
        require(len(excluded) == 4, "restoration manifest does not contain four duplicate exclusions")
        require(
            len({row["legacy_id"] for row in restored}) == len(restored),
            "restoration manifest repeats a stable ID",
        )
        require(
            len({row["source_index"] for row in restored + excluded}) == 99,
            "restoration manifest repeats or loses a source index",
        )

        inline_count = check_inline_javascript(ARCHIVE, archive_text)
        inline_count += check_inline_javascript(DOCS_ARCHIVE, docs_text)
        bridge_check = subprocess.run(
            ["node", "--check", str(BRIDGE)],
            capture_output=True,
            text=True,
            check=False,
        )
        require(
            bridge_check.returncode == 0,
            f"current_layer_bridge.js has invalid JavaScript: {bridge_check.stderr.strip()}",
        )

        print(
            f"Timeline smoke test passed: {len(active_legacy) + len(bridged):,} runtime entries, "
            f"{after_may_29} after May 29, latest {rendered_latest}; "
            f"checked {inline_count} inline scripts."
        )
        return 0
    except (OSError, json.JSONDecodeError, SmokeFailure) as exc:
        print(f"ERROR: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
