# Tasks 007: Onboard an Ubuntu VM

<!-- Small, ordered steps. T1 is always the AC tests. A task is ticked
     only when the tests for the ACs it covers pass (T1: when every AC
     test exists and fails for the expected reason). -->

- [x] **T1** Write a test for every AC in spec.md - unit (stubbed runner), live against `AI_DEPLOY_TEST_TARGET_UBUNTU`, destructive AC3, lab-destructive AC6 - plus an empty `bin/onboard-ubuntu`; run them on `ai-deploy` and confirm each fails for the expected reason, while 001's suite still passes (covers AC1-AC12)
- [x] **T2** Refactor `onboard/` into shared core + Windows profile (`profiles.py`, `windows.py`), no behaviour change - 001's full suite green before and after (regression gate for 001; no 007 AC)
- [x] **T3** Ubuntu profile, `onboard-ubuntu` CLI, `ubuntu` inventory group; usage, conflicts across both OSes, reachability (covers AC12, AC9, AC1)
- [x] **T4** Ubuntu auth-failure text and `identity` probe (id + passwordless sudo); host-key path through the shared SSH call (covers AC2, AC6 unit, AC10, AC11)
- [x] **T5** `password-auth` check from the server's offered methods; destructive AC3 run (covers AC3)
- [x] **T6** `ansible.builtin.ping` through staged / real inventory, rollback, existing-entry path (covers AC5, AC7, AC4, AC8)
- [x] **T7** `testlab/proxmox.py` snapshot helper and the lab-destructive AC6 run on a slot (covers AC6)
- [x] **T8** `AGENTS.md` (run/test commands), Ubuntu prep README; full suite (001 + 007) + `ruff check` + `ruff format --check` clean on `ai-deploy` (covers AC1-AC12)
- [x] **T9** (fix, Develop finding) A connection reset during the SSH handshake is reported as `[ssh]` naming the target's PerSourcePenalties block and the fix, for both profiles; unit tests (covers AC1, AC2 messaging; R7)
- [x] **T10** (fix, Develop finding) `initialize-ssh-onboarding.sh` adds `PerSourcePenaltyExemptList` for ai-deploy (192.168.3.2) to the keys-only sshd config, idempotently, with `--dry-run`; applied to slot 9201, then template 9001 re-sealed via a slot and copied back by the operator; full Ubuntu live suite passes in one run (covers AC10, AC2, AC8 together)
- [x] **T11** (fix, run 1 - review finding 2) `testlab/proxmox.py` refuses any VMID outside 9101-9110 / 9201-9210 before calling the API; unit test that an out-of-range VMID raises without a network call (covers AC6 test tooling)
- [x] **T12** (fix, run 1 - review finding 1) AC6 lab fixture asserts the slot's guest-agent IP equals `AI_DEPLOY_TEST_TARGET_UBUNTU` before snapshotting or breaking anything; mismatch fails with nothing changed (covers AC6)
- [x] **T13** (fix, run 2 - review finding 1) AC3 fixture puts the drop-in + restart inside the `try:`, so the drop-in is always removed and sshd restarted, even if the setup restart fails (covers AC3)
