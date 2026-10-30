# ARC3 Control v3 — selected official 28.64 source candidate

This candidate belongs to submission **57034274**,
[`szukiyu/arc3-control-v3`](https://www.kaggle.com/code/szukiyu/arc3-control-v3?scriptVersionId=356741836),
Version 1, script version 356741836. Its recorded official public score is **28.64**.
The notebook is the exact saved 571,636-byte original, SHA-256
`318aa89a1b62dbf9a331dc9ac1273dacb9a23757de034b68f835c37ee33998ad`.
It matched native readback on 2026-10-25. This local candidate is not yet a public release.

The notebook retains historical labels such as “unmeasured candidate,” an empty
prompt-prefix control, and old interim targets. They describe preparation-time
state and are preserved to keep the notebook exact. They do not supersede the
recorded official result. Inherited narrative about four demo passes is also
unchanged; the selected notebook's later override sets ordinary demo runs to one pass.

This is separate from the newer official V4 submission 57805295. The shared
original input and inherited patch match, but the selected source lacks V4's
later changes to `tool_agent.py`, `solver.py` and `taaf/benchmark.py`.
The 50.067892 public-demo result and V4's CPU envelope tests do not validate this entry.

## Verify source without running the agent

Obtain the exact external ZIP from the
[TAAF publisher, version 4](https://www.kaggle.com/datasets/jeroencottaar/taaf-kaggle-source-share/versions/4):
449,765 bytes, SHA-256
`e9d0b7221d724637bc5c19cc8d229eb58769e3822c45fc041869bc2ee4c2a94c`.
From this directory, with Python and Git:

```sh
python3 -B verify_selected_source.py --publisher-zip /absolute/path/taaf-kaggle-source-share.zip > /absolute/path/selected_verification.json
```

Keep the output outside the candidate; the manifest rejects extra files.
The verifier checks all packaged files, both notebook identities, inherited
patch extraction, cell-edit replay, all 73 publisher members, all 79 reconstructed
files and the 77 distributed text files. It applies only the inherited text patch
in temporary storage. It makes no network calls and executes no notebook,
model, game, source-transform helper or pickle. Python 3.13.1 is the tested
reconstruction interpreter; Kaggle inference uses the separately pinned container.
The manifest proves internal consistency; authenticate the whole archive using
its separately supplied hash before relying on an unfamiliar copy.

The original notebook is exact. The complete historical mounted runtime is
not proven: the source snapshot and some asset inventories were collected after
the October 10 official run. Source reconstruction is not official-score reproduction.
See [METHOD.md](METHOD.md), [CONTRIBUTIONS.md](CONTRIBUTIONS.md) and
[PUBLICATION_CHECKLIST.md](PUBLICATION_CHECKLIST.md) for the precise scope.

**Ordinary Save & Run of this notebook starts the public GPU benchmark.**
It does not have V4's packaging-only branch. Source verification and publication
preparation do not require another Save, GPU run or scored submission.

Original submitter contributions are offered under scoped MIT-0 terms in
[LICENSE](LICENSE). Upstream code, notebook passages, notices and model terms
remain separate. No weights, wheels, runtime pickles, container layers,
competition environment files or private experiment logs are distributed here.

Final private ranking, model prize eligibility and public publication are not
established by this candidate. The existing final selection is maintained.
