# WordPress Lighthouse パフォーマンス監査

WordPress サイトのパフォーマンスと Core Web Vitals を Lighthouse CLI で測定・分析します。

## 引数

$ARGUMENTS にクライアントIDを指定してください。（例: `naimono`）
オプションで対象URLを追加指定できます。（例: `naimono https://jo-katsu.com/campus/article/123`）

## 実行手順

あなたはテクニカルSEOの専門家です。以下の手順でパフォーマンス監査を実施してください。

### Step 1: クライアント設定の確認

`C:\Users\rikit\Projects\1_パーソナルデータ\wp-techseo-audit\config\clients.json` を読み込み、指定クライアントの設定を確認します。

### Step 2: 対象URL の決定

引数にURLが指定されている場合はそのURLを対象にします。
指定がない場合は、wp_reader.py でサイトの主要ページ（トップページ + カテゴリページ上位5 + 人気記事上位5）を取得して対象にします。

```bash
cd "C:\Users\rikit\Projects\1_パーソナルデータ\wp-techseo-audit"
"C:\Users\rikit\Projects\1_パーソナルデータ\seo-machine\.venv\Scripts\python" scripts/wp_reader.py --client $ARGUMENTS --action sitemap
```

### Step 3: Lighthouse 実行

対象URLに対してLighthouse監査を実行します。

```bash
"C:\Users\rikit\Projects\1_パーソナルデータ\seo-machine\.venv\Scripts\python" scripts/lighthouse_runner.py <URL> --output "./reports/" --device mobile
```

デスクトップ版も追加実行：
```bash
"C:\Users\rikit\Projects\1_パーソナルデータ\seo-machine\.venv\Scripts\python" scripts/lighthouse_runner.py <URL> --output "./reports/" --device desktop
```

### Step 4: CWV データ抽出と分析

Lighthouse の結果から以下を抽出・分析します：
- Core Web Vitals（LCP, FID/INP, CLS）の値と評価
- パフォーマンススコア（モバイル/デスクトップ）
- 改善機会（Opportunities）の優先順位付け
- 診断情報（Diagnostics）の要約

### Step 5: 問題の分類と優先度付け

`config/audit-rules.json` の閾値に基づいて問題を分類します：
- **CRITICAL**: PSI < 50 またはLCP > 4.0s
- **HIGH**: PSI < 70 または CWV が poor 判定
- **MEDIUM**: PSI < 90 または CWV が needs_improvement
- **LOW**: 軽微な最適化提案

### Step 6: レポート生成

以下の形式でレポートを出力します：

```markdown
# Lighthouse パフォーマンス監査レポート

**クライアント**: [名前]
**対象サイト**: [URL]
**実行日時**: [日時]

## サマリー

| 指標 | モバイル | デスクトップ | 評価 |
|------|---------|------------|------|
| Performance | XX | XX | 🔴/🟡/🟢 |
| LCP | X.Xs | X.Xs | 🔴/🟡/🟢 |
| FID | XXms | XXms | 🔴/🟡/🟢 |
| CLS | X.XX | X.XX | 🔴/🟡/🟢 |

## 検出された問題（優先度順）

### CRITICAL
...

### HIGH
...

## 改善施策（推定効果順）

| # | 施策 | 推定改善 | 難易度 | 対象 |
|---|------|---------|--------|------|
| 1 | ... | -XXXms | 低/中/高 | PERF/MOBL |

## 次のステップ

- 構造化データ検証: `/wp-audit-structured-data $ARGUMENTS`
- 技術SEOクロール: `/wp-audit-crawl $ARGUMENTS`
```

レポートファイルは `C:\Users\rikit\Projects\1_パーソナルデータ\wp-techseo-audit\reports\{client}_lighthouse_{date}.md` に保存します。

## 注意事項

- Lighthouse CLI が未インストールの場合は `npm install -g lighthouse` を案内
- Chrome が見つからない場合はパスを確認
- タイムアウトエラーの場合は対象URLを減らして再試行
- 結果の解釈では WordPress 特有のボトルネック（プラグイン過多、未最適化画像、レンダリングブロッキング）に言及
