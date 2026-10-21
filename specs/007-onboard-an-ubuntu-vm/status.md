# Status 007: Onboard an Ubuntu VM

**Stage:** Develop
**Last reconciled:** 2026-10-21
**Next:** Test run 3 not clean (stop condition) - operator decides: T14 then run 4, or accept with T14 open - waiting on operator

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
- 2026-10-21 - T1-T9 done: shared core refactor (001 suite green), onboard-ubuntu with identity/sudo + password-auth checks, testlab snapshot helper; 73 tests pass, AC3 + AC6 passed for real on slot 9201; found sshd PerSourcePenalties lockout -> ai-deploy exempted in initialize-ssh-onboarding.sh (T10, template copy-back pending)
- 2026-10-21 - T10 done: template 9001 copied back, 9201 re-cloned (carries the PerSourcePenalties exemption); 73 pass + 2 Ubuntu destructive pass, dc destructive not run; full suite passed across two runs, not one, because the slot changed DHCP IP (.83 -> .84) mid-run - operator accepted; per-slot DHCP reservations suggested for 009 -> Test
- 2026-10-21 - Test run 1 (2 blocking, lab tooling) -> T11-T12; Test run 2 (1 blocking, AC3 fixture) -> T13; all fixed and proven live on 9201 - Windows destructive AC3 to run on slot 9101 after a domain join, not dc; join-only account deferred, 9101 join uses the administrator credential with operator confirmation; stopped: auto mode blocked the join and the run 3 suite
- 2026-10-21 - Test run 3: 9101 domain-joined (operator-confirmed) and 001 AC3 passed on it; 118 + 2 Ubuntu destructive pass; review 1 blocking (AC3 fixture has no slot guard, advisory in runs 1-2) -> T14 added; stopped at run-3 stop condition
