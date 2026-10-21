# Spec 001: Onboard a Windows VM

**Status:** Ready
**Date:** 2026-10-20
**Brief:** [../../BRIEF.md](../../BRIEF.md) · **Roadmap item:** 001

## 1. Problem
Bringing a Windows VM under Ansible management today means manually
SSHing in, checking the shell actually works, and hand-editing
inventory — and Windows specifically has two failure modes that aren't
obvious until hit: the OpenSSH firewall rule can be scoped to a profile
that doesn't match a domain-joined connection, and the default SSH
shell is `cmd.exe`, not PowerShell, until set explicitly. Neither is
visible from a successful `ssh` login alone.

## 2. Goal
Pointing ai-deploy at a Windows VM's address and credentials results in
it being added to Ansible inventory as a verified target, or a clear,
specific failure if it isn't actually ready.

Onboarding runs on ai-deploy against the target, and writes inventory
on ai-deploy. The SSH prep (`Initialize-SshOnboarding.ps1`) is baked
into the template and assumed already run (decided 2026-10-21); a copy
stays in `utils/onboarding/windows2025/` for re-running by hand if a VM
ever needs it.

## 3. Non-goals
- Does not install OpenSSH Server, fix its firewall profile, set the
  default shell, or install the SSH key on the target — that's
  `utils/onboarding/windows2025/Initialize-SshOnboarding.ps1`, run once
  before the VM becomes a template. Onboarding assumes that's already
  true (per the brief's Shape) and verifies it, but never configures it.
- Does not onboard Ubuntu VMs (roadmap item 007, separate spec).
- Does not deploy anything to the VM once onboarded (brief non-goal).
- Does not create the Ansible playbooks that will later run against
  this target (roadmap items 003-006).
- Does not provide a Terminal/shell-access action for onboarded VMs -
  that's spec 008, a distinct concern (a live interactive session vs.
  a one-shot validate/onboard action).
- Does not provide UI Validate/Onboard buttons - moved to spec 002
  (2026-10-21) so this spec is a CLI-only first slice with no
  dependency on spec 000.

## 4. User scenarios
- As the operator, I want to point ai-deploy at a prepared Windows VM
  so that it becomes a ready Ansible target without me hand-editing
  inventory.
- As the operator, if I run onboarding against the same VM twice, I
  want the second run to be a no-op, not a duplicate entry or an error.
- As the operator, if the VM's SSH is unreachable, the login fails, or
  the shell turns out not to be PowerShell, I want a specific error
  naming which check failed, not a generic timeout or silent partial
  success.

## 5. Requirements
- **R1** The system MUST check TCP reachability to the target's SSH
  port before attempting authentication, and fail with a specific
  message if unreachable (not a generic timeout).
- **R2** The system MUST authenticate using Key B as `masterchief`,
  and fail with a specific message if authentication is rejected.
- **R3** The system MUST verify the remote shell is actually PowerShell
  (not `cmd.exe`) by running a PowerShell-specific probe and checking
  its output, and fail loudly if it isn't.
- **R4** The system MUST check whether the target is already in
  Ansible inventory (matched by inventory name or IP) before making
  changes. If it is, it MUST still run every check (R1-R3, R6, R8,
  R9): all pass -> exit cleanly reporting "already onboarded", with
  inventory unchanged; any fail -> fail naming that check and leave
  the existing entry untouched (decided 2026-10-21). If the name
  matches an entry with a different IP, or the IP matches an entry
  with a different name, it MUST fail without changing inventory,
  naming the conflicting entry.
- **R5** The system MUST add a new target to Ansible inventory under
  the operator-given inventory name, with `ansible_host` set to the
  operator-given IP, `ansible_connection: ssh`,
  `ansible_user: masterchief`, and `ansible_shell_type: powershell`.
- **R6** The system MUST confirm Ansible itself can reach the target
  through the new inventory entry (e.g. a ping-equivalent module),
  not just that raw SSH worked in R1-R3. If that check fails on a new
  target, the system MUST leave inventory exactly as it was before
  the run and fail with a message identifying the Ansible-connectivity
  check (decided 2026-10-21).
- **R7** The system SHOULD report which specific step failed when
  onboarding doesn't succeed, matching R1/R2/R3/R6/R8/R9's distinct
  failure messages rather than one generic "onboarding failed."
- **R8** The system MUST verify the authenticated session is
  `masterchief` and has local admin rights on the target (member of
  its Administrators group), and fail with a specific message if
  either isn't true.
- **R9** The system MUST handle the target's SSH host key as
  trust-on-first-use: a host with no known key has its key recorded
  on first onboarding; a host whose presented key differs from the
  recorded one MUST fail with a specific host-key-mismatch message
  naming how to clear the old key, and MUST never replace the
  recorded key itself (decided 2026-10-21).
- **R10** The system MUST take two inputs from the operator: the
  target's IP and its inventory name (e.g. `dc`) (decided 2026-10-21).

## 6. Acceptance criteria
- **AC1** (R1) Given a target with SSH blocked or unreachable, when
  onboarding runs, then it fails with a message identifying the
  reachability check, not a generic connection timeout.
- **AC2** (R2) Given a target where Key B isn't accepted for
  `masterchief` - either Key B isn't in `administrators_authorized_keys`
  or `masterchief` isn't in the target's Administrators group (sshd only
  reads that file for Administrators members, so the two look identical
  from outside) - when onboarding runs, then it fails with a message
  identifying the authentication check and naming both likely causes.
- **AC3** (R3) Given a target whose default SSH shell is `cmd.exe`
  (not PowerShell), when onboarding runs, then it fails with a message
  identifying the shell-verification check, rather than succeeding or
  failing with an unrelated syntax error.
- **AC4** (R4) Given a target already onboarded and still passing all
  checks, when onboarding runs again, then it exits reporting
  "already onboarded" and inventory is unchanged.
- **AC5** (R5, R6) Given a correctly prepared target (per
  `Initialize-SshOnboarding.ps1`), when onboarding runs, then the
  target appears in Ansible inventory and an Ansible ping-equivalent
  module against it succeeds.
- **AC6** (R8) Given a session that authenticates but whose identity
  or admin probe reports something other than `masterchief` with
  Administrators membership, when onboarding runs, then it fails with
  a message identifying the identity/admin check. Under option 1 no
  real target can reach this state (a non-admin `masterchief` fails
  at AC2 instead), so this AC is tested with a stubbed probe result,
  not a modified VM (decided 2026-10-21).
- **AC7** (R6) Given a new target that passes R1-R3, R8 and R9 but
  fails the Ansible ping-equivalent through the new entry, when
  onboarding runs, then inventory is byte-for-byte as it was before
  the run and the failure names the Ansible-connectivity check.
- **AC8** (R4) Given a target already in inventory that now fails one
  of the checks, when onboarding runs again, then it fails naming that
  check and the existing entry is unchanged.
- **AC9** (R4) Given an inventory name already used for a different
  IP (or an IP already listed under a different name), when onboarding
  runs, then it fails naming the conflicting entry and inventory is
  unchanged.
- **AC10** (R9) Given a target whose SSH host key differs from the one
  recorded on ai-deploy, when onboarding runs, then it fails with a
  host-key-mismatch message naming how to clear the old key, and the
  recorded key is unchanged.
- **AC11** (R9) Given a target with no recorded host key, when
  onboarding runs successfully, then its host key is recorded on
  ai-deploy.
- **AC12** (R10) Given onboarding is run without an IP or without an
  inventory name, when it starts, then it fails before any network
  activity with a usage message naming the missing input.

## 7. Constraints
- The brief's principles (idempotent, hypervisor-agnostic,
  verify-don't-assume, no bespoke agent software on targets).
- Connection identity (decided 2026-10-21): `masterchief`, a member of
  the target's Administrators group, authenticating via Key B in
  `administrators_authorized_keys` (option 1 in `AGENTS.md`). That
  membership is a template/prep precondition - onboarding verifies it
  (R8) but never configures it. Connecting as `masterchief` is by
  convention only: any other Administrators member holding Key B could
  also authenticate. The per-user `authorized_keys` route stays an open
  risk, outside 001.

## 8. Open questions
- [x] Which Ansible module confirms connectivity through inventory
      (R6)? Deferred to plan.md - likely `win_ping`, confirmed during
      implementation.
- [x] Exact PowerShell probe command for R3 (e.g. `$PSVersionTable`)?
      Deferred to plan.md as an implementation detail.

---
### Ready checklist
- [x] Problem and goal make sense to someone without context
- [x] Every requirement is testable (no "fast", "easy", "robust" without a number)
- [x] Every MUST has at least one acceptance criterion
- [x] Non-goals list at least one thing someone might reasonably assume is in scope
- [x] No implementation detail (that goes in plan.md)
- [x] Doesn't contradict the brief's principles or non-goals
- [x] Open questions resolved or deferred
