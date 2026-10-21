"""Shared test helpers: a stub Runner and a directory snapshot."""

from pathlib import Path

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
        self.calls.append(("run", list(argv)))
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
