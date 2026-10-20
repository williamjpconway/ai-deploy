<#
.SYNOPSIS
    Configures DNS forwarding and a reverse lookup zone on dc. The DNS
    Server role itself is already installed by Install-AiDeployForest.ps1
    via -InstallDns - this script is the configuration on top of that,
    which -InstallDns does not set up automatically.

.DESCRIPTION
    Idempotent: skips the forwarder if it's already present, and skips
    reverse zone creation if any zone for the range already exists.

    192.168.0.0/22 needs four separate reverse zones (one per
    third-octet value, 0-3) - confirmed via live testing that
    Add-DnsServerPrimaryZone -NetworkID with a shorter-than-/24 prefix
    does NOT fan out into multiple zones automatically as might be
    assumed; it only creates one. Each /24 is created individually.

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

function Get-ExpectedReverseZoneName {
    # Windows DNS Server auto-creates default security zones
    # (0.in-addr.arpa, 127.in-addr.arpa, 255.in-addr.arpa) on every
    # install - those must never be mistaken for the zone(s) this
    # script is responsible for, or idempotency checks silently skip
    # the real work. Only prefixes of /24 or shorter (i.e. spanning a
    # whole third octet or more) are handled, matching this project's
    # actual use (a /22).
    param([string]$NetworkId)
    $ipPart, $prefixPart = $NetworkId -split '/'
    $octets = $ipPart -split '\.'
    $prefixLength = [int]$prefixPart
    if ($prefixLength -gt 24) {
        throw "Get-ExpectedReverseZoneName only supports prefixes of /24 or shorter, got /$prefixLength"
    }
    $zoneCount = [math]::Pow(2, 24 - $prefixLength)
    $startThirdOctet = [int]$octets[2]
    for ($i = 0; $i -lt $zoneCount; $i++) {
        "$($startThirdOctet + $i).$($octets[1]).$($octets[0]).in-addr.arpa"
    }
}

function Test-DnsHealth {
    param([string[]]$ExpectedZoneNames)

    Write-Host "Verifying DNS health..."

    $forwarders = (Get-DnsServerForwarder).IPAddress.IPAddressToString
    if ($ForwarderIP -notin $forwarders) {
        throw "Forwarder '$ForwarderIP' is not in the configured forwarder list: $($forwarders -join ', ')"
    }
    Write-Host "Forwarder '$ForwarderIP': configured"

    $existingZoneNames = (Get-DnsServerZone).ZoneName
    $missingZones = $ExpectedZoneNames | Where-Object { $_ -notin $existingZoneNames }
    if ($missingZones) {
        throw "Missing expected reverse zone(s): $($missingZones -join ', ')"
    }
    Write-Host "Reverse zones present: $($ExpectedZoneNames -join ', ')"

    $result = Resolve-DnsName -Name $VerificationHostname -Server 127.0.0.1 -ErrorAction Stop
    if (-not $result) {
        throw "Resolve-DnsName for '$VerificationHostname' returned no results"
    }
    Write-Host "Live resolution of '$VerificationHostname' via this DNS server: OK"

    Write-Host "DNS health check PASSED"
}

$expectedZoneNames = @(Get-ExpectedReverseZoneName -NetworkId $ReverseZoneNetworkId)

$forwarderExists = $ForwarderIP -in (Get-DnsServerForwarder -ErrorAction SilentlyContinue).IPAddress.IPAddressToString
$existingZoneNamesNow = (Get-DnsServerZone -ErrorAction SilentlyContinue).ZoneName
$reverseZoneExists = -not ($expectedZoneNames | Where-Object { $_ -notin $existingZoneNamesNow })

if ($forwarderExists -and $reverseZoneExists) {
    Write-Host "Forwarder and reverse zone already configured - skipping setup, running verification only."
    Test-DnsHealth -ExpectedZoneNames $expectedZoneNames
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

$baseOctets = ($ReverseZoneNetworkId -split '/')[0] -split '\.'
foreach ($zoneName in $expectedZoneNames) {
    if ($zoneName -in $existingZoneNamesNow) {
        Write-Host "Reverse zone '$zoneName' already exists, skipping"
        continue
    }
    $thirdOctet = ($zoneName -split '\.')[0]
    $networkId24 = "$($baseOctets[0]).$($baseOctets[1]).$thirdOctet.0/24"
    Add-DnsServerPrimaryZone -NetworkID $networkId24 -ReplicationScope Forest
    Write-Host "Added reverse zone: $zoneName"
}

Test-DnsHealth -ExpectedZoneNames $expectedZoneNames
