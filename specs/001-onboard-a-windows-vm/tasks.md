# Tasks 001: Onboard a Windows VM

<!-- Small, ordered steps. T1 is always the AC tests. A task is ticked
     only when the tests for the ACs it covers pass (T1: when every AC
     test exists and fails for the expected reason). -->

- [x] **T1** Scaffolding (`pytest.ini`, `tests/conftest.py`, `.gitignore`, `ruff.toml`, empty `onboard/` package and `bin/onboard-windows` that exits non-zero) and a test for every AC in spec.md, unit and live per plan.md; run them on `ai-deploy` and confirm each fails for the expected reason - not an import or fixture error (covers AC1-AC12)
- [x] **T2** CLI args, exit codes, failure format, inventory loading and conflict detection (covers AC12, AC9)
- [x] **T3** TCP reachability check, refused vs timeout (covers AC1)
- [x] **T4** SSH runner with Key B, `BatchMode`, `accept-new` host keys; authentication and host-key failure mapping; clear the stale 192.168.3.1 entry on `ai-deploy` first (covers AC2, AC10, AC11)
- [x] **T5** PowerShell shell probe and identity/admin probe; run the AC3 destructive test only after operator confirmation (covers AC3, AC6)
- [x] **T6** Stage host file in temp inventory, `win_ping` through it, atomic commit or discard (covers AC5, AC7)
- [x] **T7** Existing-entry path: verify-only re-run, "already onboarded", no writes on failure (covers AC4, AC8)
- [x] **T8** `AGENTS.md` (Run tests / Checks / Run the app commands) and `install-ansible.sh` adds ruff via pipx with `--dry-run`; full suite + `ruff check` + `ruff format --check` clean on `ai-deploy` (covers AC1-AC12)
- [x] **T9** (fix, run 1) SSH timeout and other non-255 transport failures reported as `[ssh]`, never `[shell]`/`[identity]`; unit test for rc 124 (finding 1; covers AC3, AC6)
- [x] **T10** (fix, run 1) Commit never overwrites an existing host file (no-clobber link), and a lock spans conflict check -> commit; unit tests (finding 2; covers AC4, AC9)
- [x] **T11** (fix, run 1) AC9 name-taken test asserts the seeded conflicting IP (finding 3; covers AC9)
- [x] **T12** (fix, G4 reject) Check Key B before any network call: exists, readable, not group/world-accessible - else a named `[key]` failure naming the fix (run 2 advisory #1; covers AC2)
- [x] **T13** (fix, G4 reject) Unreadable/malformed inventory YAML -> named `[inventory]` failure; missing `ssh`/`ansible` binary -> named failure, never a traceback (run 2 advisory #3b; covers AC9, AC7)
- [x] **T14** (fix, G4 reject) `--port` range 1-65535 as a usage failure; host-key hint uses `[ip]:port` when port is not 22 (run 2 advisory #6; covers AC12, AC10)
- [x] **T15** (fix, G4 reject) known_hosts path with spaces passed safely to Ansible's ssh args (run 2 advisory #7; covers AC5)
