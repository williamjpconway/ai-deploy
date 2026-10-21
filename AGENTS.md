# Agent Rules

Read this at the start of every session. Every rule should trace back to an entry in `retro.md`.

## Project
- Stack (decided 2026-10-20, for the UI - spec 000): FastAPI (Python)
  backend, Postgres (app state), Vault (secrets - certs from spec 006,
  Key A backup), PAM auth (`python-pam` or similar, expected to work
  unprivileged via `pam_unix`'s `unix_chkpwd` helper), htmx/Alpine.js
  frontend. `xterm.js` is scoped to spec 008 (terminal) only, not the
  general frontend. No Node.js - Python drives the terminal's PTY over
  websockets directly. Onboarding (`onboard-windows`, spec 001) is
  also Python + pytest (decided 2026-10-21), so the UI (spec 002) can
  call the same code; it runs on `ai-deploy` and writes inventory to
  `~/.config/ai-deploy/inventory/` (outside the repo). Target prep
  scripts (`utils/`), Ansible and playbooks stay in PowerShell/bash
  per the existing Tools rules.
- Run tests (on `ai-deploy`, in `~/ai-deploy`, after `git pull`):
  `AI_DEPLOY_TEST_TARGET=192.168.3.1 python3 -m pytest` (unit + live;
  without the env var only unit tests run). The destructive AC3 test
  additionally needs `--allow-destructive` and explicit operator
  confirmation before every run - it changes the target's sshd shell.
- Checks (static, run at Test stage; decided in spec 001's plan):
  `ruff check .` and `ruff format --check .` (ruff via pipx, installed
  by `utils/prereqs/ai-deploy/install-ansible.sh`).
- Run the app: onboarding CLI (spec 001), on `ai-deploy`:
  `~/ai-deploy/bin/onboard-windows --name <name> --ip <ip>`. The web UI
  (spec 000) has no command yet.
- Control VM (the ai-deploy VM itself, not a target to onboard):
  hostname `ai-deploy`, IP `192.168.3.2` (eth0), Ubuntu 26.04.1 LTS, VM
  on Proxmox provisioned via cloud-init, user `masterchief`. Claude Code
  install still pending.
- Onboarding invocation model (decided 2026-10-20, clarified
  2026-10-21 in spec 001): the SSH prep script
  (`utils/onboarding/<os>/`) is baked into the VM template and assumed
  already run - the copy in `utils/` is only for re-running by hand.
  Onboarding itself (`onboard-windows` / `onboard-ubuntu`) runs on
  `ai-deploy` against the target and writes Ansible inventory on
  `ai-deploy`. Nothing runs on the target except over SSH. Exact
  script names/locations: decided in each spec's plan.

## Tools
- Script naming, per ecosystem convention (deliberate, not an
  inconsistency — each matches what that language's own tooling/linter
  expects): PowerShell scripts are `Verb-Noun.ps1` PascalCase (e.g.
  `New-ControlKey.ps1`, matching built-in cmdlet naming and
  `PSScriptAnalyzer`); shell scripts are `kebab-case.sh` (e.g.
  `new-target-key.sh`, matching Unix convention). Don't force one style
  across both languages.
- No non-ASCII characters (em dashes, smart quotes, etc.) in script
  files (`.ps1`/`.sh`) — use plain `-`/`"`/`'` instead. Windows
  PowerShell 5.1 has misread UTF-8 em dashes as corrupted bytes on file
  transfer before, breaking string literals with a confusing "missing
  terminator" parse error (retro #2). Markdown/prose files are fine as
  Unicode; this only applies to files that get parsed as code.
- Prefer an established tool over a bespoke script wherever one already
  covers the need: Ansible for configuring an onboarded VM. Reach for a
  custom script only when no suitable tool exists, and say why in the
  plan when that's the case.
- Ansible and ansible-lint are installed on `ai-deploy` via pipx
  (`utils/prereqs/ai-deploy/install-ansible.sh`, confirmed working
  2026-10-20: `ansible-core 2.21.5`, `ansible-lint 26.10.1`) — not a
  distro package, so don't assume `apt`-based version info applies.
- No provisioning tool (Terraform/OpenTofu) is in scope — this product
  never creates, deletes, or power-manages a VM, only connects to and
  configures ones that already exist - outside the spec 009 test slots.
  Still no Terraform/OpenTofu - the test tooling uses the Proxmox API,
  via Ansible where that fits.
- PowerShell Gallery modules (e.g. PSPKI) are for filling a genuine gap
  — reach for one only when no built-in RSAT module already covers the
  task, same bar as the custom-script rule above:
  - Certificate template duplication: manual, not scripted at all (see
    `utils/prereqs/dc/duplicate-certificate-template.md`) - no built-in
    cmdlet does this, and a scripted PSPKI/raw-ADSI attempt hit an
    unresolved, reproducible `E_FAIL` (retro #3). The Certificate
    Templates console's own "Duplicate Template" sidesteps it entirely.
  - AD users/groups: the built-in `ActiveDirectory` module already
    covers create/delete fully (`New-ADUser`/`Remove-ADUser`,
    `New-ADGroup`/`Remove-ADGroup`) — no Gallery module needed.
  - DNS records: the built-in `DnsServer` module already covers
    create/delete (`Add-DnsServerResourceRecord*`/
    `Remove-DnsServerResourceRecord`) — no Gallery module needed.
  - If a script needs a Gallery module, install it the same way as the
    PSPKI example: check `Get-Module -ListAvailable`, `Install-Module`
    only if missing, never assume it's pre-installed.

## Infrastructure access
<!-- Fill in once BRIEF.md's Infrastructure section names a real resource.
     One block per infra target. See skills/brief-intake for how this
     gets populated during the brief conversation. -->
- No hypervisor API access of any kind (Proxmox, vCenter, or otherwise)
  — out of scope. This product never calls a hypervisor API.
  - **Exception (decided 2026-10-21, spec 009)**: test tooling under its
    own directory may use the `ai-deploy-test@pve` Proxmox token - VMs
    9101-9102 and 9201-9202 only, cloned from 9000/9001. Product code
    (onboarding, operations, UI) must never import or call it, and no
    product test may require it - tests take any target IP.
- Two distinct SSH keys, not one shared key:
  - **Key A** — this operator's machine to `ai-deploy`. **Confirmed
    working.** Generated by `utils/prereqs/operator/New-ControlKey.ps1`, stored
    at `C:\Users\Willi\.ssh\ai_deploy_control` (non-default name, not in
    the repo). A host alias in `C:\Users\Willi\.ssh\config` makes `ssh
    ai-deploy` use it automatically:
    ```
    Host ai-deploy
        HostName 192.168.3.2
        User masterchief
        IdentityFile ~/.ssh/ai_deploy_control
        IdentitiesOnly yes
    ```
    Password authentication is now disabled on `ai-deploy` (publickey
    only, verified) — see the hardening note below for how and why.
  - **Key B** — `ai-deploy` to each onboarded target (e.g. `dc`).
    Generated (confirmed present 2026-10-21) at
    `~/.ssh/ai_deploy_targets` on `ai-deploy`, by
    `utils/prereqs/ai-deploy/new-target-key.sh`;
    its public half must be added to each target's authorized keys
    before that target can be onboarded — this is not automatically
    pre-baked for real targets, only assumed for hypothetical ones.
  - **SSH hardening on `ai-deploy`**: cloud-init's
    `/etc/ssh/sshd_config.d/50-cloud-init.conf` originally had
    `PasswordAuthentication yes` (sshd uses the first value it reads,
    so this silently overrode later config). Fixed by adding
    `/etc/ssh/sshd_config.d/00-keys-only.conf` (`PasswordAuthentication
    no`, `KbdInteractiveAuthentication no`, `PermitRootLogin no`, sorts
    before `50-cloud-init.conf`) and flipping `50-cloud-init.conf` to
    `no` as well.
  - **Known risk, not permanently fixed**: if cloud-init re-runs (`cloud-init
    clean`, a clone, or a new instance ID), it may rewrite
    `50-cloud-init.conf` back to `yes`. `00-keys-only.conf` still wins
    because it sorts first, but the permanent fix — `ssh_pwauth: false`
    in the cloud-init user-data, or leaving the Proxmox cloud-init
    password unset — isn't done yet.
  - Ubuntu's SSH is socket-activated (`ssh.socket`) — if a config change
    doesn't seem to take effect, restart both `ssh.socket` and
    `ssh.service`, not just the service.
  - Open: the `ai_deploy_control` private key isn't backed up yet — the
    Proxmox console is the only other access path to `ai-deploy` if
    it's lost. Plan (2026-10-20): back it up in the local Vault
    install below, once that exists.
- **Local Vault install (planned, not yet set up, decided 2026-10-20)**:
  intended to store issued certificates/private keys from spec 006's
  playbook, and a backup of Key A's private key. No further detail yet
  (which Vault, where it runs, auth model) - revisit when spec 006
  reaches Develop or when Key A backup is actually prioritized.
- SSH access to onboarded VMs: login as `masterchief` on both Ubuntu
  (passwordless sudo) and Windows — both over SSH (Windows uses
  `ansible_shell_type: powershell`, not WinRM).
  - **Decision 2026-10-20**: Windows scoped to the `masterchief` domain
    user specifically, not "any local admin" - matching Ubuntu's
    identity-specific model instead of the group-based one.
  - **Real gap, not yet resolved**: Windows OpenSSH's
    `administrators_authorized_keys` is checked for any local
    Administrators-group member, regardless of which username is
    specified at connect time - it isn't cryptographically bound to
    one identity the way a per-user `authorized_keys` file is. Two
    ways to actually get `masterchief`-only access, neither
    implemented yet:
    1. Add `masterchief` to the target's local Administrators group
       (so it can use `administrators_authorized_keys`), and only ever
       connect as `masterchief` by convention - closest to today's
       working setup, but anyone else in that group with Key A/B could
       still authenticate as themselves too.
    2. Install the key into `masterchief`'s own per-user
       `authorized_keys` instead (true identity-scoping, matching
       Ubuntu) - but that requires `masterchief`'s Windows user profile
       to already exist, which it doesn't until something triggers its
       creation (e.g. one interactive logon, or scripted profile
       creation). Not yet solved.
  - **Decision 2026-10-21 (spec 001)**: option 1 for now - `masterchief`
    is a member of each Windows target's Administrators group (a
    template/prep precondition; onboarding verifies it, never sets it).
    Option 2 stays open as the least-privilege path.
  - **Known risk, not yet fixed**: on a domain controller there is no
    local Administrators group - membership means the domain's
    BUILTIN\Administrators, effectively admin on every DC. Key B on
    `ai-deploy` is therefore a domain-admin-equivalent credential
    (key-based, no password), alongside the Domain Admin account noted
    below.
- Shell on onboarded VMs: bash/sh on Ubuntu, PowerShell on Windows.
- **Confirmed end-to-end on `dc` 2026-10-20 (as `Administrator`, before
  the `masterchief`-scoping decision above - not yet re-confirmed as
  `masterchief`)**: `ssh -i ~/.ssh/ai_deploy_targets Administrator@<target-ip>` from `ai-deploy`
  works and gets a real PowerShell shell. Getting there from a fresh
  Windows Server 2025 VM needed two fixes beyond what "pre-baked SSH"
  was assumed to mean — both are now real requirements for any future
  Windows target's base image/template, not just `dc`:
  - OpenSSH Server's auto-created firewall rule
    (`OpenSSH-Server-In-TCP`) defaults to the `Private` profile only.
    A domain-joined server's connection is `DomainAuthenticated`, which
    that rule doesn't match, so inbound port 22 is silently blocked
    even with `sshd` correctly listening. Fix:
    `Set-NetFirewallRule -Name 'OpenSSH-Server-In-TCP' -Profile Any`.
  - Windows OpenSSH's default shell is `cmd.exe`, not PowerShell, until
    set explicitly:
    `New-ItemProperty -Path "HKLM:\SOFTWARE\OpenSSH" -Name DefaultShell
    -Value "C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe"
    -PropertyType String -Force`, then restart `sshd`. Without this,
    `ansible_shell_type: powershell` is a lie — the remote shell is
    actually cmd, and anything with a semicolon or PowerShell syntax
    fails confusingly.
- **Not yet confirmed end-to-end for Ubuntu**: the prep script
  (`utils/onboarding/ubuntu2604/`) passed its own verification on
  `tmplubuntu2604`, but an actual `ai-deploy` → `tmplubuntu2604`
  connection test wasn't properly attempted yet - the user suspects
  SSH key access was the blocker. Revisit before treating Ubuntu
  onboarding as proven the way Windows now is.
- Rule: any destructive action on an onboarded VM always requires
  explicit confirmation regardless of mode.
  - **Exception (decided 2026-10-21, spec 009)**: no confirmation for
    actions confined to the four test slots (9101-9102, 9201-9202):
    clone, start, stop, snapshot, reset, deliberate breakage for tests,
    and removal - and for joining/removing those VMs' computer objects
    in `OU=ai-deploy-test` via the join-only account. Everything else
    keeps the confirmation rules - including any AD write outside that
    OU, anything done as Domain Admin or Key B on `dc`, and any change
    to the templates.

- Windows AD domain account (for the DC/CA/DNS target's playbooks —
  Create a Certificate, Create/Delete User, Create/Delete Group,
  Create/Delete a DNS Record):
  - Credentials: a domain account with Domain Admin rights. <fill in
    storage location and var names once set up — never in the repo,
    never printed, never pasted into chat.>
  - Scope — **known risk, not yet fixed**: Domain Admin is domain-wide
    privilege (every user, group, GPO, DC, trust relationship), far
    broader than user/group/DNS/cert CRUD actually needs. The
    least-privilege alternative is OU-scoped delegation for user/group
    management, DNS zone admin rights for records, and certificate
    template enrollment rights for certs — not implemented yet, so
    treat the confirmation rule below as the real guardrail.
  - Rule: any AD write (create/delete user, group, DNS record,
    certificate) always requires explicit confirmation regardless of
    mode — this credential can do far more than this product's
    features need, so nothing here should run unattended. (The only
    AD exception is the spec 009 join-only account inside
    `OU=ai-deploy-test` - see the test-slot exception above. It never
    applies to this Domain Admin credential.)

## Workflow
- Read `BRIEF.md` first. Specs inherit its principles and non-goals.
- The feature lifecycle (stages, gates G1-G4, reconciliation,
  bookkeeping) is defined only in `LIFECYCLE.md`. Follow it; don't
  restate it elsewhere.
- Skills under `skills/` aren't auto-loaded. When the operator says one
  of these, read and follow that skill:
  - "new feature: ..." - or a conversation converges on real scope not
    on the roadmap (confirm first) -> `skills/new-feature/SKILL.md`
  - "let's plan NNN" -> `skills/plan-feature/SKILL.md`
  - "build NNN" -> `skills/build-feature/SKILL.md`
  - "review NNN" -> `skills/accept-feature/SKILL.md`
  - "work on NNN" -> read `specs/NNN-*/status.md`, run the skill for
    its current stage
- Gates G1-G4 are the operator's decisions. Record them; never make them.
- Never write code for a feature before its G3 (plan approved) is
  recorded in its `status.md`.
- Work from `specs/NNN-*/tasks.md`, one task at a time (Develop stage).
- Built-without-error is never treated as working - only passing tests are.
- If the spec is ambiguous, stop and ask. Don't guess.

## Scripts: write → test → approve
<!-- Applies to anything that performs a real, stateful action outside
     the spec/plan/tasks pipeline — utils/ scripts, prereqs, playbooks.
     Roadmap features already get this via plan approval + AC tests;
     this is the same bar for scripts that aren't a roadmap feature. -->
- Write: include a dry-run path from the start, not bolted on after —
  `-WhatIf` for cmdlets that support `ShouldProcess` (most AD/DNS
  cmdlets do), an explicit `-DryRun` switch for anything that doesn't
  (e.g. direct ADSI calls, which ignore `-WhatIf` silently if you don't
  guard them yourself).
- Test: run the dry-run and show the user the output before any real
  run. If no safe dry-run is possible for a given action, say so
  explicitly and get the user's go-ahead before the first real
  execution of that action.
- Approve: a script isn't trusted/done until the user has seen a real
  or dry-run result and explicitly confirmed it matches what they
  expected.

## Rules from retros
<!-- Add rules here as retro.md earns them. Format: - Rule. (retro #N) -->
