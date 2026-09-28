# Richtet Claude Code mit dem Roblox Studio MCP auf Windows ein und startet es.
$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

Write-Host "== Roblox + Claude Setup ==" -ForegroundColor Cyan

# 1. Roblox Studio MCP pruefen
$mcpBat = Join-Path $env:LOCALAPPDATA "Roblox\mcp.bat"
if (-not (Test-Path $mcpBat)) {
    Write-Host ""
    Write-Host "FEHLER: $mcpBat wurde nicht gefunden." -ForegroundColor Red
    Write-Host "Bitte Roblox Studio oeffnen und das MCP-Plugin aktivieren, dann dieses Skript neu starten."
    Read-Host "Enter druecken zum Beenden"
    exit 1
}
Write-Host "[OK] Roblox Studio MCP gefunden" -ForegroundColor Green

# 2. Claude Code installieren, falls noetig
if (-not (Get-Command claude -ErrorAction SilentlyContinue)) {
    Write-Host "Claude Code wird installiert..." -ForegroundColor Yellow
    Invoke-RestMethod https://claude.ai/install.ps1 | Invoke-Expression
    $env:Path += ";$env:USERPROFILE\.local\bin"
}
if (-not (Get-Command claude -ErrorAction SilentlyContinue)) {
    Write-Host "FEHLER: Claude Code konnte nicht installiert werden. PowerShell neu starten und erneut versuchen." -ForegroundColor Red
    Read-Host "Enter druecken zum Beenden"
    exit 1
}
Write-Host "[OK] Claude Code installiert" -ForegroundColor Green

# 3. Claude in diesem Ordner starten (.mcp.json verbindet Roblox Studio automatisch)
Write-Host ""
Write-Host "Claude startet jetzt. Beim ersten Start 'Roblox_Studio' erlauben." -ForegroundColor Cyan
Write-Host "Mit /mcp kannst du pruefen, ob Roblox Studio verbunden ist."
Write-Host ""
claude
