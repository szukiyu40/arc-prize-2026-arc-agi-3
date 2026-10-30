# Third-party sources and notices

The TAAF / Duck source comes from
[Jeroen Cottaar's original dataset, version 4](https://www.kaggle.com/datasets/jeroencottaar/taaf-kaggle-source-share/versions/4).
Its metadata declares MIT and names Tufa Labs as a collaborator. All 73 archive
members match this entry's original input. The archive supplies no separate
copyright/license notice file; a bounded scan of all 71 non-pickle text members
also found no copyright/SPDX/permission-header text. This is a documented absence,
not an inference that the publisher or collaborator holds every copyright.
`LICENSES/MIT-upstream-TAAF.txt` preserves the declaration and standard MIT
permission/warranty body without inventing a holder or year.

Daniel Franzen's inherited source changes come from the
[public Milestone 2 notebook](https://www.kaggle.com/code/dfranzen/arc-agi-3-milestone-2-solution),
whose SHA-256 is `88a379f17c3a4ba8c98715fc23155346ccd6eb289bdafebadfc61a3178f9d9bd`.
The current Version 3 page explicitly declares Apache 2.0. A fresh native
readback of Version 3 matched all 569,095 bytes of this pinned source, binding
that observed license declaration to the exact inherited notebook. The dated
identity receipt is `provenance/upstream_notebook_license_identity.json`.
The related [fixed repository revision](https://github.com/da-franzen/arc-agi-3/tree/10882e332d883af3e61616df8c8a17d03a328a75)
has the unmodified Apache-2.0 text retained in this candidate. The exact inherited
patch and per-file/block correspondence are documented in CONTRIBUTIONS.md.
Underlying TAAF text remains a separate MIT layer. Existing source notices are
preserved without claiming permission to relicense upstream work.

Qwen3.8-Flash-Next derivatives use **Qwen Community License 1.0**, retained in
`LICENSES/Qwen-Community-1.0.txt`. The main checkpoint is Intel's AutoRound W4A16
quantization; the compact speculative drafter records RadixArk lineage and its
conversion description. Those descriptions are reproduced as provenance, not
an independently verified weight rebuild. The exact Kaggle model versions and
historically observed hashes are in `runtime_inputs.json`. No weights are
distributed here. Competition-specific eligibility remains unresolved.

The serving stack uses Pennyroyal v2.5.3 and separately obtained wheels. Selected
Pennyroyal, FlashInfer and embedded third-party notices remain in `LICENSES/`.
Previous provenance review matched three otherwise-unmapped wheels to their
public distribution hashes. That narrow result is not universal binary,
transitive-dependency, operating-system or container redistribution clearance.
This candidate distributes none of those binaries or container layers.

The external `deploy_target.pkl` and `benchmark_initial.pkl` contain the original
deployment and benchmark/solver objects. They remain required by the unchanged
runtime notebook, with hashes in the source contract. Their omission here does
not remove the runtime dependency; the verifier only treats their bytes as data.
It does not deserialize them.

The submitter's MIT-0 terms apply only to original contributions within the
explicit scope index. Upstream code, model terms, retained notices and public
facts are not converted to MIT-0. This notice record establishes provenance and
the intended distribution scope; it is not an organizer prize determination.
