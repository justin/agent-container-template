# Validation — 2026-09-25

Validated on this Mac's Docker 29.4.0, Linux arm64 containers. Neither source
repository was modified or had its application validation gates rerun.

| Check | Result |
| --- | --- |
| `scripts/agent-container build` in a temporary Git fixture | Passed; built the extracted Dockerfile |
| `scripts/agent-container doctor` via smoke test | Passed; non-root process, Node/Just and all three provider CLIs launch |
| `shellcheck scripts/agent-container scripts/run-agent .devcontainer/entrypoint` | Passed |
| `bash -n scripts/agent-container scripts/run-agent .devcontainer/entrypoint` | Passed |
| JSON/TOML parsing, Python AST parsing, trailing-whitespace check | Passed |
| `just --list` in the extracted image | Passed |
| `python3 tests/smoke.py` | Passed against live Docker |

The live smoke test exercised a source path containing spaces and a dollar sign,
a separate Git directory with a read-only `.git` pointer, ignored `.env` masking,
non-root execution, absent Docker socket, fresh dependency volumes, a failing
command returning status 37, the configured check hook, saved provider-volume
persistence, sterile exclusion, concurrent HTTP servers with distinct loopback
ports, independent PostgreSQL/Redis services, database isolation, TERM cleanup,
and rejection of resources lacking the ownership label. No test task resources
remained after the successful run. Build cache images remain intentionally.

The first database test caught readiness being reported by PostgreSQL's temporary
initialization server. The example health check now probes TCP, which waits for
the final server; the complete smoke test passed after that correction.

Not exercised: interactive provider authentication, the editor's devcontainer
lifecycle, Linux amd64 builds, actual JWWTVG/TogetherMade application commands,
application-specific origins, seeds/imports, or multi-service API/UI adaptations.
The starter's default project check fails until the destination supplies its gate.
