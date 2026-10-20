<#
.SYNOPSIS
    Duplicates every existing certificate template into a lab-<name> copy
    with a 2-year validity period, down from the source templates' 5-year
    validity.

.DESCRIPTION
    Uses PSPKI to enumerate templates and (eventually) to manage Enroll
    ACLs on the new lab templates. Duplication itself - a new AD object,
    a new template OID, and an adjusted pKIExpirationPeriod/
    pKIOverlapPeriod - is not a single cmdlet even in PSPKI, so it's done
    directly via ADSI here. This is the one fragile part of this script:
    OID generation is a reasonable approximation, not a collision
    guarantee. Verify each lab-* template in the Certificate Templates
    console (certtmpl.msc) before publishing it on the CA.

    Idempotent: skips source templates already named "lab-*", and skips
    creating a lab copy that already exists.

    Supports -WhatIf: direct ADSI calls don't honor -WhatIf on their
    own, so template creation is explicitly gated on
    $PSCmdlet.ShouldProcess - run with -WhatIf first to see which
    lab-* templates would be created, per AGENTS.md's write/test/approve
    rule for scripts.
#>

#Requires -Modules ActiveDirectory

[CmdletBinding(SupportsShouldProcess)]
param(
    [TimeSpan]$LabValidityPeriod = (New-TimeSpan -Days (2 * 365)),
    [TimeSpan]$LabRenewalPeriod = (New-TimeSpan -Days (6 * 7))
)

$ErrorActionPreference = "Stop"

if (-not (Get-Module -ListAvailable -Name PSPKI)) {
    # Windows PowerShell 5.1 doesn't enable TLS 1.2 by default on a fresh
    # install; PSGallery/NuGet require it, and without this the download
    # fails with a misleading "0x80070002 file not found" error instead
    # of a clear TLS error.
    [Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12

    if (-not (Get-PackageProvider -Name NuGet -ErrorAction SilentlyContinue | Where-Object { $_.Version -ge [version]'2.8.5.201' })) {
        Write-Host "NuGet provider not found or too old, installing..."
        Install-PackageProvider -Name NuGet -MinimumVersion 2.8.5.201 -Force
    }

    Write-Host "PSPKI module not found, installing from PowerShell Gallery..."
    Install-Module -Name PSPKI -Scope CurrentUser -Force -AllowClobber
}
Import-Module PSPKI

function ConvertTo-PeriodBytes {
    param([TimeSpan]$Period)
    [BitConverter]::GetBytes(-$Period.Ticks)
}

function New-TemplateOid {
    # Mirrors the shape of OIDs AD CS itself generates (forest base OID
    # plus a random suffix). Good enough for a lab; not a substitute for
    # checking the OID container for collisions in anything beyond a lab.
    $configNC = (Get-ADRootDSE).configurationNamingContext
    $oidContainer = "CN=OID,CN=Public Key Services,CN=Services,$configNC"
    $baseOid = (Get-ADObject -SearchBase $oidContainer -Filter "objectClass -eq 'msPKI-Enterprise-Oid'" -Properties 'msPKI-Cert-Template-OID' |
        Select-Object -First 1 -ExpandProperty 'msPKI-Cert-Template-OID') -replace '\.\d+\.\d+$', ''
    "$baseOid.$(Get-Random -Minimum 1000000 -Maximum 99999999).$(Get-Random -Minimum 10000000 -Maximum 99999999)"
}

# Attributes that must never be copied verbatim onto the new object.
$skipAttributes = @(
    'cn', 'name', 'displayName', 'distinguishedName', 'objectGUID',
    'whenCreated', 'whenChanged', 'uSNCreated', 'uSNChanged',
    'msPKI-Cert-Template-OID', 'nTSecurityDescriptor', 'instanceType',
    'objectCategory'
)

$templates = Get-CertificateTemplate | Where-Object { $_.Name -notlike 'lab-*' }

foreach ($template in $templates) {
    $labName = "lab-$($template.Name)"

    if (Get-CertificateTemplate -Name $labName -ErrorAction SilentlyContinue) {
        Write-Host "Lab copy '$labName' already exists, skipping"
        continue
    }

    if (-not $PSCmdlet.ShouldProcess($labName, "Create lab certificate template from '$($template.Name)'")) {
        continue
    }

    $sourceDN = $template.Properties.DistinguishedName
    $sourceEntry = [adsi]"LDAP://$sourceDN"
    $parentDN = $sourceEntry.Parent -replace '^LDAP://', ''
    $parentEntry = [adsi]"LDAP://$parentDN"

    $newEntry = $parentEntry.Create('pKICertificateTemplate', "CN=$labName")
    foreach ($propName in $sourceEntry.Properties.PropertyNames) {
        if ($propName -in $skipAttributes) { continue }
        try {
            $newEntry.Put($propName, $sourceEntry.Properties[$propName].Value)
        }
        catch {
            Write-Warning "Skipped read-only/unsupported attribute '$propName' on '$labName': $($_.Exception.Message)"
        }
    }
    $newEntry.Put('displayName', $labName)
    $newEntry.Put('msPKI-Cert-Template-OID', (New-TemplateOid))
    $newEntry.Put('pKIExpirationPeriod', (ConvertTo-PeriodBytes $LabValidityPeriod))
    $newEntry.Put('pKIOverlapPeriod', (ConvertTo-PeriodBytes $LabRenewalPeriod))
    $newEntry.SetInfo()

    Write-Host "Created '$labName' from '$($template.Name)' - validity $($LabValidityPeriod.Days) days (verify in certtmpl.msc before publishing on the CA)"
}
