# Spec 002: UI - show connected VMs

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
reflecting Ansible inventory's real state.

## 3. Non-goals
- Not a general-purpose dashboard - no metrics, logs, or deployment
  status beyond onboarding state (brief's Shape is explicit about this).
- Does not trigger onboarding itself - read-only visibility into state
  that roadmap items 001/007 produce.
- No authentication/multi-user access control - single operator (brief).

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

## 6. Acceptance criteria
- **AC1** (R1) Given 2 onboarded VMs in inventory, when the UI loads,
  then both appear.
- **AC2** (R1) Given a VM is onboarded then removed from inventory
  (out of scope how - manual edit or future un-onboard feature), when
  the UI reloads, then it no longer appears.

## 7. Constraints
-

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
