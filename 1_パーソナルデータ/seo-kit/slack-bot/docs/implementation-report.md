# SEO Machine Slack Bot — 実装ドキュメント

> 作成日: 2026-02-23
> 対象: 社内・社外共有用

---

## 目次

1. [プロジェクト概要](#1-プロジェクト概要)
2. [機能一覧 — 何ができるのか](#2-機能一覧--何ができるのか)
3. [アーキテクチャ](#3-アーキテクチャ)
4. [開発の時系列 — 何が起きたか](#4-開発の時系列--何が起きたか)
5. [発生したバグと修正](#5-発生したバグと修正)
6. [実行結果の実例](#6-実行結果の実例)
7. [SEO Machine全体のコマンド体系](#7-seo-machine全体のコマンド体系)
8. [トラブルシューティング](#8-トラブルシューティング)
9. [pm2管理コマンド](#9-pm2管理コマンド)
10. [導入手順](#10-導入手順)
11. [制限事項・できないこと](#11-制限事項できないこと)
12. [まとめ](#12-まとめ)

---

## 1. プロジェクト概要

### 何を作ったのか

jo-katsu.com（就活メディア）のSEO分析業務を、Slackのスラッシュコマンドから実行できるボットシステム。
内部でClaude Code CLIを起動し、4つのデータソース（GSC・GA4・Ahrefs・Clarity）からリアルタイムにデータを取得・分析・施策提案までを自動実行し、結果をSlackに投稿する。

### 技術スタック

| 項目 | 技術 |
|------|------|
| ランタイム | Node.js 18+ (ES Modules) |
| Slack連携 | @slack/bolt 4.1.0 (Socket Mode) |
| AI実行 | Claude Code CLI (`claude-sonnet-4-20250514`) |
| データソース | GSC (MCP), GA4 (Python CLI), Ahrefs (MCP), Clarity (MCP) |
| プロセス管理 | pm2 + pm2-windows-startup |
| 動作環境 | Windows 11 ローカルPC（クラウド不要） |

### ファイル構成

```
seo-machine/slack-bot/
├── app.js                     # メインエントリ（Bolt初期化、コマンド登録）
├── package.json               # 依存パッケージ（@slack/bolt, dotenv）
├── .env / .env.example        # Slackトークン・設定
├── bot.log                    # 実行ログ
├── lib/
│   ├── claude-runner.js       # Claude CLI実行エンジン
│   ├── command-handler.js     # 共通コマンドハンドラファクトリ
│   └── slack-formatter.js     # Markdown→Slack mrkdwn変換 + メッセージ分割
└── commands/
    ├── log-change.js          # /seo-log（モーダルフォーム）
    ├── cv-report.js           # /seo-cv
    ├── organic-top100.js      # /seo-top100
    ├── weekly-report.js       # /seo-weekly
    ├── verify-data.js         # /seo-verify
    ├── measure-change.js      # /seo-measure
    ├── executive-dashboard.js # /seo-dashboard
    └── seo-analytics.js       # /seo-analytics
```

---

## 2. 機能一覧 — 何ができるのか

### Slackコマンド9種

| コマンド | 機能 | 所要時間 |
|---------|------|---------|
| `/seo-cv [YYYY-MM]` | CV指標レポート（会員登録・資料DL数の日別推移、月次目標達成率、CTAバナー効果測定） | 2〜3分 |
| `/seo-top100` | オーガニックセッションTop100記事の前月比較 + 要対応記事の原因分析・対策提案 | 3〜5分 |
| `/seo-weekly` | 週次SEOパフォーマンスレポート（検索・順位・UX・競合） | 2〜4分 |
| `/seo-dashboard` | 月次エグゼクティブダッシュボード（KPI達成度・施策ROI・次月優先施策） | 3〜5分 |
| `/seo-analytics [依頼内容]` | 任意の分析依頼を自然言語で実行 | 2〜6分 |
| `/seo-verify [対象]` | 分析データの3重検証チェック（数値再計算・クロスチェック・信頼度スコア） | 1〜2分 |
| `/seo-measure evt-XXX` | 変更のBefore/After効果測定 | 2〜3分 |
| `/seo-log` | CTA変更等をモーダルフォームで記録（ベースラインデータ自動取得） | 1〜2分 |
| `/seo-stop` | 実行中の処理を即座に停止 | 即時 |

### 各レポートの詳細

#### /seo-cv — CV指標レポート

- GA4イベント（`pre_register_cta_click`, `dl_material_page_view`）からCV数を取得
- 日別推移・月次目標に対する達成率を算出
- CTAバナー変更の14日間Before/After比較
- CVR = CV数 / organic sessions x 100
- 検索意図分類（transactional / commercial / informational）付き

#### /seo-top100 — オーガニックTop100レポート

- GSC + GA4からTop100記事のセッション数を前月比較
- 🔴 要対応（-30%超 or 4週連続下落）→ 原因分析 + 具体的対策（P0/P1）
- ⚠️ 注意（-10%〜-30%）→ 監視リスト
- 競合コンテンツ分析: 実際の競合URL・タイトル・H2構造を提示
- ROI index = 期待月間クリック増 / 推定作業時間
- 期待効果計算式: impressions x (target CTR - current CTR)
- 全記事テーブル + データ信頼度スコア

#### /seo-weekly — 週次SEOレポート

- 月〜日曜の週単位（GSCの3日遅延を考慮）
- サイト固有CTRベンチマーク（90日間）を基準に比較
- P0（緊急）、P1（来週確認→月次判断）、P2（中期施策）に優先度分け
- 検索・順位・UX・競合の4軸で分析

#### /seo-dashboard — 月次エグゼクティブダッシュボード

- cv-report / organic-top100 / weekly-report の3レポートを統合
- KPI達成度・施策ROI・次月優先施策をサマリー
- 施策実現率 <60% → 見積精度レビューを推奨
- 優先スコア: (期待月間クリック x CVR) / 推定作業時間
- 「何もしないリスク」の定量化

#### /seo-analytics — 自由分析

- 自然言語で任意の分析依頼を実行
- 4データソースに自動アクセス
- 「事実」「解釈」「次アクション」に構造化して返答
- 3つ以上の優先アクションを提示

#### /seo-log + /seo-measure — 変更記録 & 効果測定

- `/seo-log`: Slackモーダルフォームで変更を記録（URL・種類・内容・仮説）
- 記録時にベースラインデータを自動取得・保存
- `/seo-measure evt-XXX`: 14日後にBefore/After比較
- クリック数・CTR・順位の変化を数値評価、仮説の支持/棄却を判定

---

## 3. アーキテクチャ

### システム全体図

```
Slack ユーザー
  | スラッシュコマンド（Socket Mode）
  v
+--------------------------------------+
|  Node.js (Slack Bolt) <- pm2で常駐   |
|  app.js                              |
|  +-- commands/*.js（8コマンド）       |
|  +-- lib/command-handler.js（共通）   |
|  +-- lib/slack-formatter.js（変換）   |
|  +-- lib/claude-runner.js（実行）     |
+----------+---------------------------+
           | spawn (shell:false, windowsHide:true)
           | stdin経由でプロンプト送信
           v
+--------------------------------------+
|  Claude Code CLI                     |
|  --model claude-sonnet-4-20250514    |
|  --dangerously-skip-permissions      |
|  --output-format text                |
|                                      |
|  .claude/commands/*.md を参照して     |
|  分析手順を自律実行                   |
|  +-- GSC (MCP) <- 検索パフォーマンス  |
|  +-- GA4 (Python CLI) <- CV指標       |
|  +-- Ahrefs (MCP) <- 競合・順位       |
|  +-- Clarity (MCP) <- UX行動データ    |
+----------+---------------------------+
           | stdout（レポート全文）
           v
+--------------------------------------+
|  Markdown -> Slack mrkdwn 変換       |
|  3000文字で分割                       |
|  第1チャンクで進捗メッセージを更新    |
|  第2チャンク以降はスレッドリプライ    |
|  失敗時は respond() にフォールバック  |
+--------------------------------------+
```

### 主要な設計判断

| 設計判断 | 理由 |
|---------|------|
| stdin経由プロンプト送信 | `-p` フラグではなくstdinで送信。シェルエスケープ問題を完全回避 |
| `shell: false` + `windowsHide: true` | Windows上でcmd.exe経由のシグナル伝播問題を防止（exit code 3221225786の解消） |
| CLAUDECODE環境変数削除 | Claude CLIのネストセッション検出を回避 |
| シングルプロセス制限 | 同時実行を防ぎリソース枯渇を防止。別リクエストは`/seo-stop`で中断を案内 |
| Socket Mode | WebhookのURL公開不要でファイアウォール内から動作。クラウド不要 |
| WebSocket安定化設定 | `pingPongLoopIntervalMS: 30000`, `serverPingTimeoutMS: 15000` で接続断を防止 |

### メッセージ投稿のフォールバック機構

command-handler.js は**デュアルパス + フォールバック**パターンで、確実にユーザーに結果を届ける:

```
1. chat.postMessage でボットがチャンネルに投稿できるかテスト
   |
   +-- 投稿可能 ---> chat.update で進捗を更新
   |                  結果: 第1チャンクで chat.update、第2チャンク以降はスレッド chat.postMessage
   |                  失敗時 -> respondPublic にフォールバック
   |
   +-- 投稿不可 ---> 最初から respondPublic (response_type: 'in_channel') を使用
```

- `respondPublic` はボットがチャンネル未参加でも動作する（Slack応答URLを使用）
- 全ての `respond()` 呼び出しで `response_type: 'in_channel'`（チャンネル全体に公開）

---

## 4. 開発の時系列 — 何が起きたか

### Phase 1: 仕様策定・評価・改善

Claude Code のスラッシュコマンド仕様（`.claude/commands/*.md`）を27個作成。SEO分析の各ワークフローを定義。

**初期評価:**

| レポート | スコア | 主な不足点 |
|---------|--------|----------|
| cv-report | 7/10 | CVR計算が不足 |
| organic-top100 | 8/10 | ROI指数がない |
| weekly-report | 6/10 | 季節性分析・競合詳細が不足 |

**P0改善の実装（14項目）:**

1. 検索意図分類の追加（全3レポート）
2. CVR計算用オーガニックセッション追加
3. CVR計算ロジック明示化
4. 季節性定量分析
5. 3段階コンバージョンファネル分析
6. 期待効果計算式の明示化
7. GA4-GSC整合性検証
8. 詳細競合コンテンツ分析（実URL・H2構造）
9. SERP特徴検出
10. 現行コンテンツ取得ステップ
11. ROI指数フレームワーク
12. データ検証レイヤー統合
13. 信頼度スコア付加
14. 出力形式の標準化

### Phase 2: Slack Bot本体の実装

Node.js + Slack Bolt でSocket Modeボットを構築:

1. **app.js**: Bolt初期化、認可ミドルウェア（`SLACK_ALLOWED_USER_IDS`）、8コマンド登録、`/seo-stop`、グレースフルシャットダウン（SIGINT/SIGTERM）
2. **claude-runner.js**: Claude CLIのspawn、stdin送信、5秒間隔の進捗更新、10分タイムアウト、bot.logへのログ記録、Brailleスピナーフィルタ
3. **command-handler.js**: 共通ハンドラファクトリ（`createCommandHandler()`）でコマンドごとの重複コード排除、デュアルパス + フォールバック投稿
4. **slack-formatter.js**: Markdown→Slack mrkdwn変換（テーブル→コードブロック、見出し→太字、リンク変換）、3000文字単位メッセージ分割
5. **commands/*.js**: 8コマンドそれぞれの登録・プロンプト生成。全レポートに「出力ルール」「根拠明記ルール」を明示

### Phase 3: バグ修正・安定化

→ [5. 発生したバグと修正](#5-発生したバグと修正) で詳述

### Phase 4: 品質向上 — エビデンス必須ルール

全レポートに根拠明記ルールを追加:

- 分析・判断・提案には必ず「定量データ（ツール名+数値）」または「参照ソースURL」を付記
- 🔴要対応記事には競合ページの実際のURL・タイトル・H2構成を必須
- 「※ データソース: [ツール名]」形式で帰属を明記
- 根拠なし・URL未記載の提案は禁止
- Good/Bad例 + 出力前チェックリストを仕様に追加

### Phase 5: PM2常駐化 & ドキュメント

- pm2 + pm2-windows-startup でPC起動時の自動起動を設定
- README.md に導入手順（11ステップ）、トラブルシューティング（9項目）を記載

---

## 5. 発生したバグと修正

### Bug 1: dispatch_failed エラー

| 項目 | 内容 |
|------|------|
| 症状 | `/seo-dashboard` コマンドが `dispatch_failed` で失敗 |
| 原因 | Slackアプリの設定問題（ハンドラ未登録） |
| 修正 | コマンドの登録設定を修正 |

### Bug 2: exit code 3221225786 — Windowsシグナル伝播問題

| 項目 | 内容 |
|------|------|
| 症状 | Claude CLIプロセスが異常終了。orphaned claude.exeプロセスが12個残存（合計約1.6GB消費） |
| 原因 | `shell: true` でcmd.exe経由spawn → Ctrl+Cシグナルがclaude.exeに伝播し異常終了 |
| 修正 | `shell: false` + `claude.exe` 直接spawn + `windowsHide: true` に変更 |
| 検証 | テストで正常動作確認（exit code 0）。DEP0190警告も解消 |

**修正前:**
```javascript
spawn('claude', args, { shell: true });
```

**修正後:**
```javascript
spawn('claude.exe', args, {
  shell: false,
  windowsHide: true,
});
```

### Bug 3: msg_too_long — Slackメッセージ長超過

| 項目 | 内容 |
|------|------|
| 症状 | ダッシュボードの2791文字レポートがSlack APIに `msg_too_long` で拒否。ユーザーには「処理中...」のまま表示 |
| 原因 | `MAX_SLACK_LENGTH = 3900` → Markdown→Slack変換後のオーバーヘッド（テーブルのコードブロック化等）で実際のAPI制限超過 |
| 修正 | `MAX_SLACK_LENGTH` を 3900 → 3000 に変更。3000文字超はスレッドリプライとして分割投稿 |

**修正前:**
```javascript
const MAX_SLACK_LENGTH = 3900;
```

**修正後:**
```javascript
const MAX_SLACK_LENGTH = 3000;
```

### Bug 4: organic-top100がサマリーのみ表示

| 項目 | 内容 |
|------|------|
| 症状 | MDファイルには詳細レポートが保存されているが、Slackにはサマリーしか投稿されない |
| 原因 | プロンプトの「標準出力してください」指示が曖昧で、Claude CLIがサマリーのみを出力 |
| 修正 | `buildPrompt` に「【重要: 出力ルール】」セクションを追加 |

**修正内容:**
- MDファイルと完全同一の全文を標準出力する指示を明記
- 5セクション全て必須（サマリー、🔴記事、⚠️記事、Top100テーブル、データ信頼度）
- 「サマリーのみ・要約のみの出力は不可」を明言
- 同様の出力ルールを `/seo-cv`, `/seo-weekly`, `/seo-dashboard` にも追加

### Bug 5: 変数スコープ

| 項目 | 内容 |
|------|------|
| 症状 | `initialTs` が `try` ブロック外で参照不可 |
| 修正 | `var`（tryブロック内）→ 関数スコープの `let`（`null` で初期化）に変更 |

---

## 6. 実行結果の実例

### organic-top100 レポートの実行例

GSC + GA4 データ取得 → 3件の🔴フラグ:

| 記事 | 前月比 | 分析結果 |
|------|--------|----------|
| /campus/10507/ (MBTI/外資系保険) | -60.9% | JS error 11.11%、Clarityで確認 |
| /campus/25569/ (パイロット出身大学ランキング) | -49.0% | 競合に順位を奪われた |
| /campus/11518/ (モテる職業ランキング) | -47.9% | 検索意図変化の可能性 |

- Ahrefs・Clarity統合分析を実施
- データ信頼性スコア: **67/100**（Clarity vs GA4セッション数に不一致あり）
- レポート範囲: Top30 → Top100テーブルに拡張

### executive-dashboard の実行例

- 初回: 2791文字のレポートを生成 → `msg_too_long` で投稿失敗
- 修正後: 3000文字制限で正常分割投稿

### weekly-report の実行例

- 3578文字 → 2チャンクに分割してスレッド投稿

---

## 7. SEO Machine全体のコマンド体系

Slack Bot経由で実行される9コマンド以外に、SEO Machineプロジェクトには27個のClaude Codeスラッシュコマンドが定義されている。

### コンテンツ制作系

| コマンド | 機能 |
|---------|------|
| `/article` | SEO最適化記事を4ステップリサーチパイプラインで作成 |
| `/write` | 長文SEOコンテンツ作成 |
| `/rewrite` | 既存記事の更新・改善 |
| `/optimize` | 完成記事の最終SEO最適化パス |
| `/scrub` | AI生成の痕跡除去 |
| `/publish-draft` | WordPressへの下書き公開 |

### ランディングページ系

| コマンド | 機能 |
|---------|------|
| `/landing-research` | LP機会のリサーチ |
| `/landing-write` | 高CVランディングページ作成 |
| `/landing-audit` | LP監査（CV最適化） |
| `/landing-competitor` | 競合LP分析 |
| `/landing-publish` | WordPressページとして公開 |

### リサーチ・戦略系

| コマンド | 機能 |
|---------|------|
| `/research` | キーワードリサーチ・競合分析 |
| `/research-gaps` | コンテンツギャップ特定（競合がランクしているが自サイトはない） |
| `/research-performance` | トラフィック・順位別コンテンツ分類 |
| `/research-serp` | SERP分析（Googleが求めるコンテンツの理解） |
| `/research-topics` | トピカルオーソリティ分析（キーワードクラスタリング） |
| `/research-trending` | トレンドトピック特定 |
| `/priorities` | 優先度付きコンテンツロードマップ |
| `/performance-review` | パフォーマンス分析・タスクキュー生成 |
| `/analyze-existing` | 既存記事のSEO機会分析 |

### 日本語分析系（Slack Bot連携）

| コマンド | 機能 |
|---------|------|
| `/cv-report` | CV指標レポート |
| `/organic-top100` | オーガニックTop100月次比較 |
| `/weekly-report` | 週次SEOレポート |
| `/executive-dashboard` | 月次エグゼクティブダッシュボード |
| `/log-change` | 変更記録 |
| `/measure-change` | 効果測定 |
| `/verify-data` | データ検証 |

---

## 8. トラブルシューティング

| 症状 | 原因 | 対処 |
|------|------|------|
| `invalid_auth` | Slackトークン間違い | `.env` の各トークンを再確認。`=` の前後にスペースや引用符がないこと |
| `channel_not_found` | ボット未参加 | `/invite @SEO Machine Bot` を実行 |
| `nested session` エラー | Claude Code内から起動 | pm2で起動するか独立ターミナルで実行 |
| 10分でタイムアウト | 分析が長すぎる / CLIハング | `/seo-stop` で中断して再実行 |
| コマンド表示されない | Slash Commands未登録 | Slack APIの設定を確認。登録後Slackの再起動が必要な場合あり |
| 「処理中...」のまま止まる | CLI異常終了 / 結果投稿失敗 | `pm2 logs seo-slack-bot` でログ確認 → `pm2 restart seo-slack-bot` |
| exit code 3221225786 | Windowsシグナル伝播 | `shell: false` + `windowsHide: true` を確認（claude-runner.js） |
| `msg_too_long` | Slack APIメッセージ長制限超過 | `MAX_SLACK_LENGTH` を3000以下に設定（slack-formatter.js） |
| コード変更が反映されない | pm2が旧コードで実行中 | `pm2 restart seo-slack-bot` でプロセスを再起動 |
| orphanedプロセスが残る | 旧 `shell: true` の名残 | タスクマネージャーで手動kill。現在は `shell: false` で解消済み |
| `dispatch_failed` | Slackアプリ設定不備 | コマンド登録・Socket Mode設定を確認 |

---

## 9. pm2管理コマンド

```bash
pm2 list                      # 状態確認
pm2 logs seo-slack-bot        # ログ確認
pm2 restart seo-slack-bot     # 再起動（コード変更後に必要）
pm2 stop seo-slack-bot        # 停止
pm2 start seo-slack-bot       # 起動
pm2 save                      # プロセスリスト保存（再起動復元用）
pm2-startup install           # Windows自動起動設定
```

---

## 10. 導入手順

### 前提条件

- Node.js 18以上がインストール済み
- Claude Code CLI がインストール済みで `claude` コマンドが使える
- SEO Machine ワークスペース (`seo-machine/`) がセットアップ済み

### Step 1: Slackアプリ作成

1. https://api.slack.com/apps を開く
2. 「Create New App」→「From scratch」
3. App Name: `SEO Machine Bot`、ワークスペースを選択して作成

### Step 2: Socket Mode 有効化

1. 左メニュー「Settings」→「Socket Mode」
2. Enable Socket Mode をON
3. Token Name に `socket-mode` と入力 →「Generate」
4. 表示される `xapp-...` トークンを控える

### Step 3: Bot Token Scopes 設定

1. 左メニュー「OAuth & Permissions」
2. 「Bot Token Scopes」に以下を追加:
   - `commands`
   - `chat:write`

### Step 4: Interactivity 有効化

1. 左メニュー「Interactivity & Shortcuts」
2. Interactivity をONに切り替え

### Step 5: Slash Commands 登録

左メニュー「Slash Commands」から以下を1つずつ作成:

| Command | Short Description |
|---------|------------------|
| `/seo-log` | SEO変更をイベントログに記録 |
| `/seo-cv` | CV指標レポートを生成 |
| `/seo-top100` | オーガニックTop100レポートを生成 |
| `/seo-weekly` | 週次SEOレポートを生成 |
| `/seo-verify` | データ検証チェックを実行 |
| `/seo-measure` | 変更の効果測定を実行 |
| `/seo-dashboard` | 月次エグゼクティブダッシュボードを生成 |
| `/seo-analytics` | 任意の分析依頼を実行 |
| `/seo-stop` | 実行中の処理を停止 |

※ Request URL は空欄のまま（Socket Modeでは不要）

### Step 6: ワークスペースにインストール

1. 左メニュー「Install App」→「Install to Workspace」
2. 権限を確認して「許可する」
3. 表示される Bot User OAuth Token (`xoxb-...`) を控える

### Step 7: Signing Secret 取得

1. 左メニュー「Basic Information」→「App Credentials」
2. Signing Secret の「Show」をクリックしてコピー

### Step 8: .env ファイル設定

```bash
cd seo-machine/slack-bot
cp .env.example .env
```

`.env` をエディタで開き、取得したトークンを設定:

```
SLACK_BOT_TOKEN=xoxb-取得したBot Token
SLACK_SIGNING_SECRET=取得したSigning Secret
SLACK_APP_TOKEN=xapp-取得したApp Token
SLACK_ALLOWED_USER_IDS=自分のSlackメンバーID
CLAUDE_MODEL=claude-sonnet-4-20250514
SEO_MACHINE_DIR=C:/Users/rikit/Projects/seo-machine
```

Slack メンバーIDの確認方法: Slackで自分のプロフィールを開く →「...」→「メンバーIDをコピー」

### Step 9: 依存関係インストール

```bash
cd seo-machine/slack-bot
npm install
```

### Step 10: ボットをチャンネルに招待

Slackのコマンドを使いたいチャンネルで:
```
/invite @SEO Machine Bot
```

### Step 11: 起動

```bash
node app.js
```

「SEO Machine Slack Bot 起動完了」と表示されたらOK。

### 常時起動（推奨）

```bash
# pm2 と Windows自動起動モジュールをインストール
npm install -g pm2 pm2-windows-startup

# ボットをpm2に登録して起動
cd seo-machine/slack-bot
pm2 start app.js --name seo-slack-bot

# 現在のプロセスリストを保存（再起動時に復元される）
pm2 save

# Windows起動時にpm2を自動起動するレジストリを登録
pm2-startup install
```

これでPCを再起動してもボットが自動で立ち上がる。

---

## 11. 制限事項・できないこと

| 制限 | 詳細 |
|------|------|
| 同時実行不可 | Claude CLIプロセスは1つのみ。同時に複数コマンドは実行できない（`/seo-stop`で中断は可能） |
| タイムアウト10分 | 分析が10分を超えると自動中断される |
| ローカルPC依存 | PCが起動していないと動作しない（クラウドデプロイなし） |
| Slack文字制限 | 3000文字で分割投稿。非常に長いレポートはスレッド化される |
| データソース依存 | GSC/GA4/Ahrefs/ClarityのAPI接続・MCP設定が正常でないと分析不可 |
| 認可制限 | `SLACK_ALLOWED_USER_IDS` に登録されたユーザーのみ実行可能 |
| 対象サイト固定 | 現在は jo-katsu.com 専用。他サイトへの展開は設定変更が必要 |

---

## 12. まとめ

### 実現したこと

- Slackから9つのSEOコマンドを実行可能（コマンド入力から数分で分析結果を取得）
- 4データソース（GSC・GA4・Ahrefs・Clarity）を統合した自動分析
- エビデンスベースのレポート（根拠URL・定量データ必須ルール）
- PC起動時の自動起動（pm2 + pm2-windows-startup）
- エラーハンドリング・フォールバック・進捗リアルタイム表示
- Windows固有の技術課題（シグナル伝播・プロセス管理）を解決

### 開発で解決した主要な技術課題

| 課題 | 解決策 |
|------|--------|
| Windowsシグナル伝播（orphanedプロセス） | `shell: false` + `windowsHide: true` でclaude.exe直接spawn |
| Slackメッセージ長制限 | `MAX_SLACK_LENGTH` を3000に設定 + スレッド分割投稿 |
| Claude CLI出力制御 | 明示的な「出力ルール」プロンプト（全文必須・サマリーのみ不可） |
| ネストセッション検出 | `CLAUDECODE` 環境変数を削除 |
| レポート品質 | エビデンス必須ルール + Good/Bad例 + 出力前チェックリスト |

### 数字で見る開発

- ソースコード: 11ファイル（app.js + 8コマンド + 3ライブラリ）
- コマンド仕様: 27個の `.claude/commands/*.md` ファイル
- 依存パッケージ: 2個のみ（@slack/bolt, dotenv）
- 仕様改善: 14項目のP0改善を実装
- バグ修正: 5件（シグナル伝播、メッセージ長、出力制御、変数スコープ、dispatch_failed）
