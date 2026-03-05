# CLAUDE.md — WordPress テクニカルSEO監査パッケージ

**すべての応答は日本語で行うこと。**

## 概要

WordPress サイトのテクニカルSEOを MECE に分析し、施策出し・修正適用まで一気通貫で行うスキルパッケージ。

## パッケージ構成

```
wp-techseo-audit/
├── CLAUDE.md                     ← このファイル
├── config/
│   ├── .env                      環境変数（.gitignore対象）
│   ├── .env.example              環境変数テンプレート
│   ├── clients.json              マルチクライアント接続設定
│   └── audit-rules.json          監査ルール閾値定義
├── scripts/
│   ├── requirements.txt          Python依存パッケージ
│   ├── wp_reader.py              WP REST API 読み取りクライアント
│   ├── lighthouse_runner.py      Lighthouse CLI ラッパー
│   ├── site_crawler.py           軽量サイトクローラー
│   ├── structured_data_validator.py  構造化データ検証
│   └── wp_meta_updater.py        WP REST API 書き込み（メタ更新）
├── skills/
│   ├── wp-audit-full.md          総合監査（オーケストレーター）
│   ├── wp-audit-lighthouse.md    Step1: パフォーマンス & CWV
│   ├── wp-audit-structured-data.md  Step2: 構造化データ検証
│   ├── wp-audit-crawl.md         Step3: 技術SEOクロール
│   ├── wp-audit-fix.md           Step4: WordPress修正適用
│   └── wp-audit-index.md         Step5: インデックス確認
├── templates/
│   ├── audit-report.md           レポートテンプレート
│   └── fix-plan.md               修正計画テンプレート
└── reports/                      出力レポート格納先（自動作成）
```

## セットアップ

### 1. Python依存パッケージ（seo-machine の venv を共用）

```bash
cd "C:\Users\rikit\Projects\1_パーソナルデータ\seo-machine"
.venv\Scripts\pip install beautifulsoup4 lxml requests python-dotenv
```

### 2. Lighthouse CLI

```bash
npm install -g lighthouse
# 確認: lighthouse --version → 13.0.3 (2026-02-27時点)
```

Chrome は Windows 11 にプリインストール済み（自動検出）。

### 3. 環境変数

```bash
cp config/.env.example config/.env
# config/.env を編集してクライアントのアプリパスワードを設定
```

### 4. クライアント追加

`config/clients.json` にクライアント設定を追加。

## スキル一覧

| スキル | 用途 |
|-------|------|
| `/wp-audit-full [client]` | 総合監査（全5ステップを順次実行） |
| `/wp-audit-lighthouse [client]` | パフォーマンス & CWV 監査 |
| `/wp-audit-structured-data [client]` | 構造化データ検証 |
| `/wp-audit-crawl [client]` | 技術SEOクロール監査 |
| `/wp-audit-fix [client]` | 修正適用（ユーザー確認必須） |
| `/wp-audit-index [client]` | インデックス状況確認 |

---

## 実践ワークフロー（`/wp-audit-full` の実行手順）

### 全体の並行実行戦略

full監査はステップを**可能な限り並行実行**して効率化する。依存関係は以下の通り:

```
並行グループ1（同時開始可能）:
  ├── Step 1: Lighthouse（mobile + desktop 各10ページ）  … 約20〜30分
  ├── Step 2: 構造化データ検証                           … 約2〜3分
  ├── Step 3: サイトクロール（100ページ）                 … 約5〜10分
  └── Step 5: GSCインデックス確認（MCP経由）             … 約2分

並行グループ2（グループ1の結果が必要）:
  └── Step 4: 修正計画の統合 → 統合レポート生成
```

### Phase 0: 事前準備（必須）

```bash
# 1. Lighthouse CLI の確認
lighthouse --version

# 2. クライアント設定の確認
cd "C:\Users\rikit\Projects\1_パーソナルデータ\wp-techseo-audit"
cat config/clients.json
```

### Phase 1: 対象URLの取得

サイトマップ → WP REST API（pages + posts + カスタム投稿タイプ）の順でフォールバック。

```bash
PYTHON="C:\Users\rikit\Projects\1_パーソナルデータ\seo-machine\.venv\Scripts\python"

# まずサイトマップを試す（タイムアウトすることがある）
$PYTHON scripts/wp_reader.py --client naimono --action sitemap

# サイトマップがタイムアウトした場合、WP REST APIから取得:
$PYTHON scripts/wp_reader.py --client naimono --action pages
$PYTHON scripts/wp_reader.py --client naimono --action posts
$PYTHON scripts/wp_reader.py --client naimono --action posts --post-type campus  # カスタム投稿
```

**対象URLの選定基準**（10ページ推奨）:
- トップページ（1）
- 主要固定ページ（3〜4: about, service, LP等）
- メディアトップ（1: /campus/ 等のアーカイブページ）
- 記事ページ（5: 直近の投稿から選定）

選定したURLを `reports/{client}_target_urls.txt` に保存:

```
https://jo-katsu.com/
https://jo-katsu.com/campus/
https://jo-katsu.com/service/
...
```

### Phase 2: 並行実行

以下を**全てバックグラウンドで同時起動**する:

```bash
# Step 1a: Lighthouse モバイル（バッチ）
$PYTHON scripts/lighthouse_runner.py --batch "./reports/{client}_target_urls.txt" --output "./reports/" --device mobile --json

# Step 1b: Lighthouse デスクトップ（バッチ）
$PYTHON scripts/lighthouse_runner.py --batch "./reports/{client}_target_urls.txt" --output "./reports/" --device desktop --json

# Step 2: 構造化データ検証
$PYTHON scripts/structured_data_validator.py --batch "./reports/{client}_target_urls.txt" --output "./reports/" --generate-fix

# Step 3: サイトクロール
$PYTHON scripts/site_crawler.py "https://jo-katsu.com/" --max-pages 100 --output "./reports/" --delay 0.5

# Step 5: GSCインデックス確認（MCP経由 — サブエージェントで実行）
```

### Phase 3: 分析・レポート統合

各ステップの結果を**サブエージェント（Sonnet）**に渡して分析。大きなJSONレポートはメインコンテキストを圧迫するため、必ずサブエージェントで処理する。

最後に統合レポートを生成:
- `reports/{client}_full_audit_{date}.md` — 総合監査レポート
- `reports/{client}_fix_plan_{date}.json` — 修正プラン（JSON）

---

## スクリプトCLIリファレンス

### wp_reader.py

```bash
$PYTHON scripts/wp_reader.py --client <client_id> --action <action> [options]

# アクション一覧:
--action site-info    # サイト基本情報
--action posts        # 投稿一覧（--post-type で変更可能、--status で絞り込み）
--action pages        # 固定ページ一覧
--action meta         # 個別投稿のメタ情報（--post-id 必須）
--action sitemap      # サイトマップURLの取得・パース
--action redirects    # リダイレクト設定の取得
--action health       # サイトヘルス情報

# カスタム投稿タイプの取得:
--action posts --post-type campus    # ※エンドポイント名を指定
```

### lighthouse_runner.py

```bash
# 単一URL:
$PYTHON scripts/lighthouse_runner.py <URL> --output "./reports/" --device mobile
$PYTHON scripts/lighthouse_runner.py <URL> --output "./reports/" --device desktop

# バッチ:
$PYTHON scripts/lighthouse_runner.py --batch urls.txt --output "./reports/" --device mobile --json

# ⚠ --json はlighthouse_runner.pyのみサポート。他スクリプトには付けない。
```

### structured_data_validator.py

```bash
# 単一URL:
$PYTHON scripts/structured_data_validator.py <URL>
$PYTHON scripts/structured_data_validator.py <URL> --generate-fix

# バッチ:
$PYTHON scripts/structured_data_validator.py --batch urls.txt --output "./reports/" --generate-fix

# ⚠ --json フラグは非対応
```

### site_crawler.py

```bash
$PYTHON scripts/site_crawler.py <site_url> --max-pages 100 --output "./reports/" --delay 0.5

# オプション:
--max-pages N    # クロール上限（デフォルト: clients.json の max_pages）
--delay N        # リクエスト間隔（秒、デフォルト: 0.5）
--no-robots      # robots.txt を無視
--keep-query     # クエリパラメータ付きURLも保持

# ⚠ --json フラグは非対応
```

### wp_meta_updater.py

```bash
# ドライラン（デフォルト — 書き込みゼロ）:
$PYTHON scripts/wp_meta_updater.py --client <client_id> --plan <plan_file>

# 実行（ユーザー承認必須）:
$PYTHON scripts/wp_meta_updater.py --client <client_id> --plan <plan_file> --execute
```

---

## MECE 問題分類（8カテゴリ）

| コード | カテゴリ | 対応スキル |
|--------|---------|-----------|
| PERF | パフォーマンス（CWV・速度・リソース） | lighthouse |
| META | メタ情報（title/desc/canonical/OG） | crawl |
| STRC | サイト構造（見出し・内部リンク・パンくず） | crawl |
| SCHM | 構造化データ（JSON-LD・Microdata） | structured-data |
| INDX | インデックス（noindex/robots.txt/発見性） | index |
| CONT | コンテンツ（重複・thin content・画像alt） | crawl |
| RDIR | リダイレクト（チェーン・404・ループ） | crawl |
| MOBL | モバイル（ビューポート・タップターゲット） | lighthouse |

### 重要度レベル

| レベル | SLA | 基準 |
|--------|-----|------|
| CRITICAL | 即日 | サイトダウン、インデックス喪失、PSI < 50、LCP > 4.0s |
| HIGH | 1週間 | CWV poor判定、重要ページのメタ欠落、canonical不整合 |
| MEDIUM | 1ヶ月 | CWV needs_improvement、構造化データ不備、H1重複 |
| LOW | バックログ | ベストプラクティス違反、軽微な最適化 |

## MCP連携

| ツール | 用途 | 使用ステップ |
|-------|------|------------|
| GSC MCP (mcp-gsc) | インデックス確認、検索パフォーマンス | Step 5 |
| Ahrefs MCP | 外部指標照合、競合比較 | Step 3（任意） |
| Clarity MCP | RUMデータ補完 | Step 1（任意） |

### GSC MCP で利用するツール

```
mcp-gsc:
  list_properties          — プロパティ一覧でアクセス確認
  get_performance_overview — 検索パフォーマンス概要
  inspect_url_enhanced     — 個別URLのインデックス詳細
  batch_url_inspection     — 複数URLの一括インデックス確認
  check_indexing_issues    — インデックス問題の一覧
  list_sitemaps_enhanced   — サイトマップ一覧・ステータス
  get_sitemap_details      — サイトマップ詳細
```

## 安全設計

- `wp_meta_updater.py` はデフォルトでドライラン（`--execute` なしでは書き込みゼロ）
- 変更適用時はロールバックファイルを自動生成
- スキル内でユーザーの明示的な承認を必須化
- robots.txt 準拠のクロール

## レポート出力

全レポートは `reports/` ディレクトリに保存:

| ファイル | 生成元 |
|---------|-------|
| `{client}_target_urls.txt` | Phase 1で手動作成 |
| `jo-katsu.com_*_mobile_*.json` | lighthouse_runner.py（モバイル） |
| `jo-katsu.com_*_desktop_*.json` | lighthouse_runner.py（デスクトップ） |
| `structured_data_report.json` | structured_data_validator.py |
| `{domain}_crawl_{date}.json` | site_crawler.py |
| `{client}_full_audit_{date}.md` | 統合レポート（手動生成） |
| `{client}_fix_plan_{date}.json` | 修正プラン（手動生成） |

---

## ベストプラクティスと学び（2026-02-27 初回監査より）

### 実行効率

1. **並行実行を最大化する**: Lighthouse（mobile/desktop）、構造化データ検証、クロール、GSCインデックス確認は全て独立して実行可能。`run_in_background` で同時起動すると総時間を大幅短縮できる。
2. **Lighthouseが最もボトルネック**: 10ページ × 2デバイス = 20回の監査で約20〜30分。バッチモード（`--batch`）を必ず使う。
3. **サブエージェントで分析を並行化**: 大きなJSON結果（構造化データ76KB、クロール結果等）はメインコンテキストに載せるとトークンを消費する。Sonnetサブエージェントに分析を委託する。

### 既知の注意点（トラブルシューティング）

1. **サイトマップ取得のタイムアウト**: `wp_reader.py --action sitemap` はサイトマップが遅いサイトで30秒タイムアウトする。WP REST API（`--action pages` + `--action posts --post-type <type>`）にフォールバックすること。
2. **Windowsエンコーディング問題**: `wp_reader.py` の出力が日本語文字を含む場合、`cp932` エンコードエラー（`UnicodeEncodeError`）が発生することがある。Python の `-c` インラインスクリプトでJSONファイルに直接書き出す方法で回避。
3. **`--json` フラグの対応**: `lighthouse_runner.py` のみ `--json` フラグ対応。`structured_data_validator.py` と `site_crawler.py` は非対応（付けるとエラー）。
4. **カスタム投稿タイプ**: `wp_reader.py --action posts` のデフォルトは標準 `posts`。カスタム投稿タイプ（例: campus）は `--post-type campus` で明示指定が必要。WP REST APIのエンドポイント名を使う。
5. **バックグラウンドタスクのID失効**: Claude Code のバックグラウンドタスクIDは時間経過で失効する場合がある。`reports/` ディレクトリのファイルを直接確認する方が確実。
6. **Lighthouseの結果ファイル**: `lighthouse_runner.py` は結果JSONをパース後に自動削除する（`run_audit` 内）。バッチモード + `--json` でstdoutにCWVサマリーを出力するのがベスト。ただしバッチの生JSONは残らない。個別のレポートJSON（`jo-katsu.com_*_*.json`）はバッチ実行時にも `reports/` に残る。

### 対象URL選定のコツ

- **10ページが適切**: 多すぎるとLighthouseに時間がかかりすぎ、少なすぎると網羅性に欠ける。
- **ページタイプの多様性を確保**: トップ、LP、サービスページ、記事一覧、個別記事を含める。
- **SEO的に重要なページを優先**: 内部被リンクが多いページ、トラフィック上位ページを含める。

### レポート品質

- **エグゼクティブサマリーを必ず冒頭に**: クライアントが最初に読む箇所。3〜5行で最重要の発見事項を凝縮。
- **修正ロードマップは時間軸で整理**: Week 1（CRITICAL）→ Week 2-4（HIGH/MEDIUM）→ Month 2+（LOW）。
- **数値の出典を明記**: 「PSI 38（モバイル）」「LCP 30.2s」のように具体値を示す。
- **修正プランJSON**: `/wp-audit-fix` で機械的に適用可能な形式で出力。actions フィールドに具体的な手順を記載。

### クライアント別メモ

#### naimono（ジョーカツ / jo-katsu.com）
- **初回監査日**: 2026-02-27
- **サイトURL**: https://jo-katsu.com
- **GSC対象**: https://jo-katsu.com/campus/
- **カスタム投稿タイプ**: `campus`（就活ハンドブック記事）
- **SEOプラグイン**: Yoast
- **主な問題**:
  - モバイルPSI平均38.3（CRITICAL）— TTFB遅延が根本原因
  - campusページのモバイルLCP 30秒超 — リダイレクトチェーン + サーバー遅延
  - GSCサイトマップが1年7ヶ月ダウンロードされていない
  - Article/BlogPostingスキーマ未実装（記事リッチリザルト機会損失）
  - H1重複92ページ（テーマテンプレートの構造問題）
  - noindex 15ページ（意図確認必要）
  - canonical不整合 11件（旧URL構造の名残り）
- **レポート**: `reports/naimono_full_audit_20260227.md`
