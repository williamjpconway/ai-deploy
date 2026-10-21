import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
CLI = REPO / "bin" / "onboard-windows"
KEY_B = Path.home() / ".ssh" / "ai_deploy_targets"


def pytest_addoption(parser):
    parser.addoption(
        "--allow-destructive",
        action="store_true",
        help="run tests that change the target VM (operator confirms each run)",
    )


def pytest_collection_modifyitems(config, items):
    target = os.environ.get("AI_DEPLOY_TEST_TARGET")
    destructive_ok = config.getoption("--allow-destructive")
    for item in items:
        if "live" in item.keywords and not target:
            item.add_marker(pytest.mark.skip(reason="AI_DEPLOY_TEST_TARGET not set"))
        if "destructive" in item.keywords and not destructive_ok:
            item.add_marker(pytest.mark.skip(reason="needs --allow-destructive"))


@pytest.fixture
def target_ip():
    return os.environ["AI_DEPLOY_TEST_TARGET"]


@pytest.fixture
def inventory_dir(tmp_path):
    return tmp_path / "inventory"


@pytest.fixture
def known_hosts(tmp_path):
    return tmp_path / "known_hosts"


@pytest.fixture
def cli(inventory_dir, known_hosts):
    """Run bin/onboard-windows as a process, against temp inventory and known_hosts."""

    def run(*args, env=None):
        argv = [sys.executable, str(CLI), *args]
        if "--inventory-dir" not in args:
            argv += ["--inventory-dir", str(inventory_dir)]
        if "--known-hosts" not in args:
            argv += ["--known-hosts", str(known_hosts)]
        full_env = dict(os.environ, **(env or {}))
        proc = subprocess.run(argv, capture_output=True, text=True, timeout=120, env=full_env)
        proc.output = proc.stdout + proc.stderr
        return proc

    return run


@pytest.fixture
def throwaway_key(tmp_path):
    """An ed25519 key no target has ever seen."""
    path = tmp_path / "throwaway"
    subprocess.run(
        ["ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-f", str(path)], check=True
    )
    return path


def target_ssh(ip, known_hosts, command):
    """Run one command on the test target as masterchief with Key B."""
    return subprocess.run(
        [
            "ssh",
            "-F", "/dev/null",
            "-i", str(KEY_B),
            "-o", "IdentitiesOnly=yes",
            "-o", "BatchMode=yes",
            "-o", "StrictHostKeyChecking=accept-new",
            "-o", f"UserKnownHostsFile={known_hosts}",
            f"masterchief@{ip}",
            command,
        ],
        capture_output=True,
        text=True,
        timeout=60,
    )
