/**
 * MonitorGA4.gs — GA4 全ページ一括取得 + 変動検出
 *
 * pagePath フィルタなしで全ページデータを取得し、
 * 週次の変動が大きいページを自動検出する。
 */

/**
 * GA4 から全ページのメトリクスを一括取得（Organic Search のみ）
 *
 * @param {Date} startDate - 開始日
 * @param {Date} endDate - 終了日
 * @return {Object} ページパスをキーとしたメトリクス辞書
 *   { '/campus/26469': { sessions, pageViews, engagementRate, ... }, ... }
 */
function fetchGA4BulkData(startDate, endDate) {
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
        { name: 'engagementRate' },
        { name: 'bounceRate' },
        { name: 'averageSessionDuration' },
        { name: 'keyEvents' }
      ],
      dimensionFilter: {
        filter: {
          fieldName: 'sessionDefaultChannelGroup',
          stringFilter: {
            matchType: 'EXACT',
            value: 'Organic Search'
          }
        }
      },
      limit: 10000,
      orderBys: [{
        metric: { metricName: 'sessions' },
        desc: true
      }]
    };

    const response = AnalyticsData.Properties.runReport(request, `properties/${propertyId}`);

    if (!response.rows || response.rows.length === 0) {
      Logger.log(`[MonitorGA4] データなし: ${formatDateYYYYMMDD(startDate)} - ${formatDateYYYYMMDD(endDate)}`);
      return {};
    }

    const result = {};
    response.rows.forEach(row => {
      const pagePath = row.dimensionValues[0].value;
      const metrics = row.metricValues;

      result[pagePath] = {
        sessions: parseFloat(metrics[0].value) || 0,
        pageViews: parseFloat(metrics[1].value) || 0,
        engagementRate: parseFloat(metrics[2].value) || 0,
        bounceRate: parseFloat(metrics[3].value) || 0,
        avgSessionDuration: parseFloat(metrics[4].value) || 0,
        keyEvents: parseFloat(metrics[5].value) || 0
      };
    });

    Logger.log(`[MonitorGA4] ${Object.keys(result).length} ページ取得 (${formatDateYYYYMMDD(startDate)} - ${formatDateYYYYMMDD(endDate)})`);
    return result;

  } catch (error) {
    Logger.log(`[MonitorGA4 Error] ${error.message}`);
    throw error;
  }
}

/**
 * 2期間のバルクデータを比較して変動が大きいページを検出
 *
 * @param {Object} currentWeekData - 今週の全ページデータ
 * @param {Object} previousWeekData - 先週の全ページデータ
 * @return {Array<Object>} フラグ付きページ配列（セッション変動の絶対値降順）
 */
function detectSignificantChanges(currentWeekData, previousWeekData) {
  const threshold = getMonitorConfig('SESSION_CHANGE_THRESHOLD');
  const minSessions = getMonitorConfig('MIN_SESSIONS');
  const maxPages = getMonitorConfig('MAX_FLAGGED_PAGES');

  const flagged = [];

  // 全ページパスを統合
  const allPaths = new Set([
    ...Object.keys(currentWeekData),
    ...Object.keys(previousWeekData)
  ]);

  allPaths.forEach(pagePath => {
    const current = currentWeekData[pagePath] || { sessions: 0, pageViews: 0, engagementRate: 0, bounceRate: 0, avgSessionDuration: 0, keyEvents: 0 };
    const previous = previousWeekData[pagePath] || { sessions: 0, pageViews: 0, engagementRate: 0, bounceRate: 0, avgSessionDuration: 0, keyEvents: 0 };

    // 最低セッション数チェック（両方の期間でチェック）
    if (current.sessions < minSessions && previous.sessions < minSessions) {
      return;
    }

    // セッション変化率を計算
    let changeRate;
    if (previous.sessions === 0) {
      changeRate = current.sessions >= minSessions ? 1.0 : 0;  // 新規ページで十分なセッションがあれば +100%
    } else {
      changeRate = (current.sessions - previous.sessions) / previous.sessions;
    }

    // しきい値チェック
    if (Math.abs(changeRate) >= threshold) {
      flagged.push({
        pagePath: pagePath,
        currentSessions: current.sessions,
        previousSessions: previous.sessions,
        sessionChangeRate: changeRate,
        currentGA4: current,
        previousGA4: previous,
        flagReason: `セッション ${changeRate >= 0 ? '+' : ''}${(changeRate * 100).toFixed(1)}%`
      });
    }
  });

  // セッション変動の絶対値が大きい順にソート
  flagged.sort((a, b) => Math.abs(b.sessionChangeRate) - Math.abs(a.sessionChangeRate));

  // 上限数に絞る
  const result = flagged.slice(0, maxPages);

  Logger.log(`[MonitorGA4] 変動検出: ${flagged.length} ページ中 ${result.length} ページをフラグ`);
  return result;
}

/**
 * モニタリング用の日付範囲を計算
 *
 * GSC データ遅延（3日）を考慮した日付計算:
 *   今週: [today - GSC_DELAY - 7, today - GSC_DELAY - 1]
 *   先週: [today - GSC_DELAY - 14, today - GSC_DELAY - 8]
 *
 * @return {Object} { currentStart, currentEnd, previousStart, previousEnd }
 */
function calculateMonitoringDates() {
  const today = new Date();
  const delay = getMonitorConfig('GSC_DELAY_DAYS');
  const weekDays = getMonitorConfig('CURRENT_WEEK_DAYS');

  const currentEnd = addDays(today, -(delay + 1));
  const currentStart = addDays(currentEnd, -(weekDays - 1));
  const previousEnd = addDays(currentStart, -1);
  const previousStart = addDays(previousEnd, -(weekDays - 1));

  return { currentStart, currentEnd, previousStart, previousEnd };
}
