# Agent container starter

A copyable extraction of Justin's JWWTVG and TogetherMade development workflows.
It provides a shared editor/agent image and disposable task containers without a
shared CLI package or installation service. Each repository owns its copied files.
The original repositories have not been migrated.

## Adopt it

1. Copy `.devcontainer/`, `scripts/agent-container`, and `scripts/run-agent` into a
   Git repository. Merge with existing files rather than overwriting them.
2. Edit `.devcontainer/project.json`: choose a unique lowercase `name`, set the
   bootstrap and check commands, and list every dependency/build/data directory
   that must be disposable. Bootstrap runs once per invocation; make it idempotent.
3. Edit the Dockerfile for the project's language/tool versions. It currently
   provides Node 24, Just, Git, Python, build utilities, and pinned Codex, Claude,
   and Copilot CLIs. These are the source projects' versions, not a promise that
   they are the latest releases.
4. Merge the Justfile recipes, AGENTS.md guidance, and `.gitignore` entries into
   their counterparts. The Justfile is optional; host Just is not required.
5. Copy `.codex/environments/environment.toml` if using Codex Desktop. Its setup
   checks prerequisites; its actions invoke the same runner.
6. Run `scripts/agent-container build`, `scripts/agent-container doctor`, then
   `scripts/agent-container --sterile check`.

The default check deliberately fails until you supply a real project gate.
The default bootstrap only prints a reminder. Docker with Compose v2, Git, jq,
and Bash 4+ are required on the host. The runner works from any directory inside
the repository. Use a separate Git worktree for each concurrent editing task.

```sh
scripts/agent-container shell
scripts/agent-container exec npm test
scripts/agent-container --sterile check
scripts/agent-container codex
scripts/agent-container claude
scripts/agent-container copilot
```

`exec` and `check` start configured supporting services without publishing tool
ports. `shell` and provider modes also publish the configured tool ports on
random loopback ports and print their URLs. Processes must listen on `0.0.0.0`
inside the container. `setup` runs bootstrap without supporting services.
Arguments after `shell`, `exec`, or a provider are forwarded literally.

## Project-owned configuration

`bootstrap` and `check` are JSON argument arrays, avoiding implicit shell quoting.
Use `["bash", "-c", "command && another-command"]` when shell syntax is needed.
For an existing Just workflow, a typical check is `["just", "check", "--agent"]`.
Do not point it at `container-check`, which would try to launch a nested container.

For a Node workspace, set bootstrap to your existing setup script or `npm ci`;
include the root and workspace `node_modules` directories and generated outputs
in `disposableDirectories`. For a Go project, add Go to the Dockerfile and retain
its existing module/bootstrap commands. Do not install project dependencies on
the host.

`environment` contains explicit **non-secret** tool-container variables. Values
are literal strings, including dollar signs. Put variables shared with supporting
services into Compose. The runner exposes a random `TASK_PASSWORD` for disposable
local services; it is regenerated per task. No host environment file is loaded.

`disposableDirectories` become fresh task-scoped named volumes. They must be
relative directory paths without symlinks. Use subdirectories for build tools
that delete their output directory: for example mount `ui/build` but configure
the tool to emit into `ui/build/task`, following TogetherMade's existing pattern.
The runner creates empty mountpoint directories on the host; generated contents
remain in Docker. Files generated elsewhere remain in your worktree, so include
all relevant paths for your project.

## Supporting services

Merge `examples/postgres-redis.yaml` into `.devcontainer/compose.yaml` and set
`services` to `["postgres", "redis"]`. Keep the base `tool` service. The example
uses TogetherMade's PostgreSQL/Redis image pins and a per-task database password;
choose versions appropriate for the destination project. Add health checks to
services so `up --wait` waits for readiness. Bootstrap may then migrate or seed
the disposable database.

Task Compose services must use internal named volumes/networks, no fixed
container names, and dynamic loopback bindings if publishing ports. The runner
rejects external resources and extra bind mounts, assigns per-task names to
volumes/networks, and adds ownership labels. It never layers a task over your
ordinary development/production Compose stack.

For separate API/UI services, keep their commands, readiness checks, origin
configuration, and dependency-install lifecycle in project-owned Compose and
scripts, as TogetherMade does. The base runner mounts source only in `tool`;
a multi-service application needs an explicit project extension to share source
and task volumes. This starter does not pretend that application's bootstrap,
CORS, preview, or database-import logic is generic.

## Isolation and authentication

Source is writable. Both the `.git` entry and the common Git directory are
read-only, including separate Git directory/linked-worktree layouts. Perform
Git mutations and signing on the host. No host home directory, signing socket,
SSH agent, or Docker socket is mounted. Tool processes run as `dev` with the
host UID/GID. Ordinary Docker networking is enabled; this is not an egress
sandbox or a boundary for executing an untrusted repository.

Existing `.env` and `.env.*` files enumerated by Git, including ignored files,
are hidden behind an empty read-only mount; `.env.example` files remain visible.
This is not a general secret scanner: other credential files in the writable
source mount are visible. Use clean worktrees and keep private data outside them.

Provider modes persist only that provider's container login in
`<name>-agent-<provider>-auth`. Sign in from inside the provider container;
no host credentials are imported. `--sterile` omits this volume. Shell/check/exec
modes never mount authentication volumes. Login volumes survive task cleanup.
To remove a login, deliberately remove that exact Docker volume after its active
sessions have ended. The starter does not add an automatic credential purge.

## Cleanup

Success, failure, Ctrl-C, and TERM clean up task-owned containers, networks, and
volumes. A command failure preserves its exit code unless cleanup also fails.
The runner validates all discovered ownership labels before removing anything;
it never runs Docker prune. If Docker fails or the coordinator is killed with
SIGKILL, retry using the exact project name printed at startup:

```sh
scripts/agent-container cleanup my-project-agent-0123456789abcdef01234567
```

Cleanup also stops a still-running task, so use its exact intended project name.
Authentication volumes are external to the task and survive. A failed automatic
cleanup prints the recovery command and retains its private temporary config.
After recovery, remove the printed temporary directory yourself; it can contain
disposable service credentials. Cached images remain available for later tasks.

## Editor development

Open the repository in its devcontainer to reuse the Dockerfile with `dev` as
the editor user. The supplied editor configuration is a single-container setup
with persistent dependencies, local data, and agent logins. Editor Git metadata
is writable; disposable agent restrictions do not apply to editor sessions.

Keep editor volume mounts synchronized with `disposableDirectories`. The editor
does not read project.json environment/services/ports automatically: configure
`containerEnv`/port forwarding, or adopt an editor-owned Compose overlay when
adding databases. Keep that stack and its persistent database distinct from task
resources. This mirrors the separation in TogetherMade rather than silently
turning editor data into disposable task data.

## Validation

```sh
shellcheck scripts/agent-container scripts/run-agent .devcontainer/entrypoint
python3 tests/smoke.py
```

The smoke test requires Docker, builds the image, and creates temporary Git
fixtures. It checks the provider toolchain, non-root execution, read-only Git,
environment masking, fresh dependency volumes, exit status, authentication
persistence, simultaneous loopback servers, isolated PostgreSQL/Redis stacks,
cancellation, and cleanup ownership.
It removes its own runtime resources; built image cache remains. It does not
exercise interactive provider sign-in or launch an editor.

See `EXTRACTION.md` for the source mapping and extension points, and
`VALIDATION.md` for the results collected when this starter was extracted.
