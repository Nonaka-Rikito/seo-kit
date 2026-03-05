# テクニカルSEO監査レポート テンプレート

**クライアント**: {{client_name}}
**対象サイト**: {{site_url}}
**監査日時**: {{audit_date}}
**監査担当**: malna株式会社

---

## エグゼクティブサマリー

{{executive_summary}}

---

## スコアカード

| カテゴリ | コード | 検出問題数 | CRITICAL | HIGH | MEDIUM | LOW |
|---------|--------|-----------|----------|------|--------|-----|
| パフォーマンス | PERF | {{perf_total}} | {{perf_critical}} | {{perf_high}} | {{perf_medium}} | {{perf_low}} |
| メタ情報 | META | {{meta_total}} | {{meta_critical}} | {{meta_high}} | {{meta_medium}} | {{meta_low}} |
| サイト構造 | STRC | {{strc_total}} | {{strc_critical}} | {{strc_high}} | {{strc_medium}} | {{strc_low}} |
| 構造化データ | SCHM | {{schm_total}} | {{schm_critical}} | {{schm_high}} | {{schm_medium}} | {{schm_low}} |
| インデックス | INDX | {{indx_total}} | {{indx_critical}} | {{indx_high}} | {{indx_medium}} | {{indx_low}} |
| コンテンツ | CONT | {{cont_total}} | {{cont_critical}} | {{cont_high}} | {{cont_medium}} | {{cont_low}} |
| リダイレクト | RDIR | {{rdir_total}} | {{rdir_critical}} | {{rdir_high}} | {{rdir_medium}} | {{rdir_low}} |
| モバイル | MOBL | {{mobl_total}} | {{mobl_critical}} | {{mobl_high}} | {{mobl_medium}} | {{mobl_low}} |
| **合計** | | **{{total}}** | **{{total_critical}}** | **{{total_high}}** | **{{total_medium}}** | **{{total_low}}** |

---

## Core Web Vitals

| 指標 | モバイル | デスクトップ | 基準値 | 評価 |
|------|---------|------------|--------|------|
| LCP (Largest Contentful Paint) | {{lcp_mobile}} | {{lcp_desktop}} | < 2.5s | {{lcp_rating}} |
| FID (First Input Delay) | {{fid_mobile}} | {{fid_desktop}} | < 100ms | {{fid_rating}} |
| CLS (Cumulative Layout Shift) | {{cls_mobile}} | {{cls_desktop}} | < 0.1 | {{cls_rating}} |
| FCP (First Contentful Paint) | {{fcp_mobile}} | {{fcp_desktop}} | < 1.8s | {{fcp_rating}} |
| TTFB (Time to First Byte) | {{ttfb_mobile}} | {{ttfb_desktop}} | < 0.8s | {{ttfb_rating}} |

---

## 検出された問題（重要度順）

### CRITICAL（即日対応）

{{critical_issues}}

### HIGH（1週間以内）

{{high_issues}}

### MEDIUM（1ヶ月以内）

{{medium_issues}}

### LOW（バックログ）

{{low_issues}}

---

## 問題詳細フォーマット

各問題は以下の形式で記載：

```
#### [コード]-[番号]: [問題タイトル]

- **カテゴリ**: [PERF/META/STRC/SCHM/INDX/CONT/RDIR/MOBL]
- **重要度**: [CRITICAL/HIGH/MEDIUM/LOW]
- **対象URL**: [URL]
- **現状**: [現在の値や状態]
- **推奨**: [推奨される修正内容]
- **影響**: [SEOへの影響の説明]
- **対応方法**: [具体的な修正手順]
```

---

## 修正ロードマップ

### フェーズ1: 緊急対応（1週間以内）

| # | 問題ID | 内容 | 担当 | 期限 |
|---|--------|------|------|------|
| 1 | {{issue_id}} | {{issue_title}} | {{assignee}} | {{deadline}} |

### フェーズ2: 重要対応（1ヶ月以内）

| # | 問題ID | 内容 | 担当 | 期限 |
|---|--------|------|------|------|
| 1 | {{issue_id}} | {{issue_title}} | {{assignee}} | {{deadline}} |

### フェーズ3: 継続改善（バックログ）

| # | 問題ID | 内容 | 優先度 |
|---|--------|------|--------|
| 1 | {{issue_id}} | {{issue_title}} | {{priority}} |

---

## 技術仕様

- **クロールページ数**: {{pages_crawled}} / {{total_pages}}
- **サンプリング方式**: {{sampling_method}}
- **Lighthouse バージョン**: {{lighthouse_version}}
- **デバイス**: モバイル + デスクトップ
- **クロール日時**: {{crawl_date}}

---

## 付録

### A. クロール対象URL一覧

{{url_list}}

### B. 内部リンクグラフ統計

{{link_graph_stats}}

### C. 構造化データ検出状況

{{structured_data_stats}}

---

*本レポートは malna株式会社の WordPress テクニカルSEO監査ツールにより自動生成されました。*
*データソース: Lighthouse CLI, Google Search Console, WordPress REST API*
