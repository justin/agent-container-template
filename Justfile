# Merge these recipes into an existing Justfile; keep its check recipe.
set positional-arguments

# Run a provider or shell in a disposable task.
agent *args:
    scripts/agent-container "$@"

container-build:
    scripts/agent-container build

container-check:
    scripts/agent-container --sterile check

container-shell:
    scripts/agent-container shell
