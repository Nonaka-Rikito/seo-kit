# GAS コードバグ修正 引き継ぎ依頼書

## 概要

`2_クライアントデータ/naimono/analysis/gas/` にある Google Apps Script（7ファイル + appsscript.json）のコードレビューが完了済み。
**8件のバグ/問題点** が発見されており、すべて未修正。修正を実施してほしい。

---

## 対象ファイル一覧

| ファイル | パス |
|---------|------|
| Config.gs | `C:\Users\rikit\Projects\2_クライアントデータ\naimono\analysis\gas\Config.gs` |
| Main.gs | `C:\Users\rikit\Projects\2_クライアントデータ\naimono\analysis\gas\Main.gs` |
| GA4.gs | `C:\Users\rikit\Projects\2_クライアントデータ\naimono\analysis\gas\GA4.gs` |
| GSC.gs | `C:\Users\rikit\Projects\2_クライアントデータ\naimono\analysis\gas\GSC.gs` |
| Sheet.gs | `C:\Users\rikit\Projects\2_クライアントデータ\naimono\analysis\gas\Sheet.gs` |
| Slack.gs | `C:\Users\rikit\Projects\2_クライアントデータ\naimono\analysis\gas\Slack.gs` |
| Utils.gs | `C:\Users\rikit\Projects\2_クライアントデータ\naimono\analysis\gas\Utils.gs` |
| appsscript.json | `C:\Users\rikit\Projects\2_クライアントデータ\naimono\analysis\gas\appsscript.json` |

---

## 修正すべきバグ一覧（8件）

### [致命的] Bug 1: Sheet.gs — scrollData の null 参照

- **場所**: Sheet.gs 155〜158行目（`writeDataRecord()` 関数内）
- **現状**: `scrollData.scroll_25 || 0` のように直接アクセスしている
- **原因**: Main.gs の 61行目と 169行目で `scrollData: null` を渡しているため、`null.scroll_25` で **TypeError クラッシュ**
- **修正方法**: オプショナルチェイニングを使う

```javascript
// 修正前（155〜158行目）
scrollData.scroll_25 || 0,
scrollData.scroll_50 || 0,
scrollData.scroll_75 || 0,
scrollData.scroll_90 || 0,

// 修正後
(scrollData && scrollData.scroll_25) || 0,
(scrollData && scrollData.scroll_50) || 0,
(scrollData && scrollData.scroll_75) || 0,
(scrollData && scrollData.scroll_90) || 0,
```

> ※ GAS の V8 ランタイムは `?.` をサポートしているので `scrollData?.scroll_25 || 0` でもOK

---

### [致命的] Bug 2: Slack.gs — scroll データの null 参照

- **場所**: Slack.gs 125〜128行目（`sendSlackReport()` 関数内）
- **現状**: `before.scroll.scroll_90` と `after.scroll.scroll_90` にアクセスしている
- **原因**: Main.gs で `scroll: null` をセットしており（184行目）、`null.scroll_90` で **TypeError クラッシュ**
- **修正方法**: スクロール関連のフィールドをレポートから削除する（GTM未設定のため意味のあるデータが存在しない）

```javascript
// 修正前（Slack.gs 111〜128行目の fields 配列内の4番目の要素）
{
  type: 'mrkdwn',
  text: `*スクロール90%到達*\n${before.scroll.scroll_90} → ${after.scroll.scroll_90} (${changes.scroll_90})`
}

// 修正後: この要素を丸ごと削除し、代わりにCV数を表示
{
  type: 'mrkdwn',
  text: `*CV数*\n${before.ga4.conversions} → ${after.ga4.conversions} (${changes.conversions})`
}
```

---

### [重要] Bug 3: GA4.gs — `conversions` メトリクス廃止

- **場所**: GA4.gs 36行目
- **現状**: `{ name: 'conversions' }` を指定
- **問題**: GA4 Data API で `conversions` は **2024年5月6日に廃止**されており、`keyEvents` に移行済み。現在 API を叩くとエラーまたは空データになる可能性がある
- **修正方法**: GA4.gs のメトリクス名と戻り値のプロパティ名を変更

```javascript
// GA4.gs 36行目
// 修正前
{ name: 'conversions' }
// 修正後
{ name: 'keyEvents' }

// GA4.gs 81行目
// 修正前
conversions: parseFloat(metrics[6].value) || 0,
// 修正後
keyEvents: parseFloat(metrics[6].value) || 0,
```

**連鎖修正が必要なファイル:**

1. **Config.gs 50行目**: `conversions: 0.20` → `keyEvents: 0.20`
2. **Utils.gs 79行目**: `conversions: calculateChange(before.ga4.conversions, after.ga4.conversions)` → `keyEvents: calculateChange(before.ga4.keyEvents, after.ga4.keyEvents)`
3. **Utils.gs 124行目**: `conversions: safeChangeRate(before.ga4.conversions, after.ga4.conversions)` → `keyEvents: safeChangeRate(before.ga4.keyEvents, after.ga4.keyEvents)`
4. **Sheet.gs 74行目ヘッダー**: `'CV数'` はそのまま（表示名なので変更不要）
5. **Sheet.gs 154行目**: `ga4Data.conversions || 0` → `ga4Data.keyEvents || 0`
6. **Sheet.gs 201行目**: `conversions: row[11]` → `keyEvents: row[11]`
7. **Slack.gs**: Bug 2 の修正で `before.ga4.conversions` → `before.ga4.keyEvents` に合わせる

---

### [重要] Bug 4: GSC.gs — 画像検索フィルタの誤り

- **場所**: GSC.gs 67〜110行目（`fetchGSCImageSearchData()` 関数）
- **現状**: `dimensionFilterGroups` 内で `searchAppearance` ディメンションを `'IMAGE'` でフィルタ
- **問題**: `searchAppearance` は検索結果の見た目（リッチリザルトなど）であり、画像検索タイプではない。画像検索をフィルタするには `type: 'image'` をリクエストの **トップレベルパラメータ** として指定する必要がある
- **修正方法**:

```javascript
// 修正後の fetchGSCImageSearchData
function fetchGSCImageSearchData(pageUrl, startDate, endDate) {
  const siteUrl = getConfig('GSC_SITE_URL');

  try {
    const request = {
      startDate: formatDateYYYYMMDD(startDate),
      endDate: formatDateYYYYMMDD(endDate),
      dimensions: ['page'],
      type: 'image',  // ← トップレベルに type パラメータを追加
      dimensionFilterGroups: [{
        filters: [
          {
            dimension: 'page',
            operator: 'equals',
            expression: pageUrl
          }
          // searchAppearance フィルタは削除
        ]
      }],
      rowLimit: 1
    };

    const response = Webmasters.Searchanalytics.query(request, siteUrl);

    if (!response.rows || response.rows.length === 0) {
      return { imageClicks: 0, imageImpressions: 0, noData: true };
    }

    const row = response.rows[0];
    return {
      imageClicks: row.clicks || 0,
      imageImpressions: row.impressions || 0,
      noData: false
    };

  } catch (error) {
    Logger.log(`[GSC Image Search Error] ${error.message}`);
    return { imageClicks: 0, imageImpressions: 0, noData: true, error: error.message };
  }
}
```

---

### [重要] Bug 5: Config.gs / Utils.gs — メトリクス名の不一致

- **場所**: Config.gs 45行目、Utils.gs 121行目
- **現状**: Config.gs の `METRIC_WEIGHTS` で `avgEngagementTime` と定義しているが、Utils.gs の `determineVerdict()` 関数（121行目）では `avgEngagementTime: safeChangeRate(before.ga4.avgSessionDuration, ...)` と、GA4から取得する `avgSessionDuration` を参照
- **問題**: 名前は不一致だが偶然動く（Config のキー名と Utils の変数名が一致しているため）。ただし紛らわしく、将来のメンテで事故の原因になる
- **修正方法**: Config.gs のキー名を GA4 で実際に使っている名前に統一

```javascript
// Config.gs 45行目
// 修正前
avgEngagementTime: 0.10,
// 修正後
avgSessionDuration: 0.10,
```

```javascript
// Utils.gs 121行目
// 修正前
avgEngagementTime: safeChangeRate(before.ga4.avgSessionDuration, after.ga4.avgSessionDuration),
// 修正後
avgSessionDuration: safeChangeRate(before.ga4.avgSessionDuration, after.ga4.avgSessionDuration),
```

---

### [軽微] Bug 6: Main.gs — テスト用 URL がダミーのまま

- **場所**: Main.gs 241行目
- **現状**: `'https://example.com/campus/26469'`
- **修正方法**: 実際のサイト URL に変更するか、コメントで明示的に注記を追加

```javascript
// 修正後
'https://jo-katsu.com/campus/XXXXX'  // ← テスト時に実際の記事URLに変更すること
```

---

### [軽微] Bug 7: Utils.gs — og:image の正規表現が不完全

- **場所**: Utils.gs 182行目（`scrapePageBanner()` 関数）
- **現状**: `/<meta\s+property=["']og:image["']\s+content=["']([^"']+)["']/i`
- **問題**: `content` が `property` より先に来る HTML（`<meta content="..." property="og:image">`）にマッチしない
- **修正方法**:

```javascript
// 修正後（両方の順序に対応）
const ogImageMatch = html.match(/<meta\s+(?:property=["']og:image["']\s+content=["']([^"']+)["']|content=["']([^"']+)["']\s+property=["']og:image["'])/i);
if (ogImageMatch) {
  const imageUrl = ogImageMatch[1] || ogImageMatch[2];
  Logger.log(`[Scrape] OG画像取得: ${imageUrl}`);
  return imageUrl;
}
```

---

### [軽微] Bug 8: Config.gs — getConfig() がオブジェクト型を扱えない

- **場所**: Config.gs 69〜72行目
- **現状**: `PropertiesService.getScriptProperties().getProperty(key)` は文字列しか返さないが、`CONFIG` にはオブジェクト（`METRIC_WEIGHTS`）や配列（`MONITORING_METRICS`）が含まれる
- **問題**: ScriptProperties に `METRIC_WEIGHTS` を JSON 文字列で保存した場合、`getConfig()` は文字列を返してしまい、オブジェクトとして使えない
- **修正方法**:

```javascript
// 修正後
function getConfig(key) {
  const prop = PropertiesService.getScriptProperties().getProperty(key);
  if (prop) {
    try {
      return JSON.parse(prop);
    } catch (e) {
      return prop;  // JSON でなければ文字列のまま返す
    }
  }
  return CONFIG[key];
}
```

---

## 修正の優先度

| 優先度 | Bug | 修正しないとどうなるか |
|--------|-----|----------------------|
| 致命的 | Bug 1 (Sheet.gs null) | **システムがクラッシュして全機能停止** |
| 致命的 | Bug 2 (Slack.gs null) | **レポート送信時にクラッシュ** |
| 重要 | Bug 3 (conversions廃止) | **GA4からCV数が取れない（空データ or エラー）** |
| 重要 | Bug 4 (GSC画像検索) | **画像検索データが誤り（常に0件になる可能性）** |
| 重要 | Bug 5 (メトリクス名不一致) | 現状は偶然動くが、将来の変更で事故リスク |
| 軽微 | Bug 6 (テストURL) | テスト実行時に意味のないデータが返る |
| 軽微 | Bug 7 (og:image正規表現) | 一部サイトでバナー画像が取得できない |
| 軽微 | Bug 8 (getConfig型) | ScriptPropertiesに複雑な型を入れた時に壊れる |

---

## 注意事項

- **GAS の V8 ランタイム** を使用しているため、オプショナルチェイニング (`?.`) が使用可能
- Bug 3 の `conversions` → `keyEvents` は **連鎖的に複数ファイルに影響** するので漏れなく修正すること
- 修正後、ファイル全体の整合性を確認してほしい（特に `conversions` / `keyEvents` の統一）
- Config.gs のプレースホルダー値（`XXXXXXXXX`）はまだ本番値が入っていないので、そのままでOK

---

## 参考資料

- 総合レビュー文書: `C:\Users\rikit\Projects\GA4-GSC-measurement-system-complete-summary.md`
- Agent Teams 統合レビュー: `C:\Users\rikit\Projects\2_クライアントデータ\naimono\analysis\integration-review-final-report.md`
