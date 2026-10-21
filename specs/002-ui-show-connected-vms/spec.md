# Spec 002: UI - connected VMs + Validate/Onboard actions

**Status:** Draft
**Date:** 2026-10-20
**Brief:** [../../BRIEF.md](../../BRIEF.md) · **Roadmap item:** 002

## 1. Problem
Onboarding currently only reports success or failure through the
conversation/console - there's no persistent, at-a-glance view of
which VMs are actually onboarded, matching the brief's Shape
("a UI on ai-deploy shows which VMs are connected/onboarded").

## 2. Goal
Looking at the UI shows exactly which VMs are currently onboarded,
reflecting Ansible inventory's real state, and lets the operator
Validate or Onboard a target from the same page using spec 001's
onboarding logic.

## 3. Non-goals
- Not a general-purpose dashboard - no metrics, logs, or deployment
  status beyond onboarding state (brief's Shape is explicit about this).
- Does not reimplement onboarding checks - Validate/Onboard call spec
  001's (and later 007's) existing logic, they don't duplicate it.
- No multi-user access control - login is spec 000's single-operator
  PAM auth; this page adds no roles or permissions.

## 4. User scenarios
- As the operator, I want to see which VMs are onboarded without
  re-running onboarding or reading raw inventory files.
- As the operator, if a VM was onboarded but is now unreachable, I
  want that reflected, not a stale "connected" status.

## 5. Requirements
- **R1** The system MUST show every VM currently in Ansible inventory
  as onboarded by this product.
- **R2** The system SHOULD distinguish "onboarded and currently
  reachable" from "onboarded but not currently reachable."
- **R3** (moved from spec 001 R8, 2026-10-21) The UI MUST expose a
  "Validate" action that runs spec 001's R1-R3 checks against a target
  and shows pass/fail per check, without performing R4-R6 - a target
  is never added to inventory by Validate alone, even if every check
  passes.
- **R4** (moved from spec 001 R9, 2026-10-21) The UI MUST expose an
  "Onboard" action that performs spec 001's full R1-R6 flow and
  displays the result, with the same per-step failure detail as
  spec 001's R7.

## 6. Acceptance criteria
- **AC1** (R1) Given 2 onboarded VMs in inventory, when the UI loads,
  then both appear.
- **AC2** (R1) Given a VM is onboarded then removed from inventory
  (out of scope how - manual edit or future un-onboard feature), when
  the UI reloads, then it no longer appears.
- **AC3** (R3) Given a target that would fail onboarding (e.g.
  unreachable), when "Validate" is clicked, then the UI shows which
  check failed, and the target is NOT added to inventory.
- **AC4** (R3) Given a target that would pass every check, when
  "Validate" is clicked, then the UI shows all checks passing, and the
  target is still NOT added to inventory - Validate never onboards.
- **AC5** (R4) Given a correctly prepared target, when "Onboard" is
  clicked, then the target appears in inventory and an Ansible
  ping-equivalent succeeds (spec 001's AC5), displayed in the UI.

## 7. Constraints
- Depends on spec 000 (UI foundation) and spec 001 (onboarding logic)
  both reaching Accept first.

## 8. Open questions
- [x] What renders this UI - resolved by spec 000's stack decision
      (FastAPI + htmx/Alpine.js; this page is served by that same
      foundation, not a separate web server).
- [x] How reachability is checked, and this feature's detailed
      behavior - **still explicitly deferred by the user (2026-10-20)
      until at least one VM is actually onboarded**, so the page gets
      designed against real data instead of guesses. Revisit once
      spec 001 or 007 reaches Accept.

---
### Ready checklist
- [ ] Problem and goal make sense to someone without context
- [x] Every requirement is testable (no "fast", "easy", "robust" without a number)
- [x] Every MUST has at least one acceptance criterion
- [x] Non-goals list at least one thing someone might reasonably assume is in scope
- [x] No implementation detail (that goes in plan.md)
- [x] Doesn't contradict the brief's principles or non-goals
- [ ] Open questions resolved or deferred - **NOT ready**, 3 real open questions (UI tech, reachability-check mechanism, hosting) were never actually discussed beyond the brief's one-line Shape description.
