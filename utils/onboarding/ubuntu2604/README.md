# Onboarding prep: Ubuntu 26.04

What's required before an Ubuntu 26.04 VM can be onboarded by
ai-deploy, and the script that makes it true.

## Run once, before the VM becomes a template

```bash
sudo ./initialize-ssh-onboarding.sh
```

This script:
- Creates the `masterchief` user with passwordless sudo (if not
  already present).
- Installs Key B's public key into `masterchief`'s `authorized_keys`.
- Hardens sshd against password authentication, including re-flipping
  cloud-init's own config if it tries to re-enable it.
- Ensures `ufw` (if active) allows SSH.
- Exempts `ai-deploy` (192.168.3.2, `--exempt-ip=` to change) from
  sshd's `PerSourcePenalties` lockout, so a few failed onboarding runs
  or tests can't block the management host (OpenSSH 9.8+).
- Verifies all of the above actually took effect before reporting
  success.

Idempotent and supports `--dry-run`. See the script's own header
comment for why each step exists - they're all real, confirmed gaps
found setting up `ai-deploy` itself, not hypothetical.

## Then, last: seal it as a Proxmox template (spec 009)

```bash
sudo ./seal-template.sh --dry-run    # preview
sudo ./seal-template.sh --shutdown   # seal and power off - don't boot it again
```

Then convert the VM to template 9001 (`qm set 9001 --agent 1`,
`qm template 9001`) and re-add the token's ACL on `/vms/9001` -
destroying or replacing a VM removes its ACL.

This script installs `qemu-guest-agent` (so Proxmox can report each
clone's IP), makes sure nothing stops cloud-init reading the Proxmox
cloud-init drive (so each clone gets its own hostname), resets the
machine-id, and removes the SSH host keys (each clone makes its own;
a systemd drop-in regenerates them if cloud-init ever doesn't run).
Verified 2026-10-21: a fresh clone got its IP from the guest agent, its
own hostname, machine-id and SSH host key, and Key B + passwordless
sudo still worked.

## What "ready for onboarding" means after this runs

- SSH reachable on port 22.
- Key-based auth works as `masterchief`; password auth is rejected.
- `masterchief` has passwordless sudo.

Onboarding (`bin/onboard-ubuntu`, spec 007) verifies these are true -
including that the server really doesn't offer password login - every
time it runs - it never configures them itself. If verification
fails on a VM that's supposed to already be a template of this recipe,
that's a sign the template itself needs rebuilding, not something for
onboarding to patch around.
