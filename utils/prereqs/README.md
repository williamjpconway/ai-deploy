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
- [ ] `dc/Install-AiDeployForest.ps1` — promote to the first DC of a new
  forest, `domain.internal` (NetBIOS `DOMAIN`), with DNS installed via
  `-InstallDns`. Triggers an automatic reboot; re-run after reboot to
  verify.
- [ ] `dc/New-AiDeployPrereqs.ps1` — create the `ai-deploy` OU, the
  `ai-deploy-operators` security group, and the `masterchief` user.
  Previously confirmed working against the pre-rebuild domain; needs a
  fresh run against the new forest.
- [ ] `dc/Install-AiDeployCA.ps1` — Enterprise Root CA + Web Enrollment
  only. Verification specifically checks `https://localhost/certsrv`
  responds, targeting the earlier "CA isn't opening" failure.
- [ ] `dc/New-AiDeployLabCertTemplates.ps1` — `lab-*` copies of every
  existing certificate template, 2-year validity instead of 5. Last run
  failed on a parse error (em dash in a string literal corrupted on
  transfer — retro #2, fixed) and also needs a fresh run against the
  new CA.
- [ ] `dc/Install-AiDeployDNS.ps1` — forwarder (`192.168.0.254`) and
  reverse lookup zone (`192.168.0.0/22`) on top of the DNS role
  `Install-AiDeployForest.ps1` already installed.
