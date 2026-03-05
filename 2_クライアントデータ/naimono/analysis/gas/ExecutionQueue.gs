/**
 * ExecutionQueue.gs — 施策キューシート管理
 *
 * 施策の提案→承認→実施→検証のライフサイクルを管理する。
 * 自動操作は「提案」ステータスでの書き込みのみ。
 * 承認以降のステータス変更はスプレッドシート上で手動操作。
 *
 * ステータスワークフロー:
 *   提案 → 承認 → 実施中 → 計測中 → 検証完了
 *     └──→ 却下
 */

/**
 * 「施策キュー」シートを初期化
 */
function initQueueSheet() {
  const sheet = getOrCreateSheet(MONITOR_CONFIG.SHEET_QUEUE);

  if (sheet.getLastRow() === 0) {
    const headers = [
      'キューID',
      '提案日',
      'ページURL',
      '施策タイトル',
      '施策詳細',
      'ソース',        // 「モニタリング」/「バナー差替え」
      '仮説タイプ',    // ruleId
      '優先度',        // 高/中/低
      '工数',          // 低/中/高
      'スコア',        // priority/effort
      'ステータス',    // 提案/承認/実施中/計測中/検証完了/却下
      '備考'
    ];
    sheet.getRange(1, 1, 1, headers.length).setValues([headers]).setFontWeight('bold');

    // 列幅の調整
    sheet.setColumnWidth(1, 80);   // キューID
    sheet.setColumnWidth(3, 250);  // ページURL
    sheet.setColumnWidth(4, 200);  // 施策タイトル
    sheet.setColumnWidth(5, 350);  // 施策詳細
  }

  return sheet;
}

/**
 * 施策をキューに追加
 *
 * @param {string} pageUrl - ページURL
 * @param {Array<Object>} actions - proposeActions() の出力
 * @param {string} source - 'モニタリング' | 'バナー差替え'
 * @param {Array<Object>} hypotheses - generateHypotheses() の出力
 */
function writeToQueue(pageUrl, actions, source, hypotheses) {
  const sheet = initQueueSheet();
  const now = new Date();
  let addedCount = 0;

  actions.forEach(action => {
    // 重複チェック: 同じページ+同じ施策タイトルが「提案」or「承認」ステータスで既に存在
    if (isDuplicateAction(pageUrl, action.title)) {
      Logger.log(`[Queue] 重複スキップ: ${pageUrl} / ${action.title}`);
      return;
    }

    const queueId = Utilities.getUuid().substring(0, 8);

    const row = [
      queueId,
      now,
      pageUrl,
      action.title,
      action.detail,
      source,
      action.sourceRuleId,
      action.priority,
      action.effort,
      action.score,
      '提案',
      ''
    ];

    const lastRow = sheet.getLastRow();
    sheet.getRange(lastRow + 1, 1, 1, row.length).setValues([row]);
    addedCount++;
  });

  Logger.log(`[Queue] ${addedCount} 件の施策をキューに追加 (${pageUrl})`);
}

/**
 * 重複チェック: 同じページ+同じ施策タイトルが「提案」or「承認」で既に存在するか
 *
 * @param {string} pageUrl - ページURL
 * @param {string} actionTitle - 施策タイトル
 * @return {boolean} 重複していれば true
 */
function isDuplicateAction(pageUrl, actionTitle) {
  const sheet = getOrCreateSheet(MONITOR_CONFIG.SHEET_QUEUE);
  const lastRow = sheet.getLastRow();

  if (lastRow <= 1) return false;

  const data = sheet.getRange(2, 1, lastRow - 1, 11).getValues();
  const activeStatuses = ['提案', '承認', '実施中', '計測中'];

  for (let i = 0; i < data.length; i++) {
    const rowUrl = data[i][2];       // C列: ページURL
    const rowTitle = data[i][3];     // D列: 施策タイトル
    const rowStatus = data[i][10];   // K列: ステータス

    if (rowUrl === pageUrl && rowTitle === actionTitle && activeStatuses.indexOf(rowStatus) !== -1) {
      return true;
    }
  }

  return false;
}

/**
 * キューの読み込み（ステータス別）
 *
 * @param {string} status - フィルターするステータス（省略時は全件）
 * @return {Array<Object>} キューアイテム配列
 */
function readQueueByStatus(status) {
  const sheet = getOrCreateSheet(MONITOR_CONFIG.SHEET_QUEUE);
  const lastRow = sheet.getLastRow();

  if (lastRow <= 1) return [];

  const data = sheet.getRange(2, 1, lastRow - 1, 12).getValues();
  const result = [];

  data.forEach(row => {
    const rowStatus = row[10];
    if (status && rowStatus !== status) return;

    result.push({
      queueId: row[0],
      proposedDate: row[1],
      pageUrl: row[2],
      title: row[3],
      detail: row[4],
      source: row[5],
      ruleId: row[6],
      priority: row[7],
      effort: row[8],
      score: row[9],
      status: row[10],
      note: row[11]
    });
  });

  return result;
}
