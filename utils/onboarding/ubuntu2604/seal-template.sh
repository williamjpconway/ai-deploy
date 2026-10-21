#!/usr/bin/env bash
# Seals an Ubuntu 26.04 VM so it can become the Proxmox template that
# spec 009's test slots are cloned from: every clone must come up with
# its own hostname, machine-id and SSH host keys, and report its IP
# through the QEMU guest agent.
#
# Run this LAST, as root, in the VM that is about to be converted to a
# template - after initialize-ssh-onboarding.sh (masterchief + Key B +
# sshd hardening). It doesn't repeat that script's work; it only warns
# if Key B looks missing.
#
# Every step here is a real gap found cloning tmpl-ubuntu2604 into slot
# 9201 on 2026-10-21, not a hypothetical:
# - qemu-guest-agent wasn't installed, so Proxmox couldn't report the
#   clone's IP (it had to be found by MAC on the network).
# - The clone kept the template's hostname (tmplubuntu2604): with no
#   cloud-init drive attached, cloud-init reports itself disabled. The
#   drive is added per clone (needs VM.Config.CDROM); this script makes
#   sure nothing in the image stops cloud-init reading it
#   (cloud-init.disabled, or an installer datasource_list without
#   NoCloud).
# - The clone had the template's machine-id (two clones can then ask
#   DHCP for the same lease) and the template's SSH host keys (every
#   clone looks like the same machine to SSH host-key checking).
#
# After it runs: shut down, convert the VM to a template, and on the
# Proxmox host run the commands printed at the end.
#
# Supports --dry-run (no changes; doesn't need root). --shutdown powers
# off at the end instead of leaving that to you.

set -euo pipefail

TARGET_USER="masterchief"
KEY_B_PUB="ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIFGRR8D4t1P0Y7OzU79Ch94x0e/VtC3lOXZINJfzpYRh ai-deploy target key"
DROPIN_DIR="/etc/systemd/system/ssh.service.d"
DROPIN="$DROPIN_DIR/10-regenerate-host-keys.conf"
DRY_RUN=0
SHUTDOWN=0

for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY_RUN=1 ;;
    --shutdown) SHUTDOWN=1 ;;
    *) echo "Unknown argument: $arg (use --dry-run, --shutdown)"; exit 2 ;;
  esac
done

if [[ "$DRY_RUN" -eq 0 && "$(id -u)" -ne 0 ]]; then
  echo "Run as root (sudo $0), or with --dry-run to preview."
  exit 1
fi

run() {
  if [[ "$DRY_RUN" -eq 1 ]]; then
    echo "[dry-run] would run: $*"
  else
    "$@"
  fi
}

# A result message, printed only when something was actually done.
done_msg() {
  [[ "$DRY_RUN" -eq 1 ]] || echo "$*"
}

# 0. Sanity: Key B for masterchief (initialize-ssh-onboarding.sh's job)
USER_HOME=$(getent passwd "$TARGET_USER" | cut -d: -f6 || true)
if [[ -n "$USER_HOME" ]] && sudo -n test -f "$USER_HOME/.ssh/authorized_keys" 2>/dev/null \
   && sudo -n grep -qxF "$KEY_B_PUB" "$USER_HOME/.ssh/authorized_keys" 2>/dev/null; then
  echo "Key B present for $TARGET_USER"
elif [[ -n "$USER_HOME" ]] && [[ -r "$USER_HOME/.ssh/authorized_keys" ]] \
   && grep -qxF "$KEY_B_PUB" "$USER_HOME/.ssh/authorized_keys"; then
  echo "Key B present for $TARGET_USER"
else
  echo "WARNING: Key B not found for $TARGET_USER - run initialize-ssh-onboarding.sh first"
fi

# 1. QEMU guest agent, so Proxmox can report each clone's IP
if dpkg -s qemu-guest-agent >/dev/null 2>&1; then
  echo "qemu-guest-agent already installed, skipping"
else
  run apt-get update
  run env DEBIAN_FRONTEND=noninteractive apt-get install -y qemu-guest-agent
  done_msg "Installed qemu-guest-agent (starts on boot once the VM has agent=1 in Proxmox)"
fi

# 2. cloud-init enabled, and allowed to read Proxmox's NoCloud drive
if [[ -e /etc/cloud/cloud-init.disabled ]]; then
  run rm -f /etc/cloud/cloud-init.disabled
  done_msg "Re-enabled cloud-init (removed /etc/cloud/cloud-init.disabled)"
else
  echo "cloud-init not disabled, skipping"
fi

shopt -s nullglob
for f in /etc/cloud/cloud.cfg.d/*.cfg; do
  if grep -q "datasource_list" "$f" && ! grep -q "NoCloud" "$f"; then
    run mv "$f" "$f.disabled-by-seal"
    done_msg "Disabled $f - its datasource_list would make cloud-init ignore the Proxmox drive"
  fi
done
shopt -u nullglob

# 3. Safety net: if cloud-init ever doesn't run, sshd still makes keys
#    instead of failing to start with none (ssh-keygen -A only creates
#    missing keys).
if [[ -f "$DROPIN" ]]; then
  echo "$DROPIN already exists, skipping"
else
  if [[ "$DRY_RUN" -eq 1 ]]; then
    echo "[dry-run] would write $DROPIN (ExecStartPre=/usr/bin/ssh-keygen -A)"
  else
    mkdir -p "$DROPIN_DIR"
    printf '[Service]\nExecStartPre=/usr/bin/ssh-keygen -A\n' > "$DROPIN"
    systemctl daemon-reload
    echo "Wrote $DROPIN"
  fi
fi

# 4. Per-clone identity: cloud-init state, machine-id, SSH host keys.
#    Done last - SSH sessions into this VM will fail after this until
#    a clone boots and regenerates the keys.
run cloud-init clean --logs --machine-id
done_msg "Cleared cloud-init state and reset machine-id"

host_keys=(/etc/ssh/ssh_host_*)
if [[ -e "${host_keys[0]}" ]]; then
  run rm -f /etc/ssh/ssh_host_*
  done_msg "Removed SSH host keys (each clone generates its own)"
else
  echo "No SSH host keys present, skipping"
fi

run truncate -s 0 /root/.bash_history
[[ -n "$USER_HOME" ]] && run truncate -s 0 "$USER_HOME/.bash_history"

if [[ "$DRY_RUN" -eq 1 ]]; then
  echo
  echo "[dry-run] would verify: guest agent installed, cloud-init enabled, machine-id reset, no host keys"
  exit 0
fi

echo
echo "Verifying the seal..."
fail=0
dpkg -s qemu-guest-agent >/dev/null 2>&1 && echo "qemu-guest-agent: installed" \
  || { echo "FAILED: qemu-guest-agent not installed"; fail=1; }
[[ ! -e /etc/cloud/cloud-init.disabled ]] && echo "cloud-init: enabled" \
  || { echo "FAILED: cloud-init still disabled"; fail=1; }
mid=$(cat /etc/machine-id 2>/dev/null || true)
[[ -z "$mid" || "$mid" == "uninitialized" ]] && echo "machine-id: reset" \
  || { echo "FAILED: machine-id still set ($mid)"; fail=1; }
compgen -G "/etc/ssh/ssh_host_*" >/dev/null && { echo "FAILED: SSH host keys still present"; fail=1; } \
  || echo "SSH host keys: removed"
[[ -f "$DROPIN" ]] && echo "sshd key-regeneration drop-in: present" \
  || { echo "FAILED: $DROPIN missing"; fail=1; }
[[ "$fail" -eq 0 ]] || exit 1

echo "Template seal check PASSED"
echo
echo "Next, on the Proxmox host (as root):"
echo "  qm set 9001 --agent 1"
echo "  pveum role modify AiDeployTestVM --append 1 --privs VM.Config.CDROM"
echo "Then convert this VM to template 9001."

if [[ "$SHUTDOWN" -eq 1 ]]; then
  echo "Shutting down..."
  shutdown -h now
else
  echo "Shut this VM down now - don't reboot it first, or it will regenerate its identity."
fi
