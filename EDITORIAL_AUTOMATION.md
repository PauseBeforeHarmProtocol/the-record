# The Record live-maintenance rules

This file is the durable acceptance policy for scheduled national-record updates. The automation's quota is a research target, never permission to pad the archive.

## Canonical data and generated outputs

Historical records are edited only in `data/legacy_entries.json`. Current national and IN-6 records are edited only in `data/current_entries.json`; release state belongs in `data/release.json`, and current source metadata belongs in `data/source_ledger.json`. Federated archive metadata must retain each upstream archive's own unit, scope, observation time, and provenance. Unlike upstream counts are never added together, and an upstream item does not become a verified Record entry without source-level editorial review, the complete reasoning-layer contract, and a duplicate/lifecycle decision.

The legacy blocks inside `the-record.html` and `docs/the-record.html`, the active-only compatibility view in `entries_array.js`, `data/archive_metrics.json`, `current_layer_bridge.js`, current static pages, CSV source ledger, release packs, and checksums are generated outputs. The two HTML custody representations retain superseded tombstones for stable redirects; `entries_array.js` deliberately excludes them so downstream consumers cannot double-count retired records. Do not repair or resolve one generated copy independently. Make the change in its canonical data file, regenerate every dependent output, and review the resulting diff.

Legacy stable IDs and review states must survive edits, merges, and corrections. A legacy entry marked `legacy-unreviewed` has not yet been revalidated under the current standard; that state does not assert that the entry is false.

Potential legacy content duplicates are a visible adjudication queue, not an automatic deletion. `data/archive_metrics.json` must surface exact, same-date, and cross-date heading candidates until an editor merges, distinguishes, or rejects them while preserving stable IDs and revision history. Once a duplicate is confirmed, keep the retired row as a `superseded` tombstone with `superseded_by` and `superseded_reason`; exclude it from runtime totals, sources, search, and the default timeline while redirecting its old stable permalink to the one active canonical record. A tombstone and all three state fields require an append-only ledger revision. Redirect chains, cycles, missing targets, and superseded-to-superseded targets fail the build.

Every newly added current record—and every legacy backfill that approaches the current bridge—must be compared across active legacy and national-current layers. Exact formal identifiers, canonical primary/official URLs, normalized headings, direct-source overlap, date proximity, and fact similarity are collision signals. A candidate requires an explicit `distinct_lifecycle_stage` or `false_positive` resolution with both IDs and notes. A `same_event_update` must consolidate or suppress one active row before publication; recording the label alone is not permission to double count. Duplicate legacy IDs, normalized source-ledger URLs, registry IDs/metrics, divergent generated representations, and unresolved strong cross-layer collisions are structural errors and must fail.

In the federated layer, machine candidates may coexist only as unpublished research leads. Independently derived evidence-URL, formal-ID, fact/title, canonical-target, date-interval, family, chronology, and lifecycle-cycle checks must run before review or publication; editor-entered hashes are never the only barrier. Two reviewed or published records may not claim the same event or target unless they are explicitly reciprocal, chronological stages in the same event family. A published crosswalk may target only a canonical record that has completed The Record's evidence and Maybe / Therefore standard.

For auditability, `data/federated_records.json` and other explicitly labeled research exports may publicly expose substantive AI-assisted draft fields before human review. Public accessibility is not publication authorization. Every such record must state that it is unreviewed, unauthorized for canonical publication, excluded from all canonical totals, and not presented as a finding. Public pages may summarize its origin and workflow state, but must not render draft analysis as accepted editorial content. Claims that “all AI-assisted content is human-approved” therefore apply only to canonically published findings, never to transparently exposed research-draft data.

## Publication threshold

An item qualifies when it documents a material exercise, attempted exercise, review, or measurable result of presidential or federal power. Examples include signed actions, implemented policy, formal proposals, court rulings, appropriations or expenditures, credible investigations, war-powers decisions, and evidence-based effectiveness findings.

Each entry must:

- separate sourced facts from significance and from the strongest relevant administration response;
- include a labeled **Maybe / Therefore** layer: the strongest plausible competing frame or material uncertainty, followed by the evidence-bound consequence, falsifier, or remaining test;
- describe the evidence state precisely: announced, proposed, ordered, implemented, enjoined, reversed, reported, or independently measured;
- use a primary record when reasonably available and independent reporting for corroboration or context;
- use at least two independent sources when a consequential claim rests mainly on unnamed sources;
- avoid duplicating an existing event; update an existing entry when the underlying event has evolved;
- preserve uncertainty and avoid turning an allegation, stated intent, or pending action into an accomplished fact;
- include a visible checked time, working source URLs, institutions, and a reproducible entry pack.

## Six-hour run

1. Read `data/release.json`, both canonical entry datasets, the source ledger, the generated archive metrics, the federated archive registry, and recent merged or open maintenance pull requests.
2. Refresh the Truth Social fallback with `python scripts/update_truth_social_feed.py`, then review new posts since the prior snapshot as leads. A post is a primary record of what Trump published, not independent proof of claims inside it.
3. Search from the last checked time through the run time. Aim for at least four qualifying national items.
4. Publish fewer than four when fewer than four pass the threshold. Record rejected candidates and the reason; never manufacture volume.
5. Check for corrections or material developments to existing entries before creating new IDs.
6. Edit canonical JSON and release metadata only. Use `data/legacy_entries.json` for historical remediation; never hand-edit a generated legacy representation. The landing pages summarize, while the full Trump archive remains the canonical long-form research layer.
7. Regenerate deterministic outputs in this order:
   1. `python scripts/sync_source_ledger.py`
   2. `python scripts/apply_legacy_remediations.py` when the append-only revision ledger changed
   3. `python scripts/sync_legacy_data.py`
   4. `python scripts/build_archive_metrics.py`
   5. `python scripts/sync_readme_metrics.py`
   6. `python scripts/validate_federated_records.py --self-test`
   7. `python scripts/build_legacy_bridge.py`
   8. `python scripts/package_current_release.py`
   9. `python scripts/build_current_pages.py`
   10. `python scripts/validate.py`
8. Repeat the same dependency order using each builder's `--check` mode where available: source ledger, legacy remediation ledger, legacy synchronization, archive metrics, README metrics, federated records, legacy bridge, packaging, current pages, then the repository validator. Packaging precedes page generation because the downloads page publishes the generated artifact hashes. Run the JavaScript syntax checks after the repository validator.
9. Open a reviewable pull request and wait for GitHub Actions. Merge only when the evidence checks, local validation, deterministic checks, and CI all pass. Otherwise leave the pull request open and report the blocker.

Ordinary six-hour currentizations should leave the large historical application body unchanged except for deterministic legacy synchronization when canonical legacy data actually changed. Current national entries and release metadata reach the published archive through the generated bridge.

## Correction rule

Never silently overwrite a material error. Add a timestamped correction note to the affected entry, retain the original claim in version history, regenerate its evidence pack, and summarize the correction in the run receipt.

AI output is drafting and review assistance, not a source.
