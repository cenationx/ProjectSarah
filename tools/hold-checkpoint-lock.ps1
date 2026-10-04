# Disposable existing-file write failure. Releases automatically or on probe signal.
$ErrorActionPreference = 'Stop'
$sarahRoot = Split-Path $PSScriptRoot -Parent
if ($sarahRoot -ne 'G:\Codex\Project Sarah') { throw 'Wrong project root' }
$sarahTarget = Join-Path $sarahRoot 'runtime\isolated\Saves\Rising\SarahWriteFailureRetest\SarahFoundation-a.bin'
$sarahSignal = Join-Path $sarahRoot 'runtime\isolated\Lua\SarahWriteLock-retest-20261004.txt'
if (Test-Path -LiteralPath $sarahSignal) { throw 'Stale release signal; prepare a new backed-up test' }
$sarahBefore = (Get-FileHash -LiteralPath $sarahTarget).Hash
$sarahHandle = [System.IO.File]::Open($sarahTarget,[System.IO.FileMode]::Open,[System.IO.FileAccess]::ReadWrite,[System.IO.FileShare]::None)
try {
    Write-Output 'LOCK_ACTIVE slot=a existing=true noPermissionChanges=true'
    $sarahDeadline = [DateTime]::UtcNow.AddMinutes(5)
    while ([DateTime]::UtcNow -lt $sarahDeadline -and -not (Test-Path -LiteralPath $sarahSignal)) {
        Start-Sleep -Milliseconds 500
    }
    $sarahReleased = Test-Path -LiteralPath $sarahSignal
} finally { $sarahHandle.Dispose() }
$sarahAfter = (Get-FileHash -LiteralPath $sarahTarget).Hash
Write-Output "LOCK_RELEASED probeSignal=$sarahReleased unchanged=$($sarahBefore -eq $sarahAfter)"
if (-not $sarahReleased -or $sarahBefore -ne $sarahAfter) { throw 'Lock test not completed or old file changed' }
