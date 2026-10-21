# Status 001: Onboard a Windows VM

**Stage:** Test
**Last reconciled:** 2026-10-21
**Next:** Test run 3 in progress - waiting on agent

<!-- Stage: Plan | Develop | Test | Accept. Gates, reconciliation and
     bookkeeping rules: see LIFECYCLE.md. Progress lives here only. -->

## Gates
| Gate | Touchpoint | Who | Date | Result |
|------|------------|-----|------|--------|
| G1 | Start | masterchief | 2026-10-21 | Started |
| G2 | Spec Ready | masterchief | 2026-10-21 | Ready |
| G3 | Plan approved -> Develop | masterchief | 2026-10-21 | Approved |
| G4 | Accept / reject | masterchief | 2026-10-21 | Rejected -> Develop: "can we fix any of the advisory findings now?" - fix the clearer-errors group (run 2 advisory #1, #3b, #6, #7) |

## Work log
<!-- One line per session, newest last. Never edit old lines.
     - YYYY-MM-DD - what was done - what was decided -->
- 2026-10-20 - Spec written (Draft)
- 2026-10-21 - Lifecycle rework: status.md added - UI Validate/Onboard (R8-R9, AC6-AC8) moved to spec 002; 001 is now CLI-only and first on the roadmap
- 2026-10-21 - Spec challenged to Ready (R9 host keys, R10 inputs, R4/R6 failure paths, AC6 reworded, AC7-AC12 added); plan.md + tasks.md written - Python + pytest, inventory in ~/.config/ai-deploy/inventory/, push+pull to ai-deploy, ruff checks, non-destructive tests vs 192.168.3.1; G2 + G3 approved
- 2026-10-21 - Develop started at ccec810
- 2026-10-21 - T1-T4, T6-T8 done: 23 tests pass (unit + live vs dc 192.168.3.1), ruff clean; masterchief added to BUILTIN\Administrators on dc by operator; auth/identity errors now name the exact fix - T5 open: AC3 destructive run approved but blocked by auto mode
- 2026-10-21 - T5 done (AC3 passed on dc, operator-run); Test run 1 not clean (3 blocking) -> T9-T11 fixed; Test run 2 clean, 27 tests pass, ruff clean, 10 advisory findings open - waiting on G4
