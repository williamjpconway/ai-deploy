# Product Brief: ai-deploy

**Status:** Agreed
**Last revised:** 2026-10-21

## 1. One-liner
A Claude-Code-enabled control VM for a home lab: it onboards existing
VMs as verified Ansible targets, then runs a fixed set of day-2 lab
operations against them (AD users/groups, DNS records, certificates,
terminal access).

## 2. Shape
A control-plane VM (Ubuntu, Claude Code installed) that connects via SSH
to existing, already-installed VMs. Two jobs:
- **Onboard**: verify SSH/credentials/user/shell and add the VM to
  Ansible inventory. No VM provisioning, no hypervisor API access, no
  OS installation. (The agent's own test tooling is the one exception -
  see section 7.)
- **Operate**: run a fixed, named set of day-2 operations against
  onboarded VMs via Ansible playbooks - AD users/groups, DNS records
  and certificates on the DC, plus a browser terminal to any onboarded
  VM.
Operations are driven from a Claude Code conversation or a web UI on
ai-deploy. The UI shows onboarding state and triggers the named
operations - it is not a general-purpose dashboard or monitoring tool.

## 3. Infrastructure
None at the hypervisor level. ai-deploy only needs network/SSH
reachability to target VMs via their pre-baked SSH key(s); how or where
those VMs were created is out of scope for this product. For the
Windows Domain Controller / CA / DNS target specifically, a domain
account with Domain Admin rights is required to run the AD, DNS and
certificate playbooks (see `AGENTS.md` for scope and the known-risk
note on that privilege level).

Test infrastructure only: the agent may clone, reset and remove its own
test VMs on Proxmox (spec 009) through an API token scoped to two
templates and four fixed VM slots. The product never uses this access.

## 4. Problem
There's no repeatable, agent-driven way to take a VM that already exists
and bring it into Ansible's inventory as a verified, ready target -
someone has to manually SSH in, confirm it's reachable and configured as
expected, and add it to inventory by hand for every new VM. Routine lab
chores after that (a DNS record, a service account, a group, a TLS
certificate) are also done by hand in DNS Manager, ADUC and the CA
console, with no record and no idempotency.

## 5. Users
One operator, `masterchief`, managing a home lab.

## 6. Principles
- Idempotent: onboarding a VM or running an operation twice is safe and
  lands in the same state - never a duplicate inventory entry, record,
  user or certificate, and never an error on re-run.
- Hypervisor-agnostic: onboarding works the same whether the VM came
  from Proxmox, vCenter, or anywhere else - never branches logic on
  where the VM came from. Test VMs from the Proxmox test lab are
  ordinary targets to the product - no product code knows or checks
  that a target is a test VM.
- Verify, don't assume: onboarding always confirms the target is
  actually reachable and matches the expected user/shell setup before
  marking it onboarded - never adds it to inventory on faith.
- No bespoke agent software on targets: everything relies on SSH +
  Ansible, which already exist - never installs new persistent
  software on a target VM to make onboarding or an operation work.
- Writes are confirmed: any operation that changes a target (AD, DNS,
  certificates, anything destructive) needs an explicit operator
  confirmation - nothing that writes runs unattended.

## 7. Non-goals (product level)
- No VM provisioning or lifecycle management (create/delete/power) on
  any hypervisor - this product only works with VMs that already exist.
  Exception: the agent's test tooling (spec 009) - at most 2 Windows +
  2 Ubuntu test VMs, cloned from fixed templates, never any other VM.
  This is development tooling, not a product feature.
- No application/stack deployment (GitOps or otherwise) - day-2
  operations are limited to lab infrastructure services (AD, DNS,
  certificates, terminal access), not deploying workloads onto VMs.
- No open-ended operations - only the named operations on the roadmap;
  a new operation is a new roadmap item, never an ad-hoc playbook.
- Not a monitoring or metrics dashboard.
- Onboarded VMs don't run their own Claude Code instance - control flows
  one-way from ai-deploy via SSH/Ansible, not peer agents.

## 8. Success looks like
- Pointing ai-deploy at a fresh VM's IP/hostname results in it
  appearing in Ansible inventory as a verified target, in one
  command/conversation.
- Running onboarding twice on the same VM is a no-op the second time,
  not a duplicate or an error.
- Onboarding fails loudly (not silently) if SSH access, the expected
  user, or the expected shell doesn't match what's assumed.
- Each day-2 operation (DNS record, AD user/group, certificate) is one
  confirmed action, and re-running it is a no-op.
