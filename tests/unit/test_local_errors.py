"""G4 reject fixes (T12-T15): problems on ai-deploy itself get a named check and
a message pointing at ai-deploy, never a traceback or a target-side diagnosis."""

import shlex

import pytest
from helpers import StubRunner, check_tag, snapshot

from onboard.checks import CheckFailed
from onboard.cli import main
from onboard.runner import Runner


def run(tmp_path, runner, capsys, *extra, inventory=None):
    argv = [
        "--name",
        "win-test",
        "--ip",
        "192.168.3.1",
        "--inventory-dir",
        str(inventory or tmp_path / "inventory"),
        "--known-hosts",
        str(tmp_path / "kh"),
        *extra,
    ]
    rc = main(argv, runner=runner)
    out = capsys.readouterr()
    return rc, out.out + out.err


# T12 - Key B checked before any network call (AC2's message only for real rejections)


def test_missing_key_is_a_key_failure_before_network(tmp_path, capsys):
    runner = StubRunner()
    missing = tmp_path / "nope"
    rc, output = run(tmp_path, runner, capsys, "--key", str(missing))
    assert rc != 0
    assert check_tag(output) == "key"
    assert str(missing) in output
    assert "new-target-key.sh" in output
    assert runner.calls == []


def test_group_readable_key_is_a_key_failure_naming_chmod(tmp_path, capsys):
    loose = tmp_path / "loose"
    loose.write_text("x\n")
    loose.chmod(0o644)
    runner = StubRunner()
    rc, output = run(tmp_path, runner, capsys, "--key", str(loose))
    assert rc != 0
    assert check_tag(output) == "key"
    assert f"chmod 600 {loose}" in output
    assert runner.calls == []


def test_unreadable_key_is_a_key_failure(tmp_path, capsys):
    locked = tmp_path / "locked"
    locked.write_text("x\n")
    locked.chmod(0o000)
    runner = StubRunner()
    rc, output = run(tmp_path, runner, capsys, "--key", str(locked))
    assert rc != 0
    assert check_tag(output) == "key"
    assert runner.calls == []


# T13 - unreadable inventory and missing binaries


@pytest.mark.parametrize(
    "content",
    [
        "windows: [unclosed\n",  # not valid YAML
        "- just\n- a list\n",  # valid YAML, not an inventory mapping
    ],
)
def test_malformed_inventory_file_is_an_inventory_failure(content, tmp_path, capsys):
    inventory = tmp_path / "inventory"
    inventory.mkdir()
    (inventory / "broken.yml").write_text(content)
    before = snapshot(inventory)
    runner = StubRunner()

    rc, output = run(tmp_path, runner, capsys, inventory=inventory)

    assert rc != 0
    assert check_tag(output) == "inventory"
    assert "broken.yml" in output
    assert "Traceback" not in output
    assert runner.calls == []
    assert snapshot(inventory) == before


def test_missing_binary_is_a_named_failure_not_a_traceback(tmp_path):
    with pytest.raises(CheckFailed) as failed:
        Runner().run([str(tmp_path / "no-such-ansible"), "--version"], timeout=5)
    assert failed.value.check == "prereq"
    assert "no-such-ansible" in failed.value.message
    assert "install-ansible.sh" in failed.value.message


# T14 - port range and the host-key hint on a non-22 port


@pytest.mark.parametrize("port", ["0", "65536", "70000", "-1"])
def test_out_of_range_port_is_a_usage_failure(port, tmp_path, capsys):
    runner = StubRunner()
    rc, output = run(tmp_path, runner, capsys, "--port", port)
    assert rc != 0
    assert check_tag(output) == "usage"
    assert "Traceback" not in output
    assert runner.calls == []


def test_host_key_hint_uses_bracketed_host_port_off_22(tmp_path, capsys):
    runner = StubRunner(shell_probe=(255, "", "Host key verification failed.\r\n"))
    rc, output = run(tmp_path, runner, capsys, "--port", "2222")
    assert check_tag(output) == "host-key"
    assert "ssh-keygen -R '[192.168.3.1]:2222'" in output


# T15 - a known_hosts path with spaces reaches both ssh and Ansible intact


def test_known_hosts_path_with_spaces_is_one_file_for_ssh_and_ansible(tmp_path, capsys):
    kh = tmp_path / "my keys" / "known hosts"
    runner = StubRunner()
    rc = main(
        [
            "--name",
            "win-test",
            "--ip",
            "192.168.3.1",
            "--inventory-dir",
            str(tmp_path / "inventory"),
            "--known-hosts",
            str(kh),
        ],
        runner=runner,
    )
    assert rc == 0, capsys.readouterr()

    expected = f'UserKnownHostsFile="{kh}"'
    ssh_calls = [argv for _, argv, _ in runner.calls[1:] if argv[0] == "ssh"]
    assert ssh_calls and all(expected in argv for argv in ssh_calls)
    ping_env = next(env for _, argv, env in runner.calls[1:] if "win_ping" in " ".join(argv))
    assert shlex.split(ping_env["ANSIBLE_SSH_COMMON_ARGS"]) == ["-o", expected]
