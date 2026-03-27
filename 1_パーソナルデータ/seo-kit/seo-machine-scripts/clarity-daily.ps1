# Clarity日次データ蓄積スクリプト
# Windows Task Schedulerで毎日AM2:00に実行
#
# 登録コマンド:
# schtasks /create /tn "ClarityDailyJob" /tr "powershell.exe -ExecutionPolicy Bypass -File c:\Users\your-user\Projects\seo-machine\scripts\clarity-daily.ps1" /sc daily /st 02:00

$ErrorActionPreference = "Stop"
$ProjectRoot = "c:\Users\your-user\Projects\seo-machine"
$PythonExe = "$ProjectRoot\.venv\Scripts\python.exe"
$LogFile = "$ProjectRoot\data\clarity\accumulator.log"

$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

try {
    Add-Content -Path $LogFile -Value "$timestamp - Starting Clarity daily accumulation"

    & $PythonExe -c @"
import sys
sys.path.insert(0, r'$ProjectRoot')
from data_sources.integrations.clarity_accumulator import ClarityAccumulator
acc = ClarityAccumulator()
print(f'Data dir: {acc.data_dir}')
print(f'Available dates: {acc.get_available_dates()[-5:]}')
print('Clarity accumulator initialized successfully')
"@

    Add-Content -Path $LogFile -Value "$timestamp - Completed successfully"
}
catch {
    Add-Content -Path $LogFile -Value "$timestamp - ERROR: $_"
    Write-Error $_
}
