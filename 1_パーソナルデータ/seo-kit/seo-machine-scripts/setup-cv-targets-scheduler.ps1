# CV Targets Sync Daily - Task Scheduler Setup
# Run as Administrator: Right-click PowerShell -> Run as Administrator
#
# Task: CVTargetsSyncDaily
# Schedule: Daily at 07:00
# Script: sync-cv-targets-daily.ps1

$ErrorActionPreference = "Stop"

$TaskName = "CVTargetsSyncDaily"
$ProjectRoot = "c:\Users\rikit\Projects\seo-machine"
$ScriptPath = "$ProjectRoot\scripts\sync-cv-targets-daily.ps1"
$EnvFile = "$ProjectRoot\data_sources\config\.env"

# --- Admin check ---
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole(
    [Security.Principal.WindowsBuiltInRole]::Administrator
)

if (-not $isAdmin) {
    Write-Host "ERROR: Please run this script as Administrator." -ForegroundColor Red
    Write-Host "Right-click PowerShell -> Run as Administrator" -ForegroundColor Yellow
    exit 1
}

Write-Host "=== CVTargetsSyncDaily Task Scheduler Setup ===" -ForegroundColor Cyan
Write-Host ""

# --- Script file check ---
if (-not (Test-Path $ScriptPath)) {
    Write-Host "ERROR: Script not found: $ScriptPath" -ForegroundColor Red
    exit 1
}

Write-Host "OK: Script found: $ScriptPath" -ForegroundColor Green

# --- Credentials check ---
if (Test-Path $EnvFile) {
    $envContent = Get-Content $EnvFile -Raw
    if ($envContent -match "GA4_CREDENTIALS_PATH=(.+)") {
        $credPath = $Matches[1].Trim()
        if (Test-Path $credPath) {
            Write-Host "OK: GA4_CREDENTIALS_PATH is configured and file exists." -ForegroundColor Green
        } else {
            Write-Host "WARNING: GA4_CREDENTIALS_PATH is set but file not found: $credPath" -ForegroundColor Yellow
        }
    } else {
        Write-Host "WARNING: GA4_CREDENTIALS_PATH is not set in .env" -ForegroundColor Yellow
    }
} else {
    Write-Host "WARNING: .env file not found: $EnvFile" -ForegroundColor Yellow
}

# --- Existing task check ---
$ErrorActionPreference = "SilentlyContinue"
$existingTask = schtasks /query /tn $TaskName 2>$null
$ErrorActionPreference = "Stop"
if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "INFO: Task '$TaskName' already exists." -ForegroundColor Yellow
    Write-Host "To re-register, delete it first:" -ForegroundColor Yellow
    Write-Host "  schtasks /delete /tn `"$TaskName`" /f" -ForegroundColor White
    Write-Host ""

    Write-Host "--- Current registration ---" -ForegroundColor Cyan
    schtasks /query /tn $TaskName /v /fo list | Select-String -Pattern "(TaskName|Next Run|Status|Task To Run|Start Time)"
    exit 0
}

# --- Register task ---
Write-Host ""
Write-Host "Registering task..." -ForegroundColor Cyan

$taskCommand = "powershell.exe -ExecutionPolicy Bypass -File `"$ScriptPath`""

schtasks /create `
    /tn $TaskName `
    /tr $taskCommand `
    /sc daily `
    /st 07:00 `
    /rl highest `
    /f

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "ERROR: Failed to register task." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "OK: Task '$TaskName' registered successfully." -ForegroundColor Green
Write-Host ""

# --- Verify registration ---
Write-Host "--- Registration details ---" -ForegroundColor Cyan
schtasks /query /tn $TaskName /v /fo list | Select-String -Pattern "(TaskName|Next Run|Status|Task To Run|Start Time|Run As)"

Write-Host ""
Write-Host "=== Done ===" -ForegroundColor Cyan
Write-Host "CV targets will be synced from spreadsheet daily at 07:00." -ForegroundColor White
Write-Host "Log: $ProjectRoot\data\logs\cv-targets-sync.log" -ForegroundColor White
