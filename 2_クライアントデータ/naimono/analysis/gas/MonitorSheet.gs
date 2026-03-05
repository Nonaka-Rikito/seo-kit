/**
 * MonitorSheet.gs — モニタリング用スプレッドシート操作
 *
 * 2つの専用シートを管理:
 *   - 週次モニタリング: フラグ付きページのサマリー
 *   - フラグ付きページ: 変動が大きいページの GA4/GSC 詳細
 */

/**
 * 「週次モニタリング」シートを初期化
 */
function initMonitorWeeklySheet() {
  const sheet = getOrCreateSheet(MONITOR_CONFIG.SHEET_MONITOR_WEEKLY);

  if (sheet.getLastRow() === 0) {
    const headers = [
      '実行ID', '実行日時', 'ページパス',
      '今週セッション', '先週セッション', '変化率',
      'フラグ', 'フラグ理由'
    ];
    sheet.getRange(1, 1, 1, headers.length).setValues([headers]).setFontWeight('bold');
  }

  return sheet;
}

/**
 * 「フラグ付きページ」シートを初期化
 */
function initMonitorFlaggedSheet() {
  const sheet = getOrCreateSheet(MONITOR_CONFIG.SHEET_MONITOR_FLAGGED);

  if (sheet.getLastRow() === 0) {
    const headers = [
      '実行ID', 'ページパス',
      // 今週 GA4
      '今週セッション', '今週PV', '今週エンゲージメント率', '今週直帰率', '今週平均滞在時間', '今週CV数',
      // 先週 GA4
      '先週セッション', '先週PV', '先週エンゲージメント率', '先週直帰率', '先週平均滞在時間', '先週CV数',
      // 今週 GSC
      '今週クリック', '今週表示回数', '今週CTR', '今週平均順位',
      // 先週 GSC
      '先週クリック', '先週表示回数', '先週CTR', '先週平均順位',
      // 画像検索
      '今週画像クリック', '今週画像表示', '先週画像クリック', '先週画像表示',
      // クエリ変動
      'クエリ変動JSON'
    ];
    sheet.getRange(1, 1, 1, headers.length).setValues([headers]).setFontWeight('bold');
  }

  return sheet;
}

/**
 * 週次モニタリングデータを書き込み（Phase 1 完了時）
 */
function writeWeeklyMonitoringData(runId, runDate, flaggedPages, totalPages) {
  const sheet = initMonitorWeeklySheet();

  const rows = flaggedPages.map(page => [
    runId,
    runDate,
    page.pagePath,
    page.currentSessions,
    page.previousSessions,
    page.sessionChangeRate,
    true,
    page.flagReason
  ]);

  if (rows.length > 0) {
    const lastRow = sheet.getLastRow();
    sheet.getRange(lastRow + 1, 1, rows.length, rows[0].length).setValues(rows);
  }

  Logger.log(`[MonitorSheet] 週次モニタリング記録: ${rows.length} 件 (全 ${totalPages} ページ中)`);
}

/**
 * フラグ付きページの詳細データを書き込み（Phase 2 完了時）
 */
function writeFlaggedPagesData(runId, flaggedPagesWithGSC) {
  const sheet = initMonitorFlaggedSheet();

  const rows = flaggedPagesWithGSC.map(page => {
    const cGA4 = page.currentGA4 || {};
    const pGA4 = page.previousGA4 || {};
    const cGSC = page.currentGSC || {};
    const pGSC = page.previousGSC || {};
    const cImg = page.currentImageSearch || {};
    const pImg = page.previousImageSearch || {};

    return [
      runId,
      page.pagePath,
      cGA4.sessions || 0, cGA4.pageViews || 0, cGA4.engagementRate || 0,
      cGA4.bounceRate || 0, cGA4.avgSessionDuration || 0, cGA4.keyEvents || 0,
      pGA4.sessions || 0, pGA4.pageViews || 0, pGA4.engagementRate || 0,
      pGA4.bounceRate || 0, pGA4.avgSessionDuration || 0, pGA4.keyEvents || 0,
      cGSC.clicks || 0, cGSC.impressions || 0, cGSC.ctr || 0, cGSC.position || 0,
      pGSC.clicks || 0, pGSC.impressions || 0, pGSC.ctr || 0, pGSC.position || 0,
      cImg.imageClicks || 0, cImg.imageImpressions || 0,
      pImg.imageClicks || 0, pImg.imageImpressions || 0,
      JSON.stringify(page.queryChanges || [])
    ];
  });

  if (rows.length > 0) {
    const lastRow = sheet.getLastRow();
    sheet.getRange(lastRow + 1, 1, rows.length, rows[0].length).setValues(rows);
  }

  Logger.log(`[MonitorSheet] フラグ付きページ詳細記録: ${rows.length} 件`);
}

/**
 * フラグ付きページデータをシートから読み込み
 */
function readFlaggedPagesData(runId) {
  const sheet = getOrCreateSheet(MONITOR_CONFIG.SHEET_MONITOR_FLAGGED);
  const data = sheet.getDataRange().getValues();
  const result = [];

  for (let i = 1; i < data.length; i++) {
    const row = data[i];
    if (row[0] !== runId) continue;

    result.push({
      pagePath: row[1],
      currentGA4: {
        sessions: row[2], pageViews: row[3], engagementRate: row[4],
        bounceRate: row[5], avgSessionDuration: row[6], keyEvents: row[7]
      },
      previousGA4: {
        sessions: row[8], pageViews: row[9], engagementRate: row[10],
        bounceRate: row[11], avgSessionDuration: row[12], keyEvents: row[13]
      },
      currentGSC: {
        clicks: row[14], impressions: row[15], ctr: row[16], position: row[17]
      },
      previousGSC: {
        clicks: row[18], impressions: row[19], ctr: row[20], position: row[21]
      },
      currentImageSearch: { imageClicks: row[22], imageImpressions: row[23] },
      previousImageSearch: { imageClicks: row[24], imageImpressions: row[25] },
      queryChanges: JSON.parse(row[26] || '[]'),
      sessionChangeRate: row[2] && row[8] ? (row[2] - row[8]) / (row[8] || 1) : 0
    });
  }

  Logger.log(`[MonitorSheet] フラグ付きページ読み込み: ${result.length} 件 (runId: ${runId})`);
  return result;
}
