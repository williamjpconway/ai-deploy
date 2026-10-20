<#
.SYNOPSIS
    Prepares a Windows VM template/image for SSH onboarding by
    ai-deploy: installs OpenSSH Server, fixes its firewall rule's
    profile scope, sets PowerShell as the default shell, and installs
    Key B's public key with the correct restrictive ACLs.

.DESCRIPTION
    Run this once when building a Windows VM template/golden image -
    not per-VM, and not by onboarding itself. Onboarding assumes SSH
    access is already pre-baked in (see BRIEF.md's Shape); this script
    is what makes that assumption true, matching the explicit non-goal
    that onboarding never provisions or configures a target VM itself.

    Every step here exists because it was a real, confirmed gap on dc
    on 2026-10-20, not a hypothetical:
    - OpenSSH Server's auto-created firewall rule defaults to the
      Private profile only, which a domain-joined server's
      DomainAuthenticated connection does not match - sshd listens
      fine, but inbound port 22 is silently blocked anyway.
    - Windows OpenSSH's default shell is cmd.exe, not PowerShell,
      until set explicitly via the registry.
    - The public key must go in administrators_authorized_keys (not
      the user's own .ssh/authorized_keys) for an Administrators-group
      account, with inheritance removed and only SYSTEM + Administrators
      granted - sshd rejects the file otherwise.

    Idempotent: each step checks current state first and skips if
    already correct.

    Supports -WhatIf.
#>

[CmdletBinding(SupportsShouldProcess)]
param(
    [Parameter(Mandatory)]
    [string]$PublicKey
)

$ErrorActionPreference = "Stop"

function Test-SshOnboardingHealth {
    Write-Host "Verifying SSH onboarding readiness..."

    $sshdStatus = (Get-Service -Name sshd -ErrorAction Stop).Status
    if ($sshdStatus -ne 'Running') {
        throw "sshd is not running (status: $sshdStatus)"
    }
    Write-Host "sshd: Running"

    $rule = Get-NetFirewallRule -Name 'OpenSSH-Server-In-TCP' -ErrorAction Stop
    if ($rule.Profile -notmatch 'Any|Domain') {
        throw "Firewall rule 'OpenSSH-Server-In-TCP' profile is '$($rule.Profile)', not scoped to allow Domain/Any"
    }
    Write-Host "Firewall rule profile: $($rule.Profile)"

    $defaultShell = (Get-ItemProperty -Path "HKLM:\SOFTWARE\OpenSSH" -Name DefaultShell -ErrorAction Stop).DefaultShell
    if ($defaultShell -notlike '*powershell.exe*') {
        throw "Default SSH shell is '$defaultShell', not PowerShell"
    }
    Write-Host "Default shell: $defaultShell"

    $keysPath = "$env:ProgramData\ssh\administrators_authorized_keys"
    if (-not (Test-Path $keysPath)) {
        throw "administrators_authorized_keys does not exist at $keysPath"
    }
    $content = Get-Content $keysPath -Raw
    if ($content.Trim() -notmatch [regex]::Escape($PublicKey.Trim())) {
        throw "administrators_authorized_keys exists but does not contain the expected public key"
    }
    Write-Host "administrators_authorized_keys: present and contains the expected key"

    Write-Host "SSH onboarding readiness check PASSED"
}

if ($WhatIfPreference) {
    Write-Host "[WhatIf] Would ensure OpenSSH.Server is installed, sshd is running and set to auto-start,"
    Write-Host "[WhatIf] the firewall rule allows Domain/Any profile, the default shell is PowerShell,"
    Write-Host "[WhatIf] and the given public key is in administrators_authorized_keys with correct ACLs."
    return
}

$capability = Get-WindowsCapability -Online -Name 'OpenSSH.Server~~~~0.0.1.0'
if ($capability.State -ne 'Installed') {
    Add-WindowsCapability -Online -Name 'OpenSSH.Server~~~~0.0.1.0' | Out-Null
    Write-Host "Installed OpenSSH.Server"
}
else {
    Write-Host "OpenSSH.Server already installed, skipping"
}

if ((Get-Service -Name sshd).Status -ne 'Running') {
    Start-Service sshd
    Write-Host "Started sshd"
}
else {
    Write-Host "sshd already running, skipping"
}
Set-Service -Name sshd -StartupType Automatic

$rule = Get-NetFirewallRule -Name 'OpenSSH-Server-In-TCP' -ErrorAction SilentlyContinue
if (-not $rule) {
    New-NetFirewallRule -Name 'OpenSSH-Server-In-TCP' -DisplayName 'OpenSSH Server (sshd)' -Enabled True -Direction Inbound -Protocol TCP -Action Allow -LocalPort 22 -Profile Any | Out-Null
    Write-Host "Created firewall rule scoped to all profiles"
}
elseif ($rule.Profile -notmatch 'Any') {
    Set-NetFirewallRule -Name 'OpenSSH-Server-In-TCP' -Profile Any
    Write-Host "Updated firewall rule to all profiles (was: $($rule.Profile))"
}
else {
    Write-Host "Firewall rule already scoped to all profiles, skipping"
}

$currentShell = (Get-ItemProperty -Path "HKLM:\SOFTWARE\OpenSSH" -Name DefaultShell -ErrorAction SilentlyContinue).DefaultShell
$powershellPath = "C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe"
if ($currentShell -ne $powershellPath) {
    New-ItemProperty -Path "HKLM:\SOFTWARE\OpenSSH" -Name DefaultShell -Value $powershellPath -PropertyType String -Force | Out-Null
    Write-Host "Set default SSH shell to PowerShell"
    Restart-Service sshd
}
else {
    Write-Host "Default SSH shell already PowerShell, skipping"
}

$keysPath = "$env:ProgramData\ssh\administrators_authorized_keys"
$needsWrite = $true
if (Test-Path $keysPath) {
    $existing = Get-Content $keysPath -Raw
    if ($existing.Trim() -match [regex]::Escape($PublicKey.Trim())) {
        $needsWrite = $false
    }
}
if ($needsWrite) {
    Set-Content -Path $keysPath -Value $PublicKey -Encoding ASCII -Force
    icacls $keysPath /inheritance:r | Out-Null
    icacls $keysPath /grant "SYSTEM:F" | Out-Null
    icacls $keysPath /grant "BUILTIN\Administrators:F" | Out-Null
    Write-Host "Installed public key into administrators_authorized_keys with correct ACLs"
}
else {
    Write-Host "Public key already present in administrators_authorized_keys, skipping"
}

Test-SshOnboardingHealth
