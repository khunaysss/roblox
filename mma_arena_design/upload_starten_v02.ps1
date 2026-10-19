# Cage Champions - Animations-Upload starten (Gruppe ANIMEXGANG), Version 2.
# Wie upload_starten.ps1, aber: nur ASCII-Zeichen, Fenster bleibt bei Fehlern offen, Fehlertext wird angezeigt.
# Start: Doppelklick auf upload_starten.bat (oder in PowerShell: .\upload_starten_v02.ps1).
# Der API-Schluessel wird verdeckt abgefragt und nirgends gespeichert.
$ErrorActionPreference = "Stop"
try {
    Set-Location -Path $PSScriptRoot
    Write-Host "Ordner: $PWD"
    $node = Get-Command node -ErrorAction SilentlyContinue
    if (-not $node) { throw "node wurde nicht gefunden. Bitte Node.js installieren (nodejs.org) oder PowerShell neu starten." }
    Write-Host ("node: " + $node.Source + "  Version " + (& node --version))
    if (-not (Test-Path ".\upload_animations_v01.js")) { throw "upload_animations_v01.js fehlt in diesem Ordner." }
    $n = (Get-ChildItem ".\export\anim_rbxmx\*.rbxmx").Count
    Write-Host "$n Animationsdateien im Ordner export\anim_rbxmx (nur die ohne ID werden hochgeladen)."
    Write-Host ""
    $sec = Read-Host -Prompt "API-Schluessel einfuegen (Strg+V, dann Enter; die Eingabe bleibt unsichtbar)" -AsSecureString
    $bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($sec)
    $env:CC_ROBLOX_API_KEY = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr)
    [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)
    if (-not $env:CC_ROBLOX_API_KEY) { throw "Kein Schluessel eingegeben." }
    Write-Host ""
    Write-Host "Test mit 1 Animation ..."
    & node upload_animations_v01.js --test
    Write-Host ""
    $weiter = Read-Host "Hat es geklappt (OK ... -> Zahl)? Dann 'j' und Enter fuer alle restlichen Animationen"
    if ($weiter -eq "j") { & node upload_animations_v01.js }
}
catch {
    Write-Host ""
    Write-Host "FEHLER: $($_.Exception.Message)" -ForegroundColor Red
}
finally {
    $env:CC_ROBLOX_API_KEY = $null
    Write-Host ""
    Read-Host "Fertig. Enter zum Schliessen"
}
