/**
 * MonitorMain.gs — 自動モニタリングのメインフロー
 *
 * GAS の6分制限に対応するため2フェーズに分割。
 *
 * Phase 1: GA4 全ページ一括取得 + 変動検出（~2分）
 * Phase 2: フラグ付きページの GSC 詳細取得 + Slack 送信（~4分）
 *
 * 深い原因分析が必要な場合は、Slack レポートを Claude Code に貼り付けて分析。
 */

// ========================================
// エントリーポイント
// ========================================

/**
 * 週次トリガーから呼ばれるエントリーポイント
 */
function startWeeklyMonitoring() {
  const props = PropertiesService.getScriptProperties();
  const currentPhase = props.getProperty(MONITOR_CONFIG.PHASE_KEY);

  // 前回の実行が未完了の場合、強制クリーンアップ
  if (currentPhase && currentPhase !== 'idle' && currentPhase !== 'error') {
    Logger.log(`[Monitor] 前回の実行が未完了 (phase: ${currentPhase})。クリーンアップします。`);
    cleanupMonitoringState();
  }

  // 新しい実行を開始
  const runId = Utilities.getUuid();
  props.setProperty(MONITOR_CONFIG.RUN_ID_KEY, runId);
  props.setProperty(MONITOR_CONFIG.PHASE_KEY, 'phase1');

  Logger.log(`[Monitor] === 週次モニタリング開始 === runId: ${runId}`);

  monitorPhase1_FetchGA4();
}

// ========================================
// Phase 1: GA4 バルクデータ取得 + 変動検出
// ========================================

function monitorPhase1_FetchGA4() {
  const props = PropertiesService.getScriptProperties();
  const runId = props.getProperty(MONITOR_CONFIG.RUN_ID_KEY);

  try {
    Logger.log(`[Phase1] 開始: runId=${runId}`);

    // 日付計算
    const dates = calculateMonitoringDates();
    Logger.log(`[Phase1] 今週: ${formatDateYYYYMMDD(dates.currentStart)} - ${formatDateYYYYMMDD(dates.currentEnd)}`);
    Logger.log(`[Phase1] 先週: ${formatDateYYYYMMDD(dates.previousStart)} - ${formatDateYYYYMMDD(dates.previousEnd)}`);

    // GA4 全ページデータ一括取得
    const currentWeekData = fetchGA4BulkData(dates.currentStart, dates.currentEnd);
    const previousWeekData = fetchGA4BulkData(dates.previousStart, dates.previousEnd);

    const totalPages = new Set([
      ...Object.keys(currentWeekData),
      ...Object.keys(previousWeekData)
    ]).size;

    // 変動検出
    const flaggedPages = detectSignificantChanges(currentWeekData, previousWeekData);

    // シートに記録
    writeWeeklyMonitoringData(runId, new Date(), flaggedPages, totalPages);

    // フラグ付きページが 0 件の場合
    if (flaggedPages.length === 0) {
      Logger.log('[Phase1] 変動なし。異常なし通知を送信して完了。');
      sendSlackNoChanges({
        totalPages: totalPages,
        dates: dates
      });
      props.setProperty(MONITOR_CONFIG.PHASE_KEY, 'idle');
      return;
    }

    // Phase 2 用のデータを保存
    const phaseData = {
      flaggedPages: flaggedPages,
      dates: {
        currentStart: dates.currentStart.toISOString(),
        currentEnd: dates.currentEnd.toISOString(),
        previousStart: dates.previousStart.toISOString(),
        previousEnd: dates.previousEnd.toISOString()
      },
      totalPages: totalPages
    };
    props.setProperty(`MONITOR_PHASE1_${runId}`, JSON.stringify(phaseData));

    // Phase 2 をスケジュール
    props.setProperty(MONITOR_CONFIG.PHASE_KEY, 'phase2');
    scheduleNextPhase('monitorPhase2_FetchGSCAndReport', 1);

    Logger.log(`[Phase1] 完了。${flaggedPages.length} ページをフラグ。Phase 2 を1分後に実行。`);

  } catch (error) {
    Logger.log(`[Phase1 Error] ${error.message}\n${error.stack}`);
    sendSlackMonitoringError('Phase 1 (GA4 データ取得)', error.message);
    props.setProperty(MONITOR_CONFIG.PHASE_KEY, 'error');
  }
}

// ========================================
// Phase 2: GSC 詳細取得 + Slack レポート送信
// ========================================

function monitorPhase2_FetchGSCAndReport() {
  const props = PropertiesService.getScriptProperties();
  const runId = props.getProperty(MONITOR_CONFIG.RUN_ID_KEY);

  try {
    Logger.log(`[Phase2] 開始: runId=${runId}`);

    // Phase 1 のデータを復元
    const phaseDataJson = props.getProperty(`MONITOR_PHASE1_${runId}`);
    if (!phaseDataJson) {
      throw new Error('Phase 1 のデータが見つかりません');
    }
    const phaseData = JSON.parse(phaseDataJson);

    const dates = {
      currentStart: new Date(phaseData.dates.currentStart),
      currentEnd: new Date(phaseData.dates.currentEnd),
      previousStart: new Date(phaseData.dates.previousStart),
      previousEnd: new Date(phaseData.dates.previousEnd)
    };

    // フラグ付きページの GSC 詳細を取得
    const flaggedPagesWithGSC = fetchGSCDetailsForFlaggedPages(
      phaseData.flaggedPages,
      dates.currentStart, dates.currentEnd,
      dates.previousStart, dates.previousEnd
    );

    // 仮説生成 + 施策提案
    flaggedPagesWithGSC.forEach(page => {
      const hypotheses = generateHypotheses(page, 'monitoring');
      const actions = proposeActions(hypotheses, page);
      page.hypotheses = hypotheses;
      page.actions = actions;

      // 施策キューに書き込み
      if (actions.length > 0) {
        writeToQueue(MONITOR_CONFIG.SITE_URL + page.pagePath, actions, 'モニタリング', hypotheses);
      }
    });

    // シートに記録
    writeFlaggedPagesData(runId, flaggedPagesWithGSC);

    // Slack にレポート送信
    const runMeta = {
      runId: runId,
      runDate: new Date(),
      totalPages: phaseData.totalPages,
      flaggedCount: flaggedPagesWithGSC.length,
      dates: dates
    };
    sendSlackMonitoringReport(flaggedPagesWithGSC, runMeta);

    // クリーンアップ
    props.deleteProperty(`MONITOR_PHASE1_${runId}`);
    props.setProperty(MONITOR_CONFIG.PHASE_KEY, 'idle');

    Logger.log(`[Phase2] 完了。レポート送信済み。`);
    Logger.log(`[Monitor] === 週次モニタリング完了 === runId: ${runId}`);

  } catch (error) {
    Logger.log(`[Phase2 Error] ${error.message}\n${error.stack}`);
    sendSlackMonitoringError('Phase 2 (GSC データ取得 + レポート送信)', error.message);
    props.setProperty(MONITOR_CONFIG.PHASE_KEY, 'error');
  }

  // フェーズトリガーをクリーンアップ
  cleanupPhaseTrigger('monitorPhase2_FetchGSCAndReport');
}

// ========================================
// ユーティリティ
// ========================================

/**
 * 次フェーズのトリガーを作成
 */
function scheduleNextPhase(functionName, delayMinutes) {
  const trigger = ScriptApp.newTrigger(functionName)
    .timeBased()
    .after(delayMinutes * 60 * 1000)
    .create();

  Logger.log(`[Scheduler] ${functionName} を ${delayMinutes}分後に実行予約`);
  return trigger.getUniqueId();
}

/**
 * 特定のフェーズ関数のトリガーを削除
 */
function cleanupPhaseTrigger(functionName) {
  ScriptApp.getProjectTriggers().forEach(trigger => {
    if (trigger.getHandlerFunction() === functionName) {
      ScriptApp.deleteTrigger(trigger);
    }
  });
}

/**
 * モニタリング状態を全リセット
 */
function cleanupMonitoringState() {
  const props = PropertiesService.getScriptProperties();
  const runId = props.getProperty(MONITOR_CONFIG.RUN_ID_KEY);

  if (runId) {
    props.deleteProperty(`MONITOR_PHASE1_${runId}`);
  }
  props.deleteProperty(MONITOR_CONFIG.PHASE_KEY);
  props.deleteProperty(MONITOR_CONFIG.RUN_ID_KEY);

  // 残存フェーズトリガーを削除
  cleanupPhaseTrigger('monitorPhase2_FetchGSCAndReport');

  Logger.log('[Monitor] 状態をリセットしました');
}

// ========================================
// セットアップ
// ========================================

/**
 * 初回セットアップ: 毎週月曜 AM 9:00 のトリガーを作成
 * GAS エディタから1回だけ手動実行する。
 */
function setupWeeklyTrigger() {
  // 既存の週次トリガーを削除（重複防止）
  ScriptApp.getProjectTriggers().forEach(trigger => {
    if (trigger.getHandlerFunction() === 'startWeeklyMonitoring') {
      ScriptApp.deleteTrigger(trigger);
    }
  });

  ScriptApp.newTrigger('startWeeklyMonitoring')
    .timeBased()
    .onWeekDay(ScriptApp.WeekDay.MONDAY)
    .atHour(9)
    .create();

  Logger.log('[Setup] 週次トリガーを作成しました: 毎週月曜 AM 9:00');
}

// ========================================
// テスト・リカバリ
// ========================================

/**
 * テスト用: 手動実行
 */
function testWeeklyMonitoring() {
  Logger.log('=== テスト実行開始 ===');
  startWeeklyMonitoring();
  Logger.log('=== Phase 1 完了。Phase 2 は約1分後に自動実行されます ===');
}

/**
 * Phase 2 から再実行
 */
function retryFromPhase2() {
  const props = PropertiesService.getScriptProperties();
  props.setProperty(MONITOR_CONFIG.PHASE_KEY, 'phase2');
  monitorPhase2_FetchGSCAndReport();
}

/**
 * 全モニタリング状態をリセット（トラブル時）
 */
function resetMonitoringState() {
  cleanupMonitoringState();
  Logger.log('モニタリング状態を完全にリセットしました。');
}
