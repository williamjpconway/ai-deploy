<#
.SYNOPSIS
    Installs an Enterprise Root CA plus the Web Enrollment role only -
    no OCSP, NDES, or CEP/CES.

.DESCRIPTION
    Idempotent: if the CertSvc service already exists, skips install
    and runs verification only.

    Verification specifically targets the "CA isn't opening" failure
    mode seen before: confirms CertSvc is actually running (not just
    installed), that certutil -ping succeeds, and that the Web
    Enrollment site actually responds at https://localhost/certsrv -
    "installed without error" is not treated as "works," per
    AGENTS.md's write/test/approve rule.

    Supports -WhatIf for the install step.
#>

[CmdletBinding(SupportsShouldProcess)]
param()

$ErrorActionPreference = "Stop"

function Test-CAHealth {
    Write-Host "Verifying CA health..."

    $svc = Get-Service -Name CertSvc -ErrorAction Stop
    if ($svc.Status -ne 'Running') {
        throw "CertSvc is not running (status: $($svc.Status))"
    }
    Write-Host "CertSvc: Running"

    certutil -ping | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "certutil -ping failed (exit code $LASTEXITCODE) - the CA is not responding"
    }
    Write-Host "certutil -ping: OK"

    $prevCallback = [System.Net.ServicePointManager]::ServerCertificateValidationCallback
    [System.Net.ServicePointManager]::ServerCertificateValidationCallback = { $true }
    try {
        $response = Invoke-WebRequest -Uri "https://localhost/certsrv" -UseDefaultCredentials -ErrorAction Stop
        if ($response.StatusCode -ne 200) {
            throw "Web Enrollment returned status $($response.StatusCode), expected 200"
        }
        Write-Host "Web Enrollment (https://localhost/certsrv): OK (200)"
    }
    finally {
        [System.Net.ServicePointManager]::ServerCertificateValidationCallback = $prevCallback
    }

    Write-Host "CA health check PASSED"
}

$alreadyInstalled = [bool](Get-Service -Name CertSvc -ErrorAction SilentlyContinue)

if ($alreadyInstalled) {
    Write-Host "CertSvc already exists - skipping install, running verification only."
    Test-CAHealth
    return
}

if ($WhatIfPreference) {
    Write-Host "[WhatIf] Would install ADCS-Cert-Authority and ADCS-Web-Enrollment, then run:"
    Write-Host "[WhatIf]   Install-AdcsCertificationAuthority -CAType EnterpriseRootCA -Force"
    Write-Host "[WhatIf]   Install-AdcsWebEnrollment -Force"
    return
}

Install-WindowsFeature -Name ADCS-Cert-Authority, ADCS-Web-Enrollment -IncludeManagementTools | Out-Null
Import-Module ADCSDeployment

Write-Host "Installing Enterprise Root CA..."
Install-AdcsCertificationAuthority -CAType EnterpriseRootCA -Force | Out-Null

Write-Host "Installing Web Enrollment..."
Install-AdcsWebEnrollment -Force | Out-Null

Test-CAHealth
