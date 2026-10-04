param([switch]$NoDebug)
$ErrorActionPreference = 'Stop'
$sarahRoot = Split-Path $PSScriptRoot -Parent
$sarahCache = Join-Path $sarahRoot 'runtime\isolated'
if (-not (Test-Path -LiteralPath "$sarahCache\mods\SarahM0\42\mod.info")) { throw 'The isolated probe profile is missing.' }
$sarahGameArgs = @('-Xmx3072m', '--enable-native-access=ALL-UNNAMED', '--add-exports=java.base/jdk.internal.misc=ALL-UNNAMED', '-Dzomboid.steam=0', '-Djava.library.path=G:\Games\ProjectZomboid', '-cp', 'G:\Games\ProjectZomboid\projectzomboid.jar', 'zombie.gameStates.MainScreenState', "-cachedir=`"$sarahCache`"", '-debug')
if ($NoDebug) { $sarahGameArgs = $sarahGameArgs | Where-Object { $_ -ne '-debug' } }
$sarahProcess = Start-Process -FilePath 'G:\Games\ProjectZomboid\jre64\bin\javaw.exe' -ArgumentList $sarahGameArgs -WorkingDirectory 'G:\Games\ProjectZomboid' -WindowStyle Hidden -PassThru
$sarahProcess.Id | Set-Content -LiteralPath (Join-Path $sarahRoot 'runtime\game-pid.txt')
Write-Host 'Launched the disposable Sarah M0 profile. Use Continue to open its test world.'
