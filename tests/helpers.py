"""Shared test helpers: a stub Runner and a directory snapshot."""

import os
from pathlib import Path

import pytest
import yaml

from onboard.runner import Result

GOOD_SHELL = "PSOK:5"
GOOD_IDENTITY = "ID:LAB\\masterchief|ADMIN:True"
CMD_EXE_ERROR = (
    "'Write-Output' is not recognized as an internal or external command,\r\n"
    "operable program or batch file.\r\n"
)


class StubRunner:
    """Answers onboarding's processes without a network.

    Classifies each command by what it is: the Ansible ping, the identity
    probe (asks for the Administrators SID) or the shell probe (PSOK marker).
    """

    def __init__(
        self,
        shell_probe=(0, GOOD_SHELL, ""),
        identity=(0, GOOD_IDENTITY, ""),
        ansible_rc=0,
        tcp_error=None,
        ssh_timeout=False,
        on_ping=None,
    ):
        self.shell_probe = shell_probe
        self.identity = identity
        self.ansible_rc = ansible_rc
        self.tcp_error = tcp_error
        self.ssh_timeout = ssh_timeout
        self.on_ping = on_ping
        self.calls = []

    def tcp_connect(self, host, port, timeout):
        self.calls.append(("tcp", host, port))
        if self.tcp_error:
            raise self.tcp_error

    def run(self, argv, timeout, env=None):
        self.calls.append(("run", list(argv), env))
        joined = " ".join(argv)
        if "win_ping" in joined:
            if self.on_ping:
                self.on_ping()
            err = "" if self.ansible_rc == 0 else "win-test | UNREACHABLE!"
            return Result(self.ansible_rc, "", err)
        if self.ssh_timeout and argv[0] == "ssh":
            return Result(124, "", f"timed out after {timeout}s", timed_out=True)
        if "S-1-5-32-544" in joined:
            return Result(*self.identity)
        if "PSOK" in joined:
            return Result(*self.shell_probe)
        raise AssertionError(f"unexpected command: {argv}")


def snapshot(path):
    """Every file under path, as {relative path: bytes}. Missing dir -> {}."""
    root = Path(path)
    if not root.exists():
        return {}
    return {str(p.relative_to(root)): p.read_bytes() for p in root.rglob("*") if p.is_file()}


def write_host(inventory_dir, name, ip, key="~/.ssh/ai_deploy_targets"):
    """Seed an inventory host file in the format R5 describes."""
    inventory_dir = Path(inventory_dir)
    inventory_dir.mkdir(parents=True, exist_ok=True)
    data = {
        "windows": {
            "hosts": {
                name: {
                    "ansible_host": ip,
                    "ansible_connection": "ssh",
                    "ansible_user": "masterchief",
                    "ansible_shell_type": "powershell",
                    "ansible_ssh_private_key_file": key,
                }
            }
        }
    }
    (inventory_dir / f"{name}.yml").write_text(yaml.safe_dump(data, sort_keys=False))


def check_tag(output):
    """The [check] tag from a FAILED line, or None."""
    for line in output.splitlines():
        if "FAILED [" in line:
            return line.split("FAILED [", 1)[1].split("]", 1)[0]
    return None


GOOD_UBUNTU_IDENTITY = "ID:masterchief|SUDO:yes"
KEYS_ONLY = "masterchief@192.168.3.1: Permission denied (publickey).\r\n"


class UbuntuStubRunner(StubRunner):
    """Answers onboard-ubuntu's processes: the identity/sudo probe (`sudo -n true`),
    the offered-auth-methods probe (`PreferredAuthentications=none`) and the
    Ansible ping. Anything else - e.g. a Windows probe - is a test failure."""

    def __init__(self, identity=(0, GOOD_UBUNTU_IDENTITY, ""), methods=(255, "", KEYS_ONLY), **kw):
        super().__init__(identity=identity, **kw)
        self.methods = methods

    def run(self, argv, timeout, env=None):
        self.calls.append(("run", list(argv), env))
        joined = " ".join(argv)
        if "ansible.builtin.ping" in joined:
            if self.on_ping:
                self.on_ping()
            err = "" if self.ansible_rc == 0 else "ubuntu-test | UNREACHABLE!"
            return Result(self.ansible_rc, "", err)
        if self.ssh_timeout and argv[0] == "ssh":
            return Result(124, "", f"timed out after {timeout}s", timed_out=True)
        if "PreferredAuthentications=none" in joined:
            return Result(*self.methods)
        if "sudo -n true" in joined:
            return Result(*self.identity)
        raise AssertionError(f"unexpected command for onboard-ubuntu: {argv}")


def write_ubuntu_host(inventory_dir, name, ip, key="~/.ssh/ai_deploy_targets"):
    """Seed an Ubuntu inventory host file in the format 007's R5 describes."""
    inventory_dir = Path(inventory_dir)
    inventory_dir.mkdir(parents=True, exist_ok=True)
    data = {
        "ubuntu": {
            "hosts": {
                name: {
                    "ansible_host": ip,
                    "ansible_connection": "ssh",
                    "ansible_user": "masterchief",
                    "ansible_ssh_private_key_file": key,
                }
            }
        }
    }
    (inventory_dir / f"{name}.yml").write_text(yaml.safe_dump(data, sort_keys=False))


def require_slot_or_confirmed(config, ip):
    """Skip unless ip is the lab slot (AI_DEPLOY_TEST_LAB_VMID) or named with
    --confirmed-target. Destructive fixtures call this before changing anything:
    slots need no confirmation, everything else does (AGENTS.md)."""
    vmid = os.environ.get("AI_DEPLOY_TEST_LAB_VMID")
    slot_ip = None
    if vmid:
        from testlab import proxmox

        slot_ip = proxmox.ipv4(vmid)
        if slot_ip == ip:
            return
    if ip in config.getoption("--confirmed-target"):
        return
    where = f"slot {vmid} is at {slot_ip}, not {ip}; " if vmid else ""
    pytest.skip(f"{ip} is not a test slot - {where}needs --confirmed-target={ip} (nothing changed)")
