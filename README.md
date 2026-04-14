# HomeoGrid Experimental Platform

Исследовательская MVP-платформа для проверки связки:
замкнутая grid-world среда, embodied-дефициты, fast-memory,
slow-memory, replay/consolidation и live-мониторинг оператора.

## Установка

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.lock
pip install -e .
```

## Запуск

```bash
python -m homeogrid.app.main run --config configs/full.yaml
python -m homeogrid.app.main ablate --config configs/ablation.yaml
python -m homeogrid.app.main replay --file artifacts/monitoring/<run>/<episode>.jsonl
```

## Основные URL

- `http://127.0.0.1:8000/monitor`
- `http://127.0.0.1:8000/replay/<run_id>/<episode_id>`
- `http://127.0.0.1:8000/api/monitor/bootstrap`
- `http://127.0.0.1:8000/api/monitor/stream`

## Артефакты

- `artifacts/memory/slow_memory.npz`
- `artifacts/reports/metrics.csv`
- `artifacts/reports/ablation_results.csv`
- `artifacts/logs/episode_summaries.jsonl`
- `artifacts/monitoring/<run_id>/<episode_id>.jsonl`
