"""AC3 (R3) for real: the test target's SSH shell set to cmd.exe, then restored.

Changes the target VM. Skipped unless --allow-destructive is passed, and per
AGENTS.md the operator confirms each run before it's started.
"""

import pytest
from conftest import target_ssh
from helpers import check_tag, snapshot

pytestmark = [pytest.mark.live, pytest.mark.destructive]

POWERSHELL = r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe"
CMD = r"C:\Windows\System32\cmd.exe"
READ_SHELL = "(Get-ItemProperty HKLM:\\SOFTWARE\\OpenSSH -Name DefaultShell).DefaultShell"


@pytest.fixture
def cmd_shell_target(target_ip, tmp_path):
    kh = tmp_path / "admin_known_hosts"
    before = target_ssh(target_ip, kh, READ_SHELL)
    assert before.returncode == 0 and before.stdout.strip() == POWERSHELL, before
    print(f"DefaultShell before: {before.stdout.strip()}")

    changed = target_ssh(
        target_ip, kh, f"Set-ItemProperty HKLM:\\SOFTWARE\\OpenSSH -Name DefaultShell -Value '{CMD}'"
    )
    assert changed.returncode == 0, changed
    try:
        yield target_ip
    finally:
        # The shell is cmd.exe now, so the restore has to be cmd syntax.
        restore = target_ssh(
            target_ip,
            kh,
            f'reg add HKLM\\SOFTWARE\\OpenSSH /v DefaultShell /t REG_SZ /d "{POWERSHELL}" /f',
        )
        after = target_ssh(target_ip, kh, READ_SHELL)
        print(f"DefaultShell after: {after.stdout.strip()}")
        assert restore.returncode == 0, restore
        assert after.stdout.strip() == POWERSHELL, after


def test_ac3_cmd_exe_shell_fails_the_shell_check(cli, cmd_shell_target, inventory_dir):
    proc = cli("--name", "win-test", "--ip", cmd_shell_target)
    assert proc.returncode != 0
    assert check_tag(proc.output) == "shell"
    assert snapshot(inventory_dir) == {}
