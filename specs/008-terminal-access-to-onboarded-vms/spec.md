# Spec 008: Terminal Access to Onboarded VMs

**Status:** Draft
**Date:** 2026-10-20
**Brief:** [../../BRIEF.md](../../BRIEF.md) · **Roadmap item:** 008

## 1. Problem
Once a VM is onboarded, there's no way to get a shell on it from the
UI without switching to a separate SSH client - deliberately split out
from spec 001 rather than bundled in, since a browser terminal is a
different class of problem (a live, interactive proxied session) from
a one-shot validate/onboard action.

## 2. Goal
From the UI, clicking "Terminal" on an onboarded VM opens a working,
interactive shell session to that VM in the browser.

## 3. Non-goals
- Does not add any new SSH access path - reuses Key B and whichever
  identity onboarding already connects as (per spec 001/007 and the
  `masterchief`-scoping decision in `AGENTS.md`).
- Does not persist terminal session history/logging beyond what the
  underlying SSH session itself would produce - no separate audit
  trail is built here, that's a distinct concern if ever needed.
- Does not support multiple simultaneous terminal sessions to the same
  VM from different browser tabs sharing one PTY - each session is
  independent.

## 4. User scenarios
- As the operator, I want to click a VM and get a working terminal to
  it, without opening a separate SSH client.
- As the operator, if the VM becomes unreachable mid-session, I want
  the terminal to show that clearly (connection closed), not hang.
- As the operator, closing the browser tab should end the session, not
  leave an orphaned connection to the target.

## 5. Requirements
- **R1** The system MUST open a real interactive shell session to the
  target VM when "Terminal" is clicked on an onboarded entry.
- **R2** The session MUST use the same SSH key and connecting identity
  already established for that VM by onboarding - no separate
  credential path.
- **R3** The session MUST close cleanly on the target when the browser
  tab/connection closes - no orphaned SSH sessions left running.
- **R4** A target that becomes unreachable mid-session MUST surface
  that in the terminal UI, not hang indefinitely.

## 6. Acceptance criteria
- **AC1** (R1) Given an onboarded VM, when "Terminal" is clicked, then
  a working shell session opens and commands can be run.
- **AC2** (R3) Given an open terminal session, when the browser tab is
  closed, then the corresponding SSH process/session on `ai-deploy` no
  longer exists shortly after.
- **AC3** (R4) Given an open session, when the target becomes
  unreachable, then the terminal UI shows the session ended, not a
  silent hang.

## 7. Constraints
- Depends on spec 000 (auth/foundation) existing first.
- Depends on at least one onboarding spec (001 or 007) actually
  working, since there's nothing to open a terminal to otherwise.

## 8. Open questions
- [x] Rendering/transport: `xterm.js` in the browser, proxied over a
      websocket to a PTY on `ai-deploy` running the actual `ssh`
      session - decided 2026-10-20 as part of spec 000's stack
      discussion. No Node.js needed - Python can drive a PTY over
      websockets directly.
- [ ] Exact PTY/websocket library choice on the backend - deferred to
      plan.md.

---
### Ready checklist
- [x] Problem and goal make sense to someone without context
- [x] Every requirement is testable (no "fast", "easy", "robust" without a number)
- [x] Every MUST has at least one acceptance criterion
- [x] Non-goals list at least one thing someone might reasonably assume is in scope
- [x] No implementation detail beyond the transport decision itself (that goes in plan.md)
- [x] Doesn't contradict the brief's principles or non-goals
- [x] Open questions resolved or deferred
