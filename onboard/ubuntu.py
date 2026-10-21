"""Ubuntu profile probes (spec 007): masterchief with passwordless sudo, and
password authentication really off."""

import re

from onboard.checks import SSH_TIMEOUT, USER, CheckFailed, known_host_name, ssh, ssh_argv

PREP_SCRIPT = "utils/onboarding/ubuntu2604/initialize-ssh-onboarding.sh"
IDENTITY_PROBE = (
    "printf 'ID:%s|SUDO:' \"$(id -un)\"; "
    "if sudo -n true 2>/dev/null; then echo yes; else echo no; fi"
)
# With no key offered and the 'none' method, the server answers with the list
# of methods it would accept - what it really allows, whatever its config says.
METHODS_OPTIONS = ("-o", "PreferredAuthentications=none", "-o", "PubkeyAuthentication=no")
METHODS_REPLY = re.compile(r"Permission denied \(([^)]*)\)")
PASSWORD_METHODS = {"password", "keyboard-interactive"}


def auth_message(ip, key):
    return (
        f"{ip} rejected key {key} for {USER}. The public half ({key}.pub) must be in "
        f"/home/{USER}/.ssh/authorized_keys on the target - re-run {PREP_SCRIPT} to install it."
    )


def identity(runner, ip, port, key, known_hosts):
    """R2 + R8: authenticate, and check the session is masterchief with passwordless sudo."""
    result = ssh(runner, ip, port, key, known_hosts, IDENTITY_PROBE, auth_message)
    line = next((x.strip() for x in result.stdout.splitlines() if x.startswith("ID:")), "")
    user, _, sudo = line[3:].partition("|SUDO:")
    if user != USER:
        raise CheckFailed("identity", f"session on {ip} is {user or 'unknown'!r}, not {USER}")
    if sudo != "yes":
        raise CheckFailed(
            "identity",
            f"{USER} on {ip} can't use sudo without a password, which Ansible needs. "
            f"/etc/sudoers.d/90-{USER} must contain '{USER} ALL=(ALL) NOPASSWD:ALL' - "
            f"re-run {PREP_SCRIPT} to set it up.",
        )


def password_auth(runner, ip, port, key, known_hosts):
    """R3: the server doesn't offer password login, whatever its config files say."""
    argv = ssh_argv(ip, port, key, known_hosts, "exit", extra_options=METHODS_OPTIONS)
    result = runner.run(argv, timeout=SSH_TIMEOUT)
    err = result.stderr
    if "Host key verification failed" in err:
        raise CheckFailed(
            "host-key",
            f"{ip}'s SSH host key changed between checks - clear it with: "
            f"ssh-keygen -R {known_host_name(ip, port)} -f {known_hosts}",
        )
    match = METHODS_REPLY.search(err)
    if result.timed_out or result.returncode != 255 or not match:
        raise CheckFailed(
            "password-auth",
            f"couldn't tell which login methods {ip} offers, so password login can't be "
            f"ruled out (ssh exit {result.returncode}: {err.strip()[:200] or 'no output'})",
        )
    offered = {m.strip() for m in match.group(1).split(",")}
    if offered & PASSWORD_METHODS:
        raise CheckFailed(
            "password-auth",
            f"{ip} still offers password login (methods: {', '.join(sorted(offered))}). "
            "On Ubuntu, cloud-init can silently turn it back on. "
            "/etc/ssh/sshd_config.d/00-keys-only.conf must set PasswordAuthentication no and "
            "KbdInteractiveAuthentication no (it sorts first, so it wins), 50-cloud-init.conf "
            "should say no as well, then restart ssh.socket and ssh.service - "
            f"{PREP_SCRIPT} sets this up.",
        )
