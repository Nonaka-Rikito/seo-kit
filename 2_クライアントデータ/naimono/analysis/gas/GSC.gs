/**
 * GSC.gs — Google Search Console API 連携
 *
 * Search Console API (Advanced Service) を使ってデータを取得する。
 * Advanced Service の有効化: GAS エディタ「サービス」→「Google Search Console API」を追加
 */

/**
 * GSC からページ単位の検索パフォーマンスデータを取得
 *
 * @param {string} pageUrl - 完全なページURL（例: https://example.com/campus/26469）
 * @param {Date} startDate - 開始日
 * @param {Date} endDate - 終了日
 * @return {Object} GSC データ、またはデータなしの場合は {noData: true}
 */
function fetchGSCData(pageUrl, startDate, endDate) {
  const siteUrl = getConfig('GSC_SITE_URL');

  try {
    const request = {
      startDate: formatDateYYYYMMDD(startDate),
      endDate: formatDateYYYYMMDD(endDate),
      dimensions: ['page'],
      dimensionFilterGroups: [{
        filters: [{
          dimension: 'page',
          operator: 'equals',
          expression: pageUrl
        }]
      }],
      rowLimit: 1
    };

    const response = Webmasters.Searchanalytics.query(request, siteUrl);

    if (!response.rows || response.rows.length === 0) {
      Logger.log(`[GSC] データなし: ${pageUrl} (${formatDateYYYYMMDD(startDate)} - ${formatDateYYYYMMDD(endDate)})`);
      return { noData: true };
    }

    const row = response.rows[0];

    return {
      clicks: row.clicks || 0,
      impressions: row.impressions || 0,
      ctr: row.ctr || 0,
      position: row.position || 0,
      noData: false
    };

  } catch (error) {
    Logger.log(`[GSC Error] ${error.message}`);
    return { noData: true, error: error.message };
  }
}

/**
 * GSC から画像検索のデータを取得
 *
 * 画像検索経由の流入を計測する。
 *
 * @param {string} pageUrl - 完全なページURL
 * @param {Date} startDate - 開始日
 * @param {Date} endDate - 終了日
 * @return {Object} 画像検索のデータ
 */
function fetchGSCImageSearchData(pageUrl, startDate, endDate) {
  const siteUrl = getConfig('GSC_SITE_URL');

  try {
    const request = {
      startDate: formatDateYYYYMMDD(startDate),
      endDate: formatDateYYYYMMDD(endDate),
      dimensions: ['page'],
      type: 'image',  // 画像検索タイプをトップレベルで指定
      dimensionFilterGroups: [{
        filters: [{
          dimension: 'page',
          operator: 'equals',
          expression: pageUrl
        }]
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

/**
 * GSC からクエリ別のデータを取得（オプション・詳細分析用）
 *
 * 上位クエリの順位変動を確認したい場合に使う。
 *
 * @param {string} pageUrl - 完全なページURL
 * @param {Date} startDate - 開始日
 * @param {Date} endDate - 終了日
 * @param {number} limit - 取得件数（デフォルト: 10）
 * @return {Array} クエリ別データの配列
 */
function fetchGSCQueryData(pageUrl, startDate, endDate, limit = 10) {
  const siteUrl = getConfig('GSC_SITE_URL');

  try {
    const request = {
      startDate: formatDateYYYYMMDD(startDate),
      endDate: formatDateYYYYMMDD(endDate),
      dimensions: ['query'],
      dimensionFilterGroups: [{
        filters: [{
          dimension: 'page',
          operator: 'equals',
          expression: pageUrl
        }]
      }],
      rowLimit: limit
    };

    const response = Webmasters.Searchanalytics.query(request, siteUrl);

    if (!response.rows || response.rows.length === 0) {
      return [];
    }

    return response.rows.map(row => ({
      query: row.keys[0],
      clicks: row.clicks,
      impressions: row.impressions,
      ctr: row.ctr,
      position: row.position
    }));

  } catch (error) {
    Logger.log(`[GSC Query Error] ${error.message}`);
    return [];
  }
}
