# =============================================================================
# Agentic Research Scout — Run Script (PowerShell)
# =============================================================================
# Usage:  .\scripts\run.ps1 [-Config path\to\config.yaml]

param(
    [string]$Config = ""
)

$ErrorActionPreference = "Stop"
$ProjectDir = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)

if (-not $ProjectDir) {
    $ProjectDir = Split-Path -Parent $PSScriptRoot
}

Push-Location $ProjectDir

Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host "  Agentic Research Scout                               " -ForegroundColor Green
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Green

# ── 1. Check uv is installed ────────────────────────────────────────────────
try {
    $null = Get-Command uv -ErrorAction Stop
} catch {
    Write-Host "uv is not installed. Installing..." -ForegroundColor Yellow
    Invoke-RestMethod https://astral.sh/uv/install.ps1 | Invoke-Expression
    Write-Host "uv installed successfully." -ForegroundColor Green
}

# ── 2. Install / sync dependencies ──────────────────────────────────────────
Write-Host "`n[1/2] Syncing dependencies..." -ForegroundColor Yellow
uv sync

# ── 3. Run the pipeline ─────────────────────────────────────────────────────
$extraArgs = @()
if ($Config) { $extraArgs += @("--config", $Config) }

Write-Host "`n[2/2] Running research pipeline..." -ForegroundColor Yellow
uv run research-pipeline @extraArgs

Write-Host "`n═══════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host "  Done! Check the output/ directory for results.       " -ForegroundColor Green
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Green

Pop-Location
