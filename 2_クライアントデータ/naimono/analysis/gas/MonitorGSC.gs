/**
 * MonitorGSC.gs — フラグ付きページの GSC 詳細データ取得
 *
 * 既存の GSC.gs の関数（fetchGSCData, fetchGSCQueryData, fetchGSCImageSearchData）を
 * そのまま再利用し、フラグ付きページごとに詳細データを収集する。
 */

/**
 * フラグ付きページの GSC 詳細データを一括取得
 *
 * @param {Array<Object>} flaggedPages - Phase 1 で検出されたページ一覧
 * @param {Date} currentStart - 今週開始日
 * @param {Date} currentEnd - 今週終了日
 * @param {Date} previousStart - 先週開始日
 * @param {Date} previousEnd - 先週終了日
 * @return {Array<Object>} GSC データ付きのページ配列
 */
function fetchGSCDetailsForFlaggedPages(flaggedPages, currentStart, currentEnd, previousStart, previousEnd) {
  const siteUrl = getMonitorConfig('SITE_URL');
  const queryLimit = getMonitorConfig('GSC_QUERY_LIMIT');

  const result = [];

  flaggedPages.forEach((page, index) => {
    const fullUrl = siteUrl + page.pagePath;

    Logger.log(`[MonitorGSC] (${index + 1}/${flaggedPages.length}) ${page.pagePath}`);

    try {
      // GSC サマリー（今週 + 先週）
      const currentGSC = fetchGSCData(fullUrl, currentStart, currentEnd);
      const previousGSC = fetchGSCData(fullUrl, previousStart, previousEnd);

      // GSC クエリ別データ（今週 + 先週）
      const currentQueries = fetchGSCQueryData(fullUrl, currentStart, currentEnd, queryLimit);
      const previousQueries = fetchGSCQueryData(fullUrl, previousStart, previousEnd, queryLimit);

      // 画像検索データ（今週 + 先週）
      const currentImageSearch = fetchGSCImageSearchData(fullUrl, currentStart, currentEnd);
      const previousImageSearch = fetchGSCImageSearchData(fullUrl, previousStart, previousEnd);

      // クエリ変動を計算
      const queryChanges = compareQueryData(currentQueries, previousQueries);

      result.push({
        ...page,
        currentGSC: currentGSC.noData ? { clicks: 0, impressions: 0, ctr: 0, position: 0 } : currentGSC,
        previousGSC: previousGSC.noData ? { clicks: 0, impressions: 0, ctr: 0, position: 0 } : previousGSC,
        currentQueries: currentQueries,
        previousQueries: previousQueries,
        currentImageSearch: currentImageSearch,
        previousImageSearch: previousImageSearch,
        queryChanges: queryChanges
      });

    } catch (error) {
      Logger.log(`[MonitorGSC Error] ${page.pagePath}: ${error.message}`);
      // エラーが出たページもスキップせず、データなしで追加
      result.push({
        ...page,
        currentGSC: { clicks: 0, impressions: 0, ctr: 0, position: 0 },
        previousGSC: { clicks: 0, impressions: 0, ctr: 0, position: 0 },
        currentQueries: [],
        previousQueries: [],
        currentImageSearch: { imageClicks: 0, imageImpressions: 0 },
        previousImageSearch: { imageClicks: 0, imageImpressions: 0 },
        queryChanges: [],
        gscError: error.message
      });
    }
  });

  Logger.log(`[MonitorGSC] GSC 詳細取得完了: ${result.length} ページ`);
  return result;
}

/**
 * 2期間のクエリデータを比較して変動を計算
 *
 * @param {Array} currentQueries - 今週のクエリデータ
 * @param {Array} previousQueries - 先週のクエリデータ
 * @return {Array} 変動情報付きクエリ配列（クリック変動の絶対値降順）
 */
function compareQueryData(currentQueries, previousQueries) {
  // 先週のクエリをマップ化
  const prevMap = {};
  previousQueries.forEach(q => {
    prevMap[q.query] = q;
  });

  // 今週のクエリをマップ化
  const currMap = {};
  currentQueries.forEach(q => {
    currMap[q.query] = q;
  });

  // 全クエリを統合
  const allQueries = new Set([
    ...currentQueries.map(q => q.query),
    ...previousQueries.map(q => q.query)
  ]);

  const changes = [];

  allQueries.forEach(query => {
    const curr = currMap[query] || { clicks: 0, impressions: 0, ctr: 0, position: 0 };
    const prev = prevMap[query] || { clicks: 0, impressions: 0, ctr: 0, position: 0 };

    changes.push({
      query: query,
      currentClicks: curr.clicks,
      previousClicks: prev.clicks,
      clicksDelta: curr.clicks - prev.clicks,
      currentPosition: curr.position,
      previousPosition: prev.position,
      positionDelta: curr.position - prev.position,
      currentCtr: curr.ctr,
      previousCtr: prev.ctr,
      isNew: !prevMap[query],
      isLost: !currMap[query]
    });
  });

  // クリック変動の絶対値が大きい順にソート
  changes.sort((a, b) => Math.abs(b.clicksDelta) - Math.abs(a.clicksDelta));

  return changes;
}
