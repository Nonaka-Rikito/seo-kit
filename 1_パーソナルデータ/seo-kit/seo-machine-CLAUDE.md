# CLAUDE.md

このファイルは、SEO Machine ワークスペースでClaude Codeが作業する際のガイダンスを提供する。
**すべての応答は日本語で行うこと。**

## プロジェクト概要

SEO Machine は、jo-katsu.com（就活メディア）のSEO分析を自律的に行うClaude Codeワークスペース。
複数のデータソース（GSC, GA4, Clarity, Ahrefs）を統合し、
データ取得→検証→分析→施策提案を一気通貫で実行する。

### 対象サイト
- **URL**: https://jo-katsu.com/
- **GA4 Property ID**: 356839446
- **ジャンル**: 就活メディア
- **クライアント**: naimono

## セットアップ

```bash
# Python環境
.venv\Scripts\activate
pip install -r data_sources/requirements.txt
```

認証情報: `data_sources/config/.env`
サービスアカウント: `credentials/ga4-credentials.json`

## コマンド一覧

### 既存コマンド（SEO Machine標準）
- `/research [topic]` - キーワード/競合リサーチ → `research/`
- `/write [topic]` - 記事作成 → `drafts/`（最適化エージェント自動実行）
- `/rewrite [topic]` - 既存コンテンツ更新 → `rewrites/`
- `/optimize [file]` - SEO最終仕上げ
- `/analyze-existing [URL or file]` - コンテンツ健全性監査
- `/performance-review` - アナリティクス分析による優先順位付け
- `/priorities` - コンテンツ優先順位マトリクス
- `/article [topic]` - 簡易記事作成

### 新規コマンド（統合分析用）
- `/log-change` - クリエイティブ変更をイベントログに記録 + ベースライン自動取得
- `/measure-change [event_id]` - 変更のBefore/After効果測定
- `/weekly-report` - 週次SEOパフォーマンスレポート自動生成
- `/verify-data` - 分析データの3重検証チェック
- `/organic-top100` - オーガニックセッション Top100記事の月次比較 + 要対応記事の対策提案
- `/cv-report [YYYY-MM]` - CV指標（会員登録・資料DL）日次累計 + CTAバナー効果測定

## アーキテクチャ

### データソース層

| ソース | 接続方法 | 用途 |
|--------|---------|------|
| GSC | mcp-gsc（MCPサーバー） | 検索パフォーマンス、期間比較 |
| GA4 | Python API / サービスアカウント | トラフィック、エンゲージメント |
| Clarity | MCP + 日次蓄積ジョブ | UX行動分析（ヒートマップ、セッション） |
| Ahrefs | Ahrefs MCP | 競合分析、ドメインレーティング、順位データ |

### 分析パイプライン

#### 日本語対応モジュール（`data_sources/japanese/`）
- `readability_scorer_ja.py` - Janomeベースの日本語可読性スコア
- `keyword_analyzer_ja.py` - 日本語キーワード密度・共起語分析

**重要**: 英語用の `readability_scorer.py` / `keyword_analyzer.py` は日本語では正確に動作しない。
日本語コンテンツの分析には必ず `_ja` サフィックスのモジュールを使用すること。

#### 既存モジュール（`data_sources/modules/`）
1. `search_intent_analyzer.py` - 検索意図分類
2. `keyword_analyzer.py` - キーワード密度（英語用）
3. `content_length_comparator.py` - SERP上位10との比較
4. `readability_scorer.py` - 可読性スコア（英語用）
5. `seo_quality_rater.py` - 総合SEO品質スコア (0-100)
6. `opportunity_scorer.py` - 8因子のオポチュニティスコアリング

#### GA4イベント取得CLIスクリプト（`scripts/ga4_events.py`）
- `event-daily` - 指定イベントの日別カウント（`pre_register_cta_click`, `dl_material_page_view`）
- `pageviews-daily` - パスフィルタ付きPV日別カウント（`/materials/`）
- `organic-sessions` - オーガニックセッションのページ別Top N
- `organic-sessions-compare` - 2期間比較のオーガニックセッション

#### CV指標の目標管理
- `config/cv-targets.json` - 月次目標値（スプシで管理。自動同期可）
- **スプシ→cv-targets.json の自動連携**: `scripts/sync_cv_targets_from_sheet.py [スプシURL]` でスプレッドシートの目標を反映。URL省略時は `cv-targets.json` の `spreadsheet_url` を参照。事前に Google Sheets API 有効化とスプシのサービスアカウント共有が必要。
- GA4キーイベント: `pre_register_cta_click`（会員登録）, `dl_material_page_view`（資料DL）

#### 外部連携（`data_sources/integrations/`）
- `clarity_accumulator.py` - Clarityデータ日次蓄積

### データ検証レイヤー（`data_sources/verification/`）

**すべての分析レポートに検証結果を付加すること。**

- `data_verifier.py` - 1次検証: 数値再計算、範囲チェック、鮮度、サンプルサイズ
- `cross_checker.py` - 2次検証: ソース間クロスチェック、信頼度スコア

### オポチュニティスコアリング

`opportunity_scorer.py` の8つの加重因子:
Volume (25%), Position (20%), Intent (20%), Competition (15%),
Cluster (10%), CTR (5%), Freshness (5%), Trend (5%)

## Python実行

```bash
# venvを有効化してから実行
.venv\Scripts\python research_quick_wins.py
.venv\Scripts\python research_competitor_gaps.py
```

## コンテンツパイプライン

`topics/` → `research/` → `drafts/` → `review-required/` → `published/`

## コンテキストファイル

### 標準（`context/`）
- `brand-voice.md`, `style-guide.md`, `seo-guidelines.md`
- `internal-links-map.md`, `features.md`, `competitor-analysis.md`

### jo-katsu.com固有（`context/naimono/`）
- `brand-voice.md` - ジョーカツのブランドボイス定義
- `seo-guidelines.md` - 日本語SEO基準（タイトル30文字、meta 120文字等）

## データディレクトリ

- `data/clarity/` - Clarity日次蓄積データ（YYYY-MM-DD/query.json）
- `data/change_events/` - クリエイティブ変更イベントログ（events.jsonl）
- `data/cache/` - APIレスポンスキャッシュ

## 分析時の必須ルール

1. **数値を出すときは必ず検証する** - `/verify-data` または内部的に `data_verifier` + `cross_checker` を実行
2. **日本語コンテンツには日本語モジュールを使う** - `_ja` サフィックスのモジュール
3. **Before/After比較はイベントログ経由** - `/log-change` → `/measure-change` のフロー
4. **信頼度スコアをレポートに付加** - 70未満の場合は明示的に注意書きを入れる
5. **データ鮮度を確認** - GSCは3日遅延が正常。4日以上は警告

## 既存GASシステムとの関係

naimonoクライアントには既存のGASシステム（`2_クライアントデータ/naimono/analysis/gas/`）がある。
- GAS = 定型自動レポート（Slack通知、スプレッドシート記録）
- SEO Machine = 対話的AI分析、深掘り因果分析、施策提案
両者は補完関係。GASの施策キューをSEO Machineで優先順位付けする使い方が最適。
