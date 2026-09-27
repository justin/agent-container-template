# Container workflow

Run implementation, dependency installation, builds, and tests inside the editor
container or a disposable task container. Read-only inspection and authorized Git
operations may run on the host. Use a separate worktree per concurrent editing task.

- `scripts/agent-container shell` opens a disposable shell.
- `scripts/agent-container exec COMMAND [ARG...]` runs a focused command.
- `scripts/agent-container --sterile check` runs the configured complete gate.
- `scripts/agent-container codex|claude|copilot` launches a provider.
- Do not launch nested containers from inside a container.

Disposable tasks have read-only Git metadata. Perform authorized Git mutations
from the host; do not mount signing agents or weaken that boundary. Agent login
volumes are separate from host credentials. Use disposable data and preserve
unrelated work. Report exact checks run and runtime behavior left unverified.

Merge this guidance into the destination repository's existing instructions.
