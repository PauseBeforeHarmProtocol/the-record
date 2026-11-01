# Complete current-entry version history

Existing inline history rows are preserved unchanged. New rows may use
`encoding: "entry-with-history-prefix-v1"` to avoid recursively copying the same
earlier history into every subsequent snapshot.

The row's `entry` object contains **every field of the complete previous entry
except its duplicated `version_history` array**. Its
`version_history_prefix_length` must equal the row's zero-based position. If
`version_history_was_present` is true, reconstruct the full previous entry by
adding a deep copy of that exact preceding history prefix as `version_history`.
If false, the prefix must be empty and the reconstructed object must omit that
field. This preserves the distinction between an absent field and an empty
array.

`entry_sha256` binds the **entire reconstructed previous entry**, including its
full prior history, using `scripts/editorial_state.py`'s `canonical_bytes`:
UTF-8 JSON, non-ASCII preserved, sorted object keys, and compact separators.
The row also retains the snapshot timestamp and prior release version.

Use `append_entry_history(before, timestamp, release_version)` to produce an
unchanged deep copy of the prior history followed by the new row. It verifies
full-object reconstruction before returning. Use
`reconstruct_history_entry(history, index)` to recover a complete encoded prior
entry. `validate_entry_history` rejects an unknown encoding, altered checksum,
incomplete/forward prefix, wrong canonical ID, or rewriting/removing a prior
history prefix against the accepted base. Editorial validation runs this check
before checking content-bound reviews. New history representation remains part
of the entry's review hash; this format does not grant editorial approval or
advance evidence/review times.

This is lossless shared-prefix storage, not deletion, summarization, or a
replacement of old versions with prose. Existing entry packs continue to carry
the complete canonical structure in `entry.json`; all information required to
reconstruct its prior versions is inside that structure.
