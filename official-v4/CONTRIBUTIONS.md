# Contribution boundaries

The completed MIT-0 terms cover only original expression in contributions for
which the submitter holds rights. A source diff or file hash is provenance
evidence, not independent proof that every changed byte is owned, copyrightable
or eligible for a new license. Unchanged, copied and adapted upstream expression
retains its applicable source terms, including inside diffs, replacement strings
and notebook cells.

## Reproducible layers

| Stage | Evidence and contribution scope |
| --- | --- |
| TAAF publisher input | 73 files, directly matched to the pinned publisher ZIP. The publisher declares MIT. No original holder/year is inferred from account or collaborator names. |
| Inherited Franzen patch | Changes 16 source files and produces 79 total files. The public notebook's Version 3 expressly declares Apache 2.0 and its fresh native source equals the pinned original. Fifteen changed source files also exactly match repository revision `10882e332d883af3e61616df8c8a17d03a328a75`. |
| Inherited `framework/run.py` | Whole file differs from the fork. Its two added patch blocks, 74 and 402 bytes, are each present exactly once in the fork. Original base text and the retained fork differences stay separate. The submitter's source transforms do not modify this file. |
| Local overlay | Changes `inference/agent/tool_agent.py`, `inference/framework/solver.py` and `taaf/benchmark.py`. |
| Local telemetry | Changes the first two of those files. |
| Local deadline propagation | Changes `inference/agent/tool_agent.py`. The four transform programs therefore produce six successive file edits across three distinct files. |
| Notebook adaptation | The exact 27-cell notebook includes inherited code and added lifecycle/packaging behavior. `recipe/notebook_adaptation_delta.diff` records the change from the pinned original Kaggle notebook. Entire changed cells are not automatically treated as independently owned. |
| Separable new source | `notebook_support/arc3_deadline.py`, `notebook_support/arc3_ready.py`, `verify_public_source.py` and `verify_contribution_map.py` carry the submitter's original source contributions. Embedded upstream expressions, if any, are excluded from the MIT-0 grant over submitter rights. |

Paths in the local source-stage rows are relative to the original source bundle:
the first two live under `src/ARC3-Inference/`, and the third under
`src/tufa-arc-agi-framework/src/`.

`provenance/source_layer_map.json` records every file's exact hashes through all
five stages. `provenance/submitter_hunk_map.json` records each local replacement
or insertion with before/after ranges and byte hashes. Ranges are zero-based,
half-open; an insertion has equal start/end positions in the prior file. A hunk
is not licensed as a whole merely because it was inserted: copied third-party
expression is explicitly excluded from the submitter's grant.

`provenance/run_py_inherited_added_blocks.json` records both inherited block
hashes, exact text and pinned-fork line offsets. The complete inherited file
comparison is in `provenance/inherited_patch_layer_correspondence.json`.
`recipe/submitter_source_delta.patch` shows the combined later changes; its
context and deleted lines remain upstream material. The earlier
`recipe/later_source_changes.diff` is an additional historical comparison with
the previously selected reconstruction, not the primary licensing boundary.

The inherited 498,780-byte patch is the original Kaggle notebook's 498,779-byte
magic-cell body plus one final LF. That mechanical newline does not create a
submitter ownership claim over the patch. The public notebook declaration and
root repository Apache-2.0 evidence are retained for the inherited contributions; the original MIT layer is
also retained. No blanket Apache-2.0 or MIT-0 assertion is made over all 79 files.

The file-by-file scope index is `LICENSE_SCOPE.json`. New documentation and
original provenance compilation expression are MIT-0 to the extent the submitter
holds such rights. Factual hashes, public identities, quotations and retained
license texts are not claimed as new exclusive property.
