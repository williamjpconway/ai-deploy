# Plan 001: Onboard a Windows VM

<!-- Written with the operator in skills/plan-feature, approved at G3
     BEFORE any code or tests are written. -->

## Approach
A Python CLI, `onboard-windows --name <name> --ip <ip>`, run on
`ai-deploy` as `masterchief` (Python + pytest decided 2026-10-21, which
changes `AGENTS.md`'s "onboarding scripts stay PowerShell/bash" rule
for this script; it also means spec 002's UI can call the same code).
Standard library plus PyYAML only (`python3-yaml` 6.0.3 and `pytest`
9.0.2 are already installed on `ai-deploy`), so no venv and no new
packages for the code itself. Everything it does to the target goes
through the system `ssh` client and `ansible` - nothing is installed on
the target.

Checks run in a fixed order and stop at the first failure. Each failure
prints `onboard-windows: FAILED [<check>] <specific message>` and exits
with that check's own non-zero code (R7):

1. `usage` (R10, AC12) - both `--name` and `--ip` present and the IP
   parses; checked before any file or network access.
2. `inventory-conflict` (R4, AC9) - load every host file in the
   inventory dir; name matches with a different IP, or IP matches
   under a different name -> fail. Exact name+IP match -> remember
   "existing entry" and carry on verifying.
3. `reachability` (R1, AC1) - plain TCP connect to `<ip>:22` with a
   5 s timeout; refused and timed-out get distinct messages, both
   tagged `reachability`.
4. `host-key` (R9, AC10, AC11) - every SSH call uses
   `-o StrictHostKeyChecking=accept-new`, which is OpenSSH's own
   trust-on-first-use: an unknown key is recorded, a changed key is
   refused and never replaced. A refusal (stderr "REMOTE HOST
   IDENTIFICATION HAS CHANGED") becomes a `host-key` failure naming
   `ssh-keygen -R <ip>`.
5. `authentication` (R2, AC2) - `ssh -i ~/.ssh/ai_deploy_targets
   -o BatchMode=yes masterchief@<ip>`; "Permission denied" -> fail
   naming both causes (Key B not in `administrators_authorized_keys`,
   or `masterchief` not in Administrators).
6. `shell` (R3, AC3) - the probe
   `Write-Output ('PSOK:' + $PSVersionTable.PSVersion.Major)`. Under
   PowerShell it prints `PSOK:5`; under `cmd.exe` the output never
   contains `PSOK:<digit>`, so anything else fails.
7. `identity` (R8, AC6) - one PowerShell probe returning the current
   identity name and whether its groups contain the Administrators SID
   `S-1-5-32-544`. The name must end in `\masterchief` (domain or
   local) and the SID must be present.
8. `ansible` (R6, AC5, AC7) - new target: write its host file into a
   fresh temp inventory dir, run
   `ansible -i <temp> <name> -m ansible.windows.win_ping`, and only on
   success move the file into the real inventory dir with an atomic
   `os.replace`. On failure the temp dir is deleted, so the real
   inventory is never touched (AC7 byte-for-byte). Existing entry: run
   `win_ping` against the real inventory, write nothing.

Results: new target, all pass -> `onboarded <name> (<ip>)`, exit 0.
Existing entry, all pass -> `already onboarded <name> (<ip>)`, exit 0,
no writes (AC4). Existing entry, any check fails -> that check's
failure, no writes (AC8).

Inventory (decided 2026-10-21): outside the repo, default
`~/.config/ai-deploy/inventory/`, overridable with `--inventory-dir`.
One file per host, `<name>.yml`, so adding, rolling back and no-op are
all one-file operations and Ansible merges the directory:

```yaml
windows:
  hosts:
    <name>:
      ansible_host: <ip>
      ansible_connection: ssh
      ansible_user: masterchief
      ansible_shell_type: powershell
      ansible_ssh_private_key_file: ~/.ssh/ai_deploy_targets
```

Test-only options (`--port`, `--key`, `--known-hosts`) default to 22,
Key B and `~/.ssh/known_hosts`. All subprocess calls go through one
small `runner` module, which is the only place unit tests stub.

## Changes
- `onboard/__init__.py`, `onboard/cli.py` (args, check order, exit
  codes), `onboard/checks.py` (R1-R3, R8, R9 probes),
  `onboard/inventory.py` (load, conflict, stage, commit - R4, R5, R6),
  `onboard/runner.py` (subprocess wrapper for `ssh`/`ansible`).
- `bin/onboard-windows` - thin Python entry point
  (`python3 -m onboard.cli "$@"` equivalent), kebab-case per Unix
  convention.
- `tests/unit/` (stubbed runner), `tests/live/` (real target),
  `tests/conftest.py`, `pytest.ini` (markers `live`, `destructive`;
  `testpaths`).
- `ruff.toml` - ruff check + format config.
- `.gitignore` - `__pycache__/`, `.pytest_cache/`, `.ruff_cache/`.
- `AGENTS.md` - Stack line already updated at plan time (Python
  onboarding, inventory location); T8 fills Run tests, Checks and Run
  the app commands.
- `utils/prereqs/ai-deploy/install-ansible.sh` - also
  `pipx install ruff` (same idempotent, `--dry-run` pattern).

## Test setup
- **Where:** tests run on `ai-deploy` in `~/ai-deploy`. Each task is
  committed here, pushed to `origin`, then `git pull` on `ai-deploy`
  (decided 2026-10-21).
- **Commands:** `python3 -m pytest tests/unit` (no network);
  `python3 -m pytest -m live` with `AI_DEPLOY_TEST_TARGET=192.168.3.1`
  (live, non-destructive); `python3 -m pytest -m destructive
  --allow-destructive` (AC3 only). Checks: `ruff check .` and
  `ruff format --check .`.
- **Target:** test VM `192.168.3.1` (Windows, reachable on 22, prepped
  from the template). Before the first live run, its stale entry in
  `ai-deploy`'s `~/.ssh/known_hosts` is cleared with
  `ssh-keygen -R 192.168.3.1` (operator approved 2026-10-21). The live
  tests never touch the real known_hosts or real inventory - each uses
  a pytest `tmp_path` for `--known-hosts` and `--inventory-dir`.
- **Broken states, all produced from `ai-deploy` without changing the
  VM (decided 2026-10-21):**
  - AC1: `--port 1` on 192.168.3.1 (refused) and `192.0.2.1`
    (TEST-NET, unroutable -> timeout).
  - AC2: a throwaway ed25519 key generated in `tmp_path`, passed as
    `--key`.
  - AC6: unit test, stubbed identity probe output (no real target can
    reach this state - spec AC6).
  - AC7: unit test with stubbed `win_ping` failure, plus a live
    variant with `AI_DEPLOY_ANSIBLE` pointed at a script that exits 1;
    inventory dir hashed before/after.
  - AC8: temp inventory pre-seeded with a correct entry, then run with
    the throwaway key -> `authentication` fails, file hash unchanged.
  - AC9: temp inventory seeded with `<name>` -> a different IP (and
    the reverse); fails before any network access.
  - AC10: temp known_hosts seeded with a freshly generated, wrong
    ed25519 key for 192.168.3.1; file hash unchanged after.
  - AC11/AC5/AC4: empty temp known_hosts and inventory; onboard, then
    re-run.
  - AC12: unit test, missing args; runner stub asserts it was never
    called.
- **The one VM change (AC3):** set the test VM's `DefaultShell` to
  `cmd.exe` over SSH, run onboarding, then restore it with a `cmd`
  syntax `reg add HKLM\SOFTWARE\OpenSSH /v DefaultShell /d
  C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe /f`
  (restarting `sshd` only if the change doesn't apply to new sessions
  on its own), in a fixture finalizer so it's restored even on failure.
  Marked `destructive` and skipped unless `--allow-destructive` is
  passed. Per `AGENTS.md`, I ask for confirmation before **each**
  destructive run and show you the before/after `DefaultShell` value.
  A unit test with a stubbed `cmd.exe` banner also covers AC3, so a
  missed destructive run never leaves AC3 untested.
- No AD writes anywhere in 001.

## AC coverage
| AC | Test (what it asserts) | Target | Task(s) |
|----|------------------------|--------|---------|
| AC1 | `[reachability]` failure, distinct refused/timeout text, non-zero exit, no inventory written | live: 192.168.3.1:1, 192.0.2.1 | T1, T3 |
| AC2 | `[authentication]` failure naming both causes | live: 192.168.3.1 with throwaway key | T1, T4 |
| AC3 | `[shell]` failure, not success or a syntax error | unit: stubbed cmd output; destructive: 192.168.3.1 with DefaultShell=cmd.exe | T1, T5 |
| AC4 | second run prints `already onboarded`, inventory dir hash unchanged | live: 192.168.3.1, temp inventory | T1, T7 |
| AC5 | host file exists with R5 vars; independent `win_ping` via the inventory succeeds | live: 192.168.3.1, temp inventory | T1, T6 |
| AC6 | `[identity]` failure for wrong name, and for missing S-1-5-32-544 | unit: stubbed probe | T1, T5 |
| AC7 | `[ansible]` failure, inventory dir byte-identical | unit: stubbed win_ping; live: failing `AI_DEPLOY_ANSIBLE` | T1, T6 |
| AC8 | existing entry + failing check -> that check's failure, file unchanged | live: 192.168.3.1, seeded inventory, throwaway key | T1, T7 |
| AC9 | `[inventory-conflict]` naming the entry, no network, no change (both directions) | unit + CLI with seeded temp inventory | T1, T2 |
| AC10 | `[host-key]` failure naming `ssh-keygen -R`, known_hosts unchanged | live: 192.168.3.1, seeded wrong key | T1, T4 |
| AC11 | after success, temp known_hosts contains 192.168.3.1's key | live: 192.168.3.1, empty known_hosts | T1, T4 |
| AC12 | `[usage]` failure naming the missing input, runner never called | unit | T1, T2 |

## Risks / alternatives considered
- **Target prep unverified for `masterchief`.** The template script
  hasn't been updated for the `masterchief` decision, and Windows was
  only confirmed as `Administrator`. If `masterchief` isn't in the
  test VM's Administrators group, AC4/AC5/AC11 can't pass - that's a
  template fix outside 001 and will be raised, not patched around.
- **Admin check reflects group membership, not token elevation.**
  OpenSSH key auth gives admins a full token, so the SID check is
  enough today. If that changes, R8 needs a different probe.
- **Python for onboarding** departs from `AGENTS.md`'s bash/PowerShell
  rule; accepted for UI reuse (spec 002); `AGENTS.md` Stack updated
  2026-10-21.
- **DC risk (open, `AGENTS.md`):** onboarding a DC makes Key B
  domain-admin equivalent. 001 doesn't fix this.
- **Pushing every task to GitHub** publishes work-in-progress commits;
  accepted for simplicity.
- Alternative rejected: one shared inventory YAML file edited in
  place - rollback and no-op become YAML-merge problems; one file per
  host avoids that.
- Alternative rejected: a separate `ssh-keyscan` step for host keys -
  `accept-new` already gives exactly R9's semantics inside OpenSSH.
