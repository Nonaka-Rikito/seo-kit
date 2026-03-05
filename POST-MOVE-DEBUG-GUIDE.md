# フォルダ移動後のデバッグ指示書

このドキュメントは、Projects/ 配下のフォルダ整理（2026-02-26実施）後に必要なパス依存の修正作業をまとめたものです。

---

## 移動内容サマリー

| 旧パス | 新パス |
|--------|--------|
| `Projects/seo-machine/` | `Projects/1_パーソナルデータ/seo-machine/` |
| `Projects/seo-kit/` | `Projects/1_パーソナルデータ/seo-kit/` |
| `Projects/claude-talk-to-figma-mcp/` | `Projects/1_パーソナルデータ/claude-talk-to-figma-mcp/` |
| `Projects/mcp-gsc/` | `Projects/1_パーソナルデータ/mcp-gsc/` |
| `Projects/antigravity-discord-bot/` | `Projects/1_パーソナルデータ/antigravity-discord-bot/` |
| `Projects/claude-code-discord-bot/` | `Projects/1_パーソナルデータ/claude-code-discord-bot/` |
| `Projects/custom-skills/` | `Projects/1_パーソナルデータ/custom-skills/` |
| `Projects/docs/` | `Projects/1_パーソナルデータ/docs/` |
| `Projects/note-article-draft/` | `Projects/1_パーソナルデータ/note-article-draft/` |
| `Projects/slack-task-automation/` | `Projects/1_パーソナルデータ/slack-task-automation/` |
| `Projects/malna/` | `Projects/2_クライアントデータ/malna/` |

---

## 修正タスク一覧

### タスク1: pm2 seo-slack-bot のパス更新

**状況**: pm2がフルパスでapp.jsを参照しているため、移動後に起動できなくなる

**旧設定**:
```
script path: C:\Users\rikit\Projects\seo-machine\slack-bot\app.js
exec cwd:    C:\Users\rikit\Projects\seo-machine\slack-bot
```

**修正手順**:
```bash
# 1. 現在のプロセスを停止・削除
pm2 stop seo-slack-bot
pm2 delete seo-slack-bot

# 2. 新しいパスで再登録
cd /c/Users/rikit/Projects/1_パーソナルデータ/seo-machine/slack-bot
pm2 start app.js --name seo-slack-bot

# 3. 動作確認
pm2 status
pm2 logs seo-slack-bot --lines 10

# 4. 起動設定を保存（PC再起動後も自動起動するように）
pm2 save
```

**検証**: Slackで `/seo-log` 等のコマンドを実行して応答があることを確認

---

### タスク2: ~/.claude.json の MCP サーバーパス更新

**ファイル**: `C:\Users\rikit\.claude.json`

**修正箇所1: ClaudeTalkToFigma**

旧:
```json
"ClaudeTalkToFigma": {
  "type": "stdio",
  "command": "node",
  "args": [
    "C:\\Users\\rikit\\Projects\\claude-talk-to-figma-mcp\\dist\\talk_to_figma_mcp\\server.js"
  ]
}
```

新:
```json
"ClaudeTalkToFigma": {
  "type": "stdio",
  "command": "node",
  "args": [
    "C:\\Users\\rikit\\Projects\\1_パーソナルデータ\\claude-talk-to-figma-mcp\\dist\\talk_to_figma_mcp\\server.js"
  ]
}
```

**修正箇所2: mcp-gsc**

旧:
```json
"mcp-gsc": {
  "type": "stdio",
  "command": "C:\\Users\\rikit\\Projects\\mcp-gsc\\.venv\\Scripts\\python.exe",
  "args": [
    "C:\\Users\\rikit\\Projects\\mcp-gsc\\gsc_server.py"
  ],
  "env": {
    "GSC_CREDENTIALS_PATH": "C:\\Users\\rikit\\Projects\\2_クライアントデータ\\naimono\\Google\\feisty-gasket-487202-k7-992b8b630483.json",
    "GSC_SKIP_OAUTH": "true"
  }
}
```

新:
```json
"mcp-gsc": {
  "type": "stdio",
  "command": "C:\\Users\\rikit\\Projects\\1_パーソナルデータ\\mcp-gsc\\.venv\\Scripts\\python.exe",
  "args": [
    "C:\\Users\\rikit\\Projects\\1_パーソナルデータ\\mcp-gsc\\gsc_server.py"
  ],
  "env": {
    "GSC_CREDENTIALS_PATH": "C:\\Users\\rikit\\Projects\\2_クライアントデータ\\naimono\\Google\\feisty-gasket-487202-k7-992b8b630483.json",
    "GSC_SKIP_OAUTH": "true"
  }
}
```

※ `GSC_CREDENTIALS_PATH` は `2_クライアントデータ/` 配下のため変更不要

**検証**: Claude Code を再起動し、MCP ツール（`mcp__ClaudeTalkToFigma__*`, `mcp__mcp-gsc__*`）が使えることを確認

---

### タスク3: ~/.claude.json の projects セクション更新

**修正箇所**: `projects` 内の malna プロジェクトパス

旧:
```json
"C:/Users/rikit/Projects/malna": { ... }
```

新:
```json
"C:/Users/rikit/Projects/2_クライアントデータ/malna": { ... }
```

**修正箇所**: `githubRepoPaths`

旧:
```json
"nonaka-rikito/malna-nonaka": [
  "C:\\Users\\rikit\\Projects\\malna\\nonaka",
  "C:\\Users\\rikit\\Projects\\malna"
]
```

新:
```json
"nonaka-rikito/malna-nonaka": [
  "C:\\Users\\rikit\\Projects\\2_クライアントデータ\\malna\\nonaka",
  "C:\\Users\\rikit\\Projects\\2_クライアントデータ\\malna"
]
```

---

### タスク4: MEMORY.md のパス更新

**ファイル**: `C:\Users\rikit\.claude\projects\C--Users-rikit-Projects\memory\MEMORY.md`

更新箇所:
- `Figma MCP Setup` セクション: `Projects\claude-talk-to-figma-mcp\` → `Projects\1_パーソナルデータ\claude-talk-to-figma-mcp\`
- `SEO Machine Slack Bot` セクション: `Projects\seo-machine\slack-bot\` → `Projects\1_パーソナルデータ\seo-machine\slack-bot\`

---

### タスク5: DIRECTORY.md の全面更新

**ファイル**: `C:\Users\rikit\Projects\DIRECTORY.md`

移動後の新しいフォルダ構造に合わせて全面的に書き直す。特に:
- 全体構成ツリーの更新
- パス依存マップの更新
- 検索ガイドのパス更新

---

### タスク6: custom-skills/CLAUDE.md の更新

**ファイル**: `C:\Users\rikit\Projects\1_パーソナルデータ\custom-skills\CLAUDE.md`

ディレクトリ構成セクションが `malna/` 中心の古い構造のまま。新しい番号フォルダベースの構造に更新する。

---

### タスク7: git サブリポジトリの確認

以下のフォルダはそれぞれ独立した `.git` を持つ。移動後にgit操作が正常に動くか確認:

```
1_パーソナルデータ/seo-machine/.git
1_パーソナルデータ/claude-talk-to-figma-mcp/.git
1_パーソナルデータ/mcp-gsc/.git
1_パーソナルデータ/antigravity-discord-bot/.git
1_パーソナルデータ/claude-code-discord-bot/.git
1_パーソナルデータ/custom-skills/.git
1_パーソナルデータ/docs/.git
1_パーソナルデータ/note-article-draft/.git
1_パーソナルデータ/slack-task-automation/.git
2_クライアントデータ/malna/.git
```

**検証方法（各フォルダで実行）**:
```bash
cd <フォルダパス>
git status
git log --oneline -3
```

エラーが出なければOK。もし `.git` 内のパスが絶対パスで記録されている場合は修正が必要。

---

### タスク8: seo-machine 内部の相対パス確認

`seo-machine/slack-bot/lib/claude-runner.js` 内で `claude.exe` を呼び出す際、`cwd` に seo-machine のルートを指定している可能性がある。

**確認箇所**:
- `slack-bot/lib/claude-runner.js` — cwd や projectDir の設定
- `slack-bot/.env` — パス参照があれば更新
- `slack-bot/commands/*.js` — 各コマンドのファイル参照

**重要**: seo-machine 内部は全て相対パスで記述されているはずだが、念のため確認すること。

---

### タスク9: _adhoc の仕分け（任意）

`_adhoc/` の中身を適切なフォルダに移動:

| ファイル | 移動先候補 |
|---------|-----------|
| `analyze_viplimo.py`, `選定画像30枚/` | `2_クライアントデータ/lightmarks/` |
| `malna_gsc_data.csv` | `3_自社データ/` or `4_ローデータ/` |
| `gsc_rewrite_candidates_*.csv` | `2_クライアントデータ/naimono/analysis/` |
| `GA4-GSC-measurement-system-complete-summary.md` | `3_自社データ/knowledge-base/` |
| `creative-banner*.html` | `2_クライアントデータ/josys/creative/` |

---

### タスク10: その他の小修正

1. **`5_機密情報/finance/finance/`** → `5_機密情報/finance/` に統合（二重フォルダ解消）
2. **`1_パーソナルデータ/思考/slack_dup/`** → 削除OK（本体 `slack/` と完全重複）
3. **`4_ローデータ/claude-mem-main/`** → 削除 or `1_パーソナルデータ/` へ移動

---

## 作業順序（推奨）

1. タスク1（pm2）← Bot停止が先
2. タスク2（~/.claude.json MCP）
3. タスク3（~/.claude.json projects）
4. タスク4（MEMORY.md）
5. タスク5（DIRECTORY.md）
6. タスク6（CLAUDE.md）
7. タスク7（git確認）
8. タスク8（seo-machine内部パス）
9. タスク9, 10（任意整理）

## ロールバック手順

万が一、移動後に問題が発生した場合:

```bash
# 各フォルダを元の位置に戻す
mv "/c/Users/rikit/Projects/1_パーソナルデータ/seo-machine" "/c/Users/rikit/Projects/"
mv "/c/Users/rikit/Projects/1_パーソナルデータ/claude-talk-to-figma-mcp" "/c/Users/rikit/Projects/"
mv "/c/Users/rikit/Projects/1_パーソナルデータ/mcp-gsc" "/c/Users/rikit/Projects/"
# ... 他も同様

# pm2を元のパスで再登録
pm2 delete seo-slack-bot
cd /c/Users/rikit/Projects/seo-machine/slack-bot
pm2 start app.js --name seo-slack-bot
pm2 save

# ~/.claude.json のパスを元に戻す（手動編集）
```
