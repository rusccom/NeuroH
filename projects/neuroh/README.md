# HomeoGrid Runbook

Current target freeze is `mvp-rc3`.

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.lock
pip install -e .
```

## Freeze

```bash
python -m homeogrid.app.main freeze --tag mvp-rc3
```

Freeze payload includes:

- `requirements.lock`
- `configs/full.yaml`
- `configs/ablation.yaml`
- `configs/rc3_calibration.yaml`
- `configs/seeds/official.txt`
- `configs/seeds/pilot.txt`
- `README.md`
- `experiment_protocol.md`

Snapshot output goes to `artifacts/protocols/<tag>/`.

## Reproducibility

```bash
python -m homeogrid.app.main repro-check --config configs/full.yaml --mode full --seed 101 --episodes 1
```

Report path: `artifacts/reproducibility/full/seed_101/report.json`.

## Soak

```bash
python -m homeogrid.app.main soak --config configs/full.yaml --mode full --seed 101 --episodes 200
```

Summary path: `artifacts/soak/full/seed_101/soak_summary.json`.

## Pilot Core

```bash
python -m homeogrid.app.main run-matrix ^
  --config configs/ablation.yaml ^
  --seeds configs/seeds/pilot.txt ^
  --modes full,no_fast,no_slow,no_interoception ^
  --summary-name pilot_core_summary.csv
```

`configs/ablation.yaml` is the core pilot protocol:

- `train = 40`
- `eval_seen = 20`
- `eval_relocation = 0`

## Pilot Relocation

Use `configs/rc3_calibration.yaml` only for the relocation phase:

- `train = 0`
- `eval_seen = 0`
- `eval_relocation = 10`
- `relocation_step = 45`
- `relocation_probability = 1.0`

Run it after the core phase and reuse the trained `slow_memory` for the same `mode/seed`.

## Main Matrix

```bash
python -m homeogrid.app.main run-matrix ^
  --config configs/full.yaml ^
  --seeds configs/seeds/official.txt ^
  --summary-name main_summary.csv
```

To limit modes:

```bash
python -m homeogrid.app.main run-matrix --config configs/full.yaml --seeds configs/seeds/official.txt --modes full,no_fast,no_slow,no_interoception
```

## Manual Operator Check

```bash
python -m homeogrid.app.main run --config configs/full.yaml
```

Manual checks:

- `/monitor`
- `/api/monitor/stream`
- `/replay/<run_id>/<episode_id>`
- `pause`, `resume`, `reset_episode`

## Reference Files

- Protocol: `experiment_protocol.md`
- Main config: `configs/full.yaml`
- Pilot core config: `configs/ablation.yaml`
- Pilot relocation config: `configs/rc3_calibration.yaml`
- Official seeds: `configs/seeds/official.txt`
- Pilot seeds: `configs/seeds/pilot.txt`
