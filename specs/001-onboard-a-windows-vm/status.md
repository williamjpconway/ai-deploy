# Status 001: Onboard a Windows VM

**Stage:** Develop
**Last reconciled:** 2026-10-21
**Next:** fix tasks T9-T11 (Test run 1 findings 1-3) - waiting on agent

<!-- Stage: Plan | Develop | Test | Accept. Gates, reconciliation and
     bookkeeping rules: see LIFECYCLE.md. Progress lives here only. -->

## Gates
| Gate | Touchpoint | Who | Date | Result |
|------|------------|-----|------|--------|
| G1 | Start | masterchief | 2026-10-21 | Started |
| G2 | Spec Ready | masterchief | 2026-10-21 | Ready |
| G3 | Plan approved -> Develop | masterchief | 2026-10-21 | Approved |
| G4 | Accept / reject | masterchief | | |

## Work log
<!-- One line per session, newest last. Never edit old lines.
     - YYYY-MM-DD - what was done - what was decided -->
- 2026-10-20 - Spec written (Draft)
- 2026-10-21 - Lifecycle rework: status.md added - UI Validate/Onboard (R8-R9, AC6-AC8) moved to spec 002; 001 is now CLI-only and first on the roadmap
- 2026-10-21 - Spec challenged to Ready (R9 host keys, R10 inputs, R4/R6 failure paths, AC6 reworded, AC7-AC12 added); plan.md + tasks.md written - Python + pytest, inventory in ~/.config/ai-deploy/inventory/, push+pull to ai-deploy, ruff checks, non-destructive tests vs 192.168.3.1; G2 + G3 approved
- 2026-10-21 - Develop started at ccec810
- 2026-10-21 - T1-T4, T6-T8 done: 23 tests pass (unit + live vs dc 192.168.3.1), ruff clean; masterchief added to BUILTIN\Administrators on dc by operator; auth/identity errors now name the exact fix - T5 open: AC3 destructive run approved but blocked by auto mode
