# HomeoGrid Monorepo

## Projects

- `projects/neuroh/` - active development line for the live project
- `projects/homeogrid-mvp-rc3/` - frozen baseline snapshot from `mvp-rc3`
- `projects/release-tooling/` - external release assembler
- `projects/homeoorganism/` - planned v2 project folder when v2 starts

## Branch Policy

- Single active branch: `main`
- No per-project long-lived branches inside the monorepo
- Short-lived work branches may be created from `main` when needed
- Releases are represented by Git tags, not by duplicating project folders

## When To Add A New `projects/` Folder

Add a new folder only when one of these is true:

- A new independent project starts
- A frozen baseline snapshot must be preserved
- A major architectural rewrite starts as a separate codebase
- A standalone internal tool needs its own lifecycle

Do not create a new folder for a minor release of an existing project. Use tags for that.

## Artifacts

- `release-packages/` is ignored and stores generated release bundles
- `projects/neuroh/artifacts/` is ignored as runtime output
- `projects/homeogrid-mvp-rc3/artifacts/official_wave1/**/logs/episode_summaries.jsonl` is tracked as release truth source
- `projects/homeogrid-mvp-rc3/artifacts/official_wave1/**/run_manifest.json` is tracked as release truth source
- heavyweight monitoring, snapshots, and replay outputs stay ignored
