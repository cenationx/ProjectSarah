# Produce a separate, UNVERIFIED mechanical port candidate. Never deploy it automatically.
$ErrorActionPreference = 'Stop'
$sarahRoot = Split-Path $PSScriptRoot -Parent
$sarahUpstream = Join-Path $sarahRoot 'vendor\PZNS\PZNS_Framework'
$sarahCandidate = Join-Path $sarahRoot 'candidates\PZNS_B42_M0'
if (Test-Path -LiteralPath $sarahCandidate) { throw 'Candidate already exists; preserve it before creating another.' }
New-Item -ItemType Directory -Path "$sarahCandidate\42", "$sarahCandidate\common" -Force | Out-Null
Copy-Item -LiteralPath "$sarahUpstream\media" -Destination "$sarahCandidate\42" -Recurse
Copy-Item -LiteralPath "$sarahUpstream\mod.info" -Destination "$sarahCandidate\42\mod.info"
Get-ChildItem -LiteralPath "$sarahCandidate\42\media\lua" -Recurse -File -Filter '*.lua' | ForEach-Object {
    $sarahText = Get-Content -LiteralPath $_.FullName -Raw
    $sarahText = $sarahText.Replace(':setNPC(', ':setNpc(')
    $sarahText = $sarahText.Replace('npcIsoPlayerObject:setForname(', 'npcIsoPlayerObject:getDescriptor():setForename(')
    $sarahText = $sarahText.Replace('npcIsoPlayerObject:setSurname(', 'npcIsoPlayerObject:getDescriptor():setSurname(')
    $sarahText = $sarahText.Replace('require("PZNS_ISDebugPanelBase")', 'require("09_mod_ui/PZNS_ISDebugPanelBase")')
    Set-Content -LiteralPath $_.FullName -Value $sarahText -Encoding utf8
}
$sarahMetadata = Get-Content -LiteralPath "$sarahCandidate\42\mod.info" -Raw
$sarahMetadata = $sarahMetadata.Replace('id=PZNS_Framework', 'id=PZNS_B42_M0').Replace('name=PZNS_Framework', 'name=PZNS B42 M0 - UNVERIFIED candidate').Replace('versionMin=41.1','versionMin=42.21')
Set-Content -LiteralPath "$sarahCandidate\42\mod.info" -Value $sarahMetadata -Encoding utf8
Copy-Item -LiteralPath "$sarahRoot\vendor\PZNS\LICENSE" -Destination "$sarahCandidate\LICENSE"
Write-Host "Prepared unverified candidate: $sarahCandidate. Do not treat these mechanical replacements as full compatibility."
