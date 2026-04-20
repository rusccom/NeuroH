# HomeoOrganism

`homeoorganism` is the `v2` project line that follows the frozen `rc3` baseline.

Current phase:

- `vision.md` defines the program-level criteria and release roadmap.
- copied `rc3` baseline modules keep the reference stack runnable during initialization.
- `RC4` design starts only after the vision and `rc4_spec` are frozen.

Reference baseline:

- `projects/homeogrid-mvp-rc3/`
- tag `mvp-rc3`
- closure tag `mvp-rc3-closed`

## Installation

From `projects/homeoorganism/`:

```bash
pip install -e .
```

This registers `homeoorganism` as an editable package and exposes the
`homeoorganism` CLI command.

## Running

After `pip install -e .`:

```bash
homeoorganism run-matrix \
    --config configs/continuous_full.yaml \
    --seeds configs/seeds/pilot_rc4.txt
```

Without install (from `projects/homeoorganism/`):

```bash
PYTHONPATH=src python -m homeoorganism.app.main run-matrix \
    --config configs/continuous_full.yaml \
    --seeds configs/seeds/pilot_rc4.txt
```

Tests (`pytest` auto-configures the `src` path via `pyproject.toml`):

```bash
pytest tests -q
```
