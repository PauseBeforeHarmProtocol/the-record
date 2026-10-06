/* Authenticated GitData transport for functions.exec; no credentials or fs API.
 * Read this file with exec_command, then evaluate to obtain publishGitDataRuntime.
 * All shell payloads remain inside the runtime; never text() or notify() them.
 */
function gitDataResponse(result) {
  if (!result || result.isError) throw new Error("GitHub connector request failed");
  function inspect(value) {
    if (!value || typeof value !== "object") return null;
    if (value.sha || value.object || value.ref) return value;
    if (typeof value.content === "string") {
      try { const parsed = inspect(JSON.parse(value.content)); if (parsed) return parsed; }
      catch (_) { /* Plain status messages are not Git object responses. */ }
    }
    if (value.structuredContent) {
      const parsed = inspect(value.structuredContent); if (parsed) return parsed;
    }
    if (Array.isArray(value.content)) {
      for (const item of value.content) {
        if (typeof item.text === "string") {
          try { const parsed = inspect(JSON.parse(item.text)); if (parsed) return parsed; }
          catch (_) { /* Continue to the structured response. */ }
        }
      }
    }
    return null;
  }
  const parsed = inspect(result);
  if (!parsed) throw new Error("GitHub connector returned no usable Git object");
  return parsed;
}

function gitDataShellQuote(value) {
  return "'" + String(value).replace(/'/g, "'\\''") + "'";
}

async function publishGitDataRuntime({ tools, root, planPath, repository, branch,
                                     message, report = () => {} }) {
  if (!/^[A-Za-z0-9_.-]+\/[A-Za-z0-9_.-]+$/.test(repository)) {
    throw new Error("Invalid repository name");
  }
  if (!branch.startsWith("maintenance/") || /[\s~^:?*\[\\]/.test(branch) || branch.includes("..")) {
    throw new Error("Transport only updates a maintenance branch");
  }
  if (!message) throw new Error("A publication commit message is required");
  const quote = gitDataShellQuote;
  const script = "python scripts/prepare_gitdata_publish.py";
  async function shell(cmd) {
    const result = await tools.exec_command({ cmd, workdir: root,
      max_output_tokens: 300000, yield_time_ms: 10000 });
    if (result.exit_code !== 0 || result.session_id) {
      throw new Error("Local transport check did not complete successfully");
    }
    try { return JSON.parse(result.output); }
    catch (_) { throw new Error("Transport output is invalid or truncated; branch was not advanced"); }
  }
  const plan = await shell("cat " + quote(planPath));
  const args = " --plan " + quote(planPath);
  const local = await shell(script + " check" + args);
  if (local.status !== "passed" || local.target_tree !== plan.target_tree) {
    throw new Error("Publication tree no longer matches the accepted plan");
  }
  const api = "https://api.github.com/repos/" + repository;
  const read = async path => gitDataResponse(await tools.mcp__codex_apps__github_fetch({url: api + path}));
  const refPath = "/git/ref/heads/" + branch.split("/").map(encodeURIComponent).join("/");
  const [main, ref] = await Promise.all([read("/git/ref/heads/main"), read(refPath)]);
  if (main.object?.sha !== plan.base_commit || ref.object?.sha !== plan.base_commit) {
    throw new Error("Remote main or maintenance branch changed; inspect and rebuild against its head");
  }
  let cursor = 0, uploaded = 0;
  const chunkBytes = plan.chunk_bytes;
  if (!Number.isInteger(chunkBytes) || chunkBytes < 3 || chunkBytes % 3 || chunkBytes > 196608) {
    throw new Error("Invalid base64 chunk size");
  }
  async function upload(row) {
    let content = row.content;
    if (row.requires_chunks) {
      const parts = [];
      for (let offset = 0; offset < row.bytes; offset += chunkBytes) {
        const chunk = await shell(script + " blob" + args + " --sha " + quote(row.sha) +
          " --offset " + offset + " --length " + chunkBytes);
        if (chunk.sha !== row.sha || chunk.offset !== offset ||
            chunk.bytes !== Math.min(chunkBytes, row.bytes - offset) ||
            typeof chunk.content !== "string") {
          throw new Error("Blob chunk did not match its planned range");
        }
        if (offset + chunk.bytes < row.bytes && chunk.content.includes("=")) {
          throw new Error("Non-final base64 chunk contains padding");
        }
        parts.push(chunk.content);
      }
      content = parts.join("");
    }
    if (typeof content !== "string") throw new Error("Missing blob content");
    const blob = gitDataResponse(await tools.mcp__codex_apps__github_create_blob({
      repository_full_name: repository, encoding: "base64", content }));
    if (blob.sha !== row.sha) throw new Error("Uploaded blob SHA differs from accepted local blob");
    uploaded++;
  }
  while (cursor < plan.blobs.length) {
    const batch = await shell(script + " batch" + args + " --start " + cursor);
    if (!Array.isArray(batch.blobs) || !batch.blobs.length ||
        batch.next_start <= cursor || batch.next_start > plan.blobs.length) {
      throw new Error("Invalid or non-progressing blob batch");
    }
    const planned = plan.blobs.slice(cursor, batch.next_start);
    if (planned.length !== batch.blobs.length || batch.blobs.some((row, i) =>
        row.sha !== planned[i].sha || row.bytes !== planned[i].bytes)) {
      throw new Error("Blob batch differs from accepted manifest");
    }
    for (let i = 0; i < batch.blobs.length; i += 4) {
      // Wait for every result: a sibling failure must not abandon running uploads.
      const results = await Promise.allSettled(batch.blobs.slice(i, i + 4).map(upload));
      const failed = results.find(result => result.status === "rejected");
      if (failed) throw failed.reason;
    }
    cursor = batch.next_start;
    report({stage: "blobs", uploaded, total: plan.blobs.length});
  }
  for (const row of plan.trees) {
    const tree = gitDataResponse(await tools.mcp__codex_apps__github_create_tree({
      repository_full_name: repository, tree_elements: row.entries }));
    if (tree.sha !== row.sha) throw new Error("Remote subtree SHA differs from accepted local tree");
  }
  const finalCheck = await shell(script + " check" + args);
  if (finalCheck.status !== "passed" || finalCheck.target_tree !== plan.target_tree) {
    throw new Error("Accepted input drift before commit creation");
  }
  // Hash equality proves exact names, modes and bytes, including deletions.
  const commit = gitDataResponse(await tools.mcp__codex_apps__github_create_commit({
    repository_full_name: repository, message, parent_sha: plan.base_commit,
    tree_sha: plan.target_tree }));
  const verified = await read("/git/commits/" + commit.sha);
  if (verified.tree?.sha !== plan.target_tree || verified.parents?.length !== 1 ||
      verified.parents[0].sha !== plan.base_commit) {
    throw new Error("Remote commit tree or parent differs from the publication plan");
  }
  if ((await read("/git/ref/heads/main")).object?.sha !== plan.base_commit) {
    throw new Error("Remote main advanced during transport; leave objects unreferenced and rebuild");
  }
  const updated = await tools.mcp__codex_apps__github_update_ref({ repository_full_name: repository,
    branch_name: branch, sha: commit.sha, expected_sha: plan.base_commit, force: false });
  if (updated?.isError) throw new Error("GitHub connector rejected the branch update");
  const published = await read(refPath);
  if (published.object?.sha !== commit.sha) throw new Error("Remote branch verification failed");
  const remote = await read("/git/commits/" + published.object.sha);
  if (remote.tree?.sha !== plan.target_tree) throw new Error("Published branch tree differs from accepted tree");
  return {status: "branch-published", branch, commit: commit.sha, tree: plan.target_tree,
    local_commit: plan.target_commit, blobs_uploaded: uploaded,
    trees_uploaded: plan.trees.length, acceptance_sha256: plan.acceptance.sha256,
    plan_sha256: plan.plan_sha256};
}

if (typeof module !== "undefined") {
  module.exports = {gitDataResponse, gitDataShellQuote, publishGitDataRuntime};
}
