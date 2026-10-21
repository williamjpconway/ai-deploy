"""Spec 007 ACs live against an Ubuntu target (AI_DEPLOY_TEST_TARGET_UBUNTU), without
changing it. Every test uses a temp inventory dir and a temp known_hosts."""

import os
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml
from helpers import check_tag, snapshot, write_host, write_ubuntu_host

pytestmark = pytest.mark.live_ubuntu

NAME = "ubuntu-test"


def ansible_bin():
    return shutil.which("ansible") or str(Path.home() / ".local" / "bin" / "ansible")


def test_ac1_refused_port_fails_reachability(ubuntu_cli, inventory_dir):
    proc = ubuntu_cli("--name", NAME, "--ip", "127.0.0.1", "--port", "1")
    assert proc.returncode != 0
    assert check_tag(proc.output) == "reachability"
    assert "refused" in proc.output.lower()
    assert snapshot(inventory_dir) == {}


def test_ac1_unroutable_ip_fails_reachability(ubuntu_cli, inventory_dir):
    proc = ubuntu_cli("--name", NAME, "--ip", "192.0.2.1")
    assert proc.returncode != 0
    assert check_tag(proc.output) == "reachability"
    assert snapshot(inventory_dir) == {}


def test_ac2_unknown_key_fails_authentication(ubuntu_cli, ubuntu_ip, throwaway_key, inventory_dir):
    proc = ubuntu_cli("--name", NAME, "--ip", ubuntu_ip, "--key", str(throwaway_key))
    assert proc.returncode != 0
    assert check_tag(proc.output) == "authentication"
    assert "initialize-ssh-onboarding.sh" in proc.output
    assert snapshot(inventory_dir) == {}


def test_ac5_prepared_target_is_onboarded_and_pingable(
    ubuntu_cli, ubuntu_ip, inventory_dir, known_hosts
):
    proc = ubuntu_cli("--name", NAME, "--ip", ubuntu_ip)
    assert proc.returncode == 0, proc.output
    assert "onboarded" in proc.output

    host = yaml.safe_load((inventory_dir / f"{NAME}.yml").read_text())["ubuntu"]["hosts"][NAME]
    assert host["ansible_host"] == ubuntu_ip
    assert host["ansible_connection"] == "ssh"
    assert host["ansible_user"] == "masterchief"

    ping = subprocess.run(
        [ansible_bin(), "-i", str(inventory_dir), NAME, "-m", "ansible.builtin.ping"],
        capture_output=True,
        text=True,
        timeout=120,
        env=dict(os.environ, ANSIBLE_SSH_COMMON_ARGS=f'-o UserKnownHostsFile="{known_hosts}"'),
    )
    assert ping.returncode == 0, ping.stdout + ping.stderr


def test_ac11_unknown_host_key_is_recorded(ubuntu_cli, ubuntu_ip, known_hosts):
    assert not known_hosts.exists()
    proc = ubuntu_cli("--name", NAME, "--ip", ubuntu_ip)
    assert proc.returncode == 0, proc.output
    found = subprocess.run(["ssh-keygen", "-F", ubuntu_ip, "-f", str(known_hosts)], capture_output=True)
    assert found.returncode == 0


def test_ac4_second_run_is_already_onboarded(ubuntu_cli, ubuntu_ip, inventory_dir):
    first = ubuntu_cli("--name", NAME, "--ip", ubuntu_ip)
    assert first.returncode == 0, first.output
    before = snapshot(inventory_dir)
    second = ubuntu_cli("--name", NAME, "--ip", ubuntu_ip)
    assert second.returncode == 0, second.output
    assert "already onboarded" in second.output
    assert snapshot(inventory_dir) == before


def test_ac7_failed_ansible_ping_leaves_inventory_byte_identical(
    ubuntu_cli, ubuntu_ip, inventory_dir, tmp_path
):
    write_host(inventory_dir, "dc", "192.168.3.1")
    before = snapshot(inventory_dir)
    failing = tmp_path / "failing-ansible"
    failing.write_text("#!/bin/sh\necho 'ubuntu-test | UNREACHABLE!' >&2\nexit 4\n")
    failing.chmod(0o755)
    proc = ubuntu_cli("--name", NAME, "--ip", ubuntu_ip, env={"AI_DEPLOY_ANSIBLE": str(failing)})
    assert proc.returncode != 0
    assert check_tag(proc.output) == "ansible"
    assert snapshot(inventory_dir) == before


def test_ac8_existing_entry_failing_a_check_is_unchanged(
    ubuntu_cli, ubuntu_ip, inventory_dir, throwaway_key
):
    write_ubuntu_host(inventory_dir, NAME, ubuntu_ip)
    before = snapshot(inventory_dir)
    proc = ubuntu_cli("--name", NAME, "--ip", ubuntu_ip, "--key", str(throwaway_key))
    assert proc.returncode != 0
    assert check_tag(proc.output) == "authentication"
    assert snapshot(inventory_dir) == before


def test_ac9_ip_used_by_windows_entry_fails_before_network(ubuntu_cli, ubuntu_ip, inventory_dir):
    write_host(inventory_dir, "some-windows", ubuntu_ip)
    before = snapshot(inventory_dir)
    proc = ubuntu_cli("--name", NAME, "--ip", ubuntu_ip)
    assert proc.returncode != 0
    assert check_tag(proc.output) == "inventory-conflict"
    assert "some-windows" in proc.output
    assert snapshot(inventory_dir) == before


def test_ac10_changed_host_key_fails_and_is_not_replaced(
    ubuntu_cli, ubuntu_ip, known_hosts, tmp_path, inventory_dir
):
    wrong = tmp_path / "wrong_host_key"
    subprocess.run(["ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-f", str(wrong)], check=True)
    known_hosts.write_text(f"{ubuntu_ip} {wrong.with_suffix('.pub').read_text().strip()}\n")
    before = known_hosts.read_bytes()
    proc = ubuntu_cli("--name", NAME, "--ip", ubuntu_ip)
    assert proc.returncode != 0
    assert check_tag(proc.output) == "host-key"
    assert f"ssh-keygen -R {ubuntu_ip}" in proc.output
    assert known_hosts.read_bytes() == before
    assert snapshot(inventory_dir) == {}
