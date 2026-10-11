# Cage Champions – Animations-Upload starten (Gruppe ANIMEXGANG).
# Fragt den API-Schluessel verdeckt ab (nichts wird gespeichert) und startet upload_animations_v01.js.
# Start: Rechtsklick auf diese Datei -> "Mit PowerShell ausfuehren"
Set-Location -Path $PSScriptRoot
$sec = Read-Host -Prompt "API-Schluessel einfuegen (Strg+V, dann Enter; die Eingabe bleibt unsichtbar)" -AsSecureString
$bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($sec)
$env:CC_ROBLOX_API_KEY = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr)
[Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)
Write-Host ""
Write-Host "Test mit 1 Animation ..."
node upload_animations_v01.js --test
Write-Host ""
$weiter = Read-Host "Hat es geklappt (OK ... -> Zahl)? Dann 'j' und Enter fuer alle restlichen Animationen"
if ($weiter -eq "j") { node upload_animations_v01.js }
$env:CC_ROBLOX_API_KEY = $null
Write-Host ""
Read-Host "Fertig. Enter zum Schliessen"
