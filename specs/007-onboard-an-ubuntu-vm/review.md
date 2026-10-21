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

## Decision
<!-- Accepted YYYY-MM-DD (masterchief)
     or Rejected YYYY-MM-DD (masterchief) -> Develop|Plan: <reason> -->
