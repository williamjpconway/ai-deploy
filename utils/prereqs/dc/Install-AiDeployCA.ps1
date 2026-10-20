<#
.SYNOPSIS
    Installs an Enterprise Root CA plus the Web Enrollment role only -
    no OCSP, NDES, or CEP/CES.

.DESCRIPTION
    Idempotent: if the CertSvc service already exists, skips install
    and runs verification only.

    Verification specifically targets the "CA isn't opening" failure
    mode seen before: confirms CertSvc is actually running (not just
    installed), that certutil -ping succeeds, and that IIS actually
    routes to the Web Enrollment site - "installed without error" is
    not treated as "works," per AGENTS.md's write/test/approve rule.

    On this OS, /certsrv has requireSSL set by default and no HTTPS
    binding exists yet (that's deliberately out of scope here - see
    the earlier handoff notes' "HTTPS binding for /certsrv" item, which
    is separate follow-up work, not a defect in this script). So an
    HTTP request correctly gets a 403.4 ("SSL required") rather than a
    200 - that response IS the pass condition, since it confirms IIS
    is correctly routing to CertSrv. Only a connection failure, 404, or
    5xx counts as a real failure here.

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

    try {
        $response = Invoke-WebRequest -Uri "http://localhost/certsrv" -UseDefaultCredentials -ErrorAction Stop
        Write-Host "Web Enrollment (http://localhost/certsrv): OK ($($response.StatusCode))"
    }
    catch {
        $webResponse = $_.Exception.Response
        if ($webResponse -and $webResponse.StatusCode -eq [System.Net.HttpStatusCode]::Forbidden) {
            Write-Host "Web Enrollment (http://localhost/certsrv): reachable, HTTP 403 (SSL required - expected; HTTPS binding is separate, deferred work)"
        }
        else {
            throw "Web Enrollment check failed: $($_.Exception.Message)"
        }
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
