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
- Verifies all of the above actually took effect before reporting
  success.

Idempotent and supports `--dry-run`. See the script's own header
comment for why each step exists - they're all real, confirmed gaps
found setting up `ai-deploy` itself, not hypothetical.

## What "ready for onboarding" means after this runs

- SSH reachable on port 22.
- Key-based auth works as `masterchief`; password auth is rejected.
- `masterchief` has passwordless sudo.

Onboarding (`specs/007-onboard-an-ubuntu-vm/`) verifies these are true
every time it runs - it never configures them itself. If verification
fails on a VM that's supposed to already be a template of this recipe,
that's a sign the template itself needs rebuilding, not something for
onboarding to patch around.
