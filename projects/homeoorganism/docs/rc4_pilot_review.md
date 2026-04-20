# RC4 Pilot Review

Date: 21 Apr 2026
Base commit: `b256f61`

## Research Framing

- Architectural question: can the preserved `rc3` decision stack, placed in a continuous
  regenerating ecology and measured with life/window metrics, sustain long-life behavior as
  defined in `docs/vision.md`?
- Frozen in this pilot: code and configs at `b256f61`, including the four `RC4` modes and
  the preserved `v1_baseline/`.
- Variable: evaluation mode only (`continuous_full`, `continuous_no_regen`,
  `episodic_full`, `v1_baseline_full`).
- Evidence: `artifacts/aggregate/pilot_summary.csv` plus per-run `life_summaries`,
  `window_metrics`, `event_metrics`, `series_metrics`, and episodic `reports/metrics.csv`.
- Unknown after pilot: official-wave stability at larger `n`, and relocation recovery in
  continuous modes, because no life survived to tick `1000`.

## Summary

Pilot execution succeeded operationally. All four modes completed on the frozen pilot seed
set with no runtime crashes, full artifact output, and clean per-mode summaries.

Pilot did not support the `RC4` behavioral hypothesis. `continuous_full` stayed short-lived
 (`mean 130.4`, `median 135.4`, `p75 153` ticks), far below the long-life target from
 `vision.md`, and every life in all continuous modes ended by `energy_depleted`.

The implementation question and the behavioral question separate cleanly here:

- `RC4` implementation status: success
- `RC4` long-life ecology hypothesis: fail in pilot

Recommendation: proceed to the official wave on the frozen codebase. Do not rebalance body
costs or alter `RC4` semantics after pilot. That would mix cycles and violate the
one-question-per-cycle rule.

## Pilot Configuration

- Seed set: `101, 202, 303, 404, 505`
- Continuous modes: `5` lives per seed, `life_max_ticks = 5000`
- Episodic mode: `5` episodes per seed
- Execution method: four separate `run-matrix` invocations, one per config, to preserve
  mode-specific semantics

## Aggregate Results

| Mode | Protocol size | Mean | Median | P75 | Key observation |
| --- | ---: | ---: | ---: | ---: | --- |
| `continuous_full` | `25` lives | `130.4` ticks | `135.4` ticks | `153` ticks | All lives ended by `energy_depleted` |
| `continuous_no_regen` | `25` lives | `100.88` ticks | `103.2` ticks | `106` ticks | Shorter than `continuous_full`; all lives ended by `energy_depleted` |
| `episodic_full` | `25` eval episodes | `99.36` survival steps | `104.0` survival steps | n/a | Only `eval_seen` rows were emitted |
| `v1_baseline_full` | `25` lives | `130.4` ticks | `135.4` ticks | `153` ticks | Bit-for-bit identical pilot life summaries to `continuous_full` |

Shared continuous-life behavior summary:

- `mode_transition_coherence`: mean/median `1.0` in `continuous_full` and
  `v1_baseline_full`
- `mode_diversity`: mean/median `2.2` in all continuous modes
- `lifetime_learning_curve` (`survival_share` by 5-life block): `0.0` for every seed in
  every continuous mode

## Per-Seed Duration Detail

`continuous_full` life durations by seed:

| Seed | Life durations |
| --- | --- |
| `101` | `[145, 116, 156, 175, 102]` |
| `202` | `[166, 124, 166, 122, 108]` |
| `303` | `[106, 153, 164, 93, 132]` |
| `404` | `[116, 153, 58, 108, 120]` |
| `505` | `[141, 119, 130, 160, 127]` |

`v1_baseline_full` matched the same per-seed and per-life sequences exactly across all
`25` lives.

## Calibration Against Frozen rc3

Calibration was checked against frozen `rc3 official_wave1` raw artifacts for
`core/full/eval_seen`.

| Metric | RC4 pilot episodic median | Frozen rc3 official median | Relative diff | Gate |
| --- | ---: | ---: | ---: | --- |
| `survival_steps` | `104.0` | `95.0` | `+9.5%` | FAIL |
| `mean_energy_deficit` | `0.3573` | `0.3851` | `7.2%` | FAIL |
| `mean_water_deficit` | `0.1481` | `0.3203` | `53.8%` | FAIL |
| `relocation_recovery_steps` | not emitted | `2.0` | n/a | INCOMPLETE |

Calibration conclusion:

- The pilot calibration gate did not pass.
- `episodic_full` emitted only `eval_seen` rows in this pilot, so relocation recovery
  calibration was not testable from the produced artifacts.
- Inference: the corrected `v2` environment semantics, including the removal of the frozen
  `rc3` single-biome defect, likely contribute to the numeric drift. This is still a failed
  gate numerically and should be documented as such rather than normalized away.

## Attribution Through Ablations

### `continuous_full` vs `continuous_no_regen`

- Median life ratio: `103.2 / 135.4 = 0.762`
- This satisfies the `RC4` pilot exit threshold
  `median(no_regen) <= 0.80 * median(full)`
- Interpretation: ecology regeneration matters, but its effect is too small to produce
  long-life behavior under the frozen body and control configuration

### `continuous_full` vs `v1_baseline_full`

- `life_summaries.jsonl` matched exactly for all `5` seeds
- This empirically confirms the `RC4` identity invariant on pilot data, not only in tests

### `episodic_full` vs frozen rc3

- The calibration path runs and emits shared rc3 metrics
- The numeric calibration gate did not pass in pilot
- This should be carried into official as a documented limitation, not patched post hoc

## RC4 Pilot Exit Gates

| Pilot exit gate from `rc4_spec.md` | Status | Evidence |
| --- | --- | --- |
| Zero runtime crashes across all pilot runs | PASS | All four per-mode pilot runs completed successfully |
| `median(no_regen) <= 0.80 * median(full)` | PASS | `0.762` |
| `episodic_full` within `5%` of frozen rc3 calibration | FAIL / INCOMPLETE | `survival_steps`, `mean_energy_deficit`, and `mean_water_deficit` drifted beyond `5%`; relocation recovery was not emitted |
| `v1_baseline_full` median `life_duration_ticks >= 500` and median `mode_diversity >= 2` | FAIL | Duration gate failed (`135.4`), diversity gate passed (`2.2`) |

## Operational Criteria Evaluation

| Criterion | Status | Evidence |
| --- | --- | --- |
| Long-life homeostasis | FAIL | `continuous_full p75 = 153` vs long-life target `> 4000` |
| Early `W=100` energy regulation | PASS, local only | `continuous_full` first-window `energy_in_range_ratio` mean `0.949` |
| Early `W=100` water regulation | PASS, local only | `continuous_full` first-window `water_in_range_ratio` mean `0.990` |
| Early `W=100` deficit variance band | PASS, local only | `continuous_full deficit_variance` mean `0.044` within target `0.02-0.15` |
| `anticipatory_response_time` | FAIL | `continuous_full`: `7` successful events vs `22` failed, failed events mean `14` ticks |
| `post_shift_recovery_ticks` | NOT MEASURED | No continuous life reached relocation tick `1000` |
| `lifetime_learning_curve` | FAIL | All `survival_share` block values were `0.0` |
| `mode_transition_coherence` | PASS | Mean/median `1.0` in `continuous_full` |
| `mode_diversity` | FAIL | Median `2.2` vs vision target `>= 3` |
| `mode_entropy_by_state` | PARTIAL | Non-zero in non-critical states, but not enough to overturn homeostatic/adaptive failure |

Program-level interpretation: `RC4` pilot does not satisfy the simultaneous homeostatic,
adaptive, and behavioral requirements from `vision.md`.

## Known Limitations Surfaced By Pilot

- Energy-side depletion dominated all continuous lives. Inference: the inherited `rc3` body
  cost configuration likely remains energy-limited under continuous movement pressure.
- Continuous lives were too short to trigger relocation at tick `1000`, so the adaptive
  perturbation path was not exercised in pilot.
- `episodic_full` pilot output did not include relocation evaluation rows, leaving one
  calibration metric unavailable.
- `matrix_runner` still requires one config per invocation. Pilot handled this correctly via
  four separate runs; this is an operational limitation, not a blocker.

## Readiness For Official Wave

Recommendation: **Option A - proceed to official on frozen code**.

Reasons:

- The implementation path is stable and produces complete artifacts.
- The behavioral result is already clear in pilot and official will strengthen it with
  higher `n` at low compute cost.
- Changing body costs or recalibrating semantics inside `RC4` would change the question
  after freeze.

Rejected option: rebalance body costs or reopen `RC4` specs before official. That would mix
the long-life ecology question with a new calibration/body-design question better isolated in
`RC5` or a later cycle.

## Next Steps

1. Freeze the current `main` state for `RC4` validation.
2. Run the official wave with the same four per-mode invocations on `official_rc4.txt`.
3. Assemble `rc4_verdict.md` from official artifacts without code changes.
4. Carry the documented pilot limitations into the final release package rather than
   rewriting history.
