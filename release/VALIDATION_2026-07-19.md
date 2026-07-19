# The Record — July 19, 2026 validation

Release candidate: `8.0.1-rc1`

Validated locally before publication:

- Thirteen HTML files and eleven generated current routes were checked.
- Ten current records passed required-field and evidence-layer checks.
- The deterministic weekly view contains seven records: six national and one IN-6.
- The searchable Agencies map contains 26 agencies and institutions.
- Twenty-eight source-ledger records are present.
- Internal pages, anchors, downloads, ZIP archives, adjacent checksum files, and the aggregate checksum manifest resolve and validate.
- Current-page generation, the legacy Past Week bridge, and release packaging reproduce without a diff.
- JavaScript syntax passes `node --check`; Python scripts compile.
- The DOM interaction suite executed the shipped JavaScript and passed Home navigation, Weekly scope filters and search, Agencies search and compatibility alias, mobile-navigation state, and the legacy Past Week control.
- Current AI disclosure names ChatGPT 5.6 Sol Max and Claude Fable 5 Max (Cowork); original Claude (Anthropic, Opus 4) essay authorship remains intact and hash-receipted.
- Credential-pattern scanning passed.

A real-browser visual smoke pass was attempted, but the Playwright browser host returned an empty or truncated Chromium archive. No browser runtime was installed. This infrastructure limitation does not change the passing DOM interaction, structural, link, package, checksum, syntax, or credential-scan results.

Evidence boundary: this validates the July 19 current-release layer, its legacy bridge, and its packaging. It does not independently revalidate every historical entry in the preserved long-form archive.
