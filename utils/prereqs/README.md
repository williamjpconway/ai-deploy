# Prereqs

One-time setup scripts, not roadmap features — this is the
infrastructure that has to exist before any feature can be built or
tested (see the main `README.md`'s "which level?" test). Organized by
which machine each script runs on, since that's the thing that's easy
to lose track of once scripts touch three different machines.

Each checkbox below means: run per `AGENTS.md`'s write → test → approve
rule (dry-run first, real run only after review), and the user has
confirmed the result matches what they expected. This file is the
at-a-glance status — it doesn't replace that rule.

## operator (this Windows PC)
- [x] `operator/New-ControlKey.ps1` — generate Key A, install on
  `ai-deploy`. Confirmed working 2026-10-20.

## ai-deploy
- [x] `ai-deploy/new-target-key.sh` — generate Key B, for
  `ai-deploy` → onboarded targets (e.g. `dc`). Confirmed working
  2026-10-20 (`~/.ssh/ai_deploy_targets`, correct permissions). Public
  key still needs adding to `dc`'s authorized keys before onboarding.
- [x] `ai-deploy/install-ansible.sh` — install Ansible + ansible-lint.
  Confirmed working 2026-10-20 via pipx: `ansible-core 2.21.5`,
  `ansible-lint 26.10.1`. New shell session (or `source ~/.bashrc`)
  needed for `~/.local/bin` to be on PATH.

## dc
<!-- Rebuilt from scratch 2026-10-20 (the CA wasn't working); dc is now
     treated as a blank Windows Server 2025 VM with just IP/hostname
     set. Everything below runs in order against that blank VM — the
     earlier "done" status for the OU/group/user script was against
     the pre-rebuild state and no longer applies. -->
- [x] `dc/Install-AiDeployForest.ps1` — promote to the first DC of a new
  forest, `domain.internal` (NetBIOS `DOMAIN`), with DNS installed via
  `-InstallDns`. Confirmed working — subsequent steps (AD DS-dependent
  OU/user creation, CA install) succeeded against this forest.
- [x] `dc/New-AiDeployPrereqs.ps1` — create the `ai-deploy` OU, the
  `ai-deploy-operators` security group, and the `masterchief` user.
  Confirmed working against the rebuilt forest.
- [x] `dc/Install-AiDeployCA.ps1` — Enterprise Root CA + Web Enrollment
  only. Confirmed working 2026-10-20: CertSvc running, `certutil -ping`
  OK, IIS correctly routes to `/certsrv` (HTTP 403 "SSL required" is
  the expected pass condition - requireSSL is on by default and no
  HTTPS binding exists yet, which is deliberately deferred work, not a
  defect).
- Certificate template duplication: **not scripted** — see
  `dc/duplicate-certificate-template.md` for the manual process.
  Scripted raw-ADSI duplication hit a reproducible but unexplained
  `E_FAIL` that survived extensive isolated debugging (retro #3); the
  Certificate Templates console's own "Duplicate Template" sidesteps
  it entirely and this is a one-time task per template needed.
- [x] `dc/Install-AiDeployDNS.ps1` — forwarder (`192.168.0.254`) and
  reverse lookup zone (`192.168.0.0/22`) on top of the DNS role
  `Install-AiDeployForest.ps1` already installed. Confirmed working
  2026-10-20, including idempotency on a second run. Caught two real
  bugs along the way: the original verification matched Windows DNS's
  default security zones instead of the intended ones, and
  `-NetworkID` with a shorter-than-/24 prefix only creates one zone,
  not all four implied by the /22 (both fixed - now loops per /24).
- [x] `dc/Resize-SystemVolume.ps1` — deletes the Recovery partition
  blocking C: from expanding, then resizes C: into the freed space.
  Confirmed working 2026-10-20 (real run, not just `-WhatIf`). `dc`
  shouldn't need this again - kept on file for any future VM that hits
  the same recovery-partition-blocks-extend issue.

## Onboarding prep (not a prereq - moved out)
VM-onboarding prep scripts (what any Ubuntu 26.04 or Windows Server
2025 VM needs before it can be onboarded) aren't tied to one of this
project's specific machines, so they live in `utils/onboarding/`
instead, organized by OS+version with their own READMEs - see
`utils/onboarding/ubuntu2604/README.md` and
`utils/onboarding/windows2025/README.md`.
