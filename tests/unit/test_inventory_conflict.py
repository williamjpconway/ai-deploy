"""AC9 (R4): a name or IP already used by a different entry fails, untouched."""

import pytest
from helpers import StubRunner, check_tag, snapshot, write_host

from onboard.cli import main


@pytest.mark.parametrize(
    "seed_name, seed_ip, conflicting",
    [
        ("win-test", "192.168.3.9", "win-test"),  # name taken by another IP
        ("other", "192.168.3.1", "other"),  # IP taken by another name
    ],
)
def test_ac9_conflicting_entry_fails_without_network_or_change(
    seed_name, seed_ip, conflicting, tmp_path, capsys
):
    inventory = tmp_path / "inventory"
    write_host(inventory, seed_name, seed_ip)
    before = snapshot(inventory)
    runner = StubRunner()

    rc = main(
        [
            "--name",
            "win-test",
            "--ip",
            "192.168.3.1",
            "--inventory-dir",
            str(inventory),
            "--known-hosts",
            str(tmp_path / "kh"),
        ],
        runner=runner,
    )

    out = capsys.readouterr()
    output = out.out + out.err
    assert rc != 0
    assert check_tag(output) == "inventory-conflict"
    assert conflicting in output
    assert runner.calls == []
    assert snapshot(inventory) == before
