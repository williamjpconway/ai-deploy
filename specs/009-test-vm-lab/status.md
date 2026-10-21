# Status 009: Test VM lab

**Stage:** Plan
**Last reconciled:** 2026-10-21
**Next:** G2 - operator to confirm spec Ready (all open questions closed, checklist ticked), then write plan.md - waiting on operator

<!-- Stage: Plan | Develop | Test | Accept. Gates, reconciliation and
     bookkeeping rules: see LIFECYCLE.md. Progress lives here only. -->

## Gates
| Gate | Touchpoint | Who | Date | Result |
|------|------------|-----|------|--------|
| G1 | Start | masterchief | 2026-10-21 | Started |
| G2 | Spec Ready | masterchief | | |
| G3 | Plan approved -> Develop | masterchief | | |
| G4 | Accept / reject | masterchief | | |

## Work log
<!-- One line per session, newest last. Never edit old lines.
     - YYYY-MM-DD - what was done - what was decided -->
- 2026-10-21 - Feature created - agent-run disposable test VMs (2 Windows + 2 Ubuntu) on Proxmox, raised at 001's acceptance; Proxmox API user/token already set up and verified read-only by the operator
- 2026-10-21 - Plan: all 10 open questions closed (carve-out, confirmation exception, retail templates re-sealed + verified, rollback-only resets, AD prep names, plain DHCP, 10+10 slots); R9 skill, R10/AC7 prereq checks, R4 reworded; spec checklist ticked - G2 not yet confirmed, operator switched to 007
