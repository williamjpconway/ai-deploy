# Onboarding prep: Windows Server 2025

What's required before a Windows Server 2025 VM can be onboarded by
ai-deploy, and the script that makes it true.

## Run once, before the VM becomes a template

```powershell
.\Initialize-SshOnboarding.ps1
```

This script:
- Installs OpenSSH Server (if not already present).
- Fixes the auto-created firewall rule's profile scope - it defaults
  to Private only, which doesn't match a domain-joined server's
  DomainAuthenticated connection, silently blocking inbound SSH even
  though sshd is listening.
- Sets PowerShell as the default SSH shell (Windows OpenSSH defaults
  to `cmd.exe` otherwise).
- Installs Key B's public key into `administrators_authorized_keys`
  with the correct restrictive ACLs (SYSTEM + Administrators only, no
  inheritance - sshd rejects the file otherwise).
- Verifies all of the above actually took effect before reporting
  success.

Idempotent and supports `-WhatIf`. See the script's own header comment
for why each step exists - they're all real, confirmed gaps found
getting SSH onboarding working against `dc`, not hypothetical.

## What "ready for onboarding" means after this runs

- SSH reachable on port 22, regardless of network profile.
- Key-based auth works as any local Administrators-group member (not
  yet scoped to `masterchief` specifically - see the "Decision
  2026-10-20" / "Real gap" notes in `AGENTS.md`'s SSH access section;
  this script hasn't been updated for that decision yet).
- The shell on connection is actually PowerShell.

Onboarding (`specs/001-onboard-a-windows-vm/`) verifies these are true
every time it runs - it never configures them itself. If verification
fails on a VM that's supposed to already be a template of this recipe,
that's a sign the template itself needs rebuilding, not something for
onboarding to patch around.
