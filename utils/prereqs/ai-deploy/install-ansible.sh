#!/usr/bin/env bash
# Installs Ansible, ansible-lint and ruff on ai-deploy via pipx (the upstream-
# recommended install method for all three, usually newer than distro
# apt packages). ruff is the static check for the Python code (spec 001).
#
# Idempotent: skips anything already installed.
# Supports --dry-run: prints what would be installed without installing,
# per AGENTS.md's write/test/approve rule for scripts.

set -euo pipefail

DRY_RUN=0
for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY_RUN=1 ;;
  esac
done

run() {
  if [[ "$DRY_RUN" -eq 1 ]]; then
    echo "[dry-run] would run: $*"
  else
    "$@"
  fi
}

if ! command -v pipx >/dev/null 2>&1; then
  echo "pipx not found, installing via apt..."
  run sudo apt update
  run sudo apt install -y pipx
  run pipx ensurepath
else
  echo "pipx already installed, skipping"
fi

if command -v ansible >/dev/null 2>&1; then
  echo "ansible already installed ($(ansible --version | head -1)), skipping"
else
  run pipx install --include-deps ansible
fi

if command -v ansible-lint >/dev/null 2>&1; then
  echo "ansible-lint already installed ($(ansible-lint --version | head -1)), skipping"
else
  run pipx install ansible-lint
fi

if command -v ruff >/dev/null 2>&1; then
  echo "ruff already installed ($(ruff --version)), skipping"
else
  run pipx install ruff
fi

echo
echo "Note: if this is the first pipx install, you may need to restart"
echo "your shell (or 'source ~/.bashrc') before ansible/ansible-lint/ruff show"
echo "up on PATH."
