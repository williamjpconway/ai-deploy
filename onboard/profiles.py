"""Per-OS onboarding profiles: everything that differs between spec 001 (Windows)
and spec 007 (Ubuntu). The shared flow is in onboard/cli.py."""

from dataclasses import dataclass, field

from onboard import ubuntu, windows


@dataclass(frozen=True)
class Profile:
    prog: str  # command name, used in usage and failure messages
    group: str  # inventory group the host file puts the target in
    host_vars: dict = field(default_factory=dict)  # beyond host/connection/user/key
    os_checks: tuple = ()  # each (runner, ip, port, key, known_hosts) -> None, in order
    ping_module: str = ""


WINDOWS = Profile(
    prog="onboard-windows",
    group="windows",
    host_vars={"ansible_shell_type": "powershell"},
    os_checks=(windows.shell, windows.identity),
    ping_module="ansible.windows.win_ping",
)

UBUNTU = Profile(
    prog="onboard-ubuntu",
    group="ubuntu",
    os_checks=(ubuntu.identity, ubuntu.password_auth),
    ping_module="ansible.builtin.ping",
)
