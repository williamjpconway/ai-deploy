# Review 007: Onboard an Ubuntu VM

<!-- Created by skills/build-feature at the first Test run. One "Test run"
     section per run, appended - never overwritten. The Decision section is
     filled only by skills/accept-feature, at G4. -->

## Test run 1 - 2026-10-21
**Diff reviewed:** dfe1a84..042246a

### Tests
Command (on `ai-deploy`): `AI_DEPLOY_TEST_TARGET=192.168.3.1 AI_DEPLOY_TEST_TARGET_UBUNTU=192.168.0.84 python3 -m pytest` - 73 passed, 3 skipped (destructive). Then `AI_DEPLOY_TEST_TARGET_UBUNTU=192.168.0.84 AI_DEPLOY_TEST_LAB_VMID=9201 python3 -m pytest tests/live/test_ubuntu_destructive.py --allow-destructive` - 2 passed (slot 9201, fresh clone of template 9001; still at .84 after AC6's rollback). 001's destructive AC3 against `dc` not run - needs operator confirmation per run.

| AC | Test | Result |
|----|------|--------|
| AC1 | unit: refused; live: refused (loopback:1), unroutable (192.0.2.1) | Pass |
| AC2 | unit: Ubuntu fix named; live: throwaway key -> `[authentication]` | Pass |
| AC3 | unit: offered methods incl. password / keyboard-interactive, unreadable reply not a pass; destructive (slot): drop-in turns password auth on -> `[password-auth]`, restored (`sshd -T` = no) | Pass |
| AC4 | unit + live: second run "already onboarded", inventory unchanged | Pass |
| AC5 | unit + live: R5 values, independent `ansible.builtin.ping` | Pass |
| AC6 | unit: wrong user / sudo needs password / empty reply, fix named; lab-destructive (slot 9201): sudoers moved aside -> `[identity]` naming NOPASSWD, snapshot rollback, sudo back | Pass |
| AC7 | unit + live: failing ansible, inventory byte-identical | Pass |
| AC8 | unit + live: seeded entry + throwaway key, entry unchanged | Pass |
| AC9 | unit: name/IP conflict incl. Windows entry, no network; live: IP used by Windows entry | Pass |
| AC10 | unit + live: seeded wrong host key -> `[host-key]`, known_hosts unchanged | Pass |
| AC11 | live: empty known_hosts gains the slot's key | Pass |
| AC12 | unit: missing `--name` / `--ip` -> `[usage]`, runner never called | Pass |

Regression: 001's whole suite (unit + live against `dc`) passes in the same run; its destructive AC3 not run (see above).

### Static checks
| Check | Command | Result |
|-------|---------|--------|
| ruff lint | `ruff check .` | All checks passed |
| ruff format | `ruff format --check .` | 94 files already formatted |

### Independent review
Reviewer inputs: `spec.md`, the diff above, the static check output - nothing else.

| # | Severity | Finding | Location | Status |
|---|----------|---------|----------|--------|
| 1 | blocking | AC6 fixture breaks sudo on `AI_DEPLOY_TEST_TARGET_UBUNTU` but snapshots/rolls back `AI_DEPLOY_TEST_LAB_VMID` with no check they're the same VM - a mismatch leaves an unrestored host (possibly outside the slots) with sudoers in `/tmp`, and the run still goes green | `tests/live/test_ubuntu_destructive.py` `sudo_broken_on_lab_slot` | open |
| 2 | blocking | `testlab/proxmox.py` passes any VMID to the API; the token's ACL is the only guard for the 9101-9110 / 9201-9210 rule | `testlab/proxmox.py` | open |
| 3 | advisory | AC3 live test has no slot guard; `--allow-destructive` is the only gate against a non-slot target | `tests/live/test_ubuntu_destructive.py` `password_auth_on` | open |
| 4 | advisory | methods-probe timeout tagged `[password-auth]`, where the shared `ssh()` tags a stall `[ssh]` | `onboard/ubuntu.py` `password_auth` | open |
| 5 | advisory | `sudo -n true` passes for a NOPASSWD grant limited to `/bin/true`; `become` needs NOPASSWD:ALL | `onboard/ubuntu.py` `identity` | open |
| 6 | advisory | existing entry matched on name+IP only, not its group or R5 values | `onboard/cli.py` `_onboard` | open |
| 7 | advisory | Proxmox API call skips TLS verification (deferred to 009 pinning); token never printed | `testlab/proxmox.py` `_call` | open |
| 8 | advisory | exemption verify regex treats `.` as wildcard and matches substrings; `--exempt-ip` not validated | `utils/onboarding/ubuntu2604/initialize-ssh-onboarding.sh` | open |
| 9 | advisory | slot IP can change after AC6 rollback, later tests keep the old IP; `ipv4()` takes the first non-loopback address | `sudo_broken_on_lab_slot`, `testlab/proxmox.py` `ipv4` | open |
| 10 | advisory | Ubuntu AC1 timeout test asserts the tag only, not "timed out" wording (shared code, proven by 001) | `tests/live/test_ubuntu_live.py` | open |

Injection/secrets: none found (name/IP validated, list argv, constant remote commands, `yaml.safe_dump`, no AD writes).

### Outcome
Not clean - back to Develop (fix tasks T11-T12 added to tasks.md)

## Test run 2 - 2026-10-21
**Diff reviewed:** dfe1a84..3aa5b45

### Tests
Command (on `ai-deploy`): `AI_DEPLOY_TEST_TARGET=192.168.3.1 AI_DEPLOY_TEST_TARGET_UBUNTU=192.168.0.84 python3 -m pytest` - 118 passed, 3 skipped (destructive). Then `tests/live/test_ubuntu_destructive.py --allow-destructive` with `AI_DEPLOY_TEST_LAB_VMID=9201` - 2 passed (slot still at .84 after rollback). 001's destructive AC3 not run yet.

| AC | Test | Result |
|----|------|--------|
| AC1-AC12 | as run 1 | Pass |
| AC6 (tooling) | fix T11: 45 unit tests - out-of-range VMIDs refused before any API call, slots reach it; fix T12: fixture refuses when slot IP != target (checked live: 192.0.2.1 target -> refused, no snapshot taken; VMID 9001 -> refused) | Pass |

T11's test was confirmed to fail against the pre-fix helper.

### Static checks
| Check | Command | Result |
|-------|---------|--------|
| ruff lint | `ruff check .` | All checks passed |
| ruff format | `ruff format --check .` | 96 files already formatted |

### Independent review
Reviewer inputs: `spec.md`, the diff above, the static check output - nothing else (plus the slot rule from `AGENTS.md`).

| # | Severity | Finding | Location | Status |
|---|----------|---------|----------|--------|
| 1 | blocking | AC3 fixture's setup (`tee` drop-in `&&` restart) runs before `try:`; if the restart fails after the `tee`, the `PasswordAuthentication yes` drop-in is never removed | `tests/live/test_ubuntu_destructive.py` `password_auth_on` | open |
| 2 | advisory | AC3 test has no slot guard (as run 1 #3) | `test_ac3_password_auth_enabled_fails_password_auth` | open |
| 3 | advisory | methods-probe timeout tagged `[password-auth]` (as run 1 #4) | `onboard/ubuntu.py` `password_auth` | open |
| 4 | advisory | `sudo -n true` passes a narrow or cached grant (as run 1 #5); suggests `sudo -k -n` + `sudo -n -l` | `onboard/ubuntu.py` `IDENTITY_PROBE` | open |
| 5 | advisory | existing entry not checked for OS group / R5 values (as run 1 #6) | `onboard/cli.py` `_onboard` | open |
| 6 | advisory | Proxmox TLS unverified (as run 1 #7; track in 009) | `testlab/proxmox.py` `_call` | open |
| 7 | advisory | Ubuntu tests don't prove refused vs timed-out wording (as run 1 #10) | `tests/live/test_ubuntu_live.py` | open |
| 8 | advisory | AC6 fixture skips `delete_snapshot` if rollback/start/ipv4 raises (slot only) | `sudo_broken_on_lab_slot` | open |
| 9 | advisory | `ipv4()` first non-loopback address may be a second interface; fixture then fails safe (as run 1 #9) | `testlab/proxmox.py` `ipv4` | open |

Run 1 blocking #1 and #2: fixed (T12, T11) - reviewer confirmed the slot guard and no `onboard/` import of `testlab`.

### Outcome
Not clean - back to Develop (fix task T13 added to tasks.md)

## Test run 3 - 2026-10-21
**Diff reviewed:** dfe1a84..02a33e2

### Tests
Commands (on `ai-deploy`):
- `AI_DEPLOY_TEST_TARGET=192.168.3.1 AI_DEPLOY_TEST_TARGET_UBUNTU=192.168.0.84 python3 -m pytest` - 118 passed, 3 skipped (destructive, run below).
- 001's destructive AC3 on Windows slot 9101 (`test-windows-1`, 192.168.0.85 - domain-joined into `OU=ai-deploy-test` this session, operator-confirmed, `DOMAIN\masterchief` in local Administrators, snapshot `clean`): `AI_DEPLOY_TEST_TARGET=192.168.0.85 python3 -m pytest tests/live/test_destructive.py --allow-destructive` - 1 passed; DefaultShell powershell.exe before and after.
- `tests/live/test_ubuntu_destructive.py --allow-destructive` with `AI_DEPLOY_TEST_LAB_VMID=9201` - 2 passed (slot still at .84).

| AC | Test | Result |
|----|------|--------|
| AC1-AC12 | as runs 1-2 | Pass |
| AC3 (fixture) | fix T13: drop-in setup inside `try:`; forced setup failure on 9201 -> drop-in removed, `passwordauthentication no` | Pass |
| 001 AC3 (regression) | destructive on 9101 | Pass |

### Static checks
| Check | Command | Result |
|-------|---------|--------|
| ruff lint | `ruff check .` | All checks passed |
| ruff format | `ruff format --check .` | 96 files already formatted |

### Independent review
Reviewer inputs: `spec.md`, the diff above, the static check output - nothing else (plus the slot rule from `AGENTS.md`).

| # | Severity | Finding | Location | Status |
|---|----------|---------|----------|--------|
| 1 | blocking | AC3 fixture changes sshd on any `AI_DEPLOY_TEST_TARGET_UBUNTU` with no slot check (AC6 has one); `--allow-destructive` is the only gate, and the same flag also enables dc's AC3, which needs confirmation every run (advisory in runs 1-2, raised to blocking here) | `tests/live/test_ubuntu_destructive.py` `password_auth_on` | open |
| 2 | advisory | methods-probe timeout tagged `[password-auth]` (as run 2 #3) | `onboard/ubuntu.py` `password_auth` | open |
| 3 | advisory | R3 probe options come after `ssh_argv` base options; an earlier `PreferredAuthentications` would win (not visible in diff; live AC3/AC5 would catch) | `onboard/checks.py` `ssh_argv` | open |
| 4 | advisory | `sudo -n true` passes a narrow grant; suggests `sudo -n /bin/sh -c true` (as run 2 #4) | `onboard/ubuntu.py` `IDENTITY_PROBE` | open |
| 5 | advisory | wrong-user identity branch names no fix (near-unreachable) | `onboard/ubuntu.py` `identity` | open |
| 6 | advisory | password-auth check sees only methods offered to ai-deploy's address (`Match Address` blind spot) | `onboard/ubuntu.py` `password_auth` | open |
| 7 | advisory | methods probe counts toward PerSourcePenalties on targets without the exemption | `onboard/ubuntu.py` `password_auth` | open |
| 8 | advisory | slot IP can change after AC6 rollback; later live tests keep the old IP (as run 2 #9) | `sudo_broken_on_lab_slot` | open |
| 9 | advisory | Ubuntu tests don't prove timeout vs refused wording (as run 2 #7) | `tests/live/test_ubuntu_live.py` | open |
| 10 | advisory | Proxmox TLS unverified; snapshot names unescaped in path (internal) | `testlab/proxmox.py` `_call` | open |
| 11 | advisory | `--exempt-ip` not validated; bad line stays in config; loose grep | `initialize-ssh-onboarding.sh` | open |

Run 2 blocking #1: fixed (T13).

### Outcome
Not clean - stop condition (run 3 still not clean): back to Develop, fix task T14 added to tasks.md, waiting on operator.

## Decision
<!-- Accepted YYYY-MM-DD (masterchief)
     or Rejected YYYY-MM-DD (masterchief) -> Develop|Plan: <reason> -->
