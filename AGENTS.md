# Agent Rules

Read this at the start of every session. Every rule should trace back to an entry in `retro.md`.

## Project
- Stack: <fill in once you've chosen the target app>
- Run tests: `<command>`
- Run the app: `<command>`

## Tools
- Prefer an established tool over a bespoke script wherever one already
  covers the need: Terraform (or OpenTofu) for provisioning infra,
  Ansible for configuring it. Reach for a custom script only when no
  suitable tool exists, and say why in the plan when that's the case.
- Keep provisioning (Terraform) and configuration (Ansible) separate —
  don't let one do the other's job.
- The execution VM already has Terraform/OpenTofu and Ansible installed —
  don't install, bootstrap, or version-check them; just use what's there.

## Infrastructure access
<!-- Fill in once BRIEF.md's Infrastructure section names a real resource.
     One block per infra target. See skills/brief-intake for how this
     gets populated during the brief conversation. -->
- Proxmox (ai-control homelab, single node `pve`):
  - Endpoint: `https://192.168.0.199:8006/`, reached directly over the flat lab LAN (192.168.0.0/22), no VPN. TLS is self-signed by design (`insecure = true` in the provider) — not a misconfiguration to fix.
  - Credentials: a dedicated API token (not `root@pam`), stored as `LAB_PROXMOX_API_TOKEN` in `~/.config/homelab/lab.env` (mode 600, full `user@realm!id=secret` form). `scripts/tf.sh` reads it and exports it as `PROXMOX_VE_API_TOKEN` (the bpg provider's var) for that one process only. Never print, cat, grep, log, or commit that file or its contents.
  - Scope — **known risk, not yet fixed**: no resource pool isolation exists. The token's `TerraformVM` role is granted on `/` with propagation (VM.Allocate/Clone/PowerMgmt/Audit, VM.Config.*, Datastore.AllocateSpace/Audit, Pool.Audit, SDN.Use, Sys.Audit — no `Sys.Modify`/`Permissions.Modify`), and privilege separation on the token itself is off. It can technically reach anything in the cluster. Until the homelab repo adds a pool-scoped role, the off-limits list below is the *only* real boundary — treat it as absolute.
  - Off-limits, no exceptions: the `ai-control` VM itself (it runs the agent and the UI — the token's `/` scope could delete or power it off), and templates `9000`/`9001` (golden images). Everything else must already be listed in `stack.yml`; touching anything not in `stack.yml` needs the user's explicit approval first.
  - Tooling: provisioning/config already exists in `/home/masterchief/homelab` — Terraform (`bpg/proxmox` ~>0.116, local state at `~/.local/state/homelab/terraform.tfstate`, never committed) plus Ansible (`ansible/playbooks/*`, run via `python3 -I scripts/lab-run.py --`). Use the existing wrapper scripts (`scripts/vm.sh`, `scripts/tf.sh`) — never call raw `terraform apply`/`ansible-playbook` directly, and never hand-edit `stack.yml`, Terraform state, or the generated Ansible inventory.
  - SSH access: the public key is baked into templates `9000` (Ubuntu) and `9001` (Windows) at build time, not injected per-VM — cloud-init/cloudbase-init only set IP, DNS, and (on Ubuntu) hostname. One shared private key, `~/.ssh/lab_agent` on `ai-control`, selected via `~/.ssh/config.d/lab.conf` for the lab's hosts.
  - Login: `masterchief` on Ubuntu (passwordless sudo), `Administrator` on Windows — both over SSH (Windows uses `ansible_shell_type: powershell`, not WinRM).
  - Shell on deployed VMs: bash/sh on Ubuntu, PowerShell on Windows — holds for every VM in this lab (no containers or minimal images).
  - Audit: VM create/delete and playbook/terminal runs are logged under `~/.local/state/homelab/runs/`; create/delete is also a git commit to `stack.yml`; Proxmox keeps its own task log. Nothing alerts on misuse and terminal keystrokes aren't recorded — don't assume a mistake gets caught automatically.
  - Rule: any destructive action, or anything touching the off-limits list, always requires explicit confirmation regardless of mode — this is the primary guardrail here, since the technical scope is wider than it should be.

## Workflow
- Read `BRIEF.md` first. Specs inherit its principles and non-goals.
- Work from `specs/NNN-*/tasks.md`, one task at a time.
- Don't write code for a feature until its `plan.md` has been approved.
- A task is done only when its acceptance criteria pass via `<test command>`.
- If the spec is ambiguous, stop and ask. Don't guess.

## Rules from retros
<!-- Add rules here as retro.md earns them. Format: - Rule. (retro #N) -->
