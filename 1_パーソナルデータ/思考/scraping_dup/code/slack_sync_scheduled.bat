@echo off
REM === Slack定期同期バッチ ===
REM タスクスケジューラから2時間おきに実行される想定
REM 直近3日分のメッセージを取得（定期実行なので短期間で十分）

cd /d "%~dp0.."

REM ログディレクトリがなければ作成
if not exist logs mkdir logs

echo [%date% %time%] === Slack同期バッチ開始 === >> logs\slack_sync.log 2>&1

REM SYNC_DAYSを上書きして実行（.envの773日ではなく3日分）
set SYNC_DAYS=3
"C:\Program Files\nodejs\node.exe" code\slack_sync.mjs >> logs\slack_sync.log 2>&1

if %ERRORLEVEL% NEQ 0 (
    echo [%date% %time%] エラー: node終了コード=%ERRORLEVEL% >> logs\slack_sync.log
)

echo [%date% %time%] === Slack同期バッチ終了 === >> logs\slack_sync.log 2>&1

REM ログローテーション: 10MB超えたら古いログを削除
for %%F in (logs\slack_sync.log) do (
    if %%~zF GTR 10485760 (
        del logs\slack_sync.log
        echo [%date% %time%] ログローテーション実行 > logs\slack_sync.log
    )
)
