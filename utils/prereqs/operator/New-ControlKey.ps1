<#
.SYNOPSIS
    Generates the Key A keypair (this machine -> ai-deploy) and installs
    its public half into ai-deploy's authorized_keys for masterchief.

.DESCRIPTION
    One-time bootstrap: before this runs, ai-deploy only accepts a
    password login for masterchief. This generates a dedicated keypair
    locally (never inside the Factory repo) and appends the public key
    to ai-deploy over a password-authenticated SSH session - you'll be
    prompted for the password once, interactively, by ssh itself; this
    script never sees or stores it.

    Idempotent: skips key generation if the local key already exists,
    and the remote side only appends the key if it isn't already in
    authorized_keys.

    Supports -WhatIf, per AGENTS.md's write/test/approve rule for
    scripts.
#>

[CmdletBinding(SupportsShouldProcess)]
param(
    [Parameter(Mandatory)]
    [string]$AiDeployHost,

    [string]$AiDeployUser = "masterchief",

    [string]$KeyPath = (Join-Path $HOME ".ssh\ai_deploy_control")
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $KeyPath)) {
    if ($PSCmdlet.ShouldProcess($KeyPath, "Generate SSH keypair")) {
        ssh-keygen -t ed25519 -f $KeyPath -N '""' -C "control-key for $AiDeployUser@$AiDeployHost"
        Write-Host "Generated keypair at $KeyPath"
    }
}
else {
    Write-Host "Key already exists at $KeyPath, skipping generation"
}

$pubKeyPath = "$KeyPath.pub"
if (-not (Test-Path $pubKeyPath)) {
    if ($PSCmdlet.WhatIf) {
        Write-Host "[WhatIf] Would install the public key from $pubKeyPath into ${AiDeployUser}@${AiDeployHost}:~/.ssh/authorized_keys"
        return
    }
    throw "Public key not found at $pubKeyPath - key generation may have failed."
}

if ($PSCmdlet.ShouldProcess("$AiDeployUser@$AiDeployHost", "Install public key into authorized_keys (will prompt for password)")) {
    $pubKey = (Get-Content $pubKeyPath -Raw).Trim()
    $remoteScript = 'key=$(cat); mkdir -p ~/.ssh && chmod 700 ~/.ssh && touch ~/.ssh/authorized_keys && grep -qxF "$key" ~/.ssh/authorized_keys || echo "$key" >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys'
    $pubKey | ssh "$AiDeployUser@$AiDeployHost" $remoteScript
    Write-Host "Public key installed on $AiDeployHost (or was already present)"
    Write-Host "Test with: ssh -i `"$KeyPath`" $AiDeployUser@$AiDeployHost"
}
