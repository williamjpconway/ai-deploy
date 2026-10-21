"""Spec 007 ACs with a stubbed runner: onboard-ubuntu's own checks and the shared
behaviour it must inherit from spec 001."""

import pytest
import yaml
from helpers import (
    UbuntuStubRunner,
    check_tag,
    snapshot,
    write_host,
    write_ubuntu_host,
)

from onboard.cli import main
from onboard.profiles import UBUNTU

NAME = "ubuntu-test"
IP = "192.168.0.84"


def run(tmp_path, runner, capsys, *extra, name=NAME, ip=IP):
    argv = [
        "--name",
        name,
        "--ip",
        ip,
        "--inventory-dir",
        str(tmp_path / "inventory"),
        "--known-hosts",
        str(tmp_path / "kh"),
        *extra,
    ]
    rc = main(argv, runner=runner, profile=UBUNTU)
    out = capsys.readouterr()
    return rc, out.out + out.err


# AC12 (R10)


@pytest.mark.parametrize("args, missing", [([], "--name"), (["--name", NAME], "--ip")])
def test_ac12_missing_input_names_onboard_ubuntu_usage(args, missing, tmp_path, capsys):
    runner = UbuntuStubRunner()
    rc = main(
        [*args, "--inventory-dir", str(tmp_path / "inventory"), "--known-hosts", str(tmp_path / "kh")],
        runner=runner,
        profile=UBUNTU,
    )
    out = capsys.readouterr()
    output = out.out + out.err
    assert rc != 0
    assert check_tag(output) == "usage"
    assert missing in output
    assert "onboard-ubuntu --name" in output
    assert runner.calls == []


# AC9 (R4) - one inventory across both OSes


@pytest.mark.parametrize(
    "seed, conflicting",
    [
        (lambda inv: write_host(inv, NAME, "192.168.0.99"), "192.168.0.99"),  # name used by Windows
        (lambda inv: write_host(inv, "dc", IP), "dc"),  # IP used by a Windows entry
        (lambda inv: write_ubuntu_host(inv, "other", IP), "other"),  # IP used by Ubuntu entry
    ],
)
def test_ac9_conflict_with_any_entry_fails_without_network(seed, conflicting, tmp_path, capsys):
    inventory = tmp_path / "inventory"
    seed(inventory)
    before = snapshot(inventory)
    runner = UbuntuStubRunner()

    rc, output = run(tmp_path, runner, capsys)

    assert rc != 0
    assert check_tag(output) == "inventory-conflict"
    assert conflicting in output
    assert runner.calls == []
    assert snapshot(inventory) == before


# AC1 (R1)


def test_ac1_refused_is_a_reachability_failure(tmp_path, capsys):
    rc, output = run(tmp_path, UbuntuStubRunner(tcp_error=ConnectionRefusedError()), capsys)
    assert rc != 0
    assert check_tag(output) == "reachability"


# AC2 (R2)


def test_ac2_rejected_key_names_the_ubuntu_fix(tmp_path, capsys):
    denied = (255, "", "masterchief@192.168.0.84: Permission denied (publickey).\r\n")
    rc, output = run(tmp_path, UbuntuStubRunner(identity=denied), capsys)
    assert rc != 0
    assert check_tag(output) == "authentication"
    assert "/home/masterchief/.ssh/authorized_keys" in output
    assert "initialize-ssh-onboarding.sh" in output
    assert "administrators_authorized_keys" not in output


# AC6 (R8)


@pytest.mark.parametrize(
    "identity",
    [
        "ID:ubuntu|SUDO:yes",  # wrong account
        "ID:masterchief|SUDO:no",  # sudo needs a password
        "",  # probe printed nothing
    ],
)
def test_ac6_wrong_user_or_no_passwordless_sudo_fails_identity(identity, tmp_path, capsys):
    rc, output = run(tmp_path, UbuntuStubRunner(identity=(0, identity, "")), capsys)
    assert rc != 0
    assert check_tag(output) == "identity"
    assert snapshot(tmp_path / "inventory") == {}


def test_ac6_no_sudo_names_the_fix(tmp_path, capsys):
    _, output = run(tmp_path, UbuntuStubRunner(identity=(0, "ID:masterchief|SUDO:no", "")), capsys)
    assert "NOPASSWD" in output
    assert "initialize-ssh-onboarding.sh" in output


# AC3 (R3)


@pytest.mark.parametrize(
    "offered",
    ["publickey,password", "publickey,keyboard-interactive", "password,publickey"],
)
def test_ac3_server_offering_password_login_fails_password_auth(offered, tmp_path, capsys):
    methods = (255, "", f"masterchief@192.168.0.84: Permission denied ({offered}).\r\n")
    rc, output = run(tmp_path, UbuntuStubRunner(methods=methods), capsys)
    assert rc != 0
    assert check_tag(output) == "password-auth"
    assert "00-keys-only.conf" in output
    assert snapshot(tmp_path / "inventory") == {}


def test_ac3_unreadable_methods_reply_is_not_a_pass(tmp_path, capsys):
    """Verify, don't assume: no method list at all must not count as 'keys only'."""
    methods = (255, "", "Connection closed by 192.168.0.84 port 22\r\n")
    rc, output = run(tmp_path, UbuntuStubRunner(methods=methods), capsys)
    assert rc != 0
    assert check_tag(output) == "password-auth"


# AC10 (R9)


def test_ac10_changed_host_key_is_a_host_key_failure(tmp_path, capsys):
    changed = (255, "", "Host key verification failed.\r\n")
    rc, output = run(tmp_path, UbuntuStubRunner(identity=changed), capsys)
    assert check_tag(output) == "host-key"
    assert "ssh-keygen -R 192.168.0.84" in output


# AC5 (R5, R6) and AC7 (R6)


def test_ac5_new_target_gets_r5_values_and_ubuntu_ping(tmp_path, capsys):
    runner = UbuntuStubRunner()
    rc, output = run(tmp_path, runner, capsys)
    assert rc == 0, output
    assert "onboarded" in output
    data = yaml.safe_load((tmp_path / "inventory" / f"{NAME}.yml").read_text())
    host = data["ubuntu"]["hosts"][NAME]
    assert host["ansible_host"] == IP
    assert host["ansible_connection"] == "ssh"
    assert host["ansible_user"] == "masterchief"
    assert "ansible_shell_type" not in host
    assert any("ansible.builtin.ping" in " ".join(c[1]) for c in runner.calls if c[0] == "run")


def test_ac7_failed_ping_leaves_inventory_byte_identical(tmp_path, capsys):
    inventory = tmp_path / "inventory"
    write_host(inventory, "dc", "192.168.3.1")
    before = snapshot(inventory)
    rc, output = run(tmp_path, UbuntuStubRunner(ansible_rc=4), capsys)
    assert rc != 0
    assert check_tag(output) == "ansible"
    assert snapshot(inventory) == before
    assert not any(p.name.startswith(".onboard") for p in tmp_path.iterdir())


# AC4 and AC8 (R4)


def test_ac4_existing_entry_passing_all_checks_is_already_onboarded(tmp_path, capsys):
    inventory = tmp_path / "inventory"
    write_ubuntu_host(inventory, NAME, IP)
    before = snapshot(inventory)
    rc, output = run(tmp_path, UbuntuStubRunner(), capsys)
    assert rc == 0, output
    assert "already onboarded" in output
    assert snapshot(inventory) == before


def test_ac8_existing_entry_failing_a_check_is_unchanged(tmp_path, capsys):
    inventory = tmp_path / "inventory"
    write_ubuntu_host(inventory, NAME, IP)
    before = snapshot(inventory)
    rc, output = run(tmp_path, UbuntuStubRunner(identity=(0, "ID:masterchief|SUDO:no", "")), capsys)
    assert rc != 0
    assert check_tag(output) == "identity"
    assert snapshot(inventory) == before
