# Spec 001: Onboard a Windows VM

**Status:** Draft
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
- **R2** The system MUST authenticate using Key B as the expected
  admin account, and fail with a specific message if authentication
  is rejected.
- **R3** The system MUST verify the remote shell is actually PowerShell
  (not `cmd.exe`) by running a PowerShell-specific probe and checking
  its output, and fail loudly if it isn't.
- **R4** The system MUST check whether the target is already a
  verified entry in Ansible inventory before making changes, and if
  so, exit cleanly reporting "already onboarded" rather than
  duplicating the entry or erroring.
- **R5** The system MUST add a new target to Ansible inventory with
  `ansible_connection: ssh`, the correct `ansible_user`, and
  `ansible_shell_type: powershell`.
- **R6** The system MUST confirm Ansible itself can reach the target
  through the newly-written inventory entry (e.g. a ping-equivalent
  module), not just that raw SSH worked in R1-R3.
- **R7** The system SHOULD report which specific step failed when
  onboarding doesn't succeed, matching R1/R2/R3's distinct failure
  messages rather than one generic "onboarding failed."
- **R8** (added 2026-10-20) The UI (spec 000) MUST expose a "Validate"
  action that runs R1-R3 against a target and shows pass/fail per
  check, without performing R4-R6 - a target is never added to
  inventory by Validate alone, even if every check passes.
- **R9** (added 2026-10-20) The UI MUST expose an "Onboard" action that
  performs the full R1-R6 flow and displays the result, with the same
  per-step failure detail as R7.

## 6. Acceptance criteria
- **AC1** (R1) Given a target with SSH blocked or unreachable, when
  onboarding runs, then it fails with a message identifying the
  reachability check, not a generic connection timeout.
- **AC2** (R2) Given a target where Key B isn't installed for the
  expected account, when onboarding runs, then it fails with a message
  identifying the authentication check.
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
- **AC6** (R8) Given a target that would fail onboarding (e.g.
  unreachable), when "Validate" is clicked in the UI, then the UI
  shows which check failed, and the target is NOT added to inventory.
- **AC7** (R8) Given a target that would pass every check, when
  "Validate" is clicked, then the UI shows all checks passing, and the
  target is still NOT added to inventory - Validate never onboards.
- **AC8** (R9) Given a correctly prepared target, when "Onboard" is
  clicked in the UI, then the same outcome as AC5 occurs, displayed in
  the UI.

## 7. Constraints
- None beyond the brief's principles (idempotent, hypervisor-agnostic,
  verify-don't-assume, no bespoke agent software on targets).
- R8/R9 depend on spec 000 (UI foundation) existing first - this spec
  can still reach Develop/Test on its non-UI requirements (R1-R7)
  independently, since those don't need a UI to exist.

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
