"""Ansible inventory as a directory with one <name>.yml file per host (R4, R5, R6)."""

import fcntl
import os
import shutil
import tempfile
from contextlib import contextmanager
from pathlib import Path

import yaml

GROUP = "windows"


def load_hosts(inventory_dir):
    """Every host in the inventory dir, as {name: ansible_host}."""
    hosts = {}
    root = Path(inventory_dir)
    if not root.is_dir():
        return hosts
    for path in sorted(root.glob("*.yml")) + sorted(root.glob("*.yaml")):
        data = yaml.safe_load(path.read_text()) or {}
        for group in data.values():
            for name, hostvars in ((group or {}).get("hosts") or {}).items():
                hosts[name] = (hostvars or {}).get("ansible_host", name)
    return hosts


def find(hosts, name, ip):
    """("existing", None), ("new", None) or ("conflict", description)."""
    if hosts.get(name) == ip:
        return "existing", None
    if name in hosts:
        return "conflict", f"inventory name '{name}' is already used for {hosts[name]}"
    for other, other_ip in hosts.items():
        if other_ip == ip:
            return "conflict", f"IP {ip} is already in inventory as '{other}'"
    return "new", None


def file_taken(inventory_dir, name):
    """The host file this run would create, if something already occupies it."""
    path = Path(inventory_dir) / f"{name}.yml"
    return path if path.exists() else None


class Busy(Exception):
    pass


@contextmanager
def locked(inventory_dir):
    """Hold an exclusive lock from the conflict check to the commit (R4).

    Two runs at once could otherwise both see "new" and both commit.
    """
    parent = Path(inventory_dir).parent
    parent.mkdir(parents=True, exist_ok=True)
    with open(parent / "onboard-windows.lock", "w") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise Busy(str(parent / "onboard-windows.lock")) from None
        yield


class Clobber(Exception):
    pass


def host_file(name, ip, key):
    data = {
        GROUP: {
            "hosts": {
                name: {
                    "ansible_host": ip,
                    "ansible_connection": "ssh",
                    "ansible_user": "masterchief",
                    "ansible_shell_type": "powershell",
                    "ansible_ssh_private_key_file": str(key),
                }
            }
        }
    }
    return yaml.safe_dump(data, sort_keys=False)


class Staged:
    """A one-host inventory in a temp dir beside the real one.

    commit() hard-links the host file into the real inventory - atomic, and
    fails rather than replacing a file that's already there; discard()
    deletes the staging dir. Until commit() the real inventory is never written.
    """

    def __init__(self, inventory_dir, name, ip, key):
        self.inventory_dir = Path(inventory_dir)
        self.name = name
        parent = self.inventory_dir.parent
        parent.mkdir(parents=True, exist_ok=True)
        self.dir = Path(tempfile.mkdtemp(prefix=".onboard-", dir=parent))
        self.file = self.dir / f"{name}.yml"
        self.file.write_text(host_file(name, ip, key))

    def commit(self):
        """Link the file into place. Never overwrites: raises Clobber if it exists."""
        self.inventory_dir.mkdir(parents=True, exist_ok=True)
        target = self.inventory_dir / f"{self.name}.yml"
        try:
            os.link(self.file, target)
        except FileExistsError:
            raise Clobber(str(target)) from None
        self.discard()

    def discard(self):
        shutil.rmtree(self.dir, ignore_errors=True)
