# HomeoGrid Runbook

Текущий стенд зафиксирован как `mvp-rc1`. Дальше проект используется не для расширения логики, а для воспроизводимых pilot/main-экспериментов на фиксированной версии.

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.lock
pip install -e .
```

## Freeze

```bash
python -m homeogrid.app.main freeze --tag mvp-rc1
```

Что фиксируется:

- `requirements.lock`
- `configs/full.yaml`
- `configs/ablation.yaml`
- `configs/seeds/official.txt`
- `configs/seeds/pilot.txt`
- `README.md`
- `experiment_protocol.md`

Снимок складывается в `artifacts/protocols/<tag>/`.

## Reproducibility

Один и тот же сценарий дважды на одном seed:

```bash
python -m homeogrid.app.main repro-check --config configs/full.yaml --mode full --seed 101 --episodes 1
```

Отчёт пишется в `artifacts/reproducibility/full/seed_101/report.json`.

## Soak

Серия эпизодов без расширения системы, с replay/monitoring-артефактами:

```bash
python -m homeogrid.app.main soak --config configs/full.yaml --mode full --seed 101 --episodes 200
```

Сводка пишется в `artifacts/soak/full/seed_101/soak_summary.json`.

## Pilot Matrix

```bash
python -m homeogrid.app.main run-matrix ^
  --config configs/ablation.yaml ^
  --seeds configs/seeds/pilot.txt ^
  --modes full,no_fast,no_slow,no_interoception ^
  --summary-name pilot_summary.csv
```

Структура артефактов:

```text
artifacts/
  runs/
    full/
      seed_101/
    no_fast/
      seed_101/
  aggregate/
    pilot_summary.csv
```

## Main Matrix

```bash
python -m homeogrid.app.main run-matrix ^
  --config configs/full.yaml ^
  --seeds configs/seeds/official.txt ^
  --summary-name main_summary.csv
```

Если нужно ограничить режимы:

```bash
python -m homeogrid.app.main run-matrix --config configs/full.yaml --seeds configs/seeds/official.txt --modes full,no_fast,no_slow,no_interoception
```

## Manual Operator Check

Полный стенд с UI:

```bash
python -m homeogrid.app.main run --config configs/full.yaml
```

Проверить вручную:

- `/monitor`
- `/api/monitor/stream`
- `/replay/<run_id>/<episode_id>`
- `pause`, `resume`, `reset_episode`
- реакцию 3D-индикатора на `energy`, `water` и нестабильность

## Reference Files

- Protocol: `experiment_protocol.md`
- Main config: `configs/full.yaml`
- Pilot config: `configs/ablation.yaml`
- Official seeds: `configs/seeds/official.txt`
- Pilot seeds: `configs/seeds/pilot.txt`
