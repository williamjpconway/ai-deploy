# Status 007: Onboard an Ubuntu VM

**Stage:** Develop
**Last reconciled:** 2026-10-21
**Next:** build 007 - T1 (AC tests, confirm they fail) - waiting on agent

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
- 2026-10-21 - Lifecycle rework: status.md added
- 2026-10-21 - Spec brought to 001 parity and marked Ready; plan + tasks written - shared core with per-OS profiles, password-auth via offered methods, AC6 live via lab snapshot; G2 + G3 approved
- 2026-10-21 - Develop started at dfe1a84
