# 001: Physical Fork of v2 Active Agent from v1_baseline

## Context

At `RC4` implementation time, the runtime still imported the full agent
stack from `v1_baseline/`. As a result, `continuous_full` and
`v1_baseline_full` ran the same code, which made the baseline ablation
meaningless once `v2` needed to evolve independently.

## Decision

Create physical copies of `agent/`, `decision/`, `memory/`, and
`planning/` in `src/homeoorganism/` as the active `v2` stack. During
`RC4`, these copies remain bit-for-bit identical to `v1_baseline/`.
Identity is enforced by `test_v1_baseline_identity.py`.

Starting with `RC5`, the active `v2` stack may diverge while
`v1_baseline/` remains immutable.

## Alternatives Considered

- Defer the fork to `RC5`.
  Rejected because it would mix architectural setup and plastic-trust
  work in one cycle.
- Keep a single shared stack forever.
  Rejected because `v1_baseline_full` would stop being a real regression
  condition as soon as active `v2` changes.

## Consequences

- `RC4` temporarily duplicates code between active `v2` packages and
  `v1_baseline/`. This is intentional.
- `RC5` can modify the active stack without touching the preserved
  baseline.
- `v1_baseline_full` becomes a meaningful ablation path for later cycles.

## Release Cycle

RC4
