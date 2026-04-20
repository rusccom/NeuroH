# RC4 Smoke Notes

Date: 21 Apr 2026
Base commit: `3a35e02`

## Scope

Smoke was executed as a validation pre-step for `RC4` on the installed CLI entry point
`homeoorganism`.

- Seed set: `101` only
- Lives / episodes per mode: `1`
- Continuous smoke cap: `500` ticks
- Monitoring smoke cap: `2000` ticks

Temporary smoke-only config copies were used outside the repo so the frozen RC4 configs in
`configs/` stayed unchanged.

Smoke is an infrastructure check, not a behavioral measurement run. The purpose here is to
verify end-to-end execution, artifact production, and monitoring availability before the
pilot wave.

## Results

All four RC4 modes executed without CLI/runtime errors.

| Mode | Wall time | Observation |
|---|---:|---|
| `continuous_full` | 1.75s | Life ended at tick `145`; `life_summaries.jsonl`, `window_metrics.jsonl`, and aggregate CSV were produced |
| `continuous_no_regen` | 1.76s | Life ended at tick `99`; aggregate CSV was produced, but `window_metrics.jsonl` stayed empty because no 100-step window closed before depletion |
| `episodic_full` | 1.60s | Episode completed and `reports/metrics.csv` plus aggregate CSV were produced |
| `v1_baseline_full` | 1.69s | Life ended at tick `145`; produced the same smoke summary shape as `continuous_full` |

## Artifact Check

- `artifacts/aggregate/smoke_continuous_full.csv` exists and is non-empty
- `artifacts/aggregate/smoke_continuous_no_regen.csv` exists and is non-empty
- `artifacts/aggregate/smoke_episodic_full.csv` exists and is non-empty
- `artifacts/aggregate/smoke_v1_baseline_full.csv` exists and is non-empty
- `artifacts/runs/continuous_full/seed_101/life_summaries.jsonl` exists and is non-empty
- `artifacts/runs/continuous_full/seed_101/window_metrics.jsonl` exists and contains one closed-window record at tick `100`
- `artifacts/runs/continuous_no_regen/seed_101/life_summaries.jsonl` exists and is non-empty
- `artifacts/runs/continuous_no_regen/seed_101/window_metrics.jsonl` exists but is empty for this smoke because the life ended at tick `99`
- `artifacts/runs/episodic_full/seed_101/reports/metrics.csv` exists and is non-empty
- `artifacts/runs/v1_baseline_full/seed_101/life_summaries.jsonl` exists and is non-empty
- `artifacts/runs/v1_baseline_full/seed_101/window_metrics.jsonl` exists and contains one closed-window record at tick `100`

## Monitoring Smoke

Monitoring was verified with a short `continuous_full` run using `enable_monitoring: true`
on `127.0.0.1:8010`.

- `GET /snapshot` returned `200`
- Response payload contained a `LifeSnapshot`
- Verified fields included `life_id`, `current_tick`, `completed_lives`,
  `current_energy_ratio_100`, `current_deficit_variance`, and `next_relocation_tick`

## Known Issues For Pilot

- `continuous_no_regen` can terminate before the first 100-tick window closes. For short
  smoke runs this means `window_metrics.jsonl` may be empty by design, not because the
  writer failed. In this smoke, the life ended at tick `99`, so the first non-sliding
  window close at tick `100` never occurred.
- The episodic metrics artifact lives at `reports/metrics.csv`, not at the run root.

## Pre-Pilot Expectation

The smoke supports the intended attribution for the continuous ablation pair.

- `continuous_full` should sustain materially longer lives than `continuous_no_regen`
  during pilot if ecology regeneration is functioning correctly.
- `continuous_no_regen` is expected to stay short-lived because starting resources can be
  exhausted without replacement.
- If pilot shows the two modes behaving similarly, that would require investigation before
  the official wave.

## Ready For Pilot

YES

The smoke objective is satisfied: all four modes run end-to-end, aggregate outputs are
written, life-mode artifacts are present, episodic metrics are present, and monitoring
serves live `LifeSnapshot` data over HTTP.
