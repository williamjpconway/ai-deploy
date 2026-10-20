<#
.SYNOPSIS
    Promotes a blank Windows Server 2025 VM to the first domain
    controller of a new forest, domain.internal (NetBIOS: DOMAIN), with
    DNS installed alongside it via -InstallDns.

.DESCRIPTION
    Idempotent: if this server is already a domain controller, skips
    promotion and runs verification only. Promotion triggers an
    automatic reboot and ends the PowerShell session itself, so
    verification can't happen in the same invocation that does the
    promotion - re-run this script after the reboot completes to get
    the verification output.

    Verification checks Get-ADDomain, dcdiag, and that the core
    services (NTDS, DNS, Netlogon, KDC) are running - per AGENTS.md's
    write/test/approve rule, "ran without error" is not treated as
    "works."

    Supports -WhatIf for the promotion step (Install-ADDSForest honors
    it natively as a validation-only run); skips the password prompt
    entirely under -WhatIf since nothing would be done with it.
#>

[CmdletBinding(SupportsShouldProcess)]
param(
    [string]$DomainName = "domain.internal",
    [string]$DomainNetbiosName = "DOMAIN"
)

$ErrorActionPreference = "Stop"

function Test-DomainControllerHealth {
    Write-Host "Verifying domain controller health..."

    $domain = Get-ADDomain -ErrorAction Stop
    Write-Host "Get-ADDomain OK: $($domain.DNSRoot)"

    $dcdiagOutput = dcdiag /q
    if ($LASTEXITCODE -ne 0 -or $dcdiagOutput) {
        Write-Warning "dcdiag reported issues:"
        $dcdiagOutput | ForEach-Object { Write-Warning $_ }
        throw "dcdiag did not pass cleanly - see warnings above."
    }
    Write-Host "dcdiag OK: no issues reported"

    foreach ($svcName in 'NTDS', 'DNS', 'Netlogon', 'Kdc') {
        $status = (Get-Service -Name $svcName -ErrorAction Stop).Status
        if ($status -ne 'Running') {
            throw "Service '$svcName' is not running (status: $status)"
        }
        Write-Host "Service '$svcName': Running"
    }

    Write-Host "Domain controller health check PASSED"
}

$alreadyPromoted = $false
try {
    Get-ADDomain -ErrorAction Stop | Out-Null
    $alreadyPromoted = $true
}
catch {
    $alreadyPromoted = $false
}

if ($alreadyPromoted) {
    Write-Host "Already a domain controller for this domain - skipping promotion, running verification only."
    Test-DomainControllerHealth
    return
}

if ($WhatIfPreference) {
    Write-Host "[WhatIf] Would prompt for the DSRM password, then run:"
    Write-Host "[WhatIf]   Install-ADDSForest -DomainName $DomainName -DomainNetbiosName $DomainNetbiosName -InstallDns -Force"
    return
}

if (-not (Get-WindowsFeature -Name AD-Domain-Services).Installed) {
    Install-WindowsFeature -Name AD-Domain-Services -IncludeManagementTools | Out-Null
}

Import-Module ADDSDeployment

$dsrmPassword = $null
while ($true) {
    $attempt = Read-Host -Prompt "Safe Mode Administrator (DSRM) password" -AsSecureString
    $confirm = Read-Host -Prompt "Confirm password" -AsSecureString

    $bstr1 = [System.Runtime.InteropServices.Marshal]::SecureStringToGlobalAllocUnicode($attempt)
    $bstr2 = [System.Runtime.InteropServices.Marshal]::SecureStringToGlobalAllocUnicode($confirm)
    try {
        $matches = [System.Runtime.InteropServices.Marshal]::PtrToStringUni($bstr1) -eq [System.Runtime.InteropServices.Marshal]::PtrToStringUni($bstr2)
    }
    finally {
        [System.Runtime.InteropServices.Marshal]::ZeroFreeGlobalAllocUnicode($bstr1)
        [System.Runtime.InteropServices.Marshal]::ZeroFreeGlobalAllocUnicode($bstr2)
    }

    if ($matches) {
        $dsrmPassword = $attempt
        break
    }
    Write-Warning "Passwords did not match, try again."
}

Write-Host "Promoting this server to a new forest '$DomainName' (NetBIOS: $DomainNetbiosName)."
Write-Host "This will reboot the machine automatically once complete - that is expected, not a crash."
Write-Host "Re-run this script after the reboot to verify the result."

Install-ADDSForest `
    -DomainName $DomainName `
    -DomainNetbiosName $DomainNetbiosName `
    -InstallDns `
    -SafeModeAdministratorPassword $dsrmPassword `
    -Force
