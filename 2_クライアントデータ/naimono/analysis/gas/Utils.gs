/**
 * Utils.gs — ユーティリティ関数
 *
 * 日付操作、データ比較、フォーマット等の共通関数。
 */

/**
 * 日付を YYYY-MM-DD 形式にフォーマット
 */
function formatDateYYYYMMDD(date) {
  return Utilities.formatDate(date, 'Asia/Tokyo', 'yyyy-MM-dd');
}

/**
 * 日付を日本語形式にフォーマット
 */
function formatDateJP(date) {
  return Utilities.formatDate(date, 'Asia/Tokyo', 'yyyy年MM月dd日');
}

/**
 * 日付に日数を加算
 */
function addDays(date, days) {
  const result = new Date(date);
  result.setDate(result.getDate() + days);
  return result;
}

/**
 * 変化率を計算して文字列化
 *
 * @param {number} before - 前の値
 * @param {number} after - 後の値
 * @param {boolean} isPercentage - すでにパーセント値かどうか（デフォルト: false）
 * @param {boolean} reverseSign - 符号を逆転するか（掲載順位など、下がる方が良い指標用）
 * @return {string} 変化率の文字列（例: "+15.3%"）
 */
function calculateChange(before, after, isPercentage = false, reverseSign = false) {
  if (before === 0 && after === 0) {
    return '変化なし';
  }

  if (before === 0) {
    return 'N/A';
  }

  let change;
  if (isPercentage) {
    // すでにパーセント値の場合は差分をそのまま
    change = (after - before) * 100;
  } else {
    // 通常の値の場合は変化率を計算
    change = ((after - before) / before) * 100;
  }

  if (reverseSign) {
    change = -change;
  }

  const sign = change >= 0 ? '+' : '';
  return `${sign}${change.toFixed(1)}%`;
}

/**
 * Before/After データを比較して変化率を算出
 *
 * @param {Object} before - Before データ
 * @param {Object} after - After データ
 * @return {Object} 変化率データと判定
 */
function compareData(before, after) {
  const changes = {
    // GA4
    sessions: calculateChange(before.ga4.sessions, after.ga4.sessions),
    pageViews: calculateChange(before.ga4.pageViews, after.ga4.pageViews),
    engagementRate: calculateChange(before.ga4.engagementRate, after.ga4.engagementRate, true),
    bounceRate: calculateChange(before.ga4.bounceRate, after.ga4.bounceRate, true, true),  // 低い方が良い
    keyEvents: calculateChange(before.ga4.keyEvents, after.ga4.keyEvents),

    // Scroll 指標は除外（GTMで未設定のため）
    // scroll_25: calculateChange(before.scroll.scroll_25, after.scroll.scroll_25),
    // scroll_50: calculateChange(before.scroll.scroll_50, after.scroll.scroll_50),
    // scroll_75: calculateChange(before.scroll.scroll_75, after.scroll.scroll_75),
    // scroll_90: calculateChange(before.scroll.scroll_90, after.scroll.scroll_90),

    // GSC
    clicks: calculateChange(before.gsc.clicks, after.gsc.clicks),
    impressions: calculateChange(before.gsc.impressions, after.gsc.impressions),
    ctr: calculateChange(before.gsc.ctr, after.gsc.ctr, true),
    position: calculateChange(before.gsc.position, after.gsc.position, false, true)  // 順位は低い方が良い
  };

  // 総合判定
  const verdict = determineVerdict(before, after);

  return {
    before,
    after,
    changes,
    verdict
  };
}

/**
 * 総合判定を決定（METRIC_WEIGHTSに基づく重み付き判定）
 *
 * @param {Object} before
 * @param {Object} after
 * @return {string} "改善" / "悪化" / "変化なし"
 */
function determineVerdict(before, after) {
  const improvementThreshold = getConfig('VERDICT_IMPROVED_THRESHOLD');
  const degradedThreshold = getConfig('VERDICT_DEGRADED_THRESHOLD');
  const weights = getConfig('METRIC_WEIGHTS');

  // 各指標の変化率を計算
  const changes = {
    sessions: safeChangeRate(before.ga4.sessions, after.ga4.sessions),
    ctr: safeChangeRate(before.gsc.ctr, after.gsc.ctr),
    avgSessionDuration: safeChangeRate(before.ga4.avgSessionDuration, after.ga4.avgSessionDuration),
    engagementRate: (after.ga4.engagementRate - before.ga4.engagementRate),  // すでにパーセント値
    bounceRate: -(after.ga4.bounceRate - before.ga4.bounceRate),  // 直帰率は低い方が良いので符号反転
    keyEvents: safeChangeRate(before.ga4.keyEvents, after.ga4.keyEvents)
  };

  // 重み付きスコアを計算
  let weightedChange = 0;
  for (const [metric, weight] of Object.entries(weights)) {
    if (changes[metric] !== undefined && !isNaN(changes[metric])) {
      weightedChange += changes[metric] * weight;
    }
  }

  // 判定
  if (weightedChange >= improvementThreshold) {
    return '改善';
  } else if (weightedChange <= degradedThreshold) {
    return '悪化';
  } else {
    return '変化なし';
  }
}

/**
 * 安全な変化率計算（0除算を回避）
 *
 * @param {number} before - 前の値
 * @param {number} after - 後の値
 * @return {number} 変化率（小数）
 */
function safeChangeRate(before, after) {
  if (before === 0 && after === 0) {
    return 0;
  }
  if (before === 0) {
    return 1;  // 0から増加した場合は+100%とみなす
  }
  return (after - before) / before;
}

/**
 * ページ URL からバナー画像 URL を自動取得（スクレイピング）
 *
 * HTML を取得して og:image または最初の大きな画像を取得する。
 *
 * @param {string} pageUrl - ページURL
 * @return {string|null} 画像URL、取得できなければ null
 */
function scrapePageBanner(pageUrl) {
  try {
    const response = UrlFetchApp.fetch(pageUrl, { muteHttpExceptions: true });

    if (response.getResponseCode() !== 200) {
      Logger.log(`[Scrape] ページ取得失敗: ${pageUrl} (Status: ${response.getResponseCode()})`);
      return null;
    }

    const html = response.getContentText();

    // OGP画像を優先的に取得
    // og:image — property/content の順序両方に対応
    const ogImageMatch = html.match(/<meta\s+(?:property=["']og:image["']\s+content=["']([^"']+)["']|content=["']([^"']+)["']\s+property=["']og:image["'])/i);
    if (ogImageMatch) {
      const url = ogImageMatch[1] || ogImageMatch[2];
      Logger.log(`[Scrape] OG画像取得: ${url}`);
      return url;
    }

    // OGP画像がなければ最初の img タグを取得（簡易版）
    const imgMatch = html.match(/<img\s+[^>]*src=["']([^"']+)["']/i);
    if (imgMatch) {
      Logger.log(`[Scrape] img タグから取得: ${imgMatch[1]}`);
      return imgMatch[1];
    }

    Logger.log(`[Scrape] 画像が見つかりませんでした: ${pageUrl}`);
    return null;

  } catch (error) {
    Logger.log(`[Scrape Error] ${error.message}`);
    return null;
  }
}

/**
 * 現在の全トリガーを一覧表示（デバッグ用）
 */
function listAllTriggers() {
  const triggers = ScriptApp.getProjectTriggers();
  Logger.log(`=== 現在のトリガー一覧 (${triggers.length}件) ===`);

  triggers.forEach(trigger => {
    Logger.log(`ID: ${trigger.getUniqueId()}`);
    Logger.log(`  関数: ${trigger.getHandlerFunction()}`);
    Logger.log(`  種類: ${trigger.getEventType()}`);
  });
}

/**
 * すべてのトリガーを削除（初期化用・注意して使用）
 */
function deleteAllTriggers() {
  const triggers = ScriptApp.getProjectTriggers();
  triggers.forEach(trigger => {
    ScriptApp.deleteTrigger(trigger);
  });
  Logger.log(`${triggers.length}個のトリガーを削除しました`);
}
