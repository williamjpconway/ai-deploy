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

## Test run 2 - 2026-10-21
**Diff reviewed:** ccec810..b8eab26

### Tests
Command (on `ai-deploy`): `AI_DEPLOY_TEST_TARGET=192.168.3.1 python3 -m pytest` - 27 passed, 1 skipped (destructive AC3; passed in the operator-run confirmed run against dc, code under test unchanged since)

| AC | Test | Result |
|----|------|--------|
| AC1 | as run 1 | Pass |
| AC2 | as run 1 | Pass |
| AC3 | as run 1, plus SSH timeout reported as `[ssh]` not `[shell]` (fix T9) | Pass |
| AC4 | as run 1, plus run lock -> `[busy]` (fix T10) | Pass |
| AC5 | as run 1 | Pass |
| AC6 | as run 1 | Pass |
| AC7 | as run 1 | Pass |
| AC8 | as run 1 | Pass |
| AC9 | name-taken case now asserts the seeded IP (fix T11); occupied host file and mid-run file never overwritten (fix T10) | Pass |
| AC10 | as run 1 | Pass |
| AC11 | as run 1 | Pass |
| AC12 | as run 1 | Pass |

Fix tests T9/T10 were confirmed to fail against the pre-fix code (70d54d6).

### Static checks
| Check | Command | Result |
|-------|---------|--------|
| ruff lint | `ruff check .` | All checks passed |
| ruff format | `ruff format --check .` | 80 files already formatted |

### Independent review
Reviewer inputs: `spec.md`, the diff above, the static check output - nothing else. Run 1 blocking findings 1-3: fixed in run 2.

| # | Severity | Finding | Location | Status |
|---|----------|---------|----------|--------|
| 1 | advisory | Missing/unreadable/0644 Key B on ai-deploy reported as `[authentication]` with target-side causes; pre-check the key file (same as run 1 #6) | `onboard/checks.py` | open |
| 2 | advisory | New-host ping runs in a staging dir without the real inventory's `group_vars/`/`host_vars/` | `onboard/cli.py`, `inventory.py` | open |
| 3 | advisory | Conflict check misses `children:`/INI hosts; malformed YAML gives a traceback; IPs compared as strings (run 1 #5, #7) | `onboard/inventory.py` | open |
| 4 | advisory | "already onboarded" doesn't check the entry's vars match R5 (run 1 #8) | `onboard/cli.py` | open |
| 5 | advisory | Reserved names (`all`, `ungrouped`, `windows`) accepted (run 1 #10) | `onboard/cli.py` | open |
| 6 | advisory | Non-22 `--port`: wrong `ssh-keygen -R` hint, no range check (run 1 #4) | `onboard/checks.py`, `cli.py` | open |
| 7 | advisory | Spaces in known_hosts path break `ANSIBLE_SSH_COMMON_ARGS` (run 1 #9) | `onboard/checks.py` | open |
| 8 | advisory | Destructive test: confirmation is process-only; a non-zero Set-ItemProperty skips the restore (run 1 #11) | `tests/live/test_destructive.py` | open |
| 9 | advisory | `AI_DEPLOY_ANSIBLE` test hook in production code - document or rename | `onboard/checks.py` | open |
| 10 | advisory | Identity matched on account name only - local `HOST\masterchief` would pass | `onboard/checks.py` | open |

### Outcome
Clean - waiting on G4

## Test run 3 - 2026-10-21
**Diff reviewed:** ccec810..ccc597a (after G4 reject -> Develop, fix tasks T12-T15)

### Tests
Command (on `ai-deploy`): `AI_DEPLOY_TEST_TARGET=192.168.3.1 python3 -m pytest` - 40 passed, 1 skipped (destructive AC3; last operator-run pass was before T15 changed the ssh argv - the same ssh path is exercised live by AC2/AC5/AC10/AC11, which pass)

| AC | Test | Result |
|----|------|--------|
| AC1 | as run 2 | Pass |
| AC2 | as run 2, plus missing / unreadable / 0644 Key B -> `[key]` before any network call (T12) | Pass |
| AC3 | as run 2 | Pass (unit); destructive not re-run |
| AC4 | as run 2 | Pass |
| AC5 | as run 2, plus live onboard with a known_hosts path containing spaces (T15) | Pass |
| AC6 | as run 2 | Pass |
| AC7 | as run 2, plus missing binary -> `[prereq]` (T13) | Pass |
| AC8 | as run 2 | Pass |
| AC9 | as run 2, plus malformed / non-mapping inventory YAML -> `[inventory]`, unchanged (T13) | Pass |
| AC10 | as run 2, plus `'[ip]:port'` hint off port 22 (T14) | Pass |
| AC11 | as run 2 | Pass |
| AC12 | as run 2, plus `--port` outside 1-65535 -> `[usage]` (T14) | Pass |

All 13 new tests were confirmed failing before T12-T15 were implemented.

### Static checks
| Check | Command | Result |
|-------|---------|--------|
| ruff lint | `ruff check .` | All checks passed |
| ruff format | `ruff format --check .` | 82 files already formatted |

### Independent review
Reviewer inputs: `spec.md`, the diff above, the static check output - nothing else. Run 2 advisory #1, #3 (traceback part), #6, #7: fixed in run 3.

| # | Severity | Finding | Location | Status |
|---|----------|---------|----------|--------|
| 1 | advisory | Reserved names (`windows`, `all`, `ungrouped`, `localhost`) accepted; `--name windows` re-run pings the whole group | `onboard/cli.py` | open |
| 2 | advisory | Conflict check misses nested `children:` / INI inventory entries (R4 partly met for hand-edited inventory) | `onboard/inventory.py` | open |
| 3 | advisory | IPs compared as raw strings (IPv6 spellings) | `onboard/inventory.py` | open |
| 4 | advisory | "already onboarded" doesn't verify the entry's vars match R5 | `onboard/inventory.py`, `cli.py` | open |
| 5 | advisory | `--known-hosts` whose parent dir doesn't exist: key silently not recorded, then misreported as `[ansible]` | `onboard/checks.py` | open |
| 6 | advisory | Fix-it hints (`ssh-keygen -R ... -f`, `chmod 600`) don't shell-quote paths - wrong to paste for a path with spaces (gap left by T15) | `onboard/checks.py` | open |
| 7 | advisory | `UserKnownHostsFile="..."` doesn't escape `"`, `%`, `~` in the (hidden, operator-set) path | `onboard/checks.py` | open |
| 8 | advisory | Remaining tracebacks: PermissionError on lock/staging, `--inventory-dir` that is a file, EXDEV on cross-filesystem link, missing PyYAML (inventory never left changed) | `onboard/inventory.py`, `cli.py` | open |
| 9 | advisory | Passphrase-protected/corrupt Key B shows as `[authentication]`; `ssh-keygen -y -P ''` would catch it locally | `onboard/checks.py` | open |
| 10 | advisory | Admin SID not checked for enabled state; account matched on name only (local or other-domain `masterchief` passes) | `onboard/checks.py` | open |
| 11 | advisory | AC8 has no test for an existing entry failing the `[ansible]` check | `tests/live/test_live.py` | open |

### Outcome
Clean - waiting on G4

## Decision
<!-- Accepted YYYY-MM-DD (masterchief)
     or Rejected YYYY-MM-DD (masterchief) -> Develop|Plan: <reason> -->
Rejected 2026-10-21 (masterchief) -> Develop: "can we fix any of the advisory findings now?" - fix the clearer-errors group (Test run 2 advisory #1, #3b, #6, #7); the rest stay open.
