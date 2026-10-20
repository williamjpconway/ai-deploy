<#
.SYNOPSIS
    One-time AD prerequisite setup for ai-deploy: creates the ai-deploy OU,
    the ai-deploy-operators security group, and the masterchief user.

.DESCRIPTION
    Must be run by an account with rights to create OUs, groups and users
    in the target domain (Domain Admin, until least-privilege delegation
    is set up separately — see AGENTS.md). Idempotent: skips anything
    that already exists instead of failing on re-run.

    Supports -WhatIf: run with -WhatIf first to see what would be
    created before running for real, per AGENTS.md's write/test/approve
    rule for scripts.
#>

#Requires -Modules ActiveDirectory

[CmdletBinding(SupportsShouldProcess)]
param(
    [string]$DomainDN = "DC=domain,DC=internal",
    [string]$OuName = "ai-deploy",
    [string]$GroupName = "ai-deploy-operators",
    [string]$UserName = "masterchief"
)

$ErrorActionPreference = "Stop"
$ouPath = "OU=$OuName,$DomainDN"

if (-not (Get-ADOrganizationalUnit -Filter "Name -eq '$OuName'" -SearchBase $DomainDN -SearchScope OneLevel -ErrorAction SilentlyContinue)) {
    New-ADOrganizationalUnit -Name $OuName -Path $DomainDN -ProtectedFromAccidentalDeletion $true
    Write-Host "Created OU '$OuName' at $ouPath"
}
else {
    Write-Host "OU '$OuName' already exists at $ouPath, skipping"
}

if (-not (Get-ADGroup -Filter "Name -eq '$GroupName'" -ErrorAction SilentlyContinue)) {
    New-ADGroup -Name $GroupName -GroupScope Global -GroupCategory Security -Path $ouPath
    Write-Host "Created security group '$GroupName' in $ouPath"
}
else {
    Write-Host "Security group '$GroupName' already exists, skipping"
}

if (Get-ADUser -Filter "SamAccountName -eq '$UserName'" -ErrorAction SilentlyContinue) {
    Write-Host "User '$UserName' already exists, skipping creation"
}
else {
    $securePassword = $null
    while ($true) {
        $attempt = Read-Host -Prompt "Password for $UserName" -AsSecureString
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
            $securePassword = $attempt
            break
        }
        Write-Warning "Passwords did not match, try again."
    }

    New-ADUser -Name $UserName -SamAccountName $UserName -Path $ouPath `
        -AccountPassword $securePassword -Enabled $true -ChangePasswordAtLogon $false
    Write-Host "Created user '$UserName' in $ouPath"
}

Add-ADGroupMember -Identity $GroupName -Members $UserName -ErrorAction SilentlyContinue
Write-Host "Ensured '$UserName' is a member of '$GroupName'"
