# RC4 Implementation Progress

Tracking file for RC4 branches. Update after each commit.

## Branches

### Branch 1 - Domain objects
- Commit: 8190769 `rc4: add domain objects LifeState, EcologyConfig, ShiftEvent`
- Status: closed
- Tests: 37 passed

### Branch 2 - Ecology layer
- Commit: 821e78e `rc4: implement ecology regeneration and periodic relocation`
- Status: closed
- Tests: 44 passed
- Notes: `RelocationMode` has 3 variants, `EPISODIC_FIXED` default preserves rc3 behavior.

### Branch 3 - Windowed metrics
- Commit: 60dc9fd `rc4: implement windowed and event-based metrics`
- Status: closed
- Tests: 60 passed
- Notes: Non-sliding window emission. Old `analytics/metrics.py` untouched for rc3 fidelity.

### Branch 4 - Continuous orchestrator
- Commit: a16d244 `rc4: implement continuous life orchestrator`
- Status: closed (with fork follow-up)
- Tests: 70 passed
- Notes: `LifeOrchestrator`, `LifeRuntime`, `LifeArtifactsWriter`, `RunReport` added.

### Branch 4.5 - v2 active agent fork
- Commit: 9b8d218 `rc4: fork v2 active agent stack from v1_baseline reference`
- Status: closed
- Tests: 71 passed
- Notes: Physical copies of `agent/decision/memory/planning` from `v1_baseline/`.
  Regression test `test_v1_baseline_identity.py` verifies bit-for-bit
  identity in `RC4`; expected to start diverging in `RC5`.

### Branch 5 - Configs and CLI wiring
- Commit: 51b8b97 `rc4: add four ablation mode configurations and CLI wiring`
- Status: closed
- Tests: 77 passed
- Notes: Added 4 `RC4` mode configs, cycle-scoped `pilot_rc4.txt` and
  `official_rc4.txt`, and mode-aware matrix dispatch for continuous and
  episodic runs. Smoke `run-matrix` passes with `PYTHONPATH=src`.

### Branch 6 - Monitoring adaptations
- Commit: 2f21e4c `rc4: add continuous-life monitoring adaptations`
- Status: closed
- Tests: 85 passed
- Notes: `LifeSnapshotBuilder` added parallel to the episodic
  `SnapshotBuilder`; continuous modes now publish life-aware monitoring
  frames and `/snapshot` returns `LifeSnapshot` JSON. Existing episodic
  monitoring path and calibration anchors remain unchanged.
