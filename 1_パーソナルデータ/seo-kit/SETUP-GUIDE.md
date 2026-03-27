# セットアップガイド

新しいプロジェクトに SEO Kit を導入する手順です。
上から順番にやれば、誰でもセットアップできます。

---

## 前提条件（先に必要なもの）

| 必要なもの | 確認方法 | インストール方法 |
|-----------|---------|----------------|
| Node.js 18以上 | `node --version` | https://nodejs.org/ からダウンロード |
| Python 3.10以上 | `python --version` | https://python.org/ からダウンロード |
| Claude Code | `claude --version` | `npm install -g @anthropic-ai/claude-code` |
| Git | `git --version` | https://git-scm.com/ からダウンロード |

---

## ステップ1: フォルダをコピーする

この `seo-kit/` フォルダをプロジェクトの場所にコピーします。

```bash
# 例: 新しいプロジェクト用にコピー
cp -r seo-kit/ ~/Projects/my-new-site-seo/
cd ~/Projects/my-new-site-seo/
```

---

## ステップ2: Claude Code スキルを配置する

`claude-skills/` の中身を、Claude Code のグローバルコマンドフォルダにコピーします。

```bash
# Windows の場合
cp claude-skills/*.md ~/.claude/commands/

# Mac の場合
cp claude-skills/*.md ~/.claude/commands/
```

これで、どのプロジェクトでも `/seo-query-research` などのコマンドが使えるようになります。

---

## ステップ3: SEO Machine プロジェクトを構築する

分析対象のサイト用に SEO Machine プロジェクトを作ります。

### 3-1. プロジェクトフォルダを作る

```bash
mkdir my-site-seo
cd my-site-seo

# Claude Code の設定フォルダを作る
mkdir -p .claude/commands .claude/agents .claude/skills
mkdir -p data_sources/{modules,japanese,verification,integrations,config}
mkdir -p scripts config context
mkdir -p data/{clarity,change_events,cache}
mkdir -p topics research drafts review-required published rewrites output
```

### 3-2. ファイルを配置する

```bash
# コマンド定義をコピー
cp ../seo-kit/seo-machine-commands/*.md .claude/commands/

# エージェント定義をコピー
cp ../seo-kit/seo-machine-agents/*.md .claude/agents/

# スキル定義をコピー
cp ../seo-kit/seo-machine-skills/*.md .claude/skills/

# データソースモジュールをコピー
cp -r ../seo-kit/seo-machine-data-sources/* data_sources/

# スクリプトをコピー
cp ../seo-kit/seo-machine-scripts/*.py scripts/
cp ../seo-kit/seo-machine-scripts/*.ps1 scripts/

# 設定をコピー
cp ../seo-kit/seo-machine-config/* config/

# コンテキストをコピー
cp ../seo-kit/seo-machine-context/*.md context/
```

### 3-3. CLAUDE.md を書き換える

`seo-kit/seo-machine-CLAUDE.md` を `CLAUDE.md` としてコピーし、**自分のサイト用に書き換えます**。

```bash
cp ../seo-kit/seo-machine-CLAUDE.md CLAUDE.md
```

書き換えるポイント：

```
# 変更前（例）
- **URL**: https://example-media.com/
- **GA4 Property ID**: 356839446
- **ジャンル**: 就活メディア
- **クライアント**: example-client

# 変更後（自分のサイトに）
- **URL**: https://your-site.com/
- **GA4 Property ID**: あなたのGA4プロパティID
- **ジャンル**: あなたのサイトジャンル
- **クライアント**: あなたのクライアント名
```

### 3-4. コンテキスト文書を書き換える

`context/` フォルダの中身を、自分のサイト用に書き換えます。

| ファイル | 書くこと |
|---------|---------|
| `brand-voice.md` | サイトの文章トーン（丁寧？カジュアル？） |
| `style-guide.md` | 表記ルール（「です・ます」調、数字の書き方など） |
| `seo-guidelines.md` | SEOの基本ルール（タイトルの文字数など） |
| `internal-links-map.md` | サイト内の主要ページ一覧とURL |
| `target-keywords.md` | 狙いたいキーワード一覧 |

### 3-5. Python 環境を作る

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Mac/Linux

pip install -r data_sources/requirements.txt
```

### 3-6. API認証を設定する

`data_sources/config/.env.example` を `.env` にコピーして、APIキーを入力します。

```bash
cp data_sources/config/.env.example data_sources/config/.env
```

必要なAPIキー：
- **GA4**: Google Cloud コンソールでサービスアカウントを作成し、JSONキーを配置
- **GSC**: MCPサーバー `mcp-gsc` をセットアップ（別途手順あり）
- **Ahrefs**: Ahrefs APIキーを MCP設定に登録
- **Clarity**: Clarity MCP をセットアップ

---

## ステップ4: Slack Bot をセットアップする

### 4-1. Slack App を作る

1. https://api.slack.com/apps にアクセス
2. 「Create New App」→「From scratch」
3. App名（例: SEO Bot）とワークスペースを選択

### 4-2. 権限を設定する

「OAuth & Permissions」→「Bot Token Scopes」に以下を追加：
- `chat:write`
- `commands`

### 4-3. Socket Mode を有効化する

「Socket Mode」→ 有効にする → App Level Token を生成（名前は何でもOK）

### 4-4. スラッシュコマンドを登録する

「Slash Commands」から以下を1つずつ作成：

| Command | Description |
|---------|------------|
| `/seo-weekly` | 週次SEOレポート |
| `/seo-cv` | CV指標レポート |
| `/seo-top100` | オーガニックTop100 |
| `/seo-dashboard` | エグゼクティブダッシュボード |
| `/seo-analytics` | SEO分析 |
| `/seo-log` | 変更記録 |
| `/seo-measure` | 効果測定 |
| `/seo-verify` | データ検証 |
| `/seo-stop` | 処理停止 |

### 4-5. 環境変数を設定する

```bash
cd slack-bot/
cp .env.example .env
```

`.env` を開いて以下を入力：

```
SLACK_BOT_TOKEN=xoxb-（OAuth & Permissions のBot Token）
SLACK_SIGNING_SECRET=（Basic Information の Signing Secret）
SLACK_APP_TOKEN=xapp-（Socket Mode の App Level Token）
SLACK_ALLOWED_USER_IDS=U12345678（許可するユーザーのID、カンマ区切り）
CLAUDE_MODEL=claude-sonnet-4-20250514
SEO_MACHINE_DIR=C:/Users/あなた/Projects/my-site-seo
```

### 4-6. Slack Bot にアプリをインストール

「Install App」→「Install to Workspace」

### 4-7. ボットを起動する

```bash
cd slack-bot/
npm install
node app.js
```

「SEO Machine Slack Bot 起動完了」と表示されたら成功！

### 4-8. 常時起動にする（おすすめ）

pm2 を使うと、PCを再起動してもボットが自動で立ち上がります。

```bash
npm install -g pm2
pm2 start app.js --name seo-slack-bot
pm2 save
pm2-windows-startup     # Windows の場合
# pm2 startup            # Mac/Linux の場合
```

---

## ステップ5: 動作確認

1. Slack で `/seo-verify` を打ってみる
2. ボットが「データ検証を処理中...」と返事したらOK
3. しばらくすると検証結果が表示される

---

## トラブルシューティング

### ボットが反応しない
- `.env` のトークンが正しいか確認
- `node app.js` でエラーが出ていないか確認
- Slack App が「Install to Workspace」済みか確認

### Claude Code がエラーになる
- `claude --version` でインストール済みか確認
- `SEO_MACHINE_DIR` のパスが正しいか確認
- そのディレクトリに `CLAUDE.md` があるか確認

### データが取れない
- MCP サーバー（GSC, Ahrefs, Clarity）が設定済みか確認
- GA4 のサービスアカウントに対象サイトの閲覧権限があるか確認

### pm2 でボットが起動しない
- `pm2 logs seo-slack-bot` でログを確認
- `pm2 restart seo-slack-bot` で再起動してみる
