# Spec 007: Onboard an Ubuntu VM

**Status:** Ready
**Date:** 2026-10-21
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
  message if unreachable (refused and timed-out told apart).
- **R2** The system MUST authenticate using Key B as `masterchief`,
  and fail with a specific message if authentication is rejected.
- **R3** The system MUST verify password authentication is actually
  disabled on the target (not just that key auth worked) and fail
  loudly if it isn't - Ubuntu's real risk is cloud-init silently
  re-enabling it, the way spec 001's is the wrong default shell.
- **R4** The system MUST check whether the target is already in
  Ansible inventory (matched by inventory name or IP) before making
  changes. If it is, it MUST still run every check: all pass -> exit
  cleanly reporting "already onboarded", inventory unchanged; any
  fail -> fail naming that check and leave the existing entry
  untouched. If the name matches an entry with a different IP, or the
  IP matches an entry with a different name, it MUST fail without
  changing inventory, naming the conflicting entry (as spec 001,
  decided 2026-10-21).
- **R5** The system MUST add a new target to Ansible inventory under the
  operator-given inventory name, with `ansible_host` set to the
  operator-given IP, `ansible_connection: ssh` and
  `ansible_user: masterchief`.
- **R6** The system MUST confirm Ansible itself can reach the target
  through the new inventory entry (a ping-equivalent module), not just
  that raw SSH worked. If that check fails on a new target, the system
  MUST leave inventory exactly as it was before the run and fail
  naming the Ansible-connectivity check (as spec 001, decided
  2026-10-21).
- **R7** The system SHOULD report which specific step failed when
  onboarding doesn't succeed, each check with its own name.
- **R8** The system MUST verify the authenticated session is
  `masterchief` and that it can use sudo without a password (Ansible's
  privilege escalation needs it), and fail with a specific message
  naming the fix if either isn't true (Ubuntu's counterpart to spec
  001's identity/admin check, decided 2026-10-21).
- **R9** The system MUST handle the target's SSH host key as
  trust-on-first-use: a host with no known key has its key recorded on
  first onboarding; a changed key MUST fail with a specific message
  naming how to clear the old key, and MUST never be replaced (as spec
  001, decided 2026-10-21).
- **R10** The system MUST take two inputs from the operator: the
  target's IP and its inventory name (as spec 001, decided 2026-10-21).

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
  target appears in Ansible inventory with the R5 values and an
  Ansible ping-equivalent module against it succeeds.
- **AC6** (R8) Given a target where `masterchief` can't use sudo without
  a password, when onboarding runs, then it fails identifying the
  identity/sudo check and naming the fix.
- **AC7** (R6) Given a new target that passes the raw SSH checks but
  fails the Ansible ping-equivalent through the new entry, when
  onboarding runs, then inventory is byte-for-byte as it was before
  the run and the failure names the Ansible-connectivity check.
- **AC8** (R4) Given a target already in inventory that now fails one
  of the checks, when onboarding runs again, then it fails naming that
  check and the existing entry is unchanged.
- **AC9** (R4) Given an inventory name already used for a different IP
  (or an IP already listed under a different name), when onboarding
  runs, then it fails naming the conflicting entry and inventory is
  unchanged.
- **AC10** (R9) Given a target whose SSH host key differs from the one
  recorded on ai-deploy, when onboarding runs, then it fails with a
  host-key-mismatch message naming how to clear the old key, and the
  recorded key is unchanged.
- **AC11** (R9) Given a target with no recorded host key, when
  onboarding runs successfully, then its host key is recorded.
- **AC12** (R10) Given onboarding is run without an IP or without an
  inventory name, when it starts, then it fails before any network
  activity with a usage message naming the missing input.

## 7. Constraints
- The brief's principles (idempotent, hypervisor-agnostic,
  verify-don't-assume, no bespoke agent software on targets).
- Same inventory as spec 001 (`~/.config/ai-deploy/inventory/`, one file
  per host) - a name or IP is unique across Windows and Ubuntu
  entries alike.
- Test targets: the Ubuntu slots of spec 009 (9201-9210, cloned from
  `tmpl-ubuntu2604`) - a clone was verified 2026-10-21 to have Key B
  for `masterchief`, passwordless sudo, and its own host key. No
  product test may require the lab (`AGENTS.md`): tests take any
  target IP.

## 8. Open questions
- [x] Exact Ansible module for R6 (likely `ping`, the Linux
      equivalent of spec 001's `win_ping`) - deferred to plan.md.
- [x] How R3 is verified from outside (e.g. the auth methods the server
      offers, or `sshd -T` via sudo) - deferred to plan.md.

---
### Ready checklist
- [x] Problem and goal make sense to someone without context
- [x] Every requirement is testable (no "fast", "easy", "robust" without a number)
- [x] Every MUST has at least one acceptance criterion
- [x] Non-goals list at least one thing someone might reasonably assume is in scope
- [x] No implementation detail (that goes in plan.md)
- [x] Doesn't contradict the brief's principles or non-goals
- [x] Open questions resolved or deferred
