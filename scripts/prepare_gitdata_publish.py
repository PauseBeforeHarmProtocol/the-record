"""Prepare an accepted, immutable Git tree for authenticated connector transport.

This program does not write GitHub refs or store credentials. Payloads are read
from Git objects, never from changing working files. Scratch plans belong outside
the checkout. The companion JavaScript runs through functions.exec's tools API.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SHA = re.compile(r"[0-9a-f]{40}\Z")
# Divisible by three so base64 chunks can be concatenated without interior padding.
CHUNK_BYTES = 192 * 1024


def git(root: Path, *args: str) -> bytes:
    return subprocess.check_output(["git", *args], cwd=root)


def digest(value: dict) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                     ensure_ascii=False).encode()).hexdigest()


def tree_entries(root: Path, tree_sha: str) -> list[dict]:
    rows = []
    for item in git(root, "ls-tree", "-z", tree_sha).split(b"\0"):
        if not item:
            continue
        header, name = item.split(b"\t", 1)
        mode, kind, sha = header.decode("ascii").split()
        rows.append({"path": name.decode("utf-8"), "mode": mode,
                     "type": kind, "sha": sha})
    return rows


def object_inventory(root: Path, tree_sha: str) -> set[str]:
    output = git(root, "ls-tree", "-r", "-t", "-z", tree_sha)
    return {tree_sha} | {row.split(b"\t", 1)[0].split()[2].decode("ascii")
                         for row in output.split(b"\0") if row}


def base_tree_paths(root: Path, tree_sha: str) -> dict[str, str]:
    paths = {"": tree_sha}
    for item in git(root, "ls-tree", "-r", "-t", "-z", tree_sha).split(b"\0"):
        if not item:
            continue
        header, name = item.split(b"\t", 1)
        _mode, kind, sha = header.decode("ascii").split()
        if kind == "tree":
            paths[name.decode("utf-8")] = sha
    return paths


def tree_delta(base: list[dict], target: list[dict]) -> list[dict]:
    """Patch one tree level, retaining modes and explicit null deletions."""
    previous = {row["path"]: row for row in base}
    current = {row["path"]: row for row in target}
    changes = [row for row in target if previous.get(row["path"]) != row]
    changes.extend({**row, "sha": None} for row in base if row["path"] not in current)
    return changes


def build_plan(root: Path, base_ref: str, target_ref: str = "HEAD",
               transport_base_ref: str | None = None) -> dict:
    if any(ref.startswith("-") for ref in (base_ref, target_ref, transport_base_ref or base_ref)):
        raise ValueError("refs cannot begin with an option prefix")
    if git(root, "rev-parse", "--show-object-format").strip() != b"sha1":
        raise ValueError("GitHub transport requires SHA-1 Git objects")
    base = git(root, "rev-parse", "--verify", f"{base_ref}^{{commit}}").decode().strip()
    target = git(root, "rev-parse", "--verify", f"{target_ref}^{{commit}}").decode().strip()
    subprocess.run(["git", "merge-base", "--is-ancestor", base, target], cwd=root, check=True)
    transport_base = git(root, "rev-parse", "--verify", f"{transport_base_ref or base_ref}^{{commit}}").decode().strip()
    subprocess.run(["git", "merge-base", "--is-ancestor", base, transport_base], cwd=root, check=True)
    subprocess.run(["git", "merge-base", "--is-ancestor", transport_base, target], cwd=root, check=True)
    base_tree = git(root, "rev-parse", f"{base}^{{tree}}").decode().strip()
    transport_base_tree = git(root, "rev-parse", f"{transport_base}^{{tree}}").decode().strip()
    target_tree = git(root, "rev-parse", f"{target}^{{tree}}").decode().strip()
    known = object_inventory(root, transport_base_tree)
    counterparts = base_tree_paths(root, transport_base_tree)
    blobs: dict[str, dict] = {}
    trees: list[dict] = []
    visited = set()

    def visit(sha: str, prefix: str = "") -> None:
        if sha in known or sha in visited:
            return
        visited.add(sha)
        entries = tree_entries(root, sha)
        for row in entries:
            path = f"{prefix}/{row['path']}" if prefix else row["path"]
            if row["type"] == "tree":
                visit(row["sha"], path)
            elif row["type"] == "blob" and row["sha"] not in known:
                if row["sha"] not in blobs:
                    size = int(git(root, "cat-file", "-s", row["sha"]))
                    blobs[row["sha"]] = {"sha": row["sha"], "bytes": size, "paths": []}
                blobs[row["sha"]]["paths"].append(path)
            elif row["type"] not in ("blob", "commit"):
                raise ValueError(f"unsupported Git object type at {path}")
        # Child trees always precede the parent. Unchanged subtrees are reused.
        node = {"sha": sha, "path": prefix, "entries": entries}
        if prefix in counterparts:
            node["base_tree_sha"] = counterparts[prefix]
            node["transport_entries"] = tree_delta(tree_entries(root, counterparts[prefix]), entries)
        else:
            node["transport_entries"] = entries
        trees.append(node)

    visit(target_tree)
    items = sorted(blobs.values(), key=lambda row: (row["paths"][0], row["sha"]))
    return {"schema_version": "1.2.0", "chunk_bytes": CHUNK_BYTES,
            "base_commit": base, "base_tree": base_tree,
            "transport_base_commit": transport_base, "transport_base_tree": transport_base_tree,
            "target_commit": target, "target_tree": target_tree, "blobs": items,
            "trees": trees, "upload_bytes": sum(row["bytes"] for row in items),
            "reused_object_count": len(known)}


def accepted_inventory(root: Path, receipt_path: Path, base: str) -> dict:
    if receipt_path.resolve().is_relative_to(root.resolve()):
        raise ValueError("acceptance receipt must be outside the checkout")
    receipt = json.loads(receipt_path.read_text())
    if receipt.get("status") != "passed" or not receipt.get("steps"):
        raise ValueError("a completed, passing acceptance receipt is required")
    if any(row.get("status") != "passed" for row in receipt["steps"]):
        raise ValueError("acceptance receipt contains an incomplete or failed gate")
    if not any(row.get("name") == "input-stability" for row in receipt["steps"]):
        raise ValueError("acceptance receipt lacks input-stability gate")
    if receipt.get("base_commit") != base:
        raise ValueError("accepted base differs from publication base")
    # Match the acceptance runner's inventory, including file names and bytes.
    result = hashlib.sha256()
    names = git(root, "ls-files", "--cached", "--others", "--exclude-standard", "-z")
    for name in sorted(set(names.split(b"\0")) - {b""}):
        path = root / name.decode("utf-8")
        if path.is_file():
            result.update(path.relative_to(root).as_posix().encode() + b"\0")
            with path.open("rb") as handle:
                for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                    result.update(chunk)
    value = result.hexdigest()
    if value != receipt.get("input_sha256") or value != receipt.get("verified_input_sha256"):
        raise ValueError("checkout bytes differ from accepted inventory; rerun acceptance")
    return {"path": str(receipt_path.resolve()),
            "sha256": hashlib.sha256(receipt_path.read_bytes()).hexdigest(),
            "input_sha256": value}


def check_checkout(root: Path, target: str) -> None:
    if git(root, "rev-parse", "HEAD").decode().strip() != target:
        raise ValueError("publication target must be current HEAD")
    if git(root, "status", "--porcelain", "--untracked-files=all"):
        raise ValueError("commit the accepted tree first; checkout must be clean")


def load_plan(path: Path) -> dict:
    plan = json.loads(path.read_text())
    checksum = plan.pop("plan_sha256", None)
    if checksum != digest(plan):
        raise ValueError("publication plan checksum mismatch")
    plan["plan_sha256"] = checksum
    return plan


def check_plan_tree(root: Path, plan: dict) -> None:
    pairs = [("target_commit", "target_tree"), ("base_commit", "base_tree")]
    if "transport_base_commit" in plan:
        pairs.append(("transport_base_commit", "transport_base_tree"))
    for ref_key, tree_key in pairs:
        ref = plan.get(ref_key, "")
        if not SHA.fullmatch(ref):
            raise ValueError("invalid commit SHA in publication plan")
        actual = git(root, "rev-parse", f"{ref}^{{tree}}").decode().strip()
        if actual != plan.get(tree_key):
            raise ValueError("publication plan tree differs from immutable Git commit")


def blob_bytes(root: Path, plan: dict, sha: str) -> bytes:
    if not SHA.fullmatch(sha) or not any(row["sha"] == sha for row in plan["blobs"]):
        raise ValueError("blob SHA is not in the accepted plan")
    data = git(root, "cat-file", "blob", sha)
    actual = hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()
    if actual != sha:
        raise ValueError("local Git blob hash mismatch")
    return data


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    commands = parser.add_subparsers(dest="command", required=True)
    prepare = commands.add_parser("plan")
    prepare.add_argument("--base-ref", required=True)
    prepare.add_argument("--commit", default="HEAD")
    prepare.add_argument("--transport-base-ref", help="previous local commit already published to the maintenance branch")
    prepare.add_argument("--receipt", type=Path, required=True)
    prepare.add_argument("--output", type=Path, required=True)
    check = commands.add_parser("check")
    check.add_argument("--plan", type=Path, required=True)
    payload = commands.add_parser("blob")
    payload.add_argument("--plan", type=Path, required=True)
    payload.add_argument("--sha", required=True)
    payload.add_argument("--offset", type=int, default=0)
    payload.add_argument("--length", type=int, default=CHUNK_BYTES)
    batch = commands.add_parser("batch")
    batch.add_argument("--plan", type=Path, required=True)
    batch.add_argument("--start", type=int, default=0)
    batch.add_argument("--max-bytes", type=int, default=CHUNK_BYTES)
    args = parser.parse_args()
    root = args.root.resolve()
    try:
        if args.command == "plan":
            if args.output.resolve().is_relative_to(root):
                raise ValueError("publication plan must be outside the checkout")
            plan = build_plan(root, args.base_ref, args.commit, args.transport_base_ref)
            check_checkout(root, plan["target_commit"])
            plan["acceptance"] = accepted_inventory(root, args.receipt, plan["base_commit"])
            plan["plan_sha256"] = digest(plan)
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n")
            print(json.dumps({key: plan[key] for key in ("target_tree", "upload_bytes", "plan_sha256")} |
                             {"new_blobs": len(plan["blobs"]), "new_trees": len(plan["trees"])}))
            return 0
        plan = load_plan(args.plan)
        if args.command == "check":
            check_plan_tree(root, plan)
            check_checkout(root, plan["target_commit"])
            accepted = accepted_inventory(root, Path(plan["acceptance"]["path"]), plan["base_commit"])
            if accepted != plan["acceptance"]:
                raise ValueError("acceptance receipt changed since preparation")
            print(json.dumps({"status": "passed", "target_tree": plan["target_tree"]}))
        elif args.command == "blob":
            if args.offset < 0 or not 1 <= args.length <= CHUNK_BYTES:
                raise ValueError("invalid chunk range")
            data = blob_bytes(root, plan, args.sha)
            if args.offset > len(data):
                raise ValueError("chunk offset exceeds blob size")
            chunk = data[args.offset:args.offset + args.length]
            print(json.dumps({"sha": args.sha, "offset": args.offset, "bytes": len(chunk),
                              "content": base64.b64encode(chunk).decode("ascii")}))
        elif args.command == "batch":
            if not 0 <= args.start <= len(plan["blobs"]) or not 1 <= args.max_bytes <= CHUNK_BYTES:
                raise ValueError("invalid batch range")
            rows, used, index = [], 0, args.start
            while index < len(plan["blobs"]):
                row = plan["blobs"][index]
                if rows and used + row["bytes"] > args.max_bytes:
                    break
                result = {"sha": row["sha"], "bytes": row["bytes"]}
                if row["bytes"] > args.max_bytes:
                    result["requires_chunks"] = True
                else:
                    result["content"] = base64.b64encode(blob_bytes(root, plan, row["sha"])).decode("ascii")
                    used += row["bytes"]
                rows.append(result)
                index += 1
                if result.get("requires_chunks") or len(rows) >= 100:
                    break
            print(json.dumps({"blobs": rows, "next_start": index}))
        return 0
    except (ValueError, OSError, subprocess.CalledProcessError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
