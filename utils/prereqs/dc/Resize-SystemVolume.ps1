<#
.SYNOPSIS
    Expands the C: partition to fill available disk space, removing a
    Recovery partition that's blocking the extend if one is in the way.

.DESCRIPTION
    After growing a VM's virtual disk, Disk Management's "Extend
    Volume" is often greyed out because the new unallocated space sits
    after the Recovery partition rather than immediately after C: -
    Windows will only extend a volume into contiguous unallocated
    space. The standard fix is deleting the Recovery partition (loses
    the WinRE "Repair your computer" boot option; does not affect
    anything C: needs to function) and resizing C: into the space that
    frees up.

    This is a genuinely destructive, hard-to-reverse operation -
    deleting a partition is not something to undo casually. Review the
    -WhatIf output before running for real.

    Idempotent: if C: is already at its maximum supported size, does
    nothing. Only removes the Recovery partition if it's actually the
    thing blocking the extend (sits immediately after C: on the same
    disk) - never touches a Recovery partition elsewhere.

    General-purpose despite living under dc/ - the same disk-layout
    issue can happen on any Windows VM whose disk gets grown after
    creation.
#>

[CmdletBinding(SupportsShouldProcess)]
param(
    [string]$DriveLetter = "C"
)

$ErrorActionPreference = "Stop"

$targetPartition = Get-Partition -DriveLetter $DriveLetter
$diskNumber = $targetPartition.DiskNumber

# Check what's blocking growth BEFORE comparing against
# Get-PartitionSupportedSize - its SizeMax is computed under the
# current layout, so with a Recovery partition in the way it reports
# the current size as the max even though there's room further out on
# the disk. Comparing against it first would wrongly look idempotent.
$nextPartition = Get-Partition -DiskNumber $diskNumber |
    Where-Object { $_.Offset -gt $targetPartition.Offset } |
    Sort-Object Offset |
    Select-Object -First 1

if ($nextPartition -and $nextPartition.Type -eq 'Recovery') {
    if ($PSCmdlet.ShouldProcess("Disk $diskNumber, Partition $($nextPartition.PartitionNumber) (Recovery, $([math]::Round($nextPartition.Size / 1MB, 0)) MB)", "Delete recovery partition so $DriveLetter`: can expand")) {
        Remove-Partition -DiskNumber $diskNumber -PartitionNumber $nextPartition.PartitionNumber -Confirm:$false
        Write-Host "Deleted recovery partition $($nextPartition.PartitionNumber) on disk $diskNumber"
    }
    else {
        Write-Host "Skipped deleting the recovery partition - cannot expand $DriveLetter`: past it, stopping here"
        return
    }
}
elseif ($nextPartition) {
    throw "$DriveLetter`: cannot be expanded to its reported max - partition $($nextPartition.PartitionNumber) (type: $($nextPartition.Type)) is in the way, and it isn't a Recovery partition this script is safe to touch"
}

$maxSize = (Get-PartitionSupportedSize -DriveLetter $DriveLetter).SizeMax
if ($targetPartition.Size -ge $maxSize) {
    Write-Host "$DriveLetter`: is already at its maximum supported size ($([math]::Round($targetPartition.Size / 1GB, 2)) GB), nothing further to do"
    return
}

if ($PSCmdlet.ShouldProcess("$DriveLetter`:", "Resize from $([math]::Round($targetPartition.Size / 1GB, 2)) GB to $([math]::Round($maxSize / 1GB, 2)) GB")) {
    Resize-Partition -DriveLetter $DriveLetter -Size $maxSize
}

$finalPartition = Get-Partition -DriveLetter $DriveLetter
Write-Host "Verifying..."
if ($finalPartition.Size -le $targetPartition.Size) {
    throw "$DriveLetter`: size did not increase (before: $($targetPartition.Size), after: $($finalPartition.Size))"
}
Write-Host "$DriveLetter`: resized from $([math]::Round($targetPartition.Size / 1GB, 2)) GB to $([math]::Round($finalPartition.Size / 1GB, 2)) GB"
Write-Host "Resize verification PASSED"
