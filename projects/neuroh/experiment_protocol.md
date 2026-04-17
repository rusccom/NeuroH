# Experiment Protocol

## Frozen Build

- Code tag: `mvp-rc3`
- Frozen configs: `configs/full.yaml`, `configs/ablation.yaml`, `configs/rc3_calibration.yaml`
- Frozen dependency lock: `requirements.lock`
- Frozen seed files: `configs/seeds/official.txt`, `configs/seeds/pilot.txt`

## Modes

Pilot:

- `full`
- `no_fast`
- `no_slow`
- `no_interoception`

Main:

- `full`
- `no_fast`
- `no_slow`
- `no_interoception`
- `no_rough_cost`
- `full_observation`

## Seed Sets

Pilot uses `configs/seeds/pilot.txt`.

Main uses `configs/seeds/official.txt`.

Seed replacement by hand is not allowed after the protocol is frozen.

## Episode Budgets

Pilot core uses `configs/ablation.yaml`:

- `train = 40`
- `eval_seen = 20`
- `eval_relocation = 0`

Pilot relocation uses `configs/rc3_calibration.yaml`:

- `train = 0`
- `eval_seen = 0`
- `eval_relocation = 10`

Main uses `configs/full.yaml`:

- `train = 200`
- `eval_seen = 100`
- `eval_relocation = 50`

## Primary Metrics

- `steps_to_first_needed_resource`
- `return_steps_to_seen_resource`
- `survival_steps`
- `relocation_recovery_success_rate`
- `relocation_recovery_steps`
- `mean_energy_deficit`
- `mean_water_deficit`
- `source_fast_share`
- `source_slow_share`
- `source_explore_share`

Auxiliary artifacts per run:

- `memory/slow_memory.npz`
- `reports/metrics.csv`
- `logs/episode_summaries.jsonl`
- `monitoring/<run_id>/<episode_id>.jsonl`

## Success Criteria

- `full` vs `no_slow`: lower `steps_to_first_needed_resource` is better
- `full` vs `no_fast`: lower `return_steps_to_seen_resource` is better
- `full` vs `no_fast`: higher `relocation_recovery_success_rate` is better
- `full` vs `no_fast`: lower `relocation_recovery_steps` is better when recovery happened
- `full` vs `no_interoception`: higher `survival_steps` is better

## Comparison Formulae

For metrics where lower is better:

```text
improvement = (baseline - full) / baseline
```

For metrics where higher is better:

```text
improvement = (full - baseline) / baseline
```

## Aggregation Rules

1. Average metrics over episodes inside one seed.
2. Aggregate seed-level values with `mean`, `median`, `std`, `min`, `max`.
3. Report phase separately: `train`, `eval_seen`, `eval_relocation`.

## Reproducibility Rules

Before pilot and before main:

1. Run `repro-check` on a fixed scenario and seed.
2. Compare:
   - episode metrics
   - decision-source sequence `FAST/SLOW/EXPLORE`
   - alert count
   - `slow_memory.npz`
3. If the report is not fully matched, the protocol is blocked until the issue is explained and fixed.

## Exclusion Rules

- Seeds are not removed manually.
- Broken infrastructure runs are rerun from the start of that `mode/seed` directory.
- No partial cleanup of metrics is allowed.
- No metric definition changes are allowed after pilot freeze.

## Commands

Freeze:

```bash
python -m homeogrid.app.main freeze --tag mvp-rc3
```

Pilot core:

```bash
python -m homeogrid.app.main run-matrix --config configs/ablation.yaml --seeds configs/seeds/pilot.txt --modes full,no_fast,no_slow,no_interoception --summary-name pilot_core_summary.csv
```

Pilot relocation:

```text
Run eval_relocation on configs/rc3_calibration.yaml after the core phase, reusing the trained slow_memory for the same mode/seed artifacts root.
```

Main:

```bash
python -m homeogrid.app.main run-matrix --config configs/full.yaml --seeds configs/seeds/official.txt --summary-name main_summary.csv
```
