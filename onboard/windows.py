"""Windows profile probes (spec 001): PowerShell shell and masterchief-as-admin."""

from onboard.checks import USER, CheckFailed, ssh

ADMINISTRATORS_SID = "S-1-5-32-544"

SHELL_PROBE = "Write-Output ('PSOK:' + $PSVersionTable.PSVersion.Major)"
IDENTITY_PROBE = (
    "$i = [Security.Principal.WindowsIdentity]::GetCurrent(); "
    "$admin = [bool]($i.Groups | Where-Object { $_.Value -eq '" + ADMINISTRATORS_SID + "' }); "
    "Write-Output ('ID:' + $i.Name + '|ADMIN:' + $admin)"
)


def auth_message(ip, key):
    return (
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
        "utils/onboarding/windows2025/Initialize-SshOnboarding.ps1 to install it."
    )


def shell(runner, ip, port, key, known_hosts):
    """R2 + R3: authenticate, and prove the remote shell is PowerShell by its output."""
    result = ssh(runner, ip, port, key, known_hosts, SHELL_PROBE, auth_message)
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
    result = ssh(runner, ip, port, key, known_hosts, IDENTITY_PROBE, auth_message)
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
