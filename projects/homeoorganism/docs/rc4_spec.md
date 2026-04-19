# RC4 Spec: Long-Life Ecology

`RC4` is the first `v2` implementation cycle. This document freezes the implementation boundary for continuous life, ecology regeneration, windowed metrics, and the four evaluation modes used in pilot and official waves. It extends `docs/vision.md`; it does not replace it.

## 1. Architectural Question

Can the `rc3` agent architecture, placed in a continuously regenerating environment and measured through windowed rather than episode-anchored metrics, sustain behavior that satisfies the homeostatic, adaptive, and behavioral criteria defined in `vision.md` over horizons longer than any single `rc3` episode?

## 2. What Changes And What Does Not

| Component | RC4 status | Notes |
| --- | --- | --- |
| Decision stack: arbiter, explorer, planner, controller | Unchanged from `rc3` | The inner decision logic remains attributable to the preserved baseline stack. |
| Fast and slow memory internals | Unchanged from `rc3` | `RC4` changes lifecycle semantics, not memory algorithms. |
| Drive model and observation encoder | Unchanged from `rc3` | Homeostatic sensing stays comparable to the baseline. |
| Belief map structure | Unchanged from `rc3` | It resets at life boundaries in continuous modes. |
| `v1_baseline/` | Immutable reference | No edits. `v1_baseline_full` wraps it in `RC4` runtime semantics. |
| Environment core | Extended | Adds ecology regeneration and periodic relocation in continuous modes. |
| Orchestrator | Rewritten | Moves from episode-first control to life-series control. |
| Metrics collector | Rewritten | Adds rolling windows, event metrics, and series metrics. |
| Monitoring | Extended | Shows life boundaries, rolling charts, and ecology state. |
| App entry points and configs | Adapted | Must expose continuous modes without mutating `v1_baseline/`. |

`RC4` does not change the agent's architectural question. It changes the environment and evaluation regime around the preserved decision stack.

## 3. New Domain Objects

```python
@dataclass(frozen=True)
class LifeState:
    life_id: int
    tick: int
    started_at_ts_ms: int
    ended_at_ts_ms: int | None
    end_reason: str | None
```

`LifeState` is the life-centric replacement for episode-only progress tracking. It is the canonical unit for continuous runs and for per-life artifact rows.

```python
@dataclass(frozen=True)
class EcologyConfig:
    food_regen_mean_ticks: int
    water_regen_mean_ticks: int
    food_target_count: int
    water_target_count: int
    regen_jitter: float
    resource_ttl_ticks: int | None
    relocation_period_ticks: int
    relocation_probability: float
```

`EcologyConfig` defines the regeneration and perturbation schedule for continuous modes. `resource_ttl_ticks` is present for future extension, but `RC4` sets it to `None`.

```python
@dataclass(frozen=True)
class ShiftEvent:
    life_id: int
    tick: int
    event_type: str
    success: bool
```

`ShiftEvent` records externally induced perturbations such as relocation. It is the anchor object for `post_shift_recovery_ticks`.

## 4. Ecology Layer

- Resource consumption semantics from `rc3` remain unchanged: consuming food or water removes that node from the grid.
- `RC4` adds replenishment instead of per-episode respawn. The ecology layer restores food and water counts toward fixed targets during a life.
- Default `EcologyConfig` values for `continuous_full` and `v1_baseline_full` are:
  - `food_target_count = 2`
  - `water_target_count = 2`
  - `food_regen_mean_ticks = 35`
  - `water_regen_mean_ticks = 35`
  - `regen_jitter = 0.25`
  - `resource_ttl_ticks = None`
  - `relocation_period_ticks = 1000`
  - `relocation_probability = 0.5`
- Regeneration is one-node-at-a-time and per resource type. If current count is below target and the sampled regeneration deadline is reached, one node of that type is placed and a new deadline is sampled.
- Placement uses the existing `rc3` "near biome center" rule: candidate cells are the center plus the four cardinal neighbors around the biome's food or water center.
- Blocked cells are the landmark, the agent start cell, and any non-empty cell. If no candidate cell is free, regeneration is skipped, the skip is recorded, and the next regeneration deadline is sampled normally.
- `RC4` keeps biome identity, rough patches, and landmark placement unchanged during a life. Ecology changes only resource nodes.
- Locked decision C: continuous modes use periodic relocation. At every `1000`th tick after tick `0`, the environment performs one Bernoulli relocation check with probability `0.5`. On success, exactly one extant resource node is moved using the existing relocation placement rule.
- Regeneration and relocation never happen on the same tick. If relocation fires, regeneration is skipped for that tick to keep shift attribution clean.
- `continuous_no_regen` disables regeneration but keeps the same relocation schedule. This isolates the effect of replenishment rather than changing two variables at once.
- `episodic_full` does not use the continuous ecology layer. It retains the current episodic world generation and fixed-step relocation semantics for comparability to `rc3`.

## 5. Continuous Orchestrator

- One `RC4` run is one mode under one seed. Continuous modes execute a series of lives inside that run.
- Locked decision A: slow memory carryover is `on` inside each continuous run for modes that include slow memory. Slow memory starts empty at run start, persists across life boundaries, and is saved once at run end.
- Rationale for decision A: `RC4` asks whether the architecture can sustain continuous life with accumulated structure. Resetting slow memory every life would collapse the run into episodic evaluation with longer bookkeeping.
- Fast memory, belief map, working buffer, life-local metrics, body state, and world state reset at every life boundary.
- `v1_baseline_full` uses the preserved `v1_baseline` stack inside the same life-series wrapper and follows the same carryover policy where slow memory exists.
- Locked decision B: one life ends on depletion or on `life_max_ticks = 5000`, whichever comes first.
- Rationale for decision B: `5000` ticks is `12.5x` the current `episode_limit = 400`, large enough for long-horizon regulation while keeping compute bounded and life-level metrics comparable.
- `end_reason` values in `RC4` are `energy_depleted`, `water_depleted`, `max_ticks_reached`, or `operator_reset`.
- Life start resets the environment, body, and per-life state; run start resets run-level accumulators and clears slow memory; run end writes summary and memory artifacts.
- A continuous run writes four logical datasets: `life_summaries`, `window_metrics`, `event_metrics`, and `series_metrics`. The exact file format is implementation-level.
- `episodic_full` remains episode-centric: `episode_limit = 400`, relocation check at `step_idx = 150`, `relocation_probability = 0.25`, and episodic reset semantics preserved for direct comparison to `rc3`.
- Pilot protocol size is `5` lives per seed for continuous modes. Official protocol size is `20` lives per seed for continuous modes.

## 6. Windowed Metrics

Standard rolling windows are `W = 100`, `500`, and `1000` ticks. Windowed metrics are emitted only after the first full window closes.

Behavior state categories are:

- `critical`: `energy < 15` or `water < 15`
- `energy_dominant`: not critical and `((70 - energy) / 70) - ((70 - water) / 70) >= 0.10`
- `water_dominant`: not critical and `((70 - water) / 70) - ((70 - energy) / 70) >= 0.10`
- `neutral`: all other ticks

Behavior mode is the pair `(guidance_source, execution_mode)` taken from the selected proposal at each tick.

| Metric | Formula and units | Frequency | Output |
| --- | --- | --- | --- |
| `life_duration_ticks` | `final_tick` of the life. Units: ticks. | life end | `life_summaries` |
| `energy_in_range_ratio` | `mean(1[20 <= energy_t <= 90])` over each window `W`. Unit: ratio. | every completed window | `window_metrics` |
| `water_in_range_ratio` | `mean(1[20 <= water_t <= 90])` over each window `W`. Unit: ratio. | every completed window | `window_metrics` |
| `deficit_variance` | `0.5 * Var((energy_t - 70) / 70) + 0.5 * Var((water_t - 70) / 70)` over each window `W`. Unit: normalized variance. | every completed window | `window_metrics` |
| `anticipatory_response_time` | For each low-need event `k`, `t_directed_k - t_low_k`, where `t_low_k` is first tick crossing `< 15` for the dominant channel and `t_directed_k` is first tick of two consecutive ticks targeting that resource. Unit: ticks. Report mean and count. | event-triggered | `event_metrics` |
| `post_shift_recovery_ticks` | For each relocation event `k`, `t_recovered_k - t_shift_k`, where recovery is first post-shift needed-resource consumption followed by `energy_in_range_ratio(100) >= 0.65` and `water_in_range_ratio(100) >= 0.65`. Unit: ticks. Report mean and success rate. | event-triggered | `event_metrics` |
| `lifetime_learning_curve` | For block `b` of `5` consecutive lives, `survival_share_b = mean(1[life_duration_ticks >= 4000])`. The ordered block series is the learning curve. Unit: ratio by block. | each completed life block | `series_metrics` |
| `mode_entropy_by_state` | For each state `s`, `H_s = -sum_m p_s(m) * log2(p_s(m))`. Unit: bits. | life end | `life_summaries` |
| `mode_transition_coherence` | `coherent_mode_transitions / total_mode_transitions`, where a transition is coherent if preceded within `3` ticks by need switch, resource observation, resource consumption, relocation, or collision. Unit: ratio. | life end | `life_summaries` |
| `mode_diversity` | Count of modes with occupancy `>= 0.02` of life ticks and minimum dwell length `>= 5` ticks. Unit: count. | life end | `life_summaries` |

`episodic_full` must continue to emit the shared `rc3` comparison metrics (`survival_steps`, `mean_energy_deficit`, `mean_water_deficit`, `relocation_recovery_steps`) so that the `<= 5%` calibration gate remains testable.

## 7. Ablation Modes

| Mode | Agent | World semantics | Purpose |
| --- | --- | --- | --- |
| `continuous_full` | `v2` active architecture | Continuous life, regeneration on, periodic relocation on, slow-memory carryover on | Primary `RC4` condition |
| `continuous_no_regen` | Same as `continuous_full` | Continuous life, regeneration off, periodic relocation on, slow-memory carryover on | Sanity check that replenishment matters |
| `episodic_full` | `v2` active architecture | Episodic `rc3`-style runs on corrected `v2` environment | Direct calibration against frozen `rc3` metrics |
| `v1_baseline_full` | Preserved `v1_baseline/` stack | Continuous life, regeneration on, periodic relocation on, slow-memory carryover on | Stress test the `rc3` agent in the `RC4` world |

These are the only four `RC4` evaluation modes. `RC4` does not add `no_fast`, `no_slow`, `full_observation`, or other ablations to the official protocol.

## 8. Monitoring Adaptations

- The timeline becomes a continuous tick-range view across a life series instead of an episode-only view.
- Life boundaries are explicit timeline events: `life_start`, `life_end`, and `life_end_reason`.
- Monitoring must expose rolling plots for `energy_in_range_ratio`, `water_in_range_ratio`, and `deficit_variance`.
- Monitoring must expose ecology state: current food count, current water count, relocation events, and regeneration events.
- The world view, belief-map view, and planner view remain conceptually the same; only the time axis and overlays become life-centric.
- Snapshot cadence and downsampling policy are implementation-level decisions.

## 9. Gate Criteria

| Stage | Requirement |
| --- | --- |
| Entry | `projects/homeoorganism/docs/rc4_spec.md` is committed on `main`. |
| Entry | Smoke run: `continuous_full` completes `1` life of `500` ticks without runtime crash. |
| Pilot entry | Pilot uses `configs/seeds/pilot.txt` (`5` seeds: `101, 202, 303, 404, 505`). |
| Pilot entry | Continuous modes run `5` lives per pilot seed. `episodic_full` runs `5` episodes per pilot seed. |
| Pilot exit | Zero runtime crashes across all pilot runs. |
| Pilot exit | Median `life_duration_ticks(continuous_no_regen) <= 0.80 * median(life_duration_ticks(continuous_full))`. |
| Pilot exit | `episodic_full` stays within `5%` of frozen `rc3` calibration on `survival_steps`, `mean_energy_deficit`, `mean_water_deficit`, and `relocation_recovery_steps`. |
| Pilot exit | `v1_baseline_full` shows non-trivial behavior: median `life_duration_ticks >= 500` and median `mode_diversity >= 2`. |
| Official entry | Freeze tag created from `main`; no code changes after the freeze tag until the official wave finishes. |
| Official entry | Official uses `configs/seeds/official.txt` (`10` seeds). |
| Official exit | Continuous modes run `20` lives per official seed. `episodic_full` runs `20` episodes per official seed. |
| Official exit | Release package with prefix `v2_rc4` is assembled through `projects/release-tooling/`. |
| Official exit | Verdict states pass, fail, or inconclusive separately for the homeostatic, adaptive, and behavioral criteria groups. |

## 10. Non-Goals

- No plastic trust adaptation or any learned arbitration parameters. That begins in `RC5`.
- No fatigue, rest, or consolidation mechanics. Those belong to `RC6`.
- No novelty bonus or novelty-driven exploration terms. Those belong to `RC7a`.
- No stress-response or hazard-response architecture. Those belong to `RC7b`.
- No new medium-timescale memory tier. That belongs to `RC8`.
- No morphology work or non-point embodiment. That belongs to `RC9`.
- No reopening or silent normalization of the `full_observation` pathology. It remains a separate investigation.
- No edits to `v1_baseline/`.

## 11. Open Implementation Questions

- Which physical file formats back the logical datasets `life_summaries`, `window_metrics`, `event_metrics`, and `series_metrics` (`JSONL`, `CSV`, `Parquet`, or mixed)?
- What snapshot cadence should monitoring use for long runs: every tick, every `N` ticks, or adaptive downsampling?
- Should continuous-life CLI entry points reuse the current `run` and `run-matrix` commands or add explicit life-series commands?
- Should rolling metrics be implemented with ring buffers or by bounded recomputation, as long as the semantics above stay unchanged?

Any change to sections 4 through 10 after commit is a spec change and must land as an explicit follow-up commit before implementation changes rely on it.
