# Product Brief: ai-deploy

**Status:** Agreed
**Last revised:** 2026-10-20

## 1. One-liner
A Claude-Code-enabled control VM that onboards existing VMs as Ansible
targets, so they're ready for application deployments.

## 2. Shape
A control-plane VM (Ubuntu, Claude Code installed) that connects via SSH
to existing, already-installed VMs and onboards them — adds them to
Ansible inventory, verifies SSH/credentials work, confirms the expected
user/shell setup. No VM provisioning, no hypervisor API access, no OS
installation. Once onboarded, a VM is a ready Ansible target; what gets
deployed to it (a GitOps stack or anything else) is a separate concern,
out of scope for onboarding itself. A UI on ai-deploy shows which VMs
are connected/onboarded — visibility into onboarding state, not a
general-purpose dashboard.

## 3. Infrastructure
None at the hypervisor level. ai-deploy only needs network/SSH
reachability to target VMs via their pre-baked SSH key(s); how or where
those VMs were created is out of scope for this product. For the
Windows Domain Controller / CA / DNS target specifically, a domain
account with Domain Admin rights is required to run the AD, DNS and
certificate playbooks (see `AGENTS.md` for scope and the known-risk
note on that privilege level).

## 4. Problem
There's no repeatable, agent-driven way to take a VM that already exists
and bring it into Ansible's inventory as a verified, ready target —
someone has to manually SSH in, confirm it's reachable and configured as
expected, and add it to inventory by hand for every new VM.

## 5. Users
One operator, `masterchief`, managing a home lab.

## 6. Principles
- Idempotent: onboarding a VM twice is safe and lands in the same state
  — never a duplicate inventory entry or an error on re-run.
- Hypervisor-agnostic: onboarding works the same whether the VM came
  from Proxmox, vCenter, or anywhere else — never branches logic on
  where the VM came from.
- Verify, don't assume: onboarding always confirms the target is
  actually reachable and matches the expected user/shell setup before
  marking it onboarded — never adds it to inventory on faith.
- No bespoke agent software on targets: onboarding relies on SSH +
  Ansible, which already exist — it never installs new persistent
  software on the target VM just to make onboarding work.

## 7. Non-goals (product level)
<!-- TODO -->
- No VM provisioning or lifecycle management (create/delete/power) on
  any hypervisor — this product only onboards VMs that already exist.
- No application/stack deployment (GitOps or otherwise) — onboarding
  ends once a VM is a verified, ready Ansible target; what's deployed to
  it next is a separate concern.
- Onboarded VMs don't run their own Claude Code instance — control flows
  one-way from ai-deploy via SSH/Ansible, not peer agents.

## 8. Success looks like
- Pointing ai-deploy at a fresh VM's IP/hostname and credentials
  results in it appearing in Ansible inventory as a verified target, in
  one command/conversation.
- Running onboarding twice on the same VM is a no-op the second time,
  not a duplicate or an error.
- Onboarding fails loudly (not silently) if SSH access, the expected
  user, or the expected shell doesn't match what's assumed.
