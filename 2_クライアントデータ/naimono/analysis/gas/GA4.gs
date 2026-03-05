/**
 * GA4.gs — GA4 Data API 連携
 *
 * GA4 Data API (Advanced Service) を使ってデータを取得する。
 * Advanced Service の有効化: GAS エディタ「サービス」→「Google Analytics Data API」を追加
 */

/**
 * GA4 からページ単位のメトリクスを取得
 *
 * @param {string} pagePath - ページパス（例: /campus/26469）
 * @param {Date} startDate - 開始日
 * @param {Date} endDate - 終了日
 * @param {string} channelGroup - チャネルグループ（デフォルト: "Organic Search"）
 * @return {Object} メトリクスデータ、またはデータなしの場合は {noData: true}
 */
function fetchGA4Data(pagePath, startDate, endDate, channelGroup = 'Organic Search') {
  const propertyId = getConfig('GA4_PROPERTY_ID');

  try {
    const request = {
      dateRanges: [{
        startDate: formatDateYYYYMMDD(startDate),
        endDate: formatDateYYYYMMDD(endDate)
      }],
      dimensions: [
        { name: 'pagePath' }
      ],
      metrics: [
        { name: 'sessions' },
        { name: 'screenPageViews' },
        { name: 'engagedSessions' },
        { name: 'engagementRate' },
        { name: 'averageSessionDuration' },
        { name: 'bounceRate' },
        { name: 'keyEvents' }
      ],
      dimensionFilter: {
        andGroup: {
          expressions: [
            {
              filter: {
                fieldName: 'pagePath',
                stringFilter: {
                  matchType: 'EXACT',
                  value: pagePath
                }
              }
            },
            {
              filter: {
                fieldName: 'sessionDefaultChannelGroup',
                stringFilter: {
                  matchType: 'EXACT',
                  value: channelGroup
                }
              }
            }
          ]
        }
      }
    };

    const response = AnalyticsData.Properties.runReport(request, `properties/${propertyId}`);

    if (!response.rows || response.rows.length === 0) {
      Logger.log(`[GA4] データなし: ${pagePath} (${formatDateYYYYMMDD(startDate)} - ${formatDateYYYYMMDD(endDate)})`);
      return { noData: true };
    }

    const row = response.rows[0];
    const metrics = row.metricValues;

    return {
      sessions: parseFloat(metrics[0].value) || 0,
      pageViews: parseFloat(metrics[1].value) || 0,
      engagedSessions: parseFloat(metrics[2].value) || 0,
      engagementRate: parseFloat(metrics[3].value) || 0,
      avgSessionDuration: parseFloat(metrics[4].value) || 0,
      bounceRate: parseFloat(metrics[5].value) || 0,
      keyEvents: parseFloat(metrics[6].value) || 0,
      noData: false
    };

  } catch (error) {
    Logger.log(`[GA4 Error] ${error.message}`);
    return { noData: true, error: error.message };
  }
}

/**
 * GA4 からスクロール深度データを取得
 *
 * GTM でカスタムイベント `scroll_depth` を送信している前提。
 * イベントパラメータ `scroll_percentage` に 25/50/75/90 が入っている。
 *
 * @param {string} pagePath - ページパス
 * @param {Date} startDate - 開始日
 * @param {Date} endDate - 終了日
 * @return {Object} スクロール深度別のイベント数
 */
function fetchGA4ScrollDepth(pagePath, startDate, endDate) {
  const propertyId = getConfig('GA4_PROPERTY_ID');

  try {
    const request = {
      dateRanges: [{
        startDate: formatDateYYYYMMDD(startDate),
        endDate: formatDateYYYYMMDD(endDate)
      }],
      dimensions: [
        { name: 'pagePath' },
        { name: 'customEvent:scroll_percentage' }  // GTM から送られるカスタムパラメータ
      ],
      metrics: [
        { name: 'eventCount' }
      ],
      dimensionFilter: {
        andGroup: {
          expressions: [
            {
              filter: {
                fieldName: 'pagePath',
                stringFilter: { matchType: 'EXACT', value: pagePath }
              }
            },
            {
              filter: {
                fieldName: 'eventName',
                stringFilter: { matchType: 'EXACT', value: 'scroll_depth' }
              }
            }
          ]
        }
      }
    };

    const response = AnalyticsData.Properties.runReport(request, `properties/${propertyId}`);

    if (!response.rows || response.rows.length === 0) {
      return { noData: true };
    }

    // スクロール深度別に集計
    const scrollData = {
      scroll_25: 0,
      scroll_50: 0,
      scroll_75: 0,
      scroll_90: 0,
      noData: false
    };

    response.rows.forEach(row => {
      const percentage = row.dimensionValues[1].value;
      const count = parseInt(row.metricValues[0].value);

      if (percentage === '25') scrollData.scroll_25 = count;
      if (percentage === '50') scrollData.scroll_50 = count;
      if (percentage === '75') scrollData.scroll_75 = count;
      if (percentage === '90') scrollData.scroll_90 = count;
    });

    return scrollData;

  } catch (error) {
    Logger.log(`[GA4 Scroll Error] ${error.message}`);
    return { noData: true, error: error.message };
  }
}

/**
 * ページURLからパスを抽出
 * 例: https://example.com/campus/26469?utm=xxx → /campus/26469
 */
function extractPagePath(url) {
  try {
    const urlObj = new URL(url);
    return urlObj.pathname;
  } catch (e) {
    // URL として不正な場合はそのまま返す（すでにパス形式かもしれない）
    return url;
  }
}
