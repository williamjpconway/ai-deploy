"""Ansible inventory as a directory with one <name>.yml file per host (R4, R5, R6)."""

import os
import shutil
import tempfile
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

    commit() moves the host file into the real inventory with an atomic
    rename (same filesystem); discard() deletes it. Until commit() the real
    inventory is never written.
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
        self.inventory_dir.mkdir(parents=True, exist_ok=True)
        os.replace(self.file, self.inventory_dir / f"{self.name}.yml")
        self.discard()

    def discard(self):
        shutil.rmtree(self.dir, ignore_errors=True)
