# FILE-MAP（全ファイル詳細説明）

このドキュメントは、seo-kit 内のすべてのファイルが何をするものか、1つ1つ説明したものです。
「このファイルって何？」と思ったらここを見てください。

---

## claude-skills/（Claude Code グローバルスキル）

これらは Claude Code にインストールする「指示書」です。
`~/.claude/commands/` に置くと、どのプロジェクトからでも使えるようになります。

| ファイル | 何をするもの？ | いつ使う？ |
|---------|--------------|-----------|
| `seo-query-research.md` | 指定したキーワードについて、Google検索結果を分析し、ターゲット読者・検索意図・関連キーワード20個以上を調べる | 新しい記事を書く前の調査 |
| `seo-structure.md` | 調査結果をもとに、記事の構成案（タイトル、見出し、各セクションの内容ポイント）を作る | 記事の骨組みを決めるとき |
| `seo-writing.md` | 構成案にそって、約10,000文字の記事本文を書く | 記事の本文を作成するとき |
| `seo-rewrite.md` | AIが書いた記事を自然な日本語に直す。テンプレっぽさ、説明調、過剰な丁寧語を除去する | 記事の仕上げ段階 |
| `seo-change-brief.md` | すでに公開されている記事に対して「ここをこう直してください」という修正指示書を作る | 既存記事のメンテナンス |
| `seo-recovery-plan.md` | サイト全体のSEOデータを分析して、アクセス回復のための具体的なリライト計画を作る | アクセスが下がったとき |
| `trend-check.md` | 指定した業界やテーマの最新トレンド（ニュース、新サービス、市場データ）を収集・整理する | 月次の情報収集 |

### 記事作成の順番

```
1. /seo-query-research キーワード
       ↓（調査データが会話に蓄積される）
2. /seo-structure キーワード
       ↓（構成案が作られる）
3. /seo-writing キーワード
       ↓（記事本文が生成される）
4. /seo-rewrite
       ↓（自然な日本語に変換される）
   完成！
```

---

## slack-bot/（Slack連携ボット）

SlackとClaude Code をつなぐプログラムです。

### メインファイル

| ファイル | 何をするもの？ |
|---------|--------------|
| `app.js` | ボットのメインプログラム。Slackに接続して、コマンドを待ち受ける。すべてのコマンドの登録もここで行う |
| `package.json` | ボットが使うライブラリ（@slack/bolt, dotenv）の一覧 |
| `package-lock.json` | ライブラリのバージョンを固定するファイル（触らなくてOK） |
| `.env.example` | 環境変数（APIキー等）のお手本。これを `.env` にコピーして実際の値を入れる |

### commands/（Slackコマンド）

Slackで `/seo-○○` と打ったときに動くプログラムです。

| ファイル | Slackコマンド | 何をする？ |
|---------|-------------|-----------|
| `weekly-report.js` | `/seo-weekly` | 週次SEOレポートを生成。前週比でアクセス数の増減を分析 |
| `cv-report.js` | `/seo-cv` | CV（会員登録・資料DL）の日別推移と目標達成率を集計 |
| `organic-top100.js` | `/seo-top100` | オーガニック検索からの人気記事Top100を月次比較。急落記事を検出して対策提案 |
| `executive-dashboard.js` | `/seo-dashboard` | 経営者向けの月次サマリー。主要KPIを1枚にまとめる |
| `seo-analytics.js` | `/seo-analytics` | 自由文で分析を依頼できる万能コマンド |
| `log-change.js` | `/seo-log` | 記事の変更をフォーム入力で記録。Before/After測定のベースラインも自動取得 |
| `measure-change.js` | `/seo-measure` | 記録した変更の効果を数値で測定 |
| `verify-data.js` | `/seo-verify` | 最新レポートのデータが正確か3段階で検証 |

### lib/（共通ライブラリ）

コマンドが共通で使う部品です。

| ファイル | 何をするもの？ |
|---------|--------------|
| `claude-runner.js` | Claude CLI を起動して結果を受け取るエンジン。タイムアウト（10分）、進捗表示、エラー処理を管理 |
| `command-handler.js` | 全コマンドの共通処理パターン。「処理中」表示→Claude実行→結果投稿の流れを一元管理 |
| `slack-formatter.js` | Claude の出力（Markdown）を Slack 用フォーマットに変換。テーブルをコードブロック化、長文を分割 |

---

## seo-machine-commands/（プロジェクトコマンド 28個）

Claude Code がプロジェクト内で使うコマンドの詳細な指示書です。
Slackコマンドは、裏でこれらの指示書を読んで動きます。

### レポート・分析系

| ファイル | 何をするもの？ |
|---------|--------------|
| `weekly-report.md` | 週次SEOレポートの手順書。GSC/GA4/Ahrefsからデータを取得して前週比分析 |
| `cv-report.md` | CV指標の手順書。GA4キーイベントの日別推移と目標達成率を計算 |
| `organic-top100.md` | Top100記事の手順書。セッション急落記事を検出して競合分析付きで対策提案 |
| `executive-dashboard.md` | 経営ダッシュボードの手順書。複数レポートを統合して経営指標にまとめる |
| `performance-review.md` | パフォーマンス全体レビューの手順書 |
| `verify-data.md` | データ3重検証の手順書（数値再計算→範囲チェック→ソース間整合性） |
| `log-change.md` | 変更ログ記録の手順書（イベントログ作成→ベースライン自動取得） |
| `measure-change.md` | Before/After効果測定の手順書 |

### 記事作成系

| ファイル | 何をするもの？ |
|---------|--------------|
| `article.md` | 簡易記事作成（1コマンドで完成） |
| `write.md` | 本格的な記事執筆（構成案→本文→最適化の全工程） |
| `rewrite.md` | 既存記事のリライト |
| `optimize.md` | SEO最終仕上げ（メタタグ、内部リンク、キーワード配置の最適化） |
| `publish-draft.md` | 下書きの公開作業 |
| `scrub.md` | 記事のクレンジング（不要な表現、リンク切れ等を除去） |
| `analyze-existing.md` | 既存コンテンツの健全性監査 |

### リサーチ系

| ファイル | 何をするもの？ |
|---------|--------------|
| `research.md` | 総合キーワードリサーチ |
| `research-topics.md` | トピッククラスター分析 |
| `research-trending.md` | トレンドキーワード調査 |
| `research-serp.md` | SERP（検索結果）詳細分析 |
| `research-gaps.md` | 競合とのコンテンツギャップ分析 |
| `research-performance.md` | 記事パフォーマンス調査 |
| `priorities.md` | コンテンツ優先順位マトリクス |

### ランディングページ系

| ファイル | 何をするもの？ |
|---------|--------------|
| `landing-research.md` | LP用の市場調査 |
| `landing-write.md` | LP作成 |
| `landing-competitor.md` | LP競合分析 |
| `landing-audit.md` | LP改善監査 |
| `landing-publish.md` | LP公開作業 |

---

## seo-machine-agents/（AIエージェント 11個）

特定の専門分野に特化したAI。コマンド実行時に自動的に呼び出されます。

| ファイル | 専門分野 | 何をする？ |
|---------|---------|-----------|
| `content-analyzer.md` | コンテンツ分析 | 記事の品質、SEOスコア、改善ポイントを診断 |
| `seo-optimizer.md` | SEO最適化 | メタタグ、見出し、キーワード配置を最適化 |
| `keyword-mapper.md` | キーワード分析 | キーワードの検索意図分類、クラスタリング |
| `editor.md` | 編集 | 文章の品質チェック、校正、表現改善 |
| `headline-generator.md` | 見出し生成 | CTRが高い見出しパターンを生成 |
| `internal-linker.md` | 内部リンク | サイト内の適切なリンク先を提案 |
| `meta-creator.md` | メタタグ | SEOに最適なtitle / description を生成 |
| `performance.md` | パフォーマンス | アクセスデータから課題と改善策を分析 |
| `cro-analyst.md` | CRO | コンバージョン率の改善ポイントを分析 |
| `data-verifier.md` | データ検証 | 数値の正確性、ソース間の整合性を確認 |
| `landing-page-optimizer.md` | LP最適化 | ランディングページの改善提案 |

---

## seo-machine-skills/（専門スキル 3個）

| ファイル | 何をするもの？ |
|---------|--------------|
| `growth-lead-SKILL.md` | グロースリード（成長戦略）の観点からSEO施策を統括する |
| `ja-keyword-density.md` | 日本語の記事に含まれるキーワードの出現頻度を計算する |
| `ja-readability.md` | 日本語の記事の読みやすさをスコアリングする |

---

## seo-machine-data-sources/（データソースモジュール）

データの取得・分析・検証を行うPythonプログラム群です。

### modules/（分析モジュール）

| ファイル | 何をするもの？ |
|---------|--------------|
| `google_analytics.py` | GA4 APIからアクセスデータを取得 |
| `google_search_console.py` | GSC APIから検索パフォーマンスデータを取得 |
| `keyword_analyzer.py` | 記事のキーワード密度を分析（英語用） |
| `readability_scorer.py` | 記事の読みやすさをスコアリング（英語用） |
| `seo_quality_rater.py` | 総合SEO品質スコアを0〜100で算出 |
| `opportunity_scorer.py` | 施策の優先度を8つの指標で数値化 |
| `search_intent_analyzer.py` | 検索クエリの意図を分類（情報型/取引型/ナビ型） |
| `content_length_comparator.py` | 記事の文字数をSERP上位10件と比較 |
| `content_scorer.py` | コンテンツの品質スコア算出 |
| `data_aggregator.py` | 複数ソースのデータを統合 |
| `engagement_analyzer.py` | ユーザーエンゲージメント分析 |
| `wordpress_publisher.py` | WordPressへの記事投稿 |
| その他 | CTA分析、LP分析、競合分析等 |

### japanese/（日本語特化モジュール）

| ファイル | 何をするもの？ |
|---------|--------------|
| `keyword_analyzer_ja.py` | 日本語テキストのキーワード密度分析（Janome形態素解析使用） |
| `readability_scorer_ja.py` | 日本語テキストの読みやすさスコアリング |

**重要**: 日本語サイトの分析には必ずこちら（`_ja` 付き）を使うこと。

### verification/（データ検証）

| ファイル | 何をするもの？ |
|---------|--------------|
| `data_verifier.py` | 1次検証：数値再計算、範囲チェック、鮮度確認 |
| `cross_checker.py` | 2次検証：GSC/GA4/Ahrefs間のデータ整合性チェック |

### integrations/（外部連携）

| ファイル | 何をするもの？ |
|---------|--------------|
| `clarity_accumulator.py` | Microsoft Clarityのデータを日次で蓄積 |

### config/（設定）

| ファイル | 何をするもの？ |
|---------|--------------|
| `.env.example` | API認証情報のテンプレート。`.env` にコピーして実際の値を入れる |

---

## seo-machine-scripts/（分析スクリプト）

直接実行できるPythonスクリプトです。大規模なバッチ分析に使います。

| ファイル | 何をするもの？ |
|---------|--------------|
| `ga4_events.py` | GA4のイベントデータ（PV、CV等）を取得するCLIツール |
| `research_quick_wins.py` | すぐに効果が出そうなSEO改善ポイントを自動発見 |
| `research_competitor_gaps.py` | 競合が取れていて自分が取れていないキーワードを分析 |
| `research_topic_clusters.py` | キーワードをトピックごとにグループ分け |
| `research_serp_analysis.py` | 検索結果ページの詳細分析 |
| `research_trending.py` | いま伸びているキーワードを発見 |
| `research_performance_matrix.py` | 記事パフォーマンスのマトリクス分析 |
| `research_priorities_comprehensive.py` | 総合的な施策優先度の算出 |
| `seo_baseline_analysis.py` | サイトの現状ベースライン分析 |
| `seo_competitor_analysis.py` | 競合サイトの総合分析 |
| `seo_bofu_rankings.py` | BOFU（購入検討）キーワードの順位分析 |
| `rewrite_roi_analyzer.py` | リライトのROI（費用対効果）を試算 |

### PowerShellスクリプト（Windows用）

| ファイル | 何をするもの？ |
|---------|--------------|
| `clarity-daily.ps1` | Clarityデータの日次蓄積を実行 |
| `setup-scheduler.ps1` | Windowsタスクスケジューラに日次ジョブを登録 |
| `setup-cv-targets-scheduler.ps1` | CV目標同期の定期実行を登録 |
| `sync-cv-targets-daily.ps1` | CV目標をスプレッドシートから同期 |
| `sync_cv_targets_from_sheet.py` | スプレッドシート→cv-targets.jsonの同期 |

---

## seo-machine-config/（設定ファイル）

| ファイル | 何をするもの？ |
|---------|--------------|
| `cv-targets.json` | CV（コンバージョン）の月次目標値。レポートで目標達成率を計算するのに使う |
| `competitors.example.json` | 競合サイトの設定テンプレート。自分の競合に書き換えて使う |

---

## seo-machine-context/（コンテキスト文書）

AIに「このサイトはこういうサイトだよ」と教えるための文書です。
**新しいサイトに導入するとき、必ず書き換えてください。**

| ファイル | 何を書く？ |
|---------|-----------|
| `brand-voice.md` | サイトの文体やトーン（丁寧語？カジュアル？専門的？） |
| `style-guide.md` | 文章の書き方ルール（漢字とひらがなの使い分け、数字の書き方等） |
| `seo-guidelines.md` | SEOの基本ルール（タイトル文字数、見出しルール等） |
| `internal-links-map.md` | サイト内の主要ページとURLの一覧 |
| `target-keywords.md` | 狙いたいキーワード一覧 |
| `competitor-analysis.md` | 競合サイトの分析結果 |
| `features.md` | サイトの機能・サービス一覧 |
| `writing-examples.md` | 良い記事のお手本 |
| `cro-best-practices.md` | コンバージョン改善のベストプラクティス |
| `example-client/` | クライアント固有設定のサンプルフォルダ |

---

## ルートのファイル

| ファイル | 何をするもの？ |
|---------|--------------|
| `README.md` | このツールキットの全体説明（今読んでいるものとは別） |
| `SETUP-GUIDE.md` | 新規セットアップの手順書 |
| `FILE-MAP.md` | このファイル。全ファイルの詳細説明 |
| `seo-machine-CLAUDE.md` | SEO Machine のメイン設定ファイルのサンプル |
| `seo-machine-README.md` | SEO Machine 元のREADMEファイル |
