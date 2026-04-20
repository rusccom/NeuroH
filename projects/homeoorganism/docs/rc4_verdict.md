# RC4 Verdict

Cycle: `RC4 - Long-Life Ecology`
Date: 21 Apr 2026
Spec: `projects/homeoorganism/docs/rc4_spec.md`
Pilot freeze tag: `v2-rc4-pilot-frozen`
Pilot review: `projects/homeoorganism/docs/rc4_pilot_review.md`

## Executive Summary

`RC4` is architecturally complete and operationally stable, but it did not satisfy the
long-life ecology hypothesis under the preserved `rc3` body and control parameters.

In the official wave, `continuous_full` reached `mean 135.84`, `median 133.98`, and
`p75 153.25` life ticks, far below the long-life target from `vision.md`. Regeneration did
matter: `continuous_no_regen` stayed shorter with median `101.0`, yielding a
`no_regen / full` median ratio of `0.754`. But that effect size was too small to produce
long-horizon viability. `v1_baseline_full` remained empirically identical to
`continuous_full`, confirming that `RC4` changed the environment and evaluation regime, not
the agent architecture itself.

Verdict: implementation success, behavioral hypothesis fail. The frozen `RC4` foundation is
good enough to carry forward into `RC5`, but `RC4` itself does not justify a claim of
continuous living behavior.

## Cycle Question Answered

Architectural question:

Can the preserved `rc3` decision stack, placed in a continuously regenerating environment
and measured with life/window metrics, sustain behavior that satisfies the homeostatic,
adaptive, and behavioral criteria defined in `vision.md` over horizons longer than any
single `rc3` episode?

Answer:

**No, not under the frozen `RC4` body and control configuration.**

The agent survives somewhat longer with regeneration than without it, but still dies
consistently around tick `130-150`, usually from energy depletion. `RC4` therefore answers
its architectural question negatively while preserving attribution.

## Protocol Note

The official wave was executed on the frozen code tagged `v2-rc4-pilot-frozen` with the
official seed set and spec-sized protocol counts.

- Code and tracked configs were not edited after the freeze tag.
- To satisfy the spec requirement of `20` lives / episodes per official seed, the official
  run used temporary external config materializations identical to the frozen configs except
  for protocol-size overrides:
  `lives_per_seed: 20`, and for `episodic_full` also `eval_episodes_seen: 20`.
- This preserves the frozen codebase while matching the frozen protocol counts in
  `rc4_spec.md`.

## Quantitative Results

### Official Wave Summary

| Mode | Protocol size | Mean | Median | P75 | Main result |
| --- | ---: | ---: | ---: | ---: | --- |
| `continuous_full` | `200` lives | `135.84` ticks | `133.98` ticks | `153.25` ticks | Short-lived; regeneration not sufficient for long-life behavior |
| `continuous_no_regen` | `200` lives | `101.09` ticks | `101.0` ticks | `108.0` ticks | Shorter than `continuous_full`; regen effect is real but modest |
| `episodic_full` | `200` eval episodes | `100.65` survival steps | `102.0` survival steps | n/a | Episodic path remains stable but drifts from frozen `rc3` calibration |
| `v1_baseline_full` | `200` lives | `135.84` ticks | `133.98` ticks | `153.25` ticks | Empirically identical to `continuous_full` across all official seeds |

Continuous end reasons:

- `continuous_full`: `energy_depleted` and `water_depleted`, with energy depletion dominant
- `continuous_no_regen`: `energy_depleted` only
- `v1_baseline_full`: same pattern as `continuous_full`

### Gate Evaluation

| Gate | Status | Evidence |
| --- | --- | --- |
| Zero runtime crashes across official runs | PASS | All four per-mode official runs completed successfully |
| Continuous modes ran `20` lives per official seed | PASS | `episode_count = 200` in official continuous summaries |
| Episodic mode ran `20` episodes per official seed | PASS | `episode_count = 200` in `official_episodic_full.csv` |
| `median(no_regen) <= 0.80 * median(full)` | PASS | `101.0 / 133.98 = 0.754` |
| `episodic_full` within `5%` of frozen `rc3` calibration | FAIL / INCOMPLETE | `survival_steps`, `mean_energy_deficit`, and `mean_water_deficit` drifted beyond `5%`; `relocation_recovery_steps` was not measured |
| `v1_baseline_full` median `life_duration_ticks >= 500` and median `mode_diversity >= 2` | FAIL | Duration gate failed; diversity gate passed |

### Operational Criteria

| Criterion from `vision.md` | Status | Evidence |
| --- | --- | --- |
| Long-life homeostasis | FAIL | `continuous_full p75 = 153.25` vs target `> 4000` |
| Early `W=100` energy regulation | PASS, local only | First-window `energy_in_range_ratio` mean `0.9485` |
| Early `W=100` water regulation | PASS, local only | First-window `water_in_range_ratio` mean `0.9843` |
| Early `W=100` deficit variance band | PASS, local only | `deficit_variance` mean `0.0455`, inside target band `0.02-0.15` |
| `anticipatory_response_time` | FAIL | `66` successful vs `163` failed events in `continuous_full`; failed events mean `13.6` ticks |
| `post_shift_recovery_ticks` | NOT MEASURED | No continuous life survived to relocation tick `1000` |
| `lifetime_learning_curve` | FAIL | All `survival_share` block values were `0.0` |
| `mode_transition_coherence` | PASS | Mean / median `1.0` in official continuous runs |
| `mode_diversity` | FAIL | Official median `2.55` vs target `>= 3` |
| `mode_entropy_by_state` | PARTIAL | Non-zero state-conditioned entropy exists, but it does not overcome homeostatic and adaptive failure |

Program-level interpretation:

`RC4` does not satisfy the simultaneous homeostatic, adaptive, and behavioral pass
condition defined in `vision.md`.

## Attribution

### What Worked

- Branches 1-6 and the pre-step install/CLI work form a stable execution pipeline.
- Monitoring, matrix execution, artifact writing, and aggregate summary generation worked
  end-to-end.
- The `continuous_full` vs `continuous_no_regen` contrast is real and reproducible.
- The `v1_baseline_full` identity invariant was confirmed empirically on official data, not
  only in tests.
- The Branch 3 measurement apparatus functioned correctly at the timescales actually
  reached: window, event, and series outputs were produced where their triggering
  conditions occurred.

### What Did Not Work

- Long-life survival did not emerge.
- Slow-memory carryover did not produce upward lifetime blocks; every official
  `survival_share` block remained `0.0`.
- Regeneration extended life modestly but did not overcome energy-side collapse.
- The adaptive relocation path was never exercised in continuous life because survival was
  too short.

### What Was Not Measured And Why

- `post_shift_recovery_ticks` in continuous modes:
  not measured because no life reached tick `1000`, where relocation begins.
- `relocation_recovery_steps` in episodic calibration:
  not measured because the current `ExperimentMatrixRunner` always calls episodic
  `run_protocol(..., eval_relocation_episodes=0)`, and `episodic_full.yaml` also keeps
  `eval_episodes_relocation: 0`. This is a protocol/tooling limitation of the frozen `RC4`
  evaluation path, not a sign that relocation events occurred and the agent failed all of
  them.
- Long-window metrics `W=500` and `W=1000`:
  effectively absent because lives ended before those windows could close.

## Calibration Against Frozen rc3

Frozen reference:
`projects/homeogrid-mvp-rc3/artifacts/official_wave1/core/full/*/reports/metrics.csv`
filtered to `phase = eval_seen`.

| Metric | RC4 official episodic median | Frozen rc3 official median | Relative diff | Gate |
| --- | ---: | ---: | ---: | --- |
| `survival_steps` | `102.0` | `95.0` | `+7.4%` | FAIL |
| `mean_energy_deficit` | `0.3598` | `0.3851` | `6.6%` | FAIL |
| `mean_water_deficit` | `0.1529` | `0.3203` | `52.3%` | FAIL |
| `relocation_recovery_steps` | not measured | `2.0` | n/a | INCOMPLETE |

Calibration conclusion:

- The calibration gate formally failed.
- The drift is attributable in part to corrected `v2` environment semantics, especially the
  removal of the frozen `rc3` single-biome defect.
- This attribution does not convert the gate to a pass. The gate remains failed numerically
  and must be recorded that way.
- A cleaner calibration baseline would require rerunning `rc3` with corrected environment
  semantics, which would violate `rc3` immutability and is therefore rejected.

## Biological Principles Alignment

`RC4` exercised the foundational principles frozen in `vision.md`, but did not achieve the
program-level target.

- Homeostasis as organizing basis: exercised directly, and shown to work only locally over
  early `W=100` windows.
- Multi-timescale plasticity: fast memory and slow-memory carryover were present, but did
  not yield long-life benefit at the observed durations.
- Exploration-exploitation tension: exercised continuously through mixed source use.
- Prediction / expectation violation, stress mode switching, competitive arbitration, and
  morphology remain future-cycle questions and were not reopened in `RC4`.

## Readiness For RC5

`RC5 - Plastic Trust` is the indicated next cycle on this frozen foundation.

Conditions now established by `RC4`:

- The `v2` runtime, monitoring, and artifact pipeline are stable.
- The preserved `v1_baseline` remains a trustworthy immutable comparison anchor.
- The measurement stack is ready to detect divergence once longer-lived behavior appears.
- The unresolved gap is now concrete: regeneration alone does not produce long-life
  behavior under the inherited `rc3` body-cost regime.

Scope recommendation:

- Keep `RC5` focused on plastic trust.
- Do not mix body-cost rebalance into `RC5` unless the project intentionally reopens the
  cycle question and documents a spec change.

## Known Limitations Carried Forward

- `full_observation` pathology from frozen `rc3` remains outside `RC4`.
- `matrix_runner` still accepts one config per invocation; this is an operational
  limitation, not a release blocker.
- Continuous relocation recovery remains blocked by short survival, not by missing
  implementation of the ecology layer.
- Frozen `rc3` calibration remains constrained by the historical single-biome defect.

## Artifact Index

- Vision: `projects/homeoorganism/docs/vision.md`
- Frozen spec: `projects/homeoorganism/docs/rc4_spec.md`
- Pilot review: `projects/homeoorganism/docs/rc4_pilot_review.md`
- Verdict: `projects/homeoorganism/docs/rc4_verdict.md`
- Pilot summary: `projects/homeoorganism/artifacts/aggregate/pilot_summary.csv`
- Official summary: `projects/homeoorganism/artifacts/aggregate/official_summary.csv`
- Per-run artifacts: `projects/homeoorganism/artifacts/runs/<mode>/seed_<N>/`
- Freeze tag: `v2-rc4-pilot-frozen`

Release package assembly is a separate post-verdict step through `projects/release-tooling/`.

## Conclusion

`RC4` is complete.

- Architecture implementation: success
- Long-life ecology hypothesis: fail
- Regeneration effect: real but too weak
- Identity invariant: confirmed empirically at official scale
- Calibration gate: failed / incomplete with documented attribution
- Next cycle: `RC5 - Plastic Trust`

This is a scientifically useful negative result. The frozen `RC4` release line should be
preserved exactly as measured and used as the baseline from which `RC5` divergence begins.
