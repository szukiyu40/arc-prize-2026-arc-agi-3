# ARC-AGI-3 V4 — release candidate 2

This is a local source release candidate for official submission **57805295**,
`szukiyu/arc3-official-v4-v2-1030`, Version 1 / script version 363854386.
It has not been publicly released. The official evaluation was still
`Notebook Running` at 2026-10-30 13:28 UTC, with no published score. The existing
selected best is the separate ARC3 Control v3 entry at 28.64.

The exact 27 notebook cells and all policy/runtime source bytes match the first
immutable draft. The candidate adds a completed **MIT-0 license for original
submitter contributions**, explicit mixed-source scopes, file and hunk mappings,
and retained upstream notices. It does not grant rights over upstream code or
model weights. See [LICENSE](LICENSE) and [CONTRIBUTIONS.md](CONTRIBUTIONS.md).

## Reconstruct and check the source

Obtain the exact ZIP from the original
[TAAF publisher, version 4](https://www.kaggle.com/datasets/jeroencottaar/taaf-kaggle-source-share/versions/4):
449,765 bytes, SHA-256
`e9d0b7221d724637bc5c19cc8d229eb58769e3822c45fc041869bc2ee4c2a94c`.
All 73 members were compared byte for byte to this entry's original source input.
With Python 3.13.1 and Git, from this candidate directory:

```sh
python3 -B verify_public_source.py --publisher-zip /absolute/path/taaf-kaggle-source-share.zip > /absolute/path/verification.json
```

Place the output outside the candidate directory. The inventory rejects extra
files. No third-party Python packages are required. The verifier checks its
own file hash through the manifest, validates the exact input ZIP, applies the
known patch and source transforms in temporary storage, checks all 79 resulting
files and the 77 included text files, and emits all resulting hashes and actual
Python/Git versions. Both separately included notebook support modules are
checked against their literal notebook definitions. A repacked ZIP is rejected.

It performs no network calls, installs, notebook/model/game execution or pickle
deserialization. The known source-transform helpers execute only after package
and input checks. The self-contained manifest proves consistency, not trust in
an entirely replaced package; compare the externally supplied archive hash too.
Python 3.13.1 is the tested source-reconstruction interpreter. Runtime inference
uses the pinned Kaggle container in `notebook/original_kernel_metadata.json`.

An additional verifier independently replays the contribution map's text edits
as data, checking every intermediate stage and all final source hashes without
executing the four Python source-transform helpers:

```sh
python3 -B verify_contribution_map.py --publisher-zip /absolute/path/taaf-kaggle-source-share.zip > /absolute/path/contribution_verification.json
```

This validates the mechanical hunk mapping, not ownership of each expression.

The two runtime pickles, model weights, wheels, container layers and competition
environment data are external inputs. See [METHOD.md](METHOD.md) and
`runtime_inputs.json` for version identities, hashes, provenance dates and the
limits of that evidence. This distribution contains no private experiment logs.
The original kernel metadata records a private saved notebook; it is provenance,
not a command to publish, resubmit or replace it.

Source reconstruction does not reproduce an official score. The V4 public-demo
mean 50.067892 is a separate 25-game/7,200-second measurement. Model eligibility,
the final selected entry and actual public publication remain the explicit open
items in [PUBLICATION_CHECKLIST.md](PUBLICATION_CHECKLIST.md).
