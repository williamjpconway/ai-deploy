"""Test run 1 findings 1-2: a stalled SSH session is never blamed on the shell or
identity checks (R3, R7), and inventory is never clobbered or raced (R4)."""

import fcntl

from helpers import StubRunner, check_tag, snapshot, write_host

from onboard.cli import main


def run(tmp_path, runner, capsys):
    rc = main(
        [
            "--name",
            "win-test",
            "--ip",
            "192.168.3.1",
            "--inventory-dir",
            str(tmp_path / "inventory"),
            "--known-hosts",
            str(tmp_path / "kh"),
        ],
        runner=runner,
    )
    out = capsys.readouterr()
    return rc, out.out + out.err


def test_ssh_timeout_is_an_ssh_failure_not_a_shell_failure(tmp_path, capsys):
    rc, output = run(tmp_path, StubRunner(ssh_timeout=True), capsys)
    assert rc != 0
    assert check_tag(output) == "ssh"
    assert "DefaultShell" not in output
    assert snapshot(tmp_path / "inventory") == {}


def test_host_file_holding_another_host_is_a_conflict_before_network(tmp_path, capsys):
    inventory = tmp_path / "inventory"
    write_host(inventory, "dc01", "192.168.3.77")
    (inventory / "dc01.yml").rename(inventory / "win-test.yml")  # hand-renamed file
    before = snapshot(inventory)
    runner = StubRunner()

    rc, output = run(tmp_path, runner, capsys)

    assert rc != 0
    assert check_tag(output) == "inventory-conflict"
    assert "win-test.yml" in output
    assert runner.calls == []
    assert snapshot(inventory) == before


def test_file_appearing_during_the_run_is_never_overwritten(tmp_path, capsys):
    inventory = tmp_path / "inventory"

    def someone_else_commits():
        write_host(inventory, "win-test", "192.168.3.88")

    runner = StubRunner(on_ping=someone_else_commits)
    rc, output = run(tmp_path, runner, capsys)

    assert rc != 0
    assert check_tag(output) == "inventory-conflict"
    assert "192.168.3.88" in (inventory / "win-test.yml").read_text()
    assert not any(p.name.startswith(".onboard") for p in tmp_path.iterdir())


def test_concurrent_run_is_refused_while_another_holds_the_lock(tmp_path, capsys):
    with open(tmp_path / "onboard-windows.lock", "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        runner = StubRunner()
        rc, output = run(tmp_path, runner, capsys)

    assert rc != 0
    assert check_tag(output) == "busy"
    assert runner.calls == []
    assert snapshot(tmp_path / "inventory") == {}
