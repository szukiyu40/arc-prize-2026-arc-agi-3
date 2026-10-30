# Method and input recovery

## Agent

This entry uses Daniel Franzen's Milestone 2 notebook and patch over the
TAAF/Duck harness. Qwen3.8-Flash-Next supplies reasoning and Python tool calls
from game observations. The tool sandbox exposes game actions and observations
and retains helper functions within a game. Current-grid images, frame
differences, animations, history pruning and the inherited priority scheduler
are configured in the saved notebook. There is no submitter prompt prefix in
this control and no new training or fine-tuning step in this entry.

Inference uses Intel AutoRound W4A16 main weights and a compact speculative
MTP drafter. The serving stack is the pinned Pennyroyal v2.5.3 wheelhouse,
based on modified SGLang. The notebook creates a compatible local drafter view.
Model provenance descriptions are retained, but this package does not
independently reproduce upstream model training or quantization.

## Declared inputs

| Input | Saved identity and acquisition |
| --- | --- |
| Selected notebook | [ARC3 Control v3, script 356741836](https://www.kaggle.com/code/szukiyu/arc3-control-v3?scriptVersionId=356741836), Version 1 |
| Inherited notebook | [Franzen Milestone 2](https://www.kaggle.com/code/dfranzen/arc-agi-3-milestone-2-solution), exact Version 3 bytes included under provenance |
| Target model | `dfranzen/intel-qwen3.8-flash-next-w4a16-autoround/Transformers/default/1` |
| Drafter | `dfranzen/albucino-qwen3-8-flash-next-drafter/Transformers/default/1` |
| Serving wheelhouse | [dfranzen/pennyroyal-v253](https://www.kaggle.com/datasets/dfranzen/pennyroyal-v253) |
| Runtime source bundle | [dfranzen/taaf-kaggle-source-bundle-copy](https://www.kaggle.com/datasets/dfranzen/taaf-kaggle-source-bundle-copy) |
| Byte-matching original source | [TAAF publisher version 4](https://www.kaggle.com/datasets/jeroencottaar/taaf-kaggle-source-share/versions/4) |
| Competition runtime | `arc-prize-2026-arc-agi-3` input and its official gateway |
| Machine | One NVIDIA RTX PRO 6000; notebook checks for at least 90,000 MiB |
| Container | `gcr.io/kaggle-private-byod/python@sha256:57e612b484cf3df5026ee4dcc3cb176974b22b2bc0937fb1e16132a8be4cb13c` |

The exact model references include version 1. The saved metadata does not pin
dataset revisions. Later investigation resolved the source and serving datasets
to version 1 and retained dated file inventories. Those observations do not
prove the full inputs mounted during the October 10 official run.
`runtime_inputs.json` separates native declarations from October 12 model hashes
and October 18 dataset hashes, including three model entries not observed.
Source reconstruction uses the later 73-file snapshot, whose bytes match the
original publisher ZIP, then applies the exact notebook patch. All 79 outputs
match the previously archived selected-source reconstruction.

The external `benchmark_initial.pkl` and `deploy_target.pkl` remain runtime
dependencies. The verifier checks their bytes in the publisher archive but never
deserializes them. Weights, vendor wheels, container layers and competition data
must be obtained separately under their providers' terms. Third-party account
access and historical availability have not been proven from this local package.

## Material settings and execution

| Setting | Selected notebook value |
| --- | --- |
| Temperature / top-p / top-k | 0.7 / 0.95 / 20 |
| Thinking / reasoning history | Enabled / `reasoning_content` |
| Analyzer context / output | 131,072 / 12,288 tokens |
| Server context | 139,264 tokens |
| Tool timeout / output | 30 seconds / 3,072 tokens |
| Analyzer timeout | 900 seconds |
| Official passes / solver concurrency / active streams | 1 / 120 / 10 with priority scheduling enabled |
| Configured official per-game runtime | 532 minutes with priority scheduling; actual available time depends on the inherited runtime and platform |
| Per-game action cap | None explicitly configured |
| Quantization / KV cache | AutoRound INT4 / `fp8_e4m3` |
| Static memory fraction / prefill chunk | 0.96 / 8,192 tokens |
| Speculation | NEXTN, 3 steps, 4 draft tokens, thresholds 1.0 |
| Ordinary demo | 25 public games, 1 pass, 7,200-second benchmark limit within a 9,000-second notebook watchdog |

The notebook remains authoritative. It uses offline wheels and locally served
weights during competition evaluation. The competition branch waits for the
gateway and obtains its game list, uses one pass and retains inherited runtime
deadline handling. Its local `soft_end` remains `None` in that branch; the short
demo timer is not imposed on official evaluation. V4's shared process clock,
readiness module, propagation fix and cleanup guarantees are not in this source.
No new claim about nine-hour completion or worst-case cleanup is made here.

An ordinary Save & Run starts actual setup, serving and public game inference.
It writes the placeholder Parquet only after its demo checks. It is not a cheap
publication or packaging operation. The static verifier above is the appropriate
way to inspect this package without consuming GPU time or a submission slot.

The recorded **official public score is 28.64**, from submission 57034274, observed
complete on October 10. A public-demo score is a different measurement, and the
official private score is unknown. No new run, deterministic reproduction,
score improvement or award eligibility is established here.
