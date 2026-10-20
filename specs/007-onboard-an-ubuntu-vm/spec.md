# Spec 007: Onboard an Ubuntu VM

**Status:** Draft
**Date:** 2026-10-20
**Brief:** [../../BRIEF.md](../../BRIEF.md) · **Roadmap item:** 007

## 1. Problem
Same gap as onboarding a Windows VM (spec 001), for Ubuntu targets:
no repeatable, agent-driven way to bring an Ubuntu VM into Ansible
inventory as a verified target. Ubuntu's own confirmed gotcha is
different from Windows's - cloud-init can silently re-enable password
authentication on re-run, overriding the hardened config.

## 2. Goal
Pointing ai-deploy at an Ubuntu VM's address and credentials results
in it being added to Ansible inventory as a verified target, or a
clear, specific failure if it isn't actually ready.

## 3. Non-goals
- Does not create the `masterchief` user, install the SSH key, or
  harden sshd against password auth - that's
  `utils/onboarding/ubuntu2604/initialize-ssh-onboarding.sh`, run once
  before the VM becomes a template. Onboarding assumes that's already
  true and verifies it, but never configures it (mirrors spec 001's
  same non-goal for Windows).
- Does not onboard Windows VMs (spec 001, separate).
- Does not deploy anything to the VM once onboarded (brief non-goal).

## 4. User scenarios
- As the operator, I want to point ai-deploy at a prepared Ubuntu VM
  so that it becomes a ready Ansible target without me hand-editing
  inventory.
- As the operator, if I run onboarding against the same VM twice, I
  want the second run to be a no-op, not a duplicate entry or an error.
- As the operator, if the VM's SSH is unreachable, the login fails, or
  password authentication turns out to still be enabled (the
  cloud-init re-run risk noted in `AGENTS.md`), I want a specific error
  naming which check failed.

## 5. Requirements
- **R1** The system MUST check TCP reachability to the target's SSH
  port before attempting authentication, and fail with a specific
  message if unreachable.
- **R2** The system MUST authenticate using Key B as `masterchief`,
  and fail with a specific message if authentication is rejected.
- **R3** The system MUST verify password authentication is actually
  disabled on the target (not just that key auth worked) and fail
  loudly if it isn't - mirrors spec 001's shell-verification
  requirement, but for Ubuntu's actual risk (cloud-init silently
  re-enabling it) rather than Windows's (wrong default shell).
- **R4** The system MUST check whether the target is already a
  verified entry in Ansible inventory before making changes, and if
  so, exit cleanly reporting "already onboarded."
- **R5** The system MUST add a new target to Ansible inventory with
  `ansible_connection: ssh` and the correct `ansible_user`.
- **R6** The system MUST confirm Ansible itself can reach the target
  through the newly-written inventory entry (e.g. a ping-equivalent
  module).
- **R7** The system SHOULD report which specific step failed when
  onboarding doesn't succeed.

## 6. Acceptance criteria
- **AC1** (R1) Given a target with SSH blocked or unreachable, when
  onboarding runs, then it fails identifying the reachability check.
- **AC2** (R2) Given a target where Key B isn't installed for
  `masterchief`, when onboarding runs, then it fails identifying the
  authentication check.
- **AC3** (R3) Given a target where password authentication is
  enabled (e.g. after a cloud-init re-run reverted the hardening),
  when onboarding runs, then it fails identifying the password-auth
  check, rather than succeeding on key auth alone.
- **AC4** (R4) Given a target already onboarded and still passing all
  checks, when onboarding runs again, then it exits reporting
  "already onboarded" and inventory is unchanged.
- **AC5** (R5, R6) Given a correctly prepared target (per
  `initialize-ssh-onboarding.sh`), when onboarding runs, then the
  target appears in Ansible inventory and an Ansible ping-equivalent
  module against it succeeds.

## 7. Constraints
- None beyond the brief's principles.

## 8. Open questions
- [x] Exact Ansible module for R6 (likely `ping`, the Linux
      equivalent of spec 001's `win_ping`) - deferred to plan.md.

---
### Ready checklist
- [x] Problem and goal make sense to someone without context
- [x] Every requirement is testable (no "fast", "easy", "robust" without a number)
- [x] Every MUST has at least one acceptance criterion
- [x] Non-goals list at least one thing someone might reasonably assume is in scope
- [x] No implementation detail (that goes in plan.md)
- [x] Doesn't contradict the brief's principles or non-goals
- [x] Open questions resolved or deferred
