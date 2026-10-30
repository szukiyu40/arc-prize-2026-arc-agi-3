# ARC Prize 2026 — ARC-AGI-3 source releases

Source and method disclosure for Yu Suzuki's ARC-AGI-3 entries. The two source
snapshots are separate, pinned packages; their notebook and effective source
identities must not be interchanged.

| Package | Official entry | Recorded status at 2026-10-30 14:12 UTC |
| --- | --- | --- |
| [Control v3](selected-control-v3/README.md) | `szukiyu/arc3-control-v3`, V1, script 356741836, submission 57034274 | Official public **28.64**; selected for final evaluation |
| [V4](official-v4/README.md) | `szukiyu/arc3-official-v4-v2-1030`, V1, script 363854386, submission 57805295 | Official evaluation running; official score unknown |

V4's public-demo mean of 50.067892 on 25 games is a separate measurement, not an
official leaderboard score. No private score, first-place result or prize
eligibility is claimed. This disclosure does not change the selected entries.

Both use Daniel Franzen's Milestone 2 solution over TAAF/Duck, Qwen3.8-Flash-Next
AutoRound main weights, an MTP drafter and the pinned Pennyroyal serving stack.
Detailed parameters, provenance, external input references and reproducibility
limits are in each package's `METHOD.md` and `runtime_inputs.json`.

## Source-only verification

Obtain the original [TAAF publisher ZIP, version 4](https://www.kaggle.com/datasets/jeroencottaar/taaf-kaggle-source-share/versions/4):
449,765 bytes; SHA-256
`e9d0b7221d724637bc5c19cc8d229eb58769e3822c45fc041869bc2ee4c2a94c`.
With Python 3.13.1 and Git, run from this repository:

```sh
python3 -B verify_all.py --publisher-zip /absolute/path/taaf-kaggle-source-share.zip > /absolute/path/source_verification.json
```

Keep generated output outside this repository. This checks every release file,
reconstructs each 79-file source tree and verifies V4's contribution mapping.
No models, games, notebook cells, installations or pickle deserialization run.
V4's known source-transform helpers execute only after the package and publisher
input hashes pass. The second V4 check replays their edits as data independently.

The selected notebook is exact; the complete historical runtime inputs mounted
on October 10 are not proven. Later model and dataset hashes retain their dates.
Source reconstruction does not reproduce an official score. Original model
weights, wheels, container layers, runtime pickles and competition data remain
external inputs, acquired under their own terms.

## Runtime distinction

**Control v3's ordinary Save & Run starts a real GPU demo.** It is not a source
verification step. V4 has a separate packaging-only ordinary Save branch and
later deadline/readiness changes. Read the exact package instructions before
attempting execution. Neither verifier starts a Kaggle job or consumes a slot.

## Licensing and publication records

Original submitter expression is released under MIT-0 only where the submitter
holds those rights. TAAF's declared MIT terms, Franzen's Apache 2.0 terms and
other third-party notices remain separate. Each package includes its file and
change scope maps. The scope-specific `LICENSE` files take precedence over any
repository-wide automated license classification. Model license eligibility is
a separate unresolved competition question; no weights are distributed here.

The package directories are byte-preserved from the reviewed release candidates.
Their internal README/checklists and metadata record the earlier preparation
state, including “not published.” This top-level release record supersedes only
that publication status when this repository is publicly available; it does not
rewrite historical evidence, source, scores, eligibility or missing runtime
facts. `RELEASES.json` records exact package manifests. `SOURCE_MANIFEST.json`
covers all distributed repository files except itself.

The [public Kaggle source-distribution notebook](https://www.kaggle.com/code/szukiyu/arc-agi-3-source-release-2026)
completed as version 1 on 2026-10-30. Its three source cells and two output files
were retrieved without credentials; all 249 files in its source archive match
the original GitHub commit `d6de8555c7a5f108f4f0106542390ff525688918`
(tag `source-release-20261030`). Later GitHub commits add only publication records
and cross-links; the two package directories remain unchanged.

The distribution notebook only writes source files. It uses no competition data,
models or GPU, and is explicitly dedicated and linked to ARC-AGI-3. Kaggle rejected
the earlier attempt to attach competition data to a public notebook; no such
data are needed or included in this release. Inclusion in the competition's Code
tab and the organizer's interpretation of the sharing requirement have not been
independently confirmed. [PUBLICATION.json](PUBLICATION.json) records the dated
public readbacks and archive identity.

[ARC Prize 2026 rules](https://arcprize.org/competitions/2026) require source and
method publication before receiving official private evaluation scores. This
repository supplies source disclosure; full award compliance remains subject
to the competition's rules and review.
