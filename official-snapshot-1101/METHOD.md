# Method and measured evidence

Submission 57852450 / kernel 142012233 V1 / script 364369411 was accepted
2026-10-31T22:52:32.250Z. Official scoring is pending at the dated contract status.
It is not final-selected; the existing 28.64 Control v3 remains selected (1/2).

This version uses the same Qwen3.8-Flash-Next W4A16 AutoRound main model,
INT4 MTP drafter, Pennyroyal serving stack, observations and priority scheduling
as the included official-v4 source. See ../official-v4/METHOD.md and
../official-v4/runtime_inputs.json for exact settings, providers, terms, dated
asset hashes and gaps. No new model or model weights are distributed.

The behavioral change is the two-line guard in snapshot_change.json. When an
interrupted worker's result dictionary has no keepable_functions field, the host
keeps the last committed helper snapshot. Explicit empty snapshots still clear
it and game reset semantics are unchanged. This does not make arbitrary partial
Python source executable: complete tool calls still use the existing sandbox.

The official envelope remains offline, one pass, outer concurrency 120 / client
streams 10, with 31,800 seconds of work, 32,280 seconds of hard cleanup boundary,
and 32,400 seconds of platform budget. Setup and model startup consume the
original process deadline. The public comparison instead uses a full 7,200-second
policy window after readiness. Those are separate runtime envelopes.

The prepared source notebook differs from the published official V4 notebook
only in introductory Markdown, packaging-receipt identity, run identity and one
new overlay cell (index 8). The old published notebook and the saved native
official V4 readback have equal 27 cell types/sources but different JSON byte
serialization; both hashes are recorded. No public-demo parent is substituted.
The distributed prepared JSON is 003804b0...; the actual saved native source JSON
is 77b8209e... . All 28 cell types/sources are equal, but whole JSON bytes differ.
Both hashes are in the contract. The native readback also has no cell outputs;
no execution output is added to the source distribution.

Original metadata omits the parent's keywords=["gpu"] and
docker_image_pinning_type="original" fields. These differences are enumerated,
not silently normalized. The requested container digest and machine shape are
identical; actual native source/metadata readback also confirmed those values.
All other runtime/input settings match after the three identity fields change.

The overlay is inside if ARC3_PACKAGE_OFFICIAL. Ordinary Save only writes the
packaging receipt and placeholder Parquet; the overlay is a no-op there. Actual
repair execution is evidenced separately by 31 hosted CPU cases (141706521/V1)
and the accepted public candidate's runtime manifest (141997081/V1). Native
packaging verifies all 28 source cells and metadata, not model execution or an
official score. Official rerun internal tool logs are not available to this
publication; its result is pending at the recorded status.

Fresh ordered public comparison, all 25 games retained including zero scores:

| Measurement | Control 141977461/V1 | Repair 141997081/V1 |
| --- | ---: | ---: |
| Mean score | 48.69184411734334 | 51.478096368000514 |
| Completed levels | 110 | 111 |
| Games won | 6 | 8 |
| Game actions | 5292 | 5332 |
| Generated tokens | 4364689 | 4414840 |
| Worker 30-second timeouts | 6 | 8 |
| Explicit helper-drop notices | 157 | 0 |

Eight games improved, nine declined, eight tied. The mean change is
+2.786252250657178. This is one ordered matched comparison, not a variance
estimate, significance test, deterministic gain, causal attribution, speedup,
token saving or official-score forecast. Setup durations differed; both policy
windows were 7,200 seconds on matching observed GPU/driver/configuration.

All eight candidate timeouts joined actual viewer results and were followed by
real actions. Next actual call openers advertised the old helper names without
observed intervening name redefinition; one directly reused bfs6 successfully.
This is limited retention evidence. Per-tool clocks and exact function identity
are unavailable. Two later unjoined calls have unknown timing/cost. The dc22
score regression remains in the mean and has no established whole-run cause.
No zero-timeout, cost-reduction, or broad strategy-promotion claim is made.

Reproduction of a real competition run requires all exact external inputs and
the pinned container/GPU settings in original_kernel_metadata.json, with internet
disabled. Its private flag records the submitted notebook's provenance; it does
not publish, submit, select or replace any entry. A competition rerun consumes
GPU resources and a submission slot. The source-distribution notebook is a
separate CPU-only archive writer and initiates no such evaluation.
