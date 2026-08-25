# The Record live-maintenance rules

This file is the durable acceptance policy for scheduled national-record updates. The automation's quota is a research target, never permission to pad the archive.

## Publication threshold

An item qualifies when it documents a material exercise, attempted exercise, review, or measurable result of presidential or federal power. Examples include signed actions, implemented policy, formal proposals, court rulings, appropriations or expenditures, credible investigations, war-powers decisions, and evidence-based effectiveness findings.

Each entry must:

- separate sourced facts from significance and from the strongest relevant administration response;
- describe the evidence state precisely: announced, proposed, ordered, implemented, enjoined, reversed, reported, or independently measured;
- use a primary record when reasonably available and independent reporting for corroboration or context;
- use at least two independent sources when a consequential claim rests mainly on unnamed sources;
- avoid duplicating an existing event; update an existing entry when the underlying event has evolved;
- preserve uncertainty and avoid turning an allegation, stated intent, or pending action into an accomplished fact;
- include a visible checked time, working source URLs, institutions, and a reproducible entry pack.

## Six-hour run

1. Read `data/release.json`, the current entries, the source ledger, and recent merged or open maintenance pull requests.
2. Refresh the Truth Social fallback with `python scripts/update_truth_social_feed.py`, then review new posts since the prior snapshot as leads. A post is a primary record of what Trump published, not independent proof of claims inside it.
3. Search from the last checked time through the run time. Aim for at least four qualifying national items.
4. Publish fewer than four when fewer than four pass the threshold. Record rejected candidates and the reason; never manufacture volume.
5. Check for corrections or material developments to existing entries before creating new IDs.
6. Update canonical JSON and CSV, release metadata, the curated front-door pages, packs, checksums, the release receipt, and `current_layer_bridge.js`. The landing pages summarize; the full Trump archive remains the canonical long-form research layer.
7. Run `scripts/build_legacy_bridge.py` so current national entries and release metadata reach the archive through its small generated asset. Keep the 14 MB historical `the-record.html` application stable during ordinary scheduled runs.
8. Run every deterministic builder and validator. Open a reviewable pull request and wait for GitHub Actions.
9. Merge only when the evidence checks, local validation, and CI all pass. Otherwise leave the pull request open and report the blocker.

## Correction rule

Never silently overwrite a material error. Add a timestamped correction note to the affected entry, retain the original claim in version history, regenerate its evidence pack, and summarize the correction in the run receipt.

AI output is drafting and review assistance, not a source.
