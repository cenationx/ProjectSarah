$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
$gameRoot = 'G:\Games\ProjectZomboid'
$javaExe = Join-Path $gameRoot 'jre64\bin\java.exe'
$compilerJar = Join-Path $PSScriptRoot 'dependencies\ecj-3.43.0.jar'
$outputDir = Join-Path $PSScriptRoot 'compiled'
& $javaExe -jar $compilerJar -17 -d $outputDir (Join-Path $PSScriptRoot 'RuntimeApiProbe.java')
if ($LASTEXITCODE -ne 0) { throw 'Probe compilation failed' }
& $javaExe -cp "$gameRoot\projectzomboid.jar;$outputDir" RuntimeApiProbe 2>&1 |
    Tee-Object -FilePath (Join-Path $projectRoot 'evidence\runtime-api-probe.txt')
$probeExitCode = $LASTEXITCODE
Write-Host "Compatibility probe exit code: $probeExitCode (2 means required APIs are missing)."
exit $probeExitCode
