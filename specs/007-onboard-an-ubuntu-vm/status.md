# Status 007: Onboard an Ubuntu VM

**Stage:** Develop
**Last reconciled:** 2026-10-21
**Next:** T10 - operator copies template candidate 9202 back to 9001; then agent re-clones 9201, runs full suite incl. destructive, -> Test - waiting on operator

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
