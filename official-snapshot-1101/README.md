# ARC-AGI-3 submitted retained-snapshot repair

Source for submission 57852450, kernel 142012233 / V1, script 364369411,
submitted 2026-10-31 22:52 UTC. At the dated status in source_contract.json,
official scoring is pending. This entry is not selected for final evaluation;
Control v3 / 57034274 / 28.64 remains selected (1/2). No official improvement,
private ranking, or prize eligibility is established.

This package includes the prepared 28-cell source and original metadata as data.
All cell types/sources equal the actual native saved readback; whole notebook
JSON bytes differ. Both SHA-256 identities are in source_contract.json. The
effective agent is 94d0b3669bfbc3e25a55df6a568d64a96008c4c8099116d836227926cd5ae58f.
The other source files and dated external-input records are supplied by the
unchanged sibling official-v4 package; keep the complete repository together.

Run the repository's verify_all.py with the pinned TAAF publisher ZIP as described
in the root README. The unchanged V4 contribution-map verifier reconstructs all
79 parent files without executing Python transforms; this package's verifier
then checks the exact two-line repair, resulting 79-file hash map, submitted
notebook cells, and metadata with the two explicit omissions. Standalone:

    python3 -B verify_snapshot_source.py > /absolute/path/snapshot_verification.json

The standalone check validates distributed source consistency; the root check
additionally verifies reconstruction from the external original publisher ZIP.
No agent, model, game, notebook, dependency installation or pickle is run by this
package's verifier. Do not run an archived agent notebook just to inspect source.
Read METHOD.md for actual runtime requirements and evidence limitations.
