"""The checks onboarding runs against a target, in order. Each raises CheckFailed."""

import os
import shlex
import shutil
import stat
from pathlib import Path

USER = "masterchief"
ADMINISTRATORS_SID = "S-1-5-32-544"
TCP_TIMEOUT = 5
SSH_TIMEOUT = 60
ANSIBLE_TIMEOUT = 120

SHELL_PROBE = "Write-Output ('PSOK:' + $PSVersionTable.PSVersion.Major)"
IDENTITY_PROBE = (
    "$i = [Security.Principal.WindowsIdentity]::GetCurrent(); "
    "$admin = [bool]($i.Groups | Where-Object { $_.Value -eq '" + ADMINISTRATORS_SID + "' }); "
    "Write-Output ('ID:' + $i.Name + '|ADMIN:' + $admin)"
)


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


def ssh_argv(ip, port, key, known_hosts, command):
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
        f"{USER}@{ip}",
        command,
    ]


def ssh(runner, ip, port, key, known_hosts, command):
    """Run one command over SSH, turning host-key and auth refusals into R9/R2 failures."""
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
            raise CheckFailed(
                "authentication",
                f"{ip} rejected key {key} for {USER}. sshd can't tell these apart, so "
                "check both on the target:\n"
                f"  1. {USER} must be in the Administrators group (sshd only reads "
                "administrators_authorized_keys for its members). Add it with:\n"
                f"       domain controller: Add-ADGroupMember -Identity S-1-5-32-544 "
                f"-Members {USER}\n"
                f"       other servers:     Add-LocalGroupMember -SID S-1-5-32-544 "
                f"-Member {USER}\n"
                f"  2. The public half of the key ({key}.pub) must be in "
                "C:\\ProgramData\\ssh\\administrators_authorized_keys - re-run "
                "utils/onboarding/windows2025/Initialize-SshOnboarding.ps1 to install it.",
            )
        raise CheckFailed("ssh", f"SSH to {ip} failed: {err.strip() or 'no error output'}")
    return result


def shell(runner, ip, port, key, known_hosts):
    """R2 + R3: authenticate, and prove the remote shell is PowerShell by its output."""
    result = ssh(runner, ip, port, key, known_hosts, SHELL_PROBE)
    for line in result.stdout.splitlines():
        line = line.strip()
        if line.startswith("PSOK:") and line[5:].isdigit():
            return
    raise CheckFailed(
        "shell",
        f"{ip}'s SSH shell is not PowerShell (probe output: "
        f"{(result.stdout + result.stderr).strip()[:200]!r}). Windows OpenSSH defaults to "
        "cmd.exe until HKLM:\\SOFTWARE\\OpenSSH DefaultShell is set to powershell.exe.",
    )


def identity(runner, ip, port, key, known_hosts):
    """R8: the session is masterchief and a member of Administrators."""
    result = ssh(runner, ip, port, key, known_hosts, IDENTITY_PROBE)
    line = next((x.strip() for x in result.stdout.splitlines() if x.startswith("ID:")), "")
    name, _, admin = line[3:].partition("|ADMIN:")
    account = name.rsplit("\\", 1)[-1]
    if account.lower() != USER:
        raise CheckFailed("identity", f"session on {ip} is {name or 'unknown'!r}, not {USER}")
    if admin != "True":
        raise CheckFailed(
            "identity",
            f"session on {ip} is {name} but it isn't a member of Administrators "
            f"({ADMINISTRATORS_SID}). Add it with: Add-ADGroupMember -Identity "
            f"{ADMINISTRATORS_SID} -Members {USER} (domain controller) or "
            f"Add-LocalGroupMember -SID {ADMINISTRATORS_SID} -Member {USER} (other servers)",
        )


def ansible_bin():
    override = os.environ.get("AI_DEPLOY_ANSIBLE")
    if override:
        return override
    return shutil.which("ansible") or str(Path.home() / ".local" / "bin" / "ansible")


def ansible_ping(runner, inventory, name, known_hosts):
    """R6: Ansible itself reaches the target through the given inventory."""
    env = dict(
        os.environ,
        # Ansible shlex-splits this, then ssh parses the quoted value itself.
        ANSIBLE_SSH_COMMON_ARGS="-o " + shlex.quote(known_hosts_option(known_hosts)),
        ANSIBLE_HOST_KEY_CHECKING="True",
    )
    result = runner.run(
        [ansible_bin(), "-i", str(inventory), name, "-m", "ansible.windows.win_ping"],
        timeout=ANSIBLE_TIMEOUT,
        env=env,
    )
    if result.returncode != 0:
        detail = (result.stdout + result.stderr).strip()[-400:]
        raise CheckFailed(
            "ansible",
            f"Ansible could not reach {name} through its inventory entry "
            f"(win_ping exit {result.returncode}): {detail}",
        )
