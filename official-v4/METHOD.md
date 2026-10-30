# Method and reproduction instructions

## System

The entry uses Daniel Franzen's ARC-AGI-3 Milestone 2 solution built on Tufa Labs'
Duck/TAAF harness. Qwen3.8-Flash-Next generates reasoning and Python tool calls
from rendered game observations. The tool sandbox lets the model observe the
environment, invoke available game actions, and retain helper functions within
each game. The prompt/history and rendering behavior are preserved from the
measured V4 policy. This entry does not train or fine-tune the base model and
does not use a hosted external model during evaluation.

The main checkpoint is Intel's W4A16 AutoRound quantization. A compact INT4
group-32 MTP checkpoint is used for speculative decoding. The notebook creates
a compatible local view of that drafter; the checkpoint provenance and
transformation claims remain those recorded in the supplied model assets.
Independently reproducing their upstream quantization is outside this package.

Later source changes provide shared deadlines, subprocess and task cleanup,
server readiness checks, minimal scheduling evidence, and propagation of the
deadline exception through the analyzer path. They are applied to a private
copy of the input bundle. The rejected C2 retained-source disclosure candidate
and the later retention-snapshot repair are not in this official version.

## Inputs and resources

Use the following existing Kaggle inputs, preserving version identities and the
exact container digest in `notebook/original_kernel_metadata.json`:

| Input | Pinned identity |
| --- | --- |
| Main model | `dfranzen/intel-qwen3.8-flash-next-w4a16-autoround/Transformers/default/1`; model instance version 1007514 |
| Drafter | `dfranzen/albucino-qwen3-8-flash-next-drafter/Transformers/default/1`; model instance version 1007009 |
| Serving wheels | `dfranzen/pennyroyal-v253`; dataset 12273106, version 1 |
| Source bundle | `dfranzen/taaf-kaggle-source-bundle-copy`; dataset 12250142, version 1 |
| Competition | `arc-prize-2026-arc-agi-3` |
| GPU | NVIDIA RTX PRO 6000 Blackwell; accepted public run reported 97,887 MiB |
| Container | `gcr.io/kaggle-private-byod/python@sha256:57e612b484cf3df5026ee4dcc3cb176974b22b2bc0937fb1e16132a8be4cb13c` |

The dataset/model version identities and historical file hashes are listed in
`runtime_inputs.json`, with dates and unobserved model entries preserved. Dataset slugs in
notebook metadata alone do not prove which bytes mounted in a later official
rerun. Preserved receipts have their original dates. Full model weights, vendor
wheels, container layers, and competition environment files are not distributed
in this package. Obtain those assets from the listed providers under their terms.

The serving stack is Pennyroyal v2.5.3, a modified SGLang distribution; the
upstream notebook attributes it to John Pezzulli's fork at
`d00d88efc8d6281b12be4f4073126aec95038c55`, with additional named contributors.
Use the attached wheelhouse, not a current generic SGLang installation. The
notebook installs from local wheels with internet disabled during evaluation.

## Material parameters

| Setting | Official V4 value |
| --- | --- |
| Temperature / top-p / top-k | 0.7 / 0.95 / 20 |
| Thinking and reasoning history | Enabled, `reasoning_content` |
| Analyzer context / maximum output | 131,072 / 12,288 tokens |
| Server context | 139,264 tokens |
| Tool call timeout / tool output | 30 seconds / 3,072 tokens |
| Analyzer timeout | 900 seconds, subject to the shared remaining budget |
| Outer solver concurrency / active model streams | 120 / 10 |
| Passes / per-game action limit | 1 / no explicit per-game limit |
| Main quantization / KV cache | AutoRound INT4 / `fp8_e4m3` |
| Static memory fraction / prefill chunk | 0.96 / 8,192 tokens |
| Speculation | NEXTN, 3 steps, 4 draft tokens, acceptance thresholds 1.0 |
| Scheduling | Original priority/remaining-time scheduling; pacing disabled |
| Observation | Current grid, 10x upscale, frame differences and animations |

The exact notebook remains authoritative for every parameter and environment
variable; this table is a readable index. Randomness and platform conditions are
not fixed sufficiently to promise deterministic results.

## Execution and validation

Ordinary notebook Save enters `packaging_only`: two files are written and no
agent/game/model work is performed. The saved version was verified against all
27 source cells, attachment/settings fields, both actual output files, and an
actual Parquet read. That is packaging validation only.

On a competition rerun, the first cell checks the rerun flag and gateway URL.
The shared clock starts no later than kernel process start on Linux. The work,
hard-cleanup, and platform boundaries are respectively 31,800, 32,280, and
32,400 seconds from that origin. Input copies, patching, installation, model
startup, and readiness consume this original budget. The remaining work window
is used for gateway games; the official branch does not reset a 7,200-second
demo window. Actual platform clock origin and enforcement are distinct.

The notebook validates model health, synthetic warmup and cache flush, obtains
game names from the official gateway, and runs one pass with the original
priority scheduler. It does not use game-ID-specific policies or inspect hidden
environment internals. The official gateway supplies the scored output.

Hosted CPU 141700237/V1 exercised both candidate envelopes on public environments
with an authored analyzer, across normal completion, shared deadline, and caller
cancellation. All six cases and 486 sessions passed the saved-data audit. This
does not validate model reasoning, nine-hour behavior, or private gateway scores.
The accepted V4 public measurement 140722261/V1 scored 50.06789238626432 on 25
demo games over its 7,200-second active window. This is not an official score or
a performance forecast. Official submission 57805295 remains a separate result.

To reproduce an official evaluation, use the saved version or a reviewed exact
copy with all listed inputs, the pinned container, offline RTX PRO 6000 settings,
and a fresh competition submission. This consumes a daily slot and GPU resources;
the source verifier does not initiate it. Do not manually impersonate the
competition rerun flag in a local or ordinary interactive environment.
