"""onboard-windows: add a Windows VM to Ansible inventory as a verified target."""

import argparse
import ipaddress
import re
import sys
from pathlib import Path

from onboard import checks, inventory
from onboard.checks import CheckFailed
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
}


class _Parser(argparse.ArgumentParser):
    def error(self, message):
        raise CheckFailed("usage", message)


def parse(argv):
    p = _Parser(prog="onboard-windows", description=__doc__)
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
            f"missing {' and '.join(missing)}. Usage: onboard-windows --name <name> --ip <ip>",
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
    return args


def onboard(args, runner):
    try:
        with inventory.locked(args.inventory_dir):
            return _onboard(args, runner)
    except inventory.Busy as e:
        raise CheckFailed(
            "busy", f"another onboard-windows run holds {e} - try again when it finishes"
        ) from None


def _onboard(args, runner):
    hosts = inventory.load_hosts(args.inventory_dir)
    state, conflict = inventory.find(hosts, args.name, args.ip)
    if state == "new" and (taken := inventory.file_taken(args.inventory_dir, args.name)):
        conflict = f"{taken} already exists but doesn't hold '{args.name}' ({args.ip})"
        state = "conflict"
    if state == "conflict":
        raise CheckFailed("inventory-conflict", f"{conflict} - inventory left unchanged")

    target = (runner, args.ip, args.port, args.key, args.known_hosts)
    checks.reachability(runner, args.ip, args.port)
    checks.shell(*target)
    checks.identity(*target)

    if state == "existing":
        checks.ansible_ping(runner, args.inventory_dir, args.name, args.known_hosts)
        return f"already onboarded {args.name} ({args.ip})"

    staged = inventory.Staged(args.inventory_dir, args.name, args.ip, args.key)
    try:
        checks.ansible_ping(runner, staged.dir, args.name, args.known_hosts)
        staged.commit()
    except inventory.Clobber as e:
        raise CheckFailed(
            "inventory-conflict", f"{e} appeared during this run - left it as it is"
        ) from None
    finally:
        staged.discard()
    return f"onboarded {args.name} ({args.ip}) into {args.inventory_dir}"


def main(argv=None, runner=None):
    try:
        args = parse(sys.argv[1:] if argv is None else argv)
        print(onboard(args, runner or Runner()))
        return 0
    except CheckFailed as e:
        print(f"onboard-windows: FAILED [{e.check}] {e.message}", file=sys.stderr)
        return EXIT_CODES[e.check]
