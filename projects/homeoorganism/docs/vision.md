# HomeoOrganism Vision

## Mission Statement

We are building a closed-loop adaptive system in a controlled grid environment to study how homeostatic drives, layered memory, planning, and environmental ecology produce behavior that qualifies as "living" under explicit operational criteria. The program goal is not to maximize benchmark score or scale model size. The goal is to establish a falsifiable sequence of architectural cycles in which each added mechanism can be tied to measured behavioral change through frozen protocols, ablations, and reproducible release artifacts.

## What rc3 Proved

`rc3` established that a compact non-neural architecture can sustain an embodied perception-decision-action loop with measurable causal structure. The `full` agent survives substantially longer than `no_fast`, `no_slow`, and `no_interoception`; fast memory is required for relocation recovery, slow memory improves search efficiency, interoception changes survival behavior rather than acting as cosmetic telemetry, and planner rough-cost modeling contributes to recovery under rough terrain. These claims are backed by `official_wave1`, `wave2a`, and `wave2b`, assembled in `release-packages/official_final/`.

`rc3` also set the boundary of what the baseline does not show. It is episodic rather than continuous, runs in a static world apart from controlled relocation events, uses deterministic hand-designed control rather than plastic trust adaptation, and cannot support claims about biome generalization because the frozen baseline operated in a single biome due to the documented `_pick_biome` defect. `wave2a/full_observation` also exposed a pathological pattern that was documented but intentionally not debugged inside frozen `rc3`.

## Operational Definition Of Living Behavior

A system is considered behaviorally living in this program only if it satisfies homeostatic, adaptive, and behavioral criteria at the same time. Passing one category in isolation is insufficient. Each criterion must be measurable from recorded trajectories, attributable to specific architectural components through ablation, and reproducible across independent seeds.

### Homeostatic Criteria

| Metric | Definition | rc3 baseline or proxy | Expected "living" range |
| --- | --- | --- | --- |
| `energy_in_range_ratio` | Fraction of life ticks where `20 <= energy <= 90`. Computed over a complete life or a fixed rolling window. | Not measured directly in `rc3`; proxy evidence is `official_wave1/full mean_energy_deficit ~= 0.381` with `survival_steps ~= 93.9`. | `>= 0.80` in stable ecology windows and `>= 0.65` after environment shifts. |
| `water_in_range_ratio` | Fraction of life ticks where `20 <= water <= 90`. Computed identically to energy. | Not measured directly in `rc3`; proxy evidence is `official_wave1/full mean_water_deficit ~= 0.306` with sustained survival. | `>= 0.80` in stable ecology windows and `>= 0.65` after environment shifts. |
| `deficit_variance` | Mean of the per-window variance of signed normalized deviations from setpoint: `Var((energy - 70) / 70)` and `Var((water - 70) / 70)`. Lower values indicate bounded regulation without collapse or saturation. | Not measured directly in `rc3`; only mean deficits exist. `rc3` therefore provides no variance baseline and this metric begins in `RC4`. | Non-zero but bounded. Target band for a regulated system is `0.02-0.15`; lower may indicate dead-flat control or clipping, higher indicates unstable homeostasis. |
| `anticipatory_response_time` | Mean ticks between first crossing of `low_state_threshold` (`15` in `rc3` body config) and the first directed action sequence toward the currently dominant resource need. A directed sequence starts when the selected target source or motion plan is resource-specific rather than neutral exploration. | Proxy only. `rc3` measured `steps_to_first_needed_resource ~= 10.2-10.4`, but that includes travel and consumption, not decision onset. | `< 4` ticks in familiar conditions and `< 8` ticks after shifts. |

Homeostatic criteria matter because a system that survives only by luck, one-off rescue, or threshold oscillation does not count as living under this program. The target is not perfect regulation. The target is bounded, timely, and state-sensitive regulation over long durations.

### Adaptive Criteria

| Metric | Definition | rc3 baseline or proxy | Expected "living" range |
| --- | --- | --- | --- |
| `post_shift_recovery_ticks` | Ticks from a registered environment shift to recovery of usable behavior. In `RC4`, the default event is relocation or ecology perturbation; recovery is the first reacquisition of the needed resource followed by return of homeostatic ratios above their post-shift floor. | `official_wave1/full relocation_recovery_steps_mean ~= 2.69`; `wave2b/relocation_stress/full ~= 10.25`; `no_fast` collapses to zero recovery success. | Positive and bounded. Standard shifts should recover in `< 12` ticks; stress shifts should recover in `< 20` ticks. |
| `lifetime_learning_curve` | Trend of survival-share and homeostatic success across rolling windows of the same uninterrupted life. The curve may rise during adaptation or flatten after convergence, but must not exhibit systematic late collapse under unchanged conditions. | No direct `rc3` baseline because episodes reset state. `rc3` only proves that slower memory improves average search over episodes. | Non-negative slope after burn-in, or stable plateau with no downward drift beyond tolerance. |
| `trust_bias_dynamics` | Time evolution of trust parameters that govern arbitration between fast memory, slow memory, and other control signals. Measured as convergence, boundedness, and responsiveness of learned bias terms under environmental change. | Not present in `rc3`. This metric activates in `RC5`, not `RC4`. | Biases must remain bounded, history-sensitive, and non-saturated. Permanent collapse to a single source is failure unless justified by the environment. |

Adaptive criteria require measurable response to changed conditions, not merely high score in a fixed world. The system must recover, stabilize, and retain useful structure over time.

### Behavioral Criteria

| Metric | Definition | rc3 baseline or proxy | Expected "living" range |
| --- | --- | --- | --- |
| `mode_entropy_by_state` | State-conditioned entropy of behavioral mode selection. Modes are defined from target source plus execution mode. The metric is evaluated separately for at least `neutral`, `energy-dominant`, `water-dominant`, and `critical` states. A living system should show different distributions across states, not one stationary policy. | Proxy only. `rc3/full` uses mixed sources (`fast ~= 0.40`, `slow ~= 0.38`, `explore ~= 0.21`) and ablations change these shares, but state-conditioned entropy was not recorded. | Entropy should be non-zero within states and measurably different between states. State-contrast must be above noise floor. |
| `mode_transition_coherence` | Fraction of mode transitions that are explained by either internal-need changes or external events. For `RC4`, a transition is coherent if it follows a need switch, resource observation, relocation, collision, or similar event within a small causal window. Random flips without state change reduce the score. | Not measured in `rc3`; `need_switch_count` exists only as a weak proxy. | `>= 0.70` of transitions should be event- or state-anchored. |
| `mode_diversity` | Number of distinguishable behavior modes that appear with meaningful occupancy during a life. A mode counts only if it persists for at least a minimum dwell time and recurs under comparable conditions. | Proxy only. `rc3` proves multiple sources are used, but does not define long-life mode diversity. | At least `3` stable modes for a healthy long-life agent; collapse to `1` persistent mode is failure except in trivial environments. |

Behavioral criteria prevent a degenerate interpretation of life as mere survival. The system must regulate through differentiated, state-dependent, and causally coherent behavior.

### Program-Level Pass Condition

For any `v2` release cycle that claims progress toward living behavior, the release verdict must report all three criterion groups. A cycle may introduce new metrics progressively, but a final positive program claim requires simultaneous satisfaction of homeostatic, adaptive, and behavioral criteria under frozen evaluation conditions.

## What We Explicitly Do Not Do In v2

- No neural networks in the core architecture through `RC10`.
- No map larger than `11x11` until the current size is exhausted and failure analysis shows scale itself is the limiting factor.
- No full morphological computation before `RC7` proto-morphology shows measurable value.
- No multiple architectural questions in one release cycle.
- No merging of pilot and official waves.
- No silent baseline recalculation or post hoc reinterpretation of frozen `rc3`.

These constraints are part of the research design, not temporary convenience rules. They preserve attribution.

## Revised Roadmap RC4 To RC10

### RC4: Long-Life Ecology

Question: can the existing architecture sustain continuous life when given a regenerating environment and windowed metrics? `RC4` replaces episode-first evaluation with uninterrupted life, ecology regeneration, and rolling analysis. The cycle is successful only if continuous-life metrics show bounded homeostasis without losing the explanatory value of current ablations.

### RC5: Plastic Trust

Question: does slow adaptation of fast/slow trust biases improve behavior under environmental variability? `RC5` adds plastic arbitration while preserving interpretability of memory sources. Success requires showing that learned trust dynamics improve adaptive metrics without collapsing into one permanently dominant source.

### RC5.5: Competitive Arbitration

Question: does winner-take-all arbitration between information sources
outperform the hierarchical arbiter, and does it scale better as the
number of sources grows? `RC5.5` introduces competitive arbitration
where `fast_memory`, `slow_memory`, and `explorer` compete through
mutual inhibition rather than explicit priority rules. Each source
outputs an activation level, and dynamics select the winner.

Success requires the competitive arbiter to match or exceed the
hierarchical arbiter on primary metrics, while providing a cleaner
extension path for future sources (`RC9` medium memory, `RC8a` novelty,
`RC8b` stress). Failure results in reverting to the hierarchical
arbiter and documenting the result.

### RC6: Rest And Consolidation

Question: does a fatigue/rest cycle with safe zones produce measurable gains in long-horizon survival? `RC6` introduces structured downtime and consolidation pressure. The cycle succeeds if rest produces long-horizon benefit rather than simply adding idle ticks.

### RC7: Proto-Morphology

Question: does giving the agent a non-point body with orientation and
inertia produce behavioral change that cannot be captured by pure
control architecture? `RC7` replaces point embodiment with a minimal
extended body (two cells, with heading and turning cost in ticks).
Movement is direction-dependent, collisions carry physical cost, and
navigation through narrow corridors depends on orientation.

Success requires measurable divergence from the point-embodiment
baseline in at least one of: navigation efficiency in complex
environments, energy cost distribution, mode diversity, or safe-rest
behavior. Morphology that does not change behavior is a failed
hypothesis about embodiment and results in reverting to point.

### RC8a: Novelty Drive

Question: does explicit novelty reward improve exploration without harming homeostasis? `RC8a` isolates novelty as its own architectural question. Success requires increased useful exploration and mode diversity without raising collapse rates.

### RC8b: Stress And Hazard Response

Question: does explicit stress response improve caution behavior under threat? `RC8b` separates threat handling from novelty. Success requires safer behavior under hazard while preserving recovery and resource acquisition.

### RC9: Medium Memory

Question: does a memory tier between fast and slow improve adaptation to medium-term environmental shifts? `RC9` adds a middle timescale only if `RC5-RC8b` show a remaining gap that existing layers cannot explain. Success requires cleaner attribution than "more memory helps."

### RC10: Full Morphological Computation (Optional)

Question: does offloading parts of behavior from control architecture to
body physics produce measurable gains in robustness, energy
efficiency, or behavioral adaptivity? `RC10` extends `RC7`
proto-morphology with computations executed by body shape:
stance-dependent energy cost, geometry-dependent sensor coverage,
morphology-dependent rest efficacy.

`RC10` is optional. It starts only if `RC7` demonstrates that
proto-morphology already produces value without additional mechanisms.
If `RC7` shows morphology has no measurable effect, `RC10` is
cancelled.

## Gate Criteria Per RC

### RC4 Detailed Gate Criteria

| Stage | Requirement |
| --- | --- |
| Entry | `projects/homeoorganism/docs/vision.md` committed and treated as frozen until explicit revision. |
| Entry | `projects/homeoorganism/` initialized with copied baseline structure, immutable `v1_baseline`, and corrected `_pick_biome` in `env/`. |
| Entry | `docs/rc4_spec.md` written before implementation, including `LifeState`, `EcologyConfig`, `WindowedMetrics`, continuous replay, and ablation modes. |
| Entry | Smoke life run exists and can execute a short uninterrupted life without runtime failure. |
| Pilot exit | Pilot wave covers `continuous_full`, `continuous_no_regen`, `episodic_full`, and `v1_baseline_full` on frozen pilot protocol. |
| Pilot exit | Pilot review has no blocker and documents any limitations before freeze. |
| Official exit | Official wave is run on frozen code with no code changes after freeze tag. |
| Official exit | Release package reports all RC4 metrics, includes a verdict, and states whether continuous life satisfied the operational criteria introduced here. |
| Official exit | Results are attributable through ablations rather than isolated cherry-picked trajectories. |

### RC5-RC10 Summary Gates

| RC | Entry gate | Exit gate |
| --- | --- | --- |
| `RC5` | `RC4` verdict complete and remaining adaptation gap identified. | Plastic trust improves adaptive criteria under variability and remains interpretable. |
| `RC5.5` | `RC5` verdict complete and arbitration scaling problem explicitly framed. | Competitive arbitration matches or exceeds the hierarchical arbiter and scales cleanly to added sources. |
| `RC6` | `RC5.5` verdict complete and fatigue/rest justified by measured failure mode. | Rest/consolidation improves long-horizon survival or memory retention without trivializing control. |
| `RC7` | `RC6` verdict complete and embodiment question isolated with a point-body baseline. | Proto-morphology changes behavior measurably rather than acting as cosmetic physics. |
| `RC8a` | `RC7` verdict complete and exploration deficit documented. | Novelty drive improves exploration-related criteria without homeostatic collapse. |
| `RC8b` | `RC8a` verdict complete and hazard-response question isolated. | Stress response improves hazard behavior with measurable causal contribution. |
| `RC9` | `RC8b` verdict complete and an unresolved medium-timescale adaptation gap remains. | Medium memory adds distinct value not explained by fast or slow layers alone. |
| `RC10` | `RC9` verdict complete and `RC7` shows proto-morphology has measurable value with a remaining body-physics question. | Full morphological computation improves robustness, energy efficiency, or adaptivity beyond `RC7`. |

## Relation To v1 (rc3)

### Reused As-Is

- `env/`, with `_pick_biome` corrected as the first `v2` environment fix.
- Domain value objects and enums.
- Monitoring infrastructure and web monitor.
- Config loader and configuration dataclasses.
- Freeze and release discipline, including external release assembly.

### Forked As Independent Evolution Path

`agent/`, `decision/`, `memory/`, and `planning/` are physical copies of
`v1_baseline/` created inside `v2` so the active architecture can evolve
without mutating the preserved reference. In `RC4` these modules remain
bit-for-bit identical to `v1_baseline/` because the spec explicitly says
the agent architecture is unchanged in this cycle.

Starting in `RC5`, these active modules are allowed to diverge while
`v1_baseline/` remains immutable. This split makes `v1_baseline_full` a
real regression ablation rather than a second name for the same code.
A regression test, `test_v1_baseline_identity.py`, asserts identity in
`RC4`. Later cycles will update that expectation to require divergence.

### Transitional Bootstrap Layers

`analytics/metrics.py` and
`orchestration/experiment_orchestrator.py` remain imported from `rc3`
as calibration anchors for `episodic_full`. In `RC4` they are
intentionally not modified. Their role is to preserve a stable
comparison path while the continuous-life stack is added beside them.

### Added Alongside The Calibration Anchors

- `orchestration/life_orchestrator.py`, `life_artifacts.py`, and
  related runtime/report layers for uninterrupted life execution.
- `analytics/windowed_metrics.py`, `event_metrics.py`, and related
  rolling-series utilities for long-life measurement.
- Active-stack import wiring that can run either the forked `v2` agent
  or the immutable `v1_baseline` stack as named ablations.

### Preserved As Immutable Reference

`v1_baseline/` is an exact snapshot of the `rc3` agent, decision, memory, and planning stack preserved for direct comparison against each `v2` cycle. It is not a sandbox for convenient fixes. If comparison behavior must change, the change must live outside `v1_baseline/` and be named as a new experimental condition. In `v2`, `v1_baseline_full` runs the preserved `rc3` agent on the corrected `v2` environment. This intentionally differs from official `rc3` measurements, which were taken under the documented single-biome defect.

## Open Investigation Items From rc3

### `_pick_biome` Single-Biome Defect

Status at `v2` start: open but straightforward. The defect is caused by `np.random.choice(list(BiomeId))` collapsing `str`-Enum members. It is resolved as the first code commit of `v2` by switching to integer-index sampling and adding a regression test that all four biomes are reachable across seeds. Once that test exists and passes, the `v2` environment-side investigation is considered closed.

### `full_observation` Pathological Pattern

Status at `v2` start: open and not yet explained. Before `full_observation` is reused as a `v2` ablation mode, `RC4` must determine whether the `rc3` pathology came from metric triggering, exploration-visibility interaction, or stale belief-map state after relocation. If the root cause is metric-related, the fix belongs in `v2` metrics and the verdict must say so. If the root cause is architectural, the behavior must be documented as an expected limitation rather than quietly normalized.

## Biological Principles Guiding Architectural Choices

The program does not replicate biology. It adopts principles that
biology has empirically validated as necessary for living behavior,
while choosing engineering implementations appropriate to a
computational substrate. The long-term horizon of the program is to
approach behavioral sophistication of simple organisms (`C. elegans`,
`Drosophila`) while maintaining component-level attribution and
interpretability that full brain emulation cannot provide.

### Principles Adopted In HomeoOrganism v2

- **Homeostasis as the organizing basis for behavior.** Not an added
  feature, but structural. Implemented in `drive_model`, integral to
  every decision. Spans all cycles.
- **Multi-timescale plasticity.** Fast memory within a life, slow
  memory across lives, planned medium tier. Plastic trust biases added
  in `RC5`.
- **Prediction and expectation violation as drivers of adaptation.**
  Partially implemented as `EXPECTATION_VIOLATED` events. Full
  predictive coding deferred to later cycles.
- **Exploration-exploitation tension as a core behavioral dimension.**
  Arbiter implements it implicitly; `RC8a` novelty drive makes it
  structural.
- **Stress as a global mode switch.** Planned for `RC8b`.
- **Winner-take-all arbitration instead of hierarchical selection.**
  Biology has no central arbiter; competing parallel systems produce
  selection through mutual inhibition. Hierarchical arbiter in `rc3`
  is an engineering simplification. `RC5.5` introduces competitive
  arbitration as an alternative, with ablation comparison against
  hierarchical.
- **Morphological computation.** The body is not inert; geometry and
  physics participate in behavior. Point embodiment in `RC4` is a
  simplification. `RC7` introduces proto-morphology (extended body,
  orientation, inertia). Full morphological computation is considered
  in `RC10` and in a later transition to continuous environments.

### Principles Deferred To Continuous Environments (Project 2+)

- **Asynchrony.** Biology has no tick. Grid-world tick-based execution
  is an appropriate simplification. Continuous 2D will introduce
  multiple timescales (reflex loop, action loop, planning loop).
- **Massive parallelism.** Biology has billions of parallel elements.
  Computational substrate is different. Module independence is
  preserved architecturally, so parallel execution is possible when
  needed; actual parallel execution arrives with real robotics
  hardware.

### What This Program Is Not

- Not a simulation of any particular biological organism.
- Not an attempt at whole brain emulation.
- Not a neural network research program.
- Not a claim about consciousness, sentience, or the philosophical
  nature of life.

The claim is narrower: a minimal embodied system can be built whose
behavior satisfies operational criteria of living behavior, whose
components are individually attributable through ablation, and whose
architecture is compatible with scaling toward biological complexity
along principles biology has already validated.

## Success Criteria For The Whole v2 Program

`v2` is successful if by the end of `RC9` the system demonstrates all
three groups of operational criteria simultaneously, with clear
attribution of each criterion to specific architectural components
through ablation, and with reproducible performance across independent
seeds and environmental conditions. `RC10`, if opened, is an optional
extension for morphology-led gains rather than a prerequisite for the
core `v2` claim. A successful `v2` program therefore ends with a
system that is not only harder to break, but also easier to explain.
