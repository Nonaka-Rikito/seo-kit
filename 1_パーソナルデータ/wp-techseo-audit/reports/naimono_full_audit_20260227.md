# WordPress テクニカルSEO 総合監査レポート

**クライアント**: ナイモノ（ジョーカツ / スタキャリ）
**対象サイト**: https://jo-katsu.com
**監査日時**: 2026-02-27
**監査ステップ**: 全5ステップ完了

---

## エグゼクティブサマリー

jo-katsu.com は **モバイルパフォーマンスが壊滅的な状態** にある。モバイル平均PSIは38.3点（100点満点）、キャンパス記事ページのLCPは30秒超という異常値を記録。サーバー応答時間（TTFB）の遅さが全ページ共通のボトルネック。構造化データはエラーゼロだが、記事ページにArticleスキーマが未実装でリッチリザルト獲得を逸失。クロール監査では100ページ全件に問題があり、H1重複92件・noindex設定15件・canonical不整合11件が検出された。GSCサイトマップは1年7ヶ月間ダウンロードされておらず、新規ページのクロール遅延リスクがある。

---

## スコアカード

| カテゴリ | スコア | 検出問題数 | 最高重要度 |
|---------|--------|-----------|-----------|
| パフォーマンス (PERF) | Mobile: 38 / Desktop: 64 | 20+ | **CRITICAL** |
| メタ情報 (META) | — | 50 | HIGH |
| サイト構造 (STRC) | — | 93 | MEDIUM |
| 構造化データ (SCHM) | エラー0 / 警告42 | 42 | MEDIUM |
| インデックス (INDX) | — | 15 | HIGH |
| コンテンツ (CONT) | — | 70 | HIGH |
| リダイレクト (RDIR) | — | 11 | HIGH |
| モバイル (MOBL) | — | 20+ | **CRITICAL** |

---

## 問題サマリー（重要度別）

| 重要度 | 件数 | SLA |
|--------|------|-----|
| **CRITICAL** | 16 | 即日〜1週間 |
| **HIGH** | 34 | 1週間 |
| **MEDIUM** | 233 | 1ヶ月 |
| **LOW** | 6 | バックログ |

---

## CRITICAL 問題（即日〜1週間対応）

### 1. モバイル全ページのパフォーマンス壊滅 [PERF/MOBL]

| ページ | PSI (Mobile) | LCP | TBT | CLS |
|--------|-------------|-----|-----|-----|
| / (トップ) | **16** | 9.4s | 3,480ms | 0.282 |
| /campus/ | **33** | 30.2s | 5,450ms | 0.000 |
| /campus/37260〜37264 | **34〜46** | 31.0〜31.7s | 1,065〜2,458ms | 0.001 |
| /about/ | **43** | 9.18s | 1,510ms | 0.000 |
| /service/ | **43** | 6.01s | 2,731ms | 0.000 |
| /lp_entry/ | **54** | 7.09s | 793ms | 0.000 |

**根本原因**: サーバー応答時間（TTFB）の遅延が全ページに共通。Lighthouse の「Reduce initial server response time」が20/20ページで検出。平均1,271msの改善余地。

**対応手順**:
1. サーバーサイドキャッシュ（Redis / Memcached + WP Object Cache）の導入
2. CDN（CloudFlare等）によるTTFB削減
3. WordPress データベースクエリの最適化（特にcampusページの大量記事取得クエリ）
4. PHP OPcache の有効化確認

### 2. キャンパスページのLCP 30秒超 [PERF]

`/campus/` 一覧ページとキャンパス個別記事のモバイルLCPが30〜31秒台。

**推定原因**:
- `Avoid multiple page redirects` がcampus系10ページで検出（合計5,857ms削減余地）
- サーバーサイドの重いDBクエリ（大量の学校・記事データ取得）
- レンダリングブロックリソース（CSS/JS）

**対応手順**:
1. campusページのリダイレクトチェーンを特定・排除
2. campus記事テンプレートの重いクエリをプロファイリング → キャッシュ化
3. Above-the-fold のCSSインライン化、残りを非同期読み込み

### 3. トップページ CLS 0.282（POOR）[MOBL]

デスクトップ0.221 / モバイル0.282 で、サイト内唯一のCLS問題ページ。

**対応手順**:
1. バナー・ヒーロー画像に明示的な width/height 属性を設定
2. 遅延読み込みされるコンテンツ（スライダー等）にプレースホルダースペースを確保
3. フォント読み込みによるレイアウトシフトを `font-display: swap` + preload で軽減

---

## HIGH 問題（1週間以内）

### 4. noindex設定された15ページの確認 [INDX]

以下のページにnoindexが設定されており、Googleからインデックスされていない:

| ページ | 対応方針 |
|--------|---------|
| `/news` | **要確認** — ニュース一覧はインデックスすべきか |
| `/online` | **要確認** — オンラインサービスページ |
| `/faqs/faq1〜6` | **修正推奨** — FAQ個別ページはFAQキーワードで流入獲得可能 |
| `/gallerys/item_house/ticket/adviser` | **要確認** — ギャラリー子ページ |
| `/business`, `/biz` | 意図的noindexの可能性（法人向けLP） |
| `/story/page/2` | ページネーション2ページ目 — noindexは適切 |
| `/news/20190925` | 古いニュース — noindexでも可 |

### 5. canonical不整合 11件 [META/RDIR]

旧URL構造の名残りで、存在しないパスをcanonicalに指定:

| 現URL | canonical先（存在しない） |
|-------|------------------------|
| `/faqs/faq1〜6` | `/faq/faqs/faq1/` 等 |
| `/gallerys/item_house/ticket/adviser` | `/gallery/gallerys/item_*` 等 |
| `/news/20190925` | `/news/` |
| `/story/page/2` | `/story/` |

**対応**: Yoast SEOの各ページ設定からcanonicalを自己参照URLに修正。

### 6. 重複タイトル 8件 [CONT]

| 重複タイトル | ページ1 | ページ2 |
|------------|---------|---------|
| ニュース \| ジョーカツ | `/news` | `/news/20190925` |
| ジョーカツハウス \| ジョーカツ | `/house` | `/gallerys/item_house` |
| ジョーカツ交通費 \| ジョーカツ | `/ticket` | `/gallerys/item_ticket` |
| ジョーカツイベント \| ジョーカツ | `/event` | `/faqs/faq4` |

### 7. GSCサイトマップ未ダウンロード問題 [INDX]

- `https://jo-katsu.com/campus/sitemap.xml` が2024年7月提出以降、**一度もGoogleにダウンロードされていない**
- サイトマップURLがGoogleに「unknown」と認識されている

**対応手順**:
1. `https://jo-katsu.com/campus/sitemap.xml` にブラウザでアクセスし存在確認
2. 存在しない場合、WordPress（Yoast SEO）でサイトマップを再生成
3. GSCで既存サイトマップを削除 → 再提出

---

## MEDIUM 問題（1ヶ月以内）

### 8. H1タグ重複 92ページ [STRC]

ほぼ全ページでH1が2個存在。WordPressテーマ側の構造的問題。

**対応**: テーマテンプレート（`header.php` または各テンプレート）を修正し、ページタイトルの二重H1を解消。トップページ・`/campus/`・`/campus_list` はH1が存在しないため追加。

### 9. メタディスクリプション未設定 35ページ [META]

特に重要なページ:
- `/campus_list`（内部被リンク数1位: 748本）
- `/es-info`（ESコンテンツ群）
- `/news`、`/contact`、`/company`

### 10. 画像alt属性欠落 62ページ [CONT]

サイト全体で画像の20〜57%にalt未設定。トップページは28枚中16枚が未設定（57%）。

### 11. Article/BlogPostingスキーマ未実装 [SCHM]

`/campus/` 配下の記事ページに `Article` / `BlogPosting` スキーマが一切ない。記事リッチリザルト（著者情報・更新日表示）が獲得できていない。

**対応**: Yoast SEO / Rank Math のArticleスキーマ出力設定を有効化。または `functions.php` でカスタム投稿タイプ「campus」に対してArticleスキーマを自動出力。

### 12. Organizationスキーマの推奨フィールド欠落 [SCHM]

全ページ共通で `logo`・`contactPoint`・`address` が未設定。

```json
{
  "logo": {
    "@type": "ImageObject",
    "url": "https://jo-katsu.com/path/to/logo.png",
    "width": 512, "height": 512
  },
  "contactPoint": {
    "@type": "ContactPoint",
    "contactType": "customer service",
    "availableLanguage": "Japanese"
  },
  "address": {
    "@type": "PostalAddress",
    "addressLocality": "東京都",
    "addressCountry": "JP"
  }
}
```

### 13. 未使用CSS/JSの削減 [PERF]

- Reduce unused CSS: 16ページで検出（合計4,080ms削減余地）
- Reduce unused JavaScript: 13ページで検出（合計1,970ms削減余地）
- Minify CSS: 13ページで検出（合計1,630ms削減余地）

---

## LOW 問題（バックログ）

### 14. `/policy` の内部リンク過多 [STRC]

プライバシーポリシーが内部被リンク4位（155本）。フッター共通リンクが原因。`rel="nofollow"` 付与またはnoindex検討。

### 15. BreadcrumbList の非標準プロパティ [SCHM]

`nextItem` / `previousItem` はschema.org非標準。削除推奨だがSEOインパクトは軽微。

---

## GSCパフォーマンスデータ

| 指標 | 直近28日間 |
|------|-----------|
| 総クリック数 | **94,251** |
| 総インプレッション数 | **5,164,857** |
| 平均CTR | **1.82%** |
| 平均掲載順位 | **7.6位** |

- 2月上旬は好調（4,000〜5,200クリック/日、CTR 2.0〜2.2%）
- 2月中旬以降30〜40%のトラフィック減少（2,400〜3,500クリック/日、CTR 1.55〜1.88%）
- 就活シーズンのピーク過ぎによる季節変動の可能性

---

## 修正ロードマップ

### Week 1: 緊急対応（CRITICAL + HIGH）
- [ ] サーバーサイドキャッシュ（Object Cache）の導入検討
- [ ] campusページのリダイレクトチェーン排除
- [ ] トップページのCLS修正（画像サイズ指定）
- [ ] GSCサイトマップの再提出
- [ ] noindex 15ページの意図確認と修正
- [ ] canonical不整合 11件の修正

### Week 2-4: 重要対応（MEDIUM）
- [ ] H1タグ重複のテーマテンプレート修正
- [ ] メタディスクリプション 35ページの設定
- [ ] Article/BlogPostingスキーマの実装
- [ ] Organizationスキーマのフィールド追加
- [ ] 重複タイトル 8件の修正
- [ ] 未使用CSS/JSの削減

### Month 2+: 継続改善（LOW + 基盤強化）
- [ ] 画像alt属性の全ページ整備
- [ ] CDN導入によるTTFB根本改善
- [ ] モバイルTBT改善（JS分割・遅延実行）
- [ ] 内部リンク構造の最適化
- [ ] 月次定期監査の設定

---

## 個別レポートへのリンク

- Lighthouse結果: `reports/jo-katsu.com_*_mobile/desktop_*.json`（20ファイル）
- 構造化データ: `reports/structured_data_report.json`
- クロール: `reports/jo-katsu_com_crawl_20260227_170416.json`
- 対象URL一覧: `reports/naimono_target_urls.txt`

---

## 次のアクション

1. **CRITICAL問題の即座の修正**: サーバーキャッシュ導入が最優先（全ページに影響）
2. **GSCサイトマップ再提出**: `https://jo-katsu.com/campus/sitemap.xml` の存在確認後、再提出
3. **noindex / canonical修正**: Yoast SEO管理画面から一括修正可能
4. **修正後の再監査（1週間後推奨）**: `/wp-audit-lighthouse naimono` で効果測定
5. **月次定期監査の設定**: 毎月第1月曜日に `/wp-audit-full naimono` を実行
