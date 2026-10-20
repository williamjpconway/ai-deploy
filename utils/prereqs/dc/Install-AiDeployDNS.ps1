<#
.SYNOPSIS
    Configures DNS forwarding and a reverse lookup zone on dc. The DNS
    Server role itself is already installed by Install-AiDeployForest.ps1
    via -InstallDns - this script is the configuration on top of that,
    which -InstallDns does not set up automatically.

.DESCRIPTION
    Idempotent: skips the forwarder if it's already present, and skips
    reverse zone creation if any zone for the range already exists.

    192.168.0.0/22 has a prefix shorter than /24, so
    Add-DnsServerPrimaryZone -NetworkID creates the four underlying
    reverse zones (one per third-octet value, 0-3) automatically.

    Verification resolves a known external hostname through this DNS
    server as a live check, not just confirming the forwarder/zone
    config exists - per AGENTS.md's write/test/approve rule.

    Supports -WhatIf for both the forwarder and zone changes.
#>

[CmdletBinding(SupportsShouldProcess)]
param(
    [string]$ForwarderIP = "192.168.0.254",
    [string]$ReverseZoneNetworkId = "192.168.0.0/22",
    [string]$VerificationHostname = "www.microsoft.com"
)

$ErrorActionPreference = "Stop"

function Test-DnsHealth {
    Write-Host "Verifying DNS health..."

    $forwarders = (Get-DnsServerForwarder).IPAddress.IPAddressToString
    if ($ForwarderIP -notin $forwarders) {
        throw "Forwarder '$ForwarderIP' is not in the configured forwarder list: $($forwarders -join ', ')"
    }
    Write-Host "Forwarder '$ForwarderIP': configured"

    $zones = Get-DnsServerZone | Where-Object { $_.ZoneName -like '*.in-addr.arpa' }
    if (-not $zones) {
        throw "No reverse lookup zones found"
    }
    Write-Host "Reverse zones present: $($zones.ZoneName -join ', ')"

    $result = Resolve-DnsName -Name $VerificationHostname -Server 127.0.0.1 -ErrorAction Stop
    if (-not $result) {
        throw "Resolve-DnsName for '$VerificationHostname' returned no results"
    }
    Write-Host "Live resolution of '$VerificationHostname' via this DNS server: OK"

    Write-Host "DNS health check PASSED"
}

$forwarderExists = $ForwarderIP -in (Get-DnsServerForwarder -ErrorAction SilentlyContinue).IPAddress.IPAddressToString
$reverseZoneExists = [bool](Get-DnsServerZone -ErrorAction SilentlyContinue | Where-Object { $_.ZoneName -like '*.in-addr.arpa' })

if ($forwarderExists -and $reverseZoneExists) {
    Write-Host "Forwarder and reverse zone already configured - skipping setup, running verification only."
    Test-DnsHealth
    return
}

if ($WhatIfPreference) {
    if (-not $forwarderExists) {
        Write-Host "[WhatIf] Would add forwarder: $ForwarderIP"
    }
    if (-not $reverseZoneExists) {
        Write-Host "[WhatIf] Would add reverse zone(s) for: $ReverseZoneNetworkId"
    }
    return
}

if (-not $forwarderExists) {
    Add-DnsServerForwarder -IPAddress $ForwarderIP
    Write-Host "Added forwarder: $ForwarderIP"
}
else {
    Write-Host "Forwarder '$ForwarderIP' already present, skipping"
}

if (-not $reverseZoneExists) {
    Add-DnsServerPrimaryZone -NetworkID $ReverseZoneNetworkId -ReplicationScope Forest
    Write-Host "Added reverse zone(s) for: $ReverseZoneNetworkId"
}
else {
    Write-Host "A reverse zone already exists, skipping"
}

Test-DnsHealth
