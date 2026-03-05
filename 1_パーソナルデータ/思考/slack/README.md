# Slack コンテキスト

このディレクトリには、Slack APIから自動取得したメッセージがMarkdown形式で保存されます。

## ファイル命名規則
`{チャンネル名}_{日付}.md`（例: `general_2026-02-11.md`）

## 用途
- Claude Code / Cursor がコンテキストとして読み込むためのデータソース
- 直近のSlackでの会話内容をAIが把握し、タスク抽出や意思決定に活用する

## 同期方法
```bash
node code/slack_sync.mjs
```

## 設定
`.env` ファイルで以下を設定：
- `SLACK_USER_TOKEN` - Slack APIトークン
- `SLACK_CHANNELS` - 取得対象のチャンネル名（カンマ区切り）
- `SYNC_DAYS` - 何日前までのメッセージを取得するか
