# CV目標値スプシ同期 日次スクリプト
# Windows Task Schedulerで毎日AM7:00に実行
#
# 登録コマンド:
# schtasks /create /tn "CVTargetsSyncDaily" /tr "powershell.exe -ExecutionPolicy Bypass -File c:\Users\rikit\Projects\seo-machine\scripts\sync-cv-targets-daily.ps1" /sc daily /st 07:00

$ErrorActionPreference = "Stop"
$ProjectRoot = "c:\Users\rikit\Projects\seo-machine"
$PythonExe = "$ProjectRoot\.venv\Scripts\python.exe"
$SyncScript = "$ProjectRoot\scripts\sync_cv_targets_from_sheet.py"
$LogDir = "$ProjectRoot\data\logs"
$LogFile = "$LogDir\cv-targets-sync.log"

# ログディレクトリ作成
if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
}

$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

try {
    Add-Content -Path $LogFile -Value "$timestamp - Starting CV targets sync from spreadsheet"

    $output = & $PythonExe $SyncScript --sheet "[2026/02/06更新] 日次目標" 2>&1
    $exitCode = $LASTEXITCODE

    Add-Content -Path $LogFile -Value "$timestamp - Output: $output"

    if ($exitCode -ne 0) {
        Add-Content -Path $LogFile -Value "$timestamp - ERROR: Exit code $exitCode"
        Write-Error "sync_cv_targets_from_sheet.py failed with exit code $exitCode"
    } else {
        Add-Content -Path $LogFile -Value "$timestamp - Completed successfully"
    }
}
catch {
    Add-Content -Path $LogFile -Value "$timestamp - ERROR: $_"
    Write-Error $_
}
