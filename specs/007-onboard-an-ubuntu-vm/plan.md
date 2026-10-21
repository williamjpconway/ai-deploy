# Plan 007: Onboard an Ubuntu VM

<!-- Written with the operator in skills/plan-feature, approved at G3
     BEFORE any code or tests are written. -->

## Approach
A second CLI, `bin/onboard-ubuntu --name <name> --ip <ip>`, on
`ai-deploy`, built on spec 001's `onboard/` package rather than a copy
of it. Everything 001 proved - inputs and name rules, inventory
conflicts, the lock and no-clobber commit, the Key B pre-check, TCP
reachability, trust-on-first-use host keys, the staged Ansible ping
with rollback, the "already onboarded" re-run path, and the named
`FAILED [<check>]` output with one exit code per check - is shared.
Only what differs per OS lives in a per-OS profile:

| | Windows (001, unchanged behaviour) | Ubuntu (007) |
|---|---|---|
| Inventory group | `windows` | `ubuntu` |
| Host vars (R5) | + `ansible_shell_type: powershell` | `ansible_connection: ssh`, `ansible_user: masterchief` |
| OS checks, in order | shell probe (R3), identity/admin (R8) | identity/sudo (R8), password auth (R3) |
| Ansible module (R6) | `ansible.windows.win_ping` | `ansible.builtin.ping` |
| Auth-failure fix text | Administrators group / `administrators_authorized_keys` | Key B in `~masterchief/.ssh/authorized_keys` - re-run `initialize-ssh-onboarding.sh` |

Ubuntu check order: usage -> inventory-conflict -> key -> reachability
-> host-key / authentication (first SSH call) -> `identity` -> 
`password-auth` -> `ansible`.

- **`identity` (R8, AC6)** - one SSH call as `masterchief` with Key B
  running `id -un` and `sudo -n true`, printing
  `ID:<user>|SUDO:<yes|no>`. Wrong user, or `SUDO:no`, fails naming
  the fix (`/etc/sudoers.d/90-masterchief` with
  `masterchief ALL=(ALL) NOPASSWD:ALL`, i.e. re-run
  `initialize-ssh-onboarding.sh`).
- **`password-auth` (R3, AC3)** - checked from outside, against what
  the server actually offers rather than what its config files say: an
  SSH attempt with `PreferredAuthentications=none` and public-key auth
  off gets back the list of methods the server allows
  (`Permission denied (publickey).`). If that list contains `password`
  or `keyboard-interactive`, fail naming the cloud-init gotcha and the
  fix (`00-keys-only.conf`, `50-cloud-init.conf`, restart
  `ssh.socket` + `ssh.service`).
- **`ansible` (R6)** - as 001: new target staged in a temp inventory,
  `ansible.builtin.ping` through it, atomic no-clobber commit only on
  success; existing entry pinged through the real inventory, nothing
  written.

New exit code: `password-auth` 15. All other check names and codes are
001's. The shared inventory means a name or IP is unique across
Windows and Ubuntu entries (spec constraint).

## Changes
- `onboard/profiles.py` (new) - the Windows and Ubuntu profiles from the
  table above.
- `onboard/windows.py` (new) - 001's `shell` and `identity` probes and
  Windows auth text, moved out of `checks.py` unchanged.
- `onboard/ubuntu.py` (new) - `identity` (id + sudo) and `password_auth`.
- `onboard/checks.py` - keeps the shared checks (key, reachability, ssh
  transport with host-key/auth mapping, ansible ping); auth-failure
  text and ping module come from the profile.
- `onboard/inventory.py` - group and host vars come from the profile;
  `load_hosts` already reads every group, so conflicts span both OSes.
- `onboard/cli.py` - `main(argv, runner, profile)`; `password-auth` exit
  code.
- `bin/onboard-ubuntu` (new) - entry point, like `bin/onboard-windows`.
- `testlab/proxmox.py` (new) - minimal snapshot / rollback / start /
  delete-snapshot helper over the `ai-deploy-test@pve` token, for AC6's
  lab test only. Never imported by `onboard/`.
- `tests/unit/test_ubuntu_*.py`, `tests/live/test_ubuntu_live.py`,
  `tests/live/test_ubuntu_destructive.py` (new); `tests/helpers.py`
  stub gains the Ubuntu probes.
- `AGENTS.md` - Run the app: `onboard-ubuntu`; Run tests: the Ubuntu
  target variable.
- `utils/onboarding/ubuntu2604/README.md` - "Onboarding verifies these"
  points at the real command.

## Test setup
- **Where/how:** as 001 - on `ai-deploy` in `~/ai-deploy` after
  push + pull; `python3 -m pytest`; `ruff check .`, `ruff format --check .`.
- **Regression:** 001's whole suite (40 tests, unit + live against `dc`)
  must stay green through the refactor - it's the proof Windows
  behaviour didn't change.
- **Target:** `AI_DEPLOY_TEST_TARGET_UBUNTU=<ip>` - today the 009 Ubuntu
  slot 9201 (`test-ubuntu-1`, 192.168.0.84, its IP read from the guest
  agent). Tests take any IP and know nothing about the lab (`AGENTS.md`).
  Every live test uses a temp inventory and temp known_hosts.
- **Broken states:**
  - AC1: refused on ai-deploy's loopback port 1; firewalled/timeout on
    `192.0.2.1`.
  - AC2/AC8: a throwaway key in `tmp_path`.
  - AC7: `AI_DEPLOY_ANSIBLE` pointed at a failing script.
  - AC9: seeded temp inventory (unit, no network).
  - AC10: seeded wrong host key; AC11: empty known_hosts.
  - AC12: missing args (unit).
  - **AC3 (destructive, real):** over SSH as `masterchief`, write
    `/etc/ssh/sshd_config.d/00-a-test-password.conf`
    (`PasswordAuthentication yes` - sorts before `00-keys-only.conf`, so
    it wins), restart `ssh.socket` + `ssh.service`, run onboarding
    (expects `[password-auth]`), then delete the file and restart, in a
    fixture finalizer. Sudo still works throughout, so the restore is
    always possible.
  - **AC6 (destructive, lab-only, decided 2026-10-21):** restored by
    Proxmox snapshot. The test takes a snapshot of the slot, moves
    `/etc/sudoers.d/90-masterchief` aside, runs onboarding (expects
    `[identity]`), rolls the slot back, starts it, waits for SSH and
    checks `sudo -n true` works again, then deletes the snapshot. It
    is marked `lab` + `destructive` and skipped unless
    `AI_DEPLOY_TEST_LAB_VMID` (a slot VMID) and the Proxmox token are
    available - so it's optional and no product test requires the lab.
    The snapshot/rollback helper lives in `testlab/` (the test-tooling
    directory `AGENTS.md` allows), which 009 later grows into the full
    lab tooling.
  - Every AC also has a unit test with a stubbed runner.
- **Destructive tests** are marked `destructive` and need
  `--allow-destructive`. Against a 009 slot they need no operator
  confirmation (`AGENTS.md` sandbox exception); against any other
  target they do. Claude Code's auto mode blocked 001's equivalent run,
  so the operator may need to run them (or add a permission rule - see
  009).

## AC coverage
| AC | Test (what it asserts) | Target | Task(s) |
|----|------------------------|--------|---------|
| AC1 | `[reachability]`, refused vs no answer, no inventory written | live: loopback:1, 192.0.2.1; unit | T1, T3 |
| AC2 | `[authentication]` naming the Ubuntu fix | live: throwaway key; unit | T1, T4 |
| AC3 | `[password-auth]`, not success on key auth alone | destructive: slot with password auth on; unit | T1, T5 |
| AC4 | second run "already onboarded", inventory hash unchanged | live | T1, T6 |
| AC5 | host file has R5 values; independent `ansible.builtin.ping` succeeds | live | T1, T6 |
| AC6 | `[identity]` for wrong user and for sudo needing a password, naming the fix | unit; lab-destructive: slot with sudoers moved aside, snapshot rollback | T1, T4, T7 |
| AC7 | `[ansible]`, inventory byte-identical | unit + live (failing ansible) | T1, T6 |
| AC8 | existing entry + failing check -> that check, entry unchanged | live: seeded inventory + throwaway key | T1, T6 |
| AC9 | `[inventory-conflict]`, including a name/IP used by a Windows entry | unit | T1, T3 |
| AC10 | `[host-key]` with `ssh-keygen -R`, known_hosts unchanged | live | T1, T4 |
| AC11 | known_hosts gains the target's key | live | T1, T4 |
| AC12 | `[usage]`, runner never called | unit | T1, T3 |

## Risks / alternatives considered
- **Refactoring accepted 001 code.** Mitigated by 001's full suite as a
  regression gate in T2, before any Ubuntu behaviour is added.
- **R3 checked by offered methods, not config.** That's the point (it
  catches the cloud-init override however it happens), but it relies on
  OpenSSH's `none` method reply listing methods - standard behaviour.
  Alternative rejected: `sudo sshd -T` on the target - reads config, and
  depends on sudo working first.
- **Breaking sudo on a live target** locks the test out of its own
  restore, so AC6's live test restores by Proxmox snapshot instead
  (decided 2026-10-21). That makes it the one test that needs the lab;
  it's optional and skips cleanly without it. If a rollback ever fails,
  the slot is left without passwordless sudo - the operator rebuilds
  the slot (destroy + re-clone + re-add its ACL).
- Alternative rejected: a separate `onboard_ubuntu/` copy of 001's code -
  every 001 fix (Test runs 1-3) would have to be made twice.
