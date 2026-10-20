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
- [?] `dc/Install-AiDeployForest.ps1` — promote to the first DC of a new
  forest, `domain.internal` (NetBIOS `DOMAIN`), with DNS installed via
  `-InstallDns`. Must have succeeded (CA install below requires AD DS
  to already be up) but its own output hasn't been shown/confirmed in
  this rebuild cycle — paste it to confirm and flip to `[x]`.
- [?] `dc/New-AiDeployPrereqs.ps1` — create the `ai-deploy` OU, the
  `ai-deploy-operators` security group, and the `masterchief` user.
  Same gap as above: implied done, not yet confirmed against the new
  forest with its own output.
- [x] `dc/Install-AiDeployCA.ps1` — Enterprise Root CA + Web Enrollment
  only. Confirmed working 2026-10-20: CertSvc running, `certutil -ping`
  OK, IIS correctly routes to `/certsrv` (HTTP 403 "SSL required" is
  the expected pass condition - requireSSL is on by default and no
  HTTPS binding exists yet, which is deliberately deferred work, not a
  defect).
- [ ] `dc/New-AiDeployLabCertTemplates.ps1` — `lab-*` copies of every
  existing certificate template, 2-year validity instead of 5. Last run
  failed on a parse error (em dash in a string literal corrupted on
  transfer — retro #2, fixed) and also needs a fresh run against the
  new CA.
- [ ] `dc/Install-AiDeployDNS.ps1` — forwarder (`192.168.0.254`) and
  reverse lookup zone (`192.168.0.0/22`) on top of the DNS role
  `Install-AiDeployForest.ps1` already installed.
