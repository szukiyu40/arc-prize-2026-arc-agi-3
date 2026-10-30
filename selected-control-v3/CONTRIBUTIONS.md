# Source layers and changes

The selected notebook is byte-identical to the preserved native version. Its
23-cell upstream notebook has the documented Apache 2.0 declaration. Of those
23 source cells, 21 are unchanged in this 26-cell selected version. The two
adapted cells have zero-based selected indices 18 (configuration/diagnostics)
and 22 (demo limits, result summaries and coverage checks). Cells 0, 1 and 25
are inserted preparation text, run guards/diagnostics and final status reporting.

`provenance/notebook_cell_map.json` records each source hash and every text edit.
The verifier replays those edits as data and checks all results against the
exact notebook. `recipe/notebook_adaptation.diff` is a human-readable view;
the three added cells are also saved separately. A changed or inserted cell
does not by itself establish ownership of every expression within it.

The inherited harness patch is exactly the upstream notebook's patch body plus
one terminal LF, as materialized by the saved writefile cell. It is not a new
submitter patch. Applying it to the 73-file original publisher snapshot yields
79 files. The two runtime pickles remain external; the other 77 text files are
included under `effective_source/`.

`provenance/source_layers.json` binds each file's original and resulting hashes.
The inherited patch changes 16 files (including newly added paths). Prior direct
comparison establishes 15 complete changed-file matches to the pinned Franzen
fork. The remaining `inference/framework/run.py` is not a whole-file match,
but the patch's two added blocks each occur exactly once in that fork; the
retained correspondence records state that narrower result. No later submitter
source overlay is applied here.

The notebook, extracted edits and patches contain inherited source and context.
Original submitter expression is licensed MIT-0 only to the extent the submitter
holds those rights. Original publisher text retains declared MIT terms and
Franzen contributions retain their applicable Apache 2.0 terms. The map is a
mechanical provenance record, not a claim that modified files are wholly owned
by the submitter. `LICENSE_SCOPE.json` gives a scope entry for every packaged
file other than the manifest and itself.

The source layer is distinct from V4, whose later modifications affect three
files. This candidate contains neither V4's deadline/telemetry changes, C2's
retained-source disclosure, nor the later retention-snapshot repair.
