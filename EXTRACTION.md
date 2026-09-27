# What was extracted

Source checkouts inspected on 2026-09-25:

- JWWTVG: `/Users/justinwilliams/src/justin/jww-tvguide`, branch `main`,
  commit `67318562e10ad7fe1f162d233005971f1b3d2a07`.
- TogetherMade: `/Users/justinwilliams/src/togethermade/togetherMade`, branch
  `jww/authentication-onboarding-390-plan`,
  commit `067c1ee856450c263efff815b17349d334f1eef5`.

| Concern | Source | Reusable result |
| --- | --- | --- |
| Tool image and non-root user | Both `.devcontainer` Dockerfiles | Shared editor/agent Dockerfile with explicit provider pins |
| Dependency isolation | Both `scripts/agent-container`; TogetherMade `agent-compose-config` | Configurable task-scoped volume directories |
| Task lifecycle | TogetherMade `scripts/agent-container` | Unique Compose projects, signal handling, exact ownership-checked cleanup |
| Git isolation | Both runners; TogetherMade `agent-compose-config` | Read-only common Git directory and `.git` entry |
| Credential isolation | Both runners | Selected provider volume, separate from task volumes; sterile mode |
| Local secret masking | TogetherMade `agent-compose-config` | Existing Git-enumerated `.env` files masked without reading contents |
| Ports | Both runners | Docker-assigned loopback ports; reported after startup |
| Build reuse | Both runners | Image tag hashes Dockerfile, entrypoint, allowlist, and host identity |
| Agent dispatch | Both `scripts/run-agent` | Provider/shell/exec plus project bootstrap and check hooks |
| Editor lifecycle | Both devcontainer configurations | Same toolchain, separate persistent editor storage |
| Codex Desktop actions | TogetherMade environment TOML | Prerequisite-only setup and build/shell/check actions |

## Deliberately left with the project

- JWWTVG's Go/media toolchain, native-runtime checks, seed archive/SQLite formats,
  trusted-origin rules, API/web generation, optional firewall and capabilities.
- TogetherMade's Prisma migration/seed lifecycle, API/UI/preview services,
  environment defaults, database imports, browser caches, output-directory
  overrides, and application readiness rules.
- Existing Just check recipes and compact-output wrappers. The starter invokes
  the project's gate instead of inventing an alternative checklist.
- Dependency-prefetch layers and remote Buildx cache settings. Add them when a
  project needs them and include every copied manifest in the image hash and
  Dockerfile allowlist.

The common artifact is the development workflow, not a replacement application
Compose stack. This extraction does not change either repository or claim to
be a drop-in migration for their full application runtimes.
