#!/usr/bin/env bash
# Generates the Key B keypair (ai-deploy -> onboarded targets, e.g. dc).
# Run this ON ai-deploy itself, as masterchief, after Key A is working.
#
# Idempotent: skips generation if the key already exists.
# Supports --dry-run: prints what would happen without creating anything,
# per AGENTS.md's write/test/approve rule for scripts.

set -euo pipefail

KEY_PATH="${KEY_PATH:-$HOME/.ssh/ai_deploy_targets}"
DRY_RUN=0

for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY_RUN=1 ;;
    --key-path=*) KEY_PATH="${arg#--key-path=}" ;;
  esac
done

if [[ -f "$KEY_PATH" ]]; then
  echo "Key already exists at $KEY_PATH, skipping generation"
else
  if [[ "$DRY_RUN" -eq 1 ]]; then
    echo "[dry-run] would generate ed25519 keypair at $KEY_PATH"
  else
    ssh-keygen -t ed25519 -f "$KEY_PATH" -N "" -C "ai-deploy target key"
    echo "Generated keypair at $KEY_PATH"
  fi
fi

if [[ -f "$KEY_PATH.pub" ]]; then
  echo
  echo "Public key (add this to each target VM's authorized_keys /"
  echo "administrators_authorized_keys before onboarding it):"
  cat "$KEY_PATH.pub"
elif [[ "$DRY_RUN" -eq 1 ]]; then
  echo "[dry-run] public key would be printed here after generation"
fi
