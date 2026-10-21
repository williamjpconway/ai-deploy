"""AC3 (R3) and AC6 (R8) with stubbed probe output; AC7 (R6) with a stubbed ping."""

import pytest
from helpers import CMD_EXE_ERROR, StubRunner, check_tag, snapshot, write_host

from onboard.cli import main


def run(tmp_path, runner, capsys):
    inventory = tmp_path / "inventory"
    rc = main(
        ["--name", "win-test", "--ip", "192.168.3.1",
         "--inventory-dir", str(inventory), "--known-hosts", str(tmp_path / "kh")],
        runner=runner,
    )
    out = capsys.readouterr()
    return rc, out.out + out.err, inventory


def test_ac3_cmd_exe_shell_fails_the_shell_check(tmp_path, capsys):
    runner = StubRunner(shell=(1, "", CMD_EXE_ERROR))
    rc, output, inventory = run(tmp_path, runner, capsys)
    assert rc != 0
    assert check_tag(output) == "shell"
    assert snapshot(inventory) == {}


def test_ac3_powershell_banner_without_marker_fails_the_shell_check(tmp_path, capsys):
    """Exit 0 alone is not proof - the probe output must contain the marker."""
    runner = StubRunner(shell=(0, "Microsoft Windows [Version 10.0.26100]\r\n", ""))
    rc, output, _ = run(tmp_path, runner, capsys)
    assert rc != 0
    assert check_tag(output) == "shell"


@pytest.mark.parametrize(
    "identity",
    [
        "ID:LAB\\someoneelse|ADMIN:True",  # wrong account
        "ID:LAB\\masterchief|ADMIN:False",  # not an Administrators member
        "ID:LAB\\notmasterchief|ADMIN:True",  # suffix match must be on the whole account
    ],
)
def test_ac6_wrong_identity_or_no_admin_fails_the_identity_check(identity, tmp_path, capsys):
    runner = StubRunner(identity=(0, identity, ""))
    rc, output, inventory = run(tmp_path, runner, capsys)
    assert rc != 0
    assert check_tag(output) == "identity"
    assert snapshot(inventory) == {}


def test_ac6_missing_admin_says_what_to_add(tmp_path, capsys):
    runner = StubRunner(identity=(0, "ID:LAB\\masterchief|ADMIN:False", ""))
    _, output, _ = run(tmp_path, runner, capsys)
    assert "Add-ADGroupMember -Identity S-1-5-32-544 -Members masterchief" in output
    assert "Add-LocalGroupMember -SID S-1-5-32-544 -Member masterchief" in output


def test_ac7_failed_ansible_ping_leaves_inventory_byte_identical(tmp_path, capsys):
    inventory = tmp_path / "inventory"
    write_host(inventory, "existing", "192.168.3.50")
    before = snapshot(inventory)
    runner = StubRunner(ansible_rc=4)

    rc, output, _ = run(tmp_path, runner, capsys)

    assert rc != 0
    assert check_tag(output) == "ansible"
    assert snapshot(inventory) == before
    assert not any(p.name.startswith(".onboard") for p in tmp_path.iterdir())
