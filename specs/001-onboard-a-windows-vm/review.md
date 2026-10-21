# Review 001: Onboard a Windows VM

<!-- Created by skills/build-feature at the first Test run. One "Test run"
     section per run, appended - never overwritten. The Decision section is
     filled only by skills/accept-feature, at G4. -->

## Test run 1 - 2026-10-21
**Diff reviewed:** ccec810..70d54d6

### Tests
Command (on `ai-deploy`): `AI_DEPLOY_TEST_TARGET=192.168.3.1 python3 -m pytest` - 23 passed, 1 skipped (destructive; run separately by the operator: 1 passed)

| AC | Test | Result |
|----|------|--------|
| AC1 | live: refused (127.0.0.1:1), firewalled (dc:1), unroutable (192.0.2.1) | Pass |
| AC2 | live: throwaway key -> `[authentication]` naming both causes + fix commands | Pass |
| AC3 | unit: cmd.exe error, banner without marker; destructive: dc DefaultShell=cmd.exe, restored (operator-run, before/after powershell.exe) | Pass |
| AC4 | live: second run "already onboarded", inventory snapshot equal | Pass |
| AC5 | live: dc onboarded into temp inventory, R5 vars, independent win_ping | Pass |
| AC6 | unit: wrong account, no admin SID, suffix spoof, fix text | Pass |
| AC7 | unit + live: failing ansible, inventory byte-identical, staging dir removed | Pass |
| AC8 | live: seeded entry + throwaway key -> `[authentication]`, file unchanged | Pass |
| AC9 | unit: name taken / IP taken, no network, no change | Pass (test weak - finding 3) |
| AC10 | live: seeded wrong host key -> `[host-key]`, known_hosts unchanged | Pass |
| AC11 | live: empty known_hosts gains dc's key | Pass |
| AC12 | unit: missing --name / --ip, unsafe name, runner never called | Pass |

### Static checks
| Check | Command | Result |
|-------|---------|--------|
| ruff lint | `ruff check .` | All checks passed |
| ruff format | `ruff format --check .` | 78 files already formatted |

### Independent review
Reviewer inputs: `spec.md`, the diff above, the static check output - nothing else.

| # | Severity | Finding | Location | Status |
|---|----------|---------|----------|--------|
| 1 | blocking | SSH timeout (rc 124) / non-255 transport errors fall into probe parsing and are reported as `[shell]`/`[identity]` - wrong check named (R3, R7) | `onboard/checks.py` `ssh()` | open |
| 2 | blocking | `Staged.commit` `os.replace` overwrites an existing `<name>.yml` holding a different host (silent deletion); no lock across find->commit, so concurrent runs can both pass the conflict check (R4) | `onboard/inventory.py` | open |
| 3 | blocking | AC9 name-taken test asserts the requested name, which any message echoes - doesn't prove the conflicting entry is named | `tests/unit/test_inventory_conflict.py` | open |
| 4 | advisory | hidden `--port` not written as `ansible_port`; TOFU records `[ip]:port` | `cli.py`, `checks.py`, `inventory.py` | open |
| 5 | advisory | non-CheckFailed errors (missing ssh/ansible binary, bad YAML, mkdtemp permissions) give a traceback with no check name (R7, SHOULD) | `cli.py`, `runner.py`, `inventory.py` | open |
| 6 | advisory | missing local Key B shows "Permission denied" -> target-side causes; check the key file exists first | `checks.py` | open |
| 7 | advisory | `load_hosts` misses hosts nested under `children:`/`all:` | `inventory.py` | open |
| 8 | advisory | existing-entry path doesn't check the entry's vars match R5 | `cli.py` | open |
| 9 | advisory | `ANSIBLE_SSH_COMMON_ARGS` breaks on known_hosts paths with spaces; Ansible's ssh reads `~/.ssh/config`, raw checks don't | `checks.py` | open |
| 10 | advisory | reserved Ansible names (`all`, `windows`) pass the name pattern | `cli.py` | open |
| 11 | advisory | destructive test's restore failure should print the manual recovery command | `tests/live/test_destructive.py` | open |
| 12 | advisory | host key is recorded at first SSH call even if a later check fails (spec allows; document) | `checks.py` | open |

### Outcome
Not clean - back to Develop (fix tasks T9-T11 added to tasks.md)

## Decision
<!-- Accepted YYYY-MM-DD (masterchief)
     or Rejected YYYY-MM-DD (masterchief) -> Develop|Plan: <reason> -->
