# Tool versions extracted from TogetherMade on 2026-09-25; update deliberately.
ARG NODE_VERSION=24
FROM node:${NODE_VERSION}-bookworm-slim

ARG DEV_UID=1000
ARG DEV_GID=1000
ARG TARGETARCH
ARG JUST_VERSION=1.58.0
ARG JUST_LSP_VERSION=0.8.0
ARG CODEX_VERSION=0.146.0
ARG CLAUDE_VERSION=2.1.220
ARG COPILOT_VERSION=1.0.77
ARG UV_VERSION=0.12.12

ENV DISABLE_AUTOUPDATER=1 \
    CLAUDE_CONFIG_DIR=/home/dev/.claude \
    CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1 \
    AGENT_DEV_CONTAINER=1 \
    GIT_OPTIONAL_LOCKS=0

RUN apt-get update && apt-get install -y --no-install-recommends \
        bash ca-certificates curl git gosu jq less openssh-client procps python3 make g++ ripgrep shellcheck \
    && rm -rf /var/lib/apt/lists/*

RUN set -eu; \
    case "${TARGETARCH:-$(dpkg --print-architecture)}" in \
        amd64) target=x86_64-unknown-linux-musl ;; \
        arm64) target=aarch64-unknown-linux-musl ;; \
        *) exit 1 ;; \
    esac; \
    archive="just-${JUST_VERSION}-${target}.tar.gz"; \
    release="https://github.com/casey/just/releases/download/${JUST_VERSION}"; \
    cd /tmp; \
    curl -fsSLO "${release}/${archive}"; \
    curl -fsSLO "${release}/SHA256SUMS"; \
    grep " ${archive}$" SHA256SUMS | sha256sum --check -; \
    tar -xzf "$archive" just; \
    install -m 0755 just /usr/local/bin/just; \
    rm just "$archive" SHA256SUMS

RUN set -eu; \
    case "${TARGETARCH:-$(dpkg --print-architecture)}" in \
        amd64) target=x86_64-unknown-linux-gnu ;; \
        arm64) target=aarch64-unknown-linux-gnu ;; \
        *) exit 1 ;; \
    esac; \
    archive="just-lsp-${JUST_LSP_VERSION}-${target}.tar.gz"; \
    release="https://github.com/terror/just-lsp/releases/download/${JUST_LSP_VERSION}"; \
    cd /tmp; \
    curl -fsSLO "${release}/${archive}"; \
    curl -fsSLO "${release}/SHA256SUMS"; \
    grep " ./${archive}$" SHA256SUMS | sha256sum --check -; \
    tar -xzf "$archive" ./just-lsp; \
    install -m 0755 ./just-lsp /usr/local/bin/just-lsp; \
    rm ./just-lsp "$archive" SHA256SUMS

RUN curl -LsSf "https://astral.sh/uv/${UV_VERSION}/install.sh" -o /tmp/uv-install.sh \
    && UV_INSTALL_DIR=/usr/local/bin sh /tmp/uv-install.sh \
    && rm /tmp/uv-install.sh

RUN npm install --global npm@11 \
    && npm install --global "@openai/codex@${CODEX_VERSION}" \
        "@anthropic-ai/claude-code@${CLAUDE_VERSION}" "@github/copilot@${COPILOT_VERSION}" \
    && npm cache clean --force

RUN set -eu; \
    userdel node; \
    if ! getent group "$DEV_GID" >/dev/null; then groupadd --gid "$DEV_GID" dev; fi; \
    useradd --create-home --uid "$DEV_UID" --gid "$DEV_GID" --shell /bin/bash dev; \
    install -d -o "$DEV_UID" -g "$DEV_GID" /home/dev/.codex /home/dev/.claude /home/dev/.copilot

COPY .devcontainer/entrypoint /usr/local/bin/agent-entrypoint
RUN chmod 0755 /usr/local/bin/agent-entrypoint
WORKDIR /workspace
ENTRYPOINT ["/usr/local/bin/agent-entrypoint"]
CMD ["sleep", "infinity"]
