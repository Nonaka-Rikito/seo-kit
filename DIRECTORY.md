# Projects ディレクトリマップ

このファイルは AI（Claude Code）がフォルダ構造を即座に理解するためのガイド。

---

## 全体構成

```
C:\Users\rikit\Projects\
│
├── 1_パーソナルデータ/          個人ツール・開発プロジェクト・リサーチデータ
│   ├── seo-machine/             本番SEO分析エンジン（pm2で常時動作中のSlack Bot含む）
│   ├── seo-kit/                 seo-machineのテンプレート・配布パッケージ
│   ├── claude-talk-to-figma-mcp/ Figma連携MCPサーバー
│   ├── mcp-gsc/                 Google Search Console MCPサーバー
│   ├── antigravity-discord-bot/ Discord Bot
│   ├── claude-code-discord-bot/ Claude Code連携Discord Bot
│   ├── slack-task-automation/   GASスクリプト
│   ├── custom-skills/           カスタムスキル定義
│   ├── docs/                    マニュアル・参考資料
│   ├── note-article-draft/      note記事の執筆ドラフト
│   ├── Google-API連携/          Google API実験スクリプト
│   ├── 思考/                    業務横断の思考メモ・Slackアーカイブ
│   └── 有料記事/                参考にしている有料記事データ
│
├── 2_クライアントデータ/        全クライアントの案件ファイル（7社）
│   ├── naimono/                 ナイモノ（スタキャリ事業、新卒就活支援）
│   ├── josys/                   ジョーシス（SaaS管理、IT資産管理）
│   ├── herp/                    HERP（採用管理SaaS）
│   ├── lightmarks/              ライトマークス
│   ├── geekplus/                ギークプラス（物流ロボティクス）
│   ├── Paytner/                 ペイトナー
│   ├── salescore/               セールスコア
│   └── malna/                   コンサル業務の成果物・出力（git管理）
│
├── 3_自社データ/                malna社内資料・ブランド・ナレッジ
│   ├── branding/                ロゴ・名刺・ブランド素材
│   ├── knowledge-base/          再利用可能なナレッジ・フレームワーク
│   ├── recruiting/              採用関連素材
│   ├── service-materials/       サービス資料
│   └── deliverables/            納品物テンプレート
│
├── 4_ローデータ/                未加工リサーチデータ・議事録
│   ├── competitor-analysis/     競合分析の生データ
│   ├── industry-research/       業界調査
│   ├── market-statistics/       市場統計データ
│   └── mtg-transcripts/         ミーティング議事録
│
├── 5_機密情報/                  認証キー・財務情報（絶対外部漏洩禁止）
│   ├── finance/                 請求書・見積書・経理関連
│   └── GCPサービスアカウントキー
│
├── _adhoc/                      一時的な分析スクリプト・データファイル
│
└── [設定ファイル]
    ├── .claude/                  Claude Code プロジェクト設定
    ├── .gitignore
    ├── DIRECTORY.md              ← このファイル
    └── POST-MOVE-DEBUG-GUIDE.md  フォルダ移動後のデバッグ指示書
```

---

## パス依存マップ（動かすと壊れるもの）

| フォルダ/ファイル | 依存元 | 参照方法 |
|------------------|--------|---------|
| `1_パーソナルデータ/seo-machine/slack-bot/` | pm2 (seo-slack-bot) | フルパスで起動 |
| `1_パーソナルデータ/claude-talk-to-figma-mcp/dist/` | `~/.claude.json` → ClaudeTalkToFigma | フルパス |
| `1_パーソナルデータ/mcp-gsc/.venv/` + `gsc_server.py` | `~/.claude.json` → mcp-gsc | フルパス |
| `2_クライアントデータ/naimono/Google/*.json` | `~/.claude.json` → mcp-gsc GSC_CREDENTIALS_PATH | フルパス |
| `~/.claude/commands/` | Claude Code グローバルコマンド | 自動読込 |
| `~/.claude/agents/` | Claude Code グローバルエージェント | 自動読込 |
| `1_パーソナルデータ/seo-machine/.claude/` | Claude Code プロジェクトコマンド/エージェント | 自動読込 |

---

## 主要プロジェクト詳細

### 1_パーソナルデータ/seo-machine/ — SEO分析エンジン（本番稼働中）

対象サイト: jo-katsu.com（naimonoクライアント）

```
seo-machine/
├── slack-bot/           ← pm2常時動作。絶対に安易に触らない
│   ├── app.js           メインBot
│   ├── commands/        Slackコマンド（8個）
│   ├── lib/             共通ライブラリ
│   └── .env             認証情報
├── .claude/
│   ├── agents/          エージェント定義（11個）
│   ├── commands/        プロジェクトコマンド（28個）
│   └── skills/          スキル定義（30個以上）
├── data_sources/
│   ├── modules/         Python分析モジュール
│   ├── japanese/        日本語専用モジュール（_ja必須）
│   └── verification/    データ検証（3重チェック）
├── context/             コンテキスト文書（brand-voice, seo-guidelines等）
├── data/                ローカルデータ（clarity, change_events, cache）
└── CLAUDE.md            プロジェクトガイド
```

Slackコマンド: `/seo-log`, `/seo-cv`, `/seo-top100`, `/seo-weekly`, `/seo-verify`, `/seo-measure`, `/seo-dashboard`, `/seo-analytics`, `/seo-stop`

### 2_クライアントデータ/malna/ — コンサル業務ワークスペース

```
malna/
├── clients/naimono/     naimonoクライアント作業ファイル
├── company/nonaka/      野中個人ワークスペース
├── output/              記事変更指示書（38ファイル）← 主要成果物
└── .git/                git管理
```

**データとの関係**: 実データは番号付きフォルダ（2_〜5_）に格納。malna/はgit管理された作業出力置き場。

### 番号付きフォルダ — データレイヤー

| フォルダ | 格納内容 | git管理 |
|---------|---------|---------|
| `1_パーソナルデータ/` | SEOツール、MCPサーバー、Discord Bot、思考メモ、有料記事参考 | サブリポジトリ有 |
| `2_クライアントデータ/` | 7クライアント + malna作業ワークスペース | malna/のみgit |
| `3_自社データ/` | branding, knowledge-base, recruiting, service-materials, deliverables | なし |
| `4_ローデータ/` | 競合分析, 業界調査, 市場統計, 議事録 | なし |
| `5_機密情報/` | GCPサービスアカウントキー, 財務データ | なし |

---

## Claude Code設定（~/.claude/）

### グローバルコマンド（/コマンド名で呼び出し）
| コマンド | ファイル | 用途 |
|---------|--------|------|
| `/seo-rewrite` | commands/seo-rewrite.md | AI記事を自然な日本語にリライト |
| `/seo-change-brief` | commands/seo-change-brief.md | 既存記事の変更指示書生成 |
| `/seo-writing` | commands/seo-writing.md | SEO記事執筆 |
| `/seo-structure` | commands/seo-structure.md | 記事構成生成 |
| `/seo-query-research` | commands/seo-query-research.md | クエリ調査 |
| `/seo-recovery-plan` | commands/seo-recovery-plan.md | リカバリープラン作成 |
| `/trend-check` | commands/trend-check.md | トレンドチェック |
| `/josys-design-tonmana` | commands/josys-design-tonmana.md | Josysデザイントンマナ |
| `/organize-files` | commands/organize-files.md | ファイル整理 |

### グローバルエージェント
competitor-analyst, data-analyst, market-researcher, seo-planner, seo-researcher, seo-rewriter, seo-writer

### グローバルスキル
Figma: implement-design, code-connect-components, create-design-system-rules

---

## 検索ガイド（AIがファイルを探すとき）

| 探したいもの | 場所 |
|-------------|------|
| クライアントのデータ | `2_クライアントデータ/{クライアント名}/` |
| 記事の変更指示書 | `2_クライアントデータ/malna/output/article-changes-*.md` |
| SEO分析コマンド | `1_パーソナルデータ/seo-machine/.claude/commands/` |
| リライトのルール | `1_パーソナルデータ/seo-machine/context/writing-standards-ja.md` |
| Python分析モジュール | `1_パーソナルデータ/seo-machine/data_sources/modules/` |
| 日本語分析モジュール | `1_パーソナルデータ/seo-machine/data_sources/japanese/` |
| ブランドボイス | `1_パーソナルデータ/seo-machine/context/brand-voice.md` or `context/naimono/` |
| Slack Botのコード | `1_パーソナルデータ/seo-machine/slack-bot/` |
| グローバルSEOスキル | `~/.claude/commands/seo-*.md` |
| 認証情報 | `5_機密情報/` or `1_パーソナルデータ/seo-machine/slack-bot/.env` |
| 社内ナレッジ | `3_自社データ/knowledge-base/` |
| 議事録 | `4_ローデータ/mtg-transcripts/` |
| 一時分析スクリプト | `_adhoc/` |
| カスタムスキル定義 | `1_パーソナルデータ/custom-skills/` |
| Figma MCPサーバー | `1_パーソナルデータ/claude-talk-to-figma-mcp/` |
| GSC MCPサーバー | `1_パーソナルデータ/mcp-gsc/` |
