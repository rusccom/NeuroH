# AGENTS.md

## Mission

This repository is a research monorepo.

The project goal is not "ship an app fast". The goal is to build and evaluate a closed-loop adaptive system in a controlled environment, preserve baselines honestly, and produce reproducible release artifacts for scientific comparison.

Treat the codebase as:

- a research stand
- a release discipline system
- a sequence of frozen baselines plus new architectural cycles

## What We Are Building

We are studying adaptive behavior in a grid-world with physiology, memory, planning, monitoring, and ablation-based evaluation.

The practical workflow is:

1. define one architectural question
2. freeze the protocol
3. run pilot and official waves
4. assemble a release package
5. tag the result
6. start the next cycle without mutating the frozen baseline

## Monorepo Layout

- `projects/neuroh/` - active development line of the current live project
- `projects/homeogrid-mvp-rc3/` - frozen baseline snapshot from `mvp-rc3`
- `projects/release-tooling/` - external read-only release assembler
- `projects/homeoorganism/` - active v2 project; vision frozen, RC4 in planning
- `release-packages/` - ignored output folder for generated release bundles

If a new chat starts, inspect this file first, then inspect:

1. `README.md`
2. the relevant project folder under `projects/`
3. the current git branch and status

## Folder Policy

Create a new folder under `projects/` only when one of these is true:

- a new independent project starts
- a frozen baseline snapshot must be preserved
- a major architectural rewrite starts as a separate codebase
- a standalone internal tool needs its own lifecycle

Do not create a new folder for a minor release of an existing project.
Minor releases use tags, not duplicated project folders.

## Branch Policy

- The standard active branch is `main`
- No long-lived per-project branches as the default workflow
- Short-lived feature branches are allowed when needed
- Releases are represented by tags, not by branch-per-folder
- `main-legacy-mvp-rc1` is preserved as archive history
- `release/mvp-rc3` is a frozen reference line, not a place for new work

When pushing the current monorepo state:

```powershell
git push origin main
```

Push other branches only if they were intentionally created.

## Research and Release Discipline

This repo follows strict freeze discipline.

- One RC answers one architectural question
- No code changes between freeze and official wave
- No quick fixes inside frozen release lines
- No hidden recalculation of historical baselines
- Known limitations must be documented explicitly, not silently patched into old releases

Standard cycle:

1. spec
2. freeze
3. pilot
4. official
5. release package
6. tag
7. next cycle

## Frozen Baseline Rule

`projects/homeogrid-mvp-rc3/` is a frozen baseline snapshot.

Rules:

- do not edit it casually
- do not "improve" its experiment code in place
- do not rewrite its historical meaning
- if you need new reporting logic, use `projects/release-tooling/`
- if you find a real limitation, document it in release output

Known baseline fact:

- wave 1 in rc3 is single-biome (`BiomeId.B`) due to `_pick_biome`
- this is a documented limitation, not a reason to mutate rc3 after the fact

## Known Open Investigation Items

These are not forgotten problems. These are explicitly deferred investigation items.

Keep this list short, concrete, and tied to evidence. Add an item here when:

- the issue is real or strongly evidenced
- it was intentionally not fixed in the frozen baseline
- it must be revisited in a future architectural cycle

For each item, record:

- what is wrong or unknown
- what artifact proves it
- why it was deferred
- in which future cycle it must be reopened

Current items:

- `_pick_biome` / biome distribution defect
  Evidence: `projects/homeogrid-mvp-rc3/artifacts/official_wave1/**/logs/episode_summaries.jsonl` and release `biome_audit.json` show wave 1 runs only in `BiomeId.B`
  Consequence: rc3 results are valid as within-biome comparisons only; biome generalization is not demonstrated
  Status: explicitly deferred, do not patch inside frozen rc3
  Reopen in: v2 baseline investigation, starting from `projects/homeoorganism/`

## Artifact Policy

Generated outputs should not pollute the repo.

Ignored:

- `release-packages/`
- `projects/neuroh/artifacts/`
- heavyweight monitoring streams
- replay snapshots
- soak outputs
- caches and local virtualenvs

Tracked for frozen baseline truth source:

- `projects/homeogrid-mvp-rc3/artifacts/official_wave1/**/logs/episode_summaries.jsonl`
- `projects/homeogrid-mvp-rc3/artifacts/official_wave1/**/run_manifest.json`
- `projects/homeogrid-mvp-rc3/artifacts/aggregate/official_review.json`
- protocol files required to understand how official wave 1 was produced

Principle:

- per-episode summaries and manifests are truth source
- heavy replay and monitoring data are local debugging material

## Release Packaging

Release assembly must happen outside frozen baseline logic.

Use:

- `projects/release-tooling/assemble_release.py`

Read-only inputs:

- frozen or generated artifact roots

Write outputs only to:

- `release-packages/<package_name>/`

Expected outputs:

- `release_table.csv`
- `release_comparisons.csv`
- `biome_audit.json`
- `official_verdict.md`
- `report.md`

## How To Save Results Correctly

When experimental results matter:

1. keep truth-source files in tracked locations if they belong to a frozen baseline
2. keep heavy generated outputs ignored
3. build release bundles through `projects/release-tooling/`
4. document limitations in the verdict
5. tag only after the release package is coherent

Do not store final scientific truth only in chat text.
If it matters, it must exist in tracked files or in the generated release package.

## Architect Mode

When acting as architect, optimize for attribution and falsifiability.

Always answer:

- what exact architectural question is being tested
- what is frozen
- what is variable
- what artifact proves the conclusion
- what remains unknown

Avoid:

- blending multiple RC questions into one cycle
- mutating baselines post hoc
- using new folder copies for minor versioning
- making undocumented assumptions from local runs

## New Chat Startup Checklist

At the start of a new chat in this repo:

1. read `AGENTS.md`
2. read `README.md`
3. run `git status --short --branch`
4. identify which project folder is in scope
5. check whether the task targets live development, frozen baseline, or release tooling
6. if research output is involved, check artifact policy before editing anything

## Current Default Interpretation

If the user says "the project" without clarification:

- live development usually means `projects/neuroh/`
- frozen baseline means `projects/homeogrid-mvp-rc3/`
- release assembly means `projects/release-tooling/`

V2 work happens in `projects/homeoorganism/`. Vision is frozen in `docs/vision.md` and should not be modified without explicit reason. `RC4` implementation requires `docs/rc4_spec.md` to be committed first. Do not write new agent code until `rc4_spec.md` is committed.
