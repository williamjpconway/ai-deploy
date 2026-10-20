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
- [ ] `dc/New-AiDeployPrereqs.ps1` — create the `ai-deploy` OU, the
  `ai-deploy-operators` security group, and the `masterchief` user.
- [ ] `dc/New-AiDeployLabCertTemplates.ps1` — `lab-*` copies of every
  existing certificate template, 2-year validity instead of 5.
