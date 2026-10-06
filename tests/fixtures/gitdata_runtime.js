const assert = require("node:assert/strict");
const {publishGitDataRuntime, gitDataResponse, gitDataShellQuote} =
  require("../../scripts/publish_gitdata_runtime.js");

async function scenario(failure = null) {
  const base = "a".repeat(40), blob = "b".repeat(40), tree = "c".repeat(40), commit = "d".repeat(40);
  const plan = {base_commit: base, target_commit: "e".repeat(40), target_tree: tree,
    chunk_bytes: 3, blobs: [{sha: blob, bytes: 5}],
    trees: [{sha: tree, entries: [{path: "file", mode: "100644", type: "blob", sha: blob}]}],
    acceptance: {sha256: "receipt"}, plan_sha256: "plan"};
  let checks = 0, updated = false, created = false, mainReads = 0;
  const wrap = value => ({structuredContent: {content: JSON.stringify(value)}});
  const tools = {
    async exec_command({cmd}) {
      let value;
      if (cmd.startsWith("cat ")) value = plan;
      else if (cmd.includes(" check")) {
        checks++;
        value = {status: failure === "input-drift" && checks === 2 ? "failed" : "passed", target_tree: tree};
      } else if (cmd.includes(" batch")) value = {blobs: [{sha: blob, bytes: 5, requires_chunks: true}], next_start: 1};
      else if (cmd.includes(" blob")) {
        const offset = Number(cmd.match(/--offset (\d+)/)[1]);
        value = {sha: blob, offset, bytes: offset ? 2 : 3, content: offset ? "bG8=" : "aGVs"};
      } else throw new Error("unexpected command");
      return {exit_code: 0, output: failure === "truncated" && cmd.includes(" blob") ? "{broken" : JSON.stringify(value)};
    },
    async mcp__codex_apps__github_fetch({url}) {
      if (url.endsWith("/heads/main")) {
        mainReads++;
        return wrap({object: {sha: failure === "main-race" && mainReads > 1 ? "changed" : base}});
      }
      if (url.includes("/git/ref/heads/maintenance/")) {
        return wrap({object: {sha: failure === "branch-race" ? "changed" : updated ? commit : base}});
      }
      if (url.endsWith("/git/commits/" + commit)) return wrap({sha: commit,
        tree: {sha: failure === "commit-tree" ? "wrong" : tree}, parents: [{sha: base}]});
      throw new Error("unexpected API URL");
    },
    async mcp__codex_apps__github_create_blob({content, encoding}) {
      assert.equal(encoding, "base64");
      assert.equal(content, "aGVsbG8=");
      return wrap({sha: failure === "blob-hash" ? "wrong" : blob});
    },
    async mcp__codex_apps__github_create_tree({tree_elements}) {
      assert.deepEqual(tree_elements, plan.trees[0].entries);
      return wrap({sha: failure === "tree-hash" ? "wrong" : tree});
    },
    async mcp__codex_apps__github_create_commit({parent_sha, tree_sha}) {
      created = true;
      assert.equal(parent_sha, base); assert.equal(tree_sha, tree);
      return wrap({sha: commit});
    },
    async mcp__codex_apps__github_update_ref({expected_sha, force, sha}) {
      assert.equal(expected_sha, base); assert.equal(force, false); assert.equal(sha, commit);
      updated = true;
      return wrap({object: {sha: commit}});
    }
  };
  try {
    const receipt = await publishGitDataRuntime({tools, root: "/fixture", planPath: "/tmp/fixture",
      repository: "owner/repo", branch: failure === "unsafe-branch" ? "main" : "maintenance/fixture",
      message: "accepted fixture"});
    assert.equal(failure, null);
    assert.equal(updated, true);
    assert.equal(receipt.tree, tree);
    assert.equal(receipt.blobs_uploaded, 1);
  } catch (error) {
    if (!failure) throw error;
    assert.equal(updated, false, "failed transport must not move a branch");
    if (!["commit-tree", "main-race"].includes(failure)) assert.equal(created, false);
  }
}

(async () => {
  assert.equal(gitDataResponse({structuredContent: {sha: "x"}}).sha, "x");
  assert.throws(() => gitDataResponse({isError: true}), /failed/);
  assert.equal(gitDataShellQuote("x'$(bad)"), "'x'\\''$(bad)'");
  await scenario();
  for (const failure of ["unsafe-branch", "branch-race", "truncated", "blob-hash", "tree-hash",
                         "input-drift", "commit-tree", "main-race"]) await scenario(failure);
  console.log("PASS: connector transport guard cases");
})().catch(error => {console.error(error); process.exitCode = 1;});
