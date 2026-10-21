"""AC12 (R10): missing inputs fail before any network activity."""

import pytest
from helpers import StubRunner, check_tag, snapshot

from onboard.cli import main


@pytest.mark.parametrize(
    "args, missing",
    [
        ([], "--name"),
        (["--ip", "192.168.3.1"], "--name"),
        (["--name", "win-test"], "--ip"),
    ],
)
def test_ac12_missing_input_is_a_usage_failure(args, missing, tmp_path, capsys):
    runner = StubRunner()
    inventory = tmp_path / "inventory"
    rc = main(
        [*args, "--inventory-dir", str(inventory), "--known-hosts", str(tmp_path / "kh")],
        runner=runner,
    )
    out = capsys.readouterr()
    output = out.out + out.err
    assert rc != 0
    assert check_tag(output) == "usage"
    assert missing in output
    assert runner.calls == []
    assert snapshot(inventory) == {}


def test_ac12_unsafe_name_is_a_usage_failure(tmp_path, capsys):
    """The name becomes a file name - it must never escape the inventory dir."""
    runner = StubRunner()
    rc = main(
        ["--name", "../evil", "--ip", "192.168.3.1",
         "--inventory-dir", str(tmp_path / "inventory"), "--known-hosts", str(tmp_path / "kh")],
        runner=runner,
    )
    out = capsys.readouterr()
    assert rc != 0
    assert check_tag(out.out + out.err) == "usage"
    assert runner.calls == []
