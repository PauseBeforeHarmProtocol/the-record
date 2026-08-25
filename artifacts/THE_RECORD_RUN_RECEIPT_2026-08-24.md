# The Record — Maintenance Run Receipt

- Release: 8.2.1
- Checked: 2026-08-24 5:58 PM EDT
- Editorial window: 2026-08-24 10:43 AM EDT through 2026-08-24 5:58 PM EDT
- Added: 4 national records
- Materially refreshed: 1 national record
- Current layer: 27 records backed by 54 source-ledger records
- Full archive runtime: 4,667 records; 6,528 source references; 5,147 distinct stored URLs
- Legacy custody: 4,647 stored rows; 4,644 active; 3 duplicate tombstones excluded from totals

## Added or materially refreshed records

- `NAT-2026-08-22-001` — U.S. imposes 50% duties on selected Canadian goods as Trump announces a broader 2027 escalation
- `NAT-2026-08-24-002` — Supreme Court lifts one injunction blocking Trump's mail-voting directive
- `NAT-2026-08-24-003` — Treasury sanctions nearly 60 Iran-linked targets and broadens its secondary-sanctions warning
- `NAT-2026-08-24-004` — United States formally removes Syria from the state-sponsors-of-terrorism list
- `NAT-2026-08-24-005` — USDA reopens the Douglas cattle crossing after a 15-month livestock-import suspension

## Withheld candidates

- Reported DOJ inquiry into the 2022 Mar-a-Lago search: Still withheld because the consequential claim rested on unnamed sourcing and did not yet have the second independent source required by the live-maintenance policy.
- Plan to revoke up to 200,000 visitor visas held by asylum seekers: Withheld because the scale and timing rested on unpublished State Department documents and unnamed officials; Reuters repeated AP's report rather than independently confirming it.
- Joint Economic Committee minority estimate of gains in Trump's oil-and-gas holdings: Withheld pending the direct committee analysis and independent verification of the valuation method, holdings range, and conflict-of-interest estimate.

## Maintenance revision

- Recorded: 2026-08-25
- Scope: Legacy quality remediation, generated metrics, duplicate tombstones, archive federation, and deterministic repackaging. No new post-cutoff current-affairs finding is implied.
- Artifact identity: The maintenance version is incremented because generated packages and checksums changed while the editorial checked-through time remained unchanged.

## Verification

Current front-door pages, the canonical legacy dataset, archive bridge, individual evidence packs, aggregate packs, source ledgers, and checksums are generated deterministically. Ordinary six-hour current-only runs keep the historical application body stable; bounded legacy maintenance intentionally regenerates its canonical payload. Publication requires the repository validator and GitHub Actions to pass.
