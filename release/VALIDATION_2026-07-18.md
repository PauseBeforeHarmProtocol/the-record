# The Record — July 18, 2026 validation

Release candidate: `8.0.0-rc1`

Validated locally before publication:

- Nine HTML routes discovered and checked.
- Nine current records passed required-field and evidence-layer checks.
- Twenty-four source-ledger records are present.
- Internal page, anchor, download, and checksum targets resolve.
- JavaScript syntax passes `node --check`.
- Desktop and phone rendering were inspected.
- Live search, source expansion, copy-link feedback, mobile navigation, skip-link focus, and download-card behavior passed browser interaction checks.
- No Google-search fallback URLs are present in the current release layer.
- Credential-pattern scan passed for the public overlay.

Evidence boundary: this validates the July 18 current-release layer and its packaging. It does not independently revalidate every historical entry in the preserved long-form archive.

The validator supports both the release workspace layout (`site/`) and the GitHub-overlay layout (site files at repository root).
