"""onboard-windows / onboard-ubuntu: add a VM to Ansible inventory as a verified target."""

import argparse
import ipaddress
import re
import sys
from pathlib import Path

from onboard import checks, inventory
from onboard.checks import CheckFailed
from onboard.profiles import WINDOWS
from onboard.runner import Runner

DEFAULT_INVENTORY = Path.home() / ".config" / "ai-deploy" / "inventory"
DEFAULT_KEY = Path.home() / ".ssh" / "ai_deploy_targets"
DEFAULT_KNOWN_HOSTS = Path.home() / ".ssh" / "known_hosts"
NAME_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")

EXIT_CODES = {
    "usage": 2,
    "inventory-conflict": 3,
    "reachability": 4,
    "host-key": 5,
    "authentication": 6,
    "shell": 7,
    "identity": 8,
    "ansible": 9,
    "ssh": 10,
    "busy": 11,
    "prereq": 12,
    "key": 13,
    "inventory": 14,
    "password-auth": 15,
}


class _Parser(argparse.ArgumentParser):
    def error(self, message):
        raise CheckFailed("usage", message)


def parse(argv, prog):
    p = _Parser(prog=prog, description=__doc__)
    p.add_argument("--name", help="inventory name for the target, e.g. dc")
    p.add_argument("--ip", help="the target's IP address")
    p.add_argument("--inventory-dir", type=Path, default=DEFAULT_INVENTORY)
    p.add_argument("--key", type=Path, default=DEFAULT_KEY, help=argparse.SUPPRESS)
    p.add_argument("--known-hosts", type=Path, default=DEFAULT_KNOWN_HOSTS, help=argparse.SUPPRESS)
    p.add_argument("--port", type=int, default=22, help=argparse.SUPPRESS)
    args = p.parse_args(argv)

    missing = [flag for flag, value in (("--name", args.name), ("--ip", args.ip)) if not value]
    if missing:
        raise CheckFailed(
            "usage",
            f"missing {' and '.join(missing)}. Usage: {prog} --name <name> --ip <ip>",
        )
    if not NAME_PATTERN.match(args.name):
        raise CheckFailed(
            "usage",
            f"--name {args.name!r} must be letters, digits, '.', '_' or '-' "
            "(it becomes the inventory file name)",
        )
    try:
        ipaddress.ip_address(args.ip)
    except ValueError:
        raise CheckFailed("usage", f"--ip {args.ip!r} is not an IP address") from None
    if not 1 <= args.port <= 65535:
        raise CheckFailed("usage", f"--port {args.port} is outside 1-65535")
    return args


def onboard(args, runner, profile):
    try:
        with inventory.locked(args.inventory_dir):
            return _onboard(args, runner, profile)
    except inventory.Busy as e:
        raise CheckFailed(
            "busy", f"another onboarding run holds {e} - try again when it finishes"
        ) from None


def _onboard(args, runner, profile):
    try:
        hosts = inventory.load_hosts(args.inventory_dir)
    except inventory.Unreadable as e:
        raise CheckFailed(
            "inventory",
            f"can't read inventory file {e.path} ({e.reason}) - fix or move it; "
            "nothing was changed",
        ) from None
    state, conflict = inventory.find(hosts, args.name, args.ip)
    if state == "new" and (taken := inventory.file_taken(args.inventory_dir, args.name)):
        conflict = f"{taken} already exists but doesn't hold '{args.name}' ({args.ip})"
        state = "conflict"
    if state == "conflict":
        raise CheckFailed("inventory-conflict", f"{conflict} - inventory left unchanged")

    checks.key_file(args.key)
    target = (runner, args.ip, args.port, args.key, args.known_hosts)
    checks.reachability(runner, args.ip, args.port)
    for os_check in profile.os_checks:
        os_check(*target)

    ping = (args.name, args.known_hosts, profile.ping_module)
    if state == "existing":
        checks.ansible_ping(runner, args.inventory_dir, *ping)
        return f"already onboarded {args.name} ({args.ip})"

    staged = inventory.Staged(
        args.inventory_dir, args.name, args.ip, args.key, profile.group, profile.host_vars
    )
    try:
        checks.ansible_ping(runner, staged.dir, *ping)
        staged.commit()
    except inventory.Clobber as e:
        raise CheckFailed(
            "inventory-conflict", f"{e} appeared during this run - left it as it is"
        ) from None
    finally:
        staged.discard()
    return f"onboarded {args.name} ({args.ip}) into {args.inventory_dir}"


def main(argv=None, runner=None, profile=None):
    profile = profile or WINDOWS
    try:
        args = parse(sys.argv[1:] if argv is None else argv, profile.prog)
        print(onboard(args, runner or Runner(), profile))
        return 0
    except CheckFailed as e:
        print(f"{profile.prog}: FAILED [{e.check}] {e.message}", file=sys.stderr)
        return EXIT_CODES[e.check]
