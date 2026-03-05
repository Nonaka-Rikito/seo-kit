# SEO Kit

**Slackからコマンド1つでSEO分析・記事作成ができる自動化ツールセット**

---

## これは何？

SEO Kit は、ウェブサイトのSEO（検索エンジン最適化）を自動でやってくれる道具箱です。

ふつう、SEO分析や記事作成には「データを集めて、分析して、記事を書いて、チェックして……」という手順が必要ですが、SEO Kit なら **Slackで `/seo-weekly` と打つだけ** で、AIが全部やってくれます。

### 例えるなら

- ふつうのSEO = 自分で材料を買って、自分で料理して、自分で味見する
- SEO Kit = 「今日の晩ごはん作って」と言うだけで全部出てくる

---

## フォルダの中身（全体マップ）

```
seo-kit/
│
├── README.md .......................... このファイル（今読んでいるもの）
├── SETUP-GUIDE.md .................... 新規セットアップの手順書
├── FILE-MAP.md ....................... 全ファイルの詳細説明
│
├── claude-skills/ .................... Claude Code のスキル（指示書）
│   ├── seo-query-research.md         キーワード調査
│   ├── seo-structure.md              記事の構成案を作る
│   ├── seo-writing.md                記事を書く
│   ├── seo-rewrite.md                記事を自然な日本語に直す
│   ├── seo-change-brief.md           既存記事の修正指示書を作る
│   ├── seo-recovery-plan.md          アクセス回復の計画を作る
│   └── trend-check.md                業界トレンドを調べる
│
├── slack-bot/ ........................ Slack連携ボット
│   ├── app.js                        ボットのメインプログラム
│   ├── .env.example                  環境変数のお手本
│   ├── package.json                  使うライブラリの一覧
│   ├── commands/                     Slackコマンド（8個）
│   │   ├── weekly-report.js            /seo-weekly（週次レポート）
│   │   ├── cv-report.js                /seo-cv（CV指標レポート）
│   │   ├── organic-top100.js           /seo-top100（人気記事Top100）
│   │   ├── executive-dashboard.js      /seo-dashboard（経営ダッシュボード）
│   │   ├── seo-analytics.js            /seo-analytics（自由分析）
│   │   ├── log-change.js               /seo-log（変更記録）
│   │   ├── measure-change.js           /seo-measure（効果測定）
│   │   └── verify-data.js              /seo-verify（データ検証）
│   └── lib/                          共通ライブラリ
│       ├── claude-runner.js            Claude CLIの実行エンジン
│       ├── command-handler.js          コマンドの共通処理
│       └── slack-formatter.js          Slack向けメッセージ整形
│
├── seo-machine-commands/ ............. Claude Codeプロジェクトコマンド（28個）
│   ├── COMMANDS_SUMMARY.md           コマンド一覧
│   ├── weekly-report.md              週次レポートの詳細手順
│   ├── cv-report.md                  CV指標レポートの詳細手順
│   ├── organic-top100.md             Top100レポートの詳細手順
│   ├── article.md                    記事作成
│   ├── write.md                      記事執筆
│   ├── rewrite.md                    記事リライト
│   ├── optimize.md                   SEO最適化
│   ├── research.md                   キーワードリサーチ
│   ├── research-topics.md            トピック調査
│   ├── research-trending.md          トレンド調査
│   ├── research-serp.md              検索結果分析
│   ├── research-gaps.md              コンテンツギャップ分析
│   ├── research-performance.md       パフォーマンス調査
│   ├── landing-write.md              LP作成
│   ├── landing-audit.md              LP監査
│   ├── landing-research.md           LP調査
│   ├── landing-competitor.md         LP競合分析
│   ├── landing-publish.md            LP公開
│   └── ... その他
│
├── seo-machine-agents/ ............... AIエージェント定義（11個）
│   ├── content-analyzer.md           コンテンツ分析AI
│   ├── seo-optimizer.md              SEO最適化AI
│   ├── keyword-mapper.md             キーワード分析AI
│   ├── editor.md                     編集AI
│   ├── headline-generator.md         見出し生成AI
│   ├── internal-linker.md            内部リンク設計AI
│   ├── meta-creator.md               メタタグ生成AI
│   ├── performance.md                パフォーマンス分析AI
│   ├── cro-analyst.md                コンバージョン率分析AI
│   ├── data-verifier.md              データ検証AI
│   └── landing-page-optimizer.md     LP最適化AI
│
├── seo-machine-skills/ ............... 専門スキル（3個）
│   ├── growth-lead-SKILL.md          グロースリードAI
│   ├── ja-keyword-density.md         日本語キーワード密度分析
│   └── ja-readability.md             日本語読みやすさ分析
│
├── seo-machine-data-sources/ ......... データ取得モジュール
│   ├── requirements.txt              Python依存ライブラリ
│   ├── config/.env.example           API接続設定のお手本
│   ├── modules/                      データ分析モジュール群
│   │   ├── google_analytics.py         GA4からデータ取得
│   │   ├── google_search_console.py    GSCからデータ取得
│   │   ├── keyword_analyzer.py         キーワード密度分析
│   │   ├── readability_scorer.py       読みやすさスコア
│   │   ├── seo_quality_rater.py        SEO品質スコア
│   │   ├── opportunity_scorer.py       優先度スコアリング
│   │   ├── search_intent_analyzer.py   検索意図分類
│   │   ├── content_length_comparator.py  文字数比較
│   │   └── ... その他
│   ├── japanese/                     日本語特化モジュール
│   │   ├── keyword_analyzer_ja.py      日本語キーワード分析
│   │   └── readability_scorer_ja.py    日本語読みやすさ分析
│   ├── verification/                 データ検証
│   │   ├── data_verifier.py            数値の正確さチェック
│   │   └── cross_checker.py            複数ソース間の整合性チェック
│   └── integrations/                 外部連携
│       └── clarity_accumulator.py      Clarityデータ蓄積
│
├── seo-machine-scripts/ .............. 分析スクリプト
│   ├── ga4_events.py                 GA4イベントデータ取得
│   ├── research_quick_wins.py        すぐ効くSEO施策を発見
│   ├── research_competitor_gaps.py   競合との差を分析
│   ├── research_topic_clusters.py    トピック群を整理
│   ├── research_serp_analysis.py     検索結果を詳細分析
│   ├── research_trending.py          トレンドキーワード発見
│   ├── seo_baseline_analysis.py      現状のベースライン分析
│   ├── seo_competitor_analysis.py    競合サイト分析
│   └── ... その他
│
├── seo-machine-config/ ............... 設定ファイル
│   ├── cv-targets.json               CV目標値
│   └── competitors.example.json      競合設定のお手本
│
├── seo-machine-context/ .............. コンテキスト文書（ブランドボイス等）
│   ├── brand-voice.md                ブランドの声のトーン
│   ├── style-guide.md                文章スタイルガイド
│   ├── seo-guidelines.md             SEOルール
│   ├── internal-links-map.md         内部リンク設計図
│   ├── target-keywords.md            ターゲットキーワード
│   └── naimono/                      クライアント固有設定のサンプル
│       ├── brand-voice.md
│       └── seo-guidelines.md
│
├── seo-machine-CLAUDE.md ............. SEO Machineのメイン設定ファイル
└── seo-machine-README.md ............. SEO Machine元のREADME
```

---

## システム全体の仕組み（図解）

```
【人間がやること】           【AIが自動でやること】

Slackで                   ┌─────────────────────────────────┐
コマンドを打つ  ──────────→│  Slack Bot (slack-bot/)          │
例: /seo-weekly           │  コマンドを受け取る               │
                         └──────────┬──────────────────────┘
                                    │
                                    v
                         ┌─────────────────────────────────┐
                         │  Claude CLI                      │
                         │  AIがコマンドの指示書を読む        │
                         │  (seo-machine-commands/*.md)     │
                         └──────────┬──────────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    v               v               v
            ┌──────────┐   ┌──────────┐   ┌──────────┐
            │ GSC      │   │ GA4      │   │ Ahrefs   │
            │ 検索データ│   │ アクセス  │   │ 競合データ│
            └──────────┘   └──────────┘   └──────────┘
                    │               │               │
                    └───────────────┼───────────────┘
                                    v
                         ┌─────────────────────────────────┐
                         │  データ検証 (verification/)      │
                         │  数値が正しいかチェック           │
                         └──────────┬──────────────────────┘
                                    │
                                    v
                         ┌─────────────────────────────────┐
                         │  レポート生成 → Slackに投稿       │
                         └─────────────────────────────────┘
```

---

## 用語の説明

普段聞き慣れない言葉が出てくるので、ここで説明します。

| 用語 | 意味 |
|------|------|
| **SEO** | Search Engine Optimization。Googleで記事を上位に表示させるための工夫 |
| **Claude Code** | Anthropic社のAI「Claude」をコマンドラインから使うツール |
| **スキル (skill)** | Claude Code に「こういうやり方で仕事して」と教える指示書（.mdファイル） |
| **コマンド (command)** | Claude Code やSlackに「これやって」と伝える命令 |
| **エージェント (agent)** | 特定の専門分野に特化したAI。記事分析専門、見出し作成専門、など |
| **GSC** | Google Search Console。Googleでの検索順位やクリック数が見れるツール |
| **GA4** | Google Analytics 4。ウェブサイトへのアクセス数が見れるツール |
| **Ahrefs** | SEO分析ツール。競合サイトのデータも見れる |
| **Clarity** | Microsoft社のツール。ユーザーがサイトのどこを見ているか分析できる |
| **CV** | Conversion（コンバージョン）。会員登録や資料ダウンロードなどの成果 |
| **MCP** | Model Context Protocol。AIが外部ツールと連携するための仕組み |
| **Slack Bot** | Slackの中で動く自動プログラム。コマンドを受けてAIを動かす |
| **pm2** | Node.jsのプロセス管理ツール。ボットを常時動かし続けるために使う |

---

## Slackコマンド一覧

Slackで使えるコマンドは全部で9個あります。

### レポート系

| コマンド | 何ができる？ | 使い方 |
|---------|-------------|--------|
| `/seo-weekly` | 今週のSEO成績表を作る | そのまま打つだけ |
| `/seo-cv` | CV（会員登録・資料DL）の成績表 | `/seo-cv` or `/seo-cv 2026-02` |
| `/seo-top100` | 人気記事Top100の比較表 | そのまま打つだけ |
| `/seo-dashboard` | 経営者向けまとめレポート | そのまま打つだけ |

### 分析系

| コマンド | 何ができる？ | 使い方 |
|---------|-------------|--------|
| `/seo-analytics` | 自由な質問でSEO分析 | `/seo-analytics 今月のPV低下原因は？` |
| `/seo-verify` | データが正確か検証する | そのまま打つだけ |

### 変更管理系

| コマンド | 何ができる？ | 使い方 |
|---------|-------------|--------|
| `/seo-log` | 記事の変更を記録する | 打つとフォームが出る |
| `/seo-measure` | 変更の効果を測る | `/seo-measure evt-001` |
| `/seo-stop` | 実行中の処理を止める | そのまま打つだけ |

---

## Claude Code スキル一覧

Claude Code で直接使えるスキルは7個あります。コマンドラインで `/` を打って選びます。

### 記事を作る流れ

```
ステップ1: /seo-query-research SEO対策
    ↓  キーワードを調べる
ステップ2: /seo-structure SEO対策
    ↓  記事の構成案を作る
ステップ3: /seo-writing SEO対策
    ↓  記事を書く
ステップ4: /seo-rewrite
    ↓  自然な日本語に直す
完成！
```

### その他のスキル

| スキル | 何ができる？ |
|--------|-------------|
| `/seo-change-brief` | 既存記事の修正指示書を作る |
| `/seo-recovery-plan` | アクセスが減ったサイトの回復計画を作る |
| `/trend-check` | 業界の最新トレンドを調べる |

---

## 3つの使い方

### 1. Slackから使う（一番かんたん）

Slackのチャンネルで `/seo-weekly` などのコマンドを打つだけ。
ボットがAIを動かして、結果をチャンネルに投稿してくれます。

### 2. Claude Code から直接使う（詳しい人向け）

ターミナルで `claude` を起動して、`/seo-query-research SEO対策` のように使います。
記事作成など、対話しながら作業したいときに便利です。

### 3. Python スクリプトを実行する（エンジニア向け）

`seo-machine-scripts/` のPythonスクリプトを直接実行して、
大量のデータ分析を一気に行えます。

---

## 新しいプロジェクトに導入するには？

詳しい手順は [SETUP-GUIDE.md](SETUP-GUIDE.md) を見てください。

ざっくり言うと：

1. **このフォルダをコピー** する
2. **環境変数を設定** する（APIキー等）
3. **対象サイト情報を書き換える**（CLAUDE.md、context/）
4. **Slack Botを設定** する
5. **動作確認** する

---

## ファイルの関係図

どのファイルが何を呼び出しているか、ざっくり図にするとこうなります：

```
Slack コマンド入力
  │
  ├── slack-bot/commands/weekly-report.js
  │     │
  │     ├── lib/command-handler.js（共通処理）
  │     │     └── lib/claude-runner.js（Claude CLI実行）
  │     │           │
  │     │           └── Claude Code が起動
  │     │                 │
  │     │                 ├── seo-machine-commands/weekly-report.md を読む
  │     │                 │     （「何をすべきか」の詳細手順）
  │     │                 │
  │     │                 ├── seo-machine-agents/performance.md を参照
  │     │                 │     （パフォーマンス分析の専門知識）
  │     │                 │
  │     │                 ├── seo-machine-context/seo-guidelines.md を参照
  │     │                 │     （SEOルール）
  │     │                 │
  │     │                 └── データソース（GSC / GA4 / Ahrefs）に接続
  │     │                       │
  │     │                       └── seo-machine-data-sources/verification/
  │     │                             （データが正しいか検証）
  │     │
  │     └── lib/slack-formatter.js（結果をSlack用に整形）
  │
  └── Slackチャンネルに結果が投稿される
```

---

## よくある質問

### Q: プログラミングの知識は必要？
**A:** Slackから使うだけなら不要です。セットアップ時にはコマンドのコピペが少し必要です。

### Q: 対応しているサイトは？
**A:** どんなウェブサイトでも使えます。`seo-machine-CLAUDE.md` と `seo-machine-context/` の内容を自分のサイト用に書き換えてください。

### Q: AIの利用料はかかる？
**A:** Claude Code（Anthropic）の利用料がかかります。1回のレポート実行で数十円〜数百円程度です。

### Q: データは安全？
**A:** すべてローカル（自分のPC）で処理されます。外部にデータを送るのはAPI呼び出し時のみです。

### Q: 同時に複数のコマンドを実行できる？
**A:** いいえ。1度に1つのコマンドしか実行できません。実行中に `/seo-stop` で中断できます。

---

## ライセンス

社内利用専用。外部公開禁止。
