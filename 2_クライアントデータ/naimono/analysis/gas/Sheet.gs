/**
 * Sheet.gs — スプレッドシート操作
 *
 * スプレッドシートへの読み書きを管理する。
 */

/**
 * スプレッドシートオブジェクトを取得
 */
function getSpreadsheet() {
  const ssId = getConfig('SPREADSHEET_ID');
  return SpreadsheetApp.openById(ssId);
}

/**
 * 指定シートを取得（なければ作成）
 */
function getOrCreateSheet(sheetName) {
  const ss = getSpreadsheet();
  let sheet = ss.getSheetByName(sheetName);

  if (!sheet) {
    sheet = ss.insertSheet(sheetName);
  }

  return sheet;
}

/**
 * 「変更ログ」シートを初期化
 */
function initLogSheet() {
  const sheet = getOrCreateSheet(getConfig('SHEET_LOG'));

  if (sheet.getLastRow() === 0) {
    const headers = [
      '変更日時',
      'ページURL',
      'バナー画像URL（旧）',
      'バナー画像URL（新）',
      '記録者',
      'ステータス',
      'Before期間',
      'After期間',
      '次回レポート予定日',
      'トリガーID'
    ];
    sheet.getRange(1, 1, 1, headers.length).setValues([headers]).setFontWeight('bold');
  }

  return sheet;
}

/**
 * 「データ」シートを初期化
 */
function initDataSheet() {
  const sheet = getOrCreateSheet(getConfig('SHEET_DATA'));

  if (sheet.getLastRow() === 0) {
    const headers = [
      '変更日時',
      'ページURL',
      '期間種別',  // "Before" or "After"
      '開始日',
      '終了日',
      // GA4
      'セッション数',
      'PV数',
      'エンゲージセッション数',
      'エンゲージメント率',
      '平均セッション時間',
      '直帰率',
      'CV数',
      'スクロール25%',
      'スクロール50%',
      'スクロール75%',
      'スクロール90%',
      // GSC
      'クリック数',
      '表示回数',
      'CTR',
      '平均掲載順位',
      '画像検索クリック',
      '画像検索表示回数'
    ];
    sheet.getRange(1, 1, 1, headers.length).setValues([headers]).setFontWeight('bold');
  }

  return sheet;
}

/**
 * 変更ログに記録
 *
 * @param {Object} data - 記録するデータ
 */
function writeChangeLog(data) {
  const sheet = initLogSheet();
  const lastRow = sheet.getLastRow();

  const row = [
    data.changeDate,
    data.pageUrl,
    data.oldBannerUrl || '',
    data.newBannerUrl || '',
    data.recorder || Session.getActiveUser().getEmail(),
    data.status || '計測中',
    data.beforePeriod || '',
    data.afterPeriod || '',
    data.nextReportDate || '',
    data.triggerId || ''
  ];

  sheet.getRange(lastRow + 1, 1, 1, row.length).setValues([row]);

  Logger.log(`[Sheet] 変更ログに記録: ${data.pageUrl}`);
}

/**
 * データシートに Before/After データを記録
 *
 * @param {Object} params
 */
function writeDataRecord(params) {
  const sheet = initDataSheet();
  const lastRow = sheet.getLastRow();

  const {
    changeDate,
    pageUrl,
    periodType,  // "Before" or "After"
    startDate,
    endDate,
    ga4Data,
    scrollData,
    gscData,
    imageSearchData
  } = params;

  const row = [
    changeDate,
    pageUrl,
    periodType,
    startDate,
    endDate,
    // GA4
    ga4Data.sessions || 0,
    ga4Data.pageViews || 0,
    ga4Data.engagedSessions || 0,
    ga4Data.engagementRate || 0,
    ga4Data.avgSessionDuration || 0,
    ga4Data.bounceRate || 0,
    ga4Data.keyEvents || 0,
    (scrollData && scrollData.scroll_25) || 0,
    (scrollData && scrollData.scroll_50) || 0,
    (scrollData && scrollData.scroll_75) || 0,
    (scrollData && scrollData.scroll_90) || 0,
    // GSC
    gscData.clicks || 0,
    gscData.impressions || 0,
    gscData.ctr || 0,
    gscData.position || 0,
    imageSearchData.imageClicks || 0,
    imageSearchData.imageImpressions || 0
  ];

  sheet.getRange(lastRow + 1, 1, 1, row.length).setValues([row]);

  Logger.log(`[Sheet] データ記録: ${pageUrl} (${periodType})`);
}

/**
 * 変更ログから Before データを取得
 *
 * @param {string} pageUrl
 * @param {Date} changeDate
 * @return {Object|null} Before データ、見つからなければ null
 */
function getBeforeData(pageUrl, changeDate) {
  const sheet = getOrCreateSheet(getConfig('SHEET_DATA'));
  const data = sheet.getDataRange().getValues();

  // ヘッダー行をスキップして検索
  for (let i = 1; i < data.length; i++) {
    const row = data[i];
    const rowChangeDate = new Date(row[0]);
    const rowPageUrl = row[1];
    const rowPeriodType = row[2];

    // Google Sheets は Date のミリ秒を切り捨てるため、秒単位で比較
    if (rowPageUrl === pageUrl &&
        Math.floor(rowChangeDate.getTime() / 1000) === Math.floor(changeDate.getTime() / 1000) &&
        rowPeriodType === 'Before') {

      return {
        ga4: {
          sessions: row[5],
          pageViews: row[6],
          engagedSessions: row[7],
          engagementRate: row[8],
          avgSessionDuration: row[9],
          bounceRate: row[10],
          keyEvents: row[11]
        },
        scroll: {
          scroll_25: row[12],
          scroll_50: row[13],
          scroll_75: row[14],
          scroll_90: row[15]
        },
        gsc: {
          clicks: row[16],
          impressions: row[17],
          ctr: row[18],
          position: row[19]
        },
        imageSearch: {
          imageClicks: row[20],
          imageImpressions: row[21]
        }
      };
    }
  }

  return null;
}

/**
 * トリガーIDで変更ログのステータスを更新
 *
 * @param {string} triggerId
 * @param {string} status
 */
function updateLogStatus(triggerId, status) {
  const sheet = getOrCreateSheet(getConfig('SHEET_LOG'));
  const data = sheet.getDataRange().getValues();

  for (let i = 1; i < data.length; i++) {
    if (data[i][9] === triggerId) {  // トリガーID列
      sheet.getRange(i + 1, 6).setValue(status);  // ステータス列
      Logger.log(`[Sheet] ステータス更新: ${triggerId} → ${status}`);
      return;
    }
  }
}
