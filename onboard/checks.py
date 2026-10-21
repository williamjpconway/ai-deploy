"""Checks shared by every OS profile. Each raises CheckFailed.

OS-specific probes live in onboard/windows.py and onboard/ubuntu.py.
"""

import os
import shlex
import shutil
import stat
from pathlib import Path

USER = "masterchief"
TCP_TIMEOUT = 5
SSH_TIMEOUT = 60
ANSIBLE_TIMEOUT = 120


class CheckFailed(Exception):
    def __init__(self, check, message):
        super().__init__(message)
        self.check = check
        self.message = message


def key_file(path):
    """Key B is usable on ai-deploy, before blaming the target for a rejection."""
    if not path.is_file():
        raise CheckFailed(
            "key",
            f"key {path} does not exist on ai-deploy - generate it with "
            "utils/prereqs/ai-deploy/new-target-key.sh, then install its .pub on the target",
        )
    if not os.access(path, os.R_OK):
        raise CheckFailed("key", f"key {path} isn't readable by this user on ai-deploy")
    if stat.S_IMODE(path.stat().st_mode) & 0o077:
        raise CheckFailed(
            "key",
            f"key {path} is readable by other users, so ssh will refuse to use it - "
            f"fix with: chmod 600 {path}",
        )


def reachability(runner, ip, port):
    """R1: plain TCP to the SSH port, before any authentication."""
    try:
        runner.tcp_connect(ip, port, TCP_TIMEOUT)
    except ConnectionRefusedError:
        raise CheckFailed(
            "reachability",
            f"{ip}:{port} refused the connection - nothing is listening for SSH there "
            "(is sshd running?)",
        ) from None
    except TimeoutError:
        raise CheckFailed(
            "reachability",
            f"{ip}:{port} did not answer within {TCP_TIMEOUT}s - the host is down, "
            "or a firewall is dropping SSH (check the OpenSSH-Server-In-TCP rule's profile)",
        ) from None
    except OSError as e:
        raise CheckFailed(
            "reachability", f"{ip}:{port} is unreachable: {e.strerror or e}"
        ) from None


def known_host_name(ip, port):
    """How known_hosts names this target: bare IP on 22, '[ip]:port' otherwise."""
    return ip if port == 22 else f"'[{ip}]:{port}'"


def known_hosts_option(known_hosts):
    # ssh splits UserKnownHostsFile on whitespace unless the value is quoted.
    return f'UserKnownHostsFile="{known_hosts}"'


def ssh_argv(ip, port, key, known_hosts, command, extra_options=()):
    return [
        "ssh",
        "-F",
        "/dev/null",
        "-p",
        str(port),
        "-i",
        str(key),
        "-o",
        "IdentitiesOnly=yes",
        "-o",
        "BatchMode=yes",
        "-o",
        "ConnectTimeout=10",
        # R9: OpenSSH's own trust-on-first-use. Unknown keys are recorded,
        # changed keys are refused and never replaced.
        "-o",
        "StrictHostKeyChecking=accept-new",
        "-o",
        known_hosts_option(known_hosts),
        *extra_options,
        f"{USER}@{ip}",
        command,
    ]


def ssh(runner, ip, port, key, known_hosts, command, auth_message):
    """Run one command over SSH, turning host-key and auth refusals into R9/R2 failures.

    auth_message(ip, key) is the OS profile's explanation of a rejected key.
    """
    result = runner.run(ssh_argv(ip, port, key, known_hosts, command), timeout=SSH_TIMEOUT)
    if result.timed_out:
        # TCP already answered (R1), so this is a stalled session, not a shell problem.
        raise CheckFailed(
            "ssh",
            f"SSH to {ip} connected but the session didn't finish within {SSH_TIMEOUT}s - "
            "the target is slow or hung (e.g. a user profile load). Nothing about its "
            "shell or identity was checked.",
        )
    if result.returncode == 255:
        err = result.stderr
        if "REMOTE HOST IDENTIFICATION HAS CHANGED" in err or "Host key verification failed" in err:
            raise CheckFailed(
                "host-key",
                f"{ip} presented a different SSH host key from the one recorded in "
                f"{known_hosts}. If the VM was rebuilt or the IP reused, clear the old key "
                f"with: ssh-keygen -R {known_host_name(ip, port)} -f {known_hosts}",
            )
        if "Permission denied" in err:
            raise CheckFailed("authentication", auth_message(ip, key))
        raise CheckFailed("ssh", f"SSH to {ip} failed: {err.strip() or 'no error output'}")
    return result


def ansible_bin():
    override = os.environ.get("AI_DEPLOY_ANSIBLE")
    if override:
        return override
    return shutil.which("ansible") or str(Path.home() / ".local" / "bin" / "ansible")


def ansible_ping(runner, inventory, name, known_hosts, module):
    """R6: Ansible itself reaches the target through the given inventory."""
    env = dict(
        os.environ,
        # Ansible shlex-splits this, then ssh parses the quoted value itself.
        ANSIBLE_SSH_COMMON_ARGS="-o " + shlex.quote(known_hosts_option(known_hosts)),
        ANSIBLE_HOST_KEY_CHECKING="True",
    )
    result = runner.run(
        [ansible_bin(), "-i", str(inventory), name, "-m", module],
        timeout=ANSIBLE_TIMEOUT,
        env=env,
    )
    if result.returncode != 0:
        detail = (result.stdout + result.stderr).strip()[-400:]
        raise CheckFailed(
            "ansible",
            f"Ansible could not reach {name} through its inventory entry "
            f"({module.rsplit('.', 1)[-1]} exit {result.returncode}): {detail}",
        )
