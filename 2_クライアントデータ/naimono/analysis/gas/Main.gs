/**
 * Main.gs — メインフロー
 *
 * Google フォームからのトリガーとレポート生成を管理する。
 */

/**
 * Google フォーム送信時に実行される（エントリーポイント）
 *
 * Google フォームと連携する場合:
 * 1. Google フォームを作成
 * 2. 質問: 「ページURL」（短答式）
 * 3. フォームの「回答」→「スプレッドシートに表示」でスプレッドシートを作成
 * 4. そのスプレッドシートから「拡張機能」→「Apps Script」でこのコードをコピー
 * 5. トリガー設定: 「フォーム送信時」トリガーで onFormSubmit を設定
 *
 * @param {Object} e - フォーム送信イベント
 */
function onFormSubmit(e) {
  try {
    // フォーム回答から各フィールドを取得
    // e.values[0] = タイムスタンプ
    // e.values[1] = ページURL
    // e.values[2] = CTA遷移先URL（任意）
    // e.values[3] = 変更内容メモ（任意）
    // e.values[4] = 旧CTA画像（Googleドライブ URL）（任意）
    // e.values[5] = 新CTA画像（Googleドライブ URL）（任意）
    const pageUrl = e.values[1].trim();
    const ctaTargetUrl = (e.values[2] || '').trim();
    const changeMemo = (e.values[3] || '').trim();
    const oldCtaImageUrl = (e.values[4] || '').trim();
    const newCtaImageUrl = (e.values[5] || '').trim();
    const changeDate = new Date();

    Logger.log(`[Main] フォーム送信を受信: ${pageUrl}`);

    // ページURLのバリデーション
    if (!pageUrl || pageUrl.indexOf('http') !== 0) {
      throw new Error('無効なURLです: ' + pageUrl);
    }

    // バナー画像URLを自動取得
    const bannerUrl = scrapePageBanner(pageUrl);

    // Before 期間の計算
    const beforeDays = getConfig('BEFORE_DAYS');
    const beforeStart = addDays(changeDate, -beforeDays);
    const beforeEnd = addDays(changeDate, -1);

    Logger.log(`[Main] Before期間: ${formatDateYYYYMMDD(beforeStart)} - ${formatDateYYYYMMDD(beforeEnd)}`);

    // Before データの取得
    const pagePath = extractPagePath(pageUrl);

    const beforeGA4 = fetchGA4Data(pagePath, beforeStart, beforeEnd);
    // スクロール指標は除外（GTMで未設定のため）
    // const beforeScroll = fetchGA4ScrollDepth(pagePath, beforeStart, beforeEnd);
    const beforeGSC = fetchGSCData(pageUrl, beforeStart, beforeEnd);
    const beforeImageSearch = fetchGSCImageSearchData(pageUrl, beforeStart, beforeEnd);

    // スプレッドシートに Before データを記録
    writeDataRecord({
      changeDate: changeDate,
      pageUrl: pageUrl,
      periodType: 'Before',
      startDate: formatDateYYYYMMDD(beforeStart),
      endDate: formatDateYYYYMMDD(beforeEnd),
      ga4Data: beforeGA4,
      scrollData: null,  // スクロール指標は除外
      gscData: beforeGSC,
      imageSearchData: beforeImageSearch
    });

    // After レポート生成のトリガーを作成
    const reportDate = new Date(changeDate.getTime() + getConfig('REPORT_DELAY_MS'));

    const trigger = ScriptApp.newTrigger('generateReport')
      .timeBased()
      .at(reportDate)
      .create();

    const triggerId = trigger.getUniqueId();

    // トリガー情報を保存（レポート生成時に使う）
    PropertiesService.getScriptProperties().setProperty(
      triggerId,
      JSON.stringify({
        pageUrl: pageUrl,
        changeDate: changeDate.toISOString(),
        bannerUrl: bannerUrl,
        ctaTargetUrl: ctaTargetUrl,
        changeMemo: changeMemo,
        oldCtaImageUrl: oldCtaImageUrl,
        newCtaImageUrl: newCtaImageUrl
      })
    );

    // 変更ログに記録
    writeChangeLog({
      changeDate: changeDate,
      pageUrl: pageUrl,
      oldBannerUrl: oldCtaImageUrl || '',
      newBannerUrl: newCtaImageUrl || bannerUrl,
      status: '計測中',
      beforePeriod: `${formatDateYYYYMMDD(beforeStart)} - ${formatDateYYYYMMDD(beforeEnd)}`,
      afterPeriod: '（未取得）',
      nextReportDate: formatDateYYYYMMDD(reportDate),
      triggerId: triggerId
    });

    // Slack 通知
    sendSlackDetection({
      pageUrl: pageUrl,
      changeDate: changeDate
    });

    Logger.log(`[Main] 処理完了。トリガーID: ${triggerId}`);

  } catch (error) {
    Logger.log(`[Main Error] ${error.message}\n${error.stack}`);
    sendSlackError(`フォーム送信処理でエラー: ${error.message}`);
  }
}

/**
 * After データを取得してレポートを生成（時限トリガーから実行される）
 *
 * @param {Object} e - トリガーイベント
 */
function generateReport(e) {
  const triggerId = e && e.triggerUid;

  if (!triggerId) {
    Logger.log('[Report Error] トリガーIDが取得できません');
    return;
  }

  try {
    Logger.log(`[Report] レポート生成開始: ${triggerId}`);

    // トリガー情報を取得
    const props = PropertiesService.getScriptProperties();
    const dataJson = props.getProperty(triggerId);

    if (!dataJson) {
      throw new Error(`トリガー情報が見つかりません: ${triggerId}`);
    }

    const data = JSON.parse(dataJson);
    const pageUrl = data.pageUrl;
    const changeDate = new Date(data.changeDate);

    Logger.log(`[Report] 対象ページ: ${pageUrl}`);

    // After 期間の計算（GSC 遅延バッファを考慮）
    const afterDays = getConfig('AFTER_DAYS');
    const gscDelayBuffer = getConfig('GSC_DELAY_BUFFER');

    const afterStart = addDays(changeDate, gscDelayBuffer);
    const afterEnd = addDays(changeDate, gscDelayBuffer + afterDays - 1);

    Logger.log(`[Report] After期間: ${formatDateYYYYMMDD(afterStart)} - ${formatDateYYYYMMDD(afterEnd)}`);

    // After データの取得
    const pagePath = extractPagePath(pageUrl);

    const afterGA4 = fetchGA4Data(pagePath, afterStart, afterEnd);
    // スクロール指標は除外（GTMで未設定のため）
    // const afterScroll = fetchGA4ScrollDepth(pagePath, afterStart, afterEnd);
    const afterGSC = fetchGSCData(pageUrl, afterStart, afterEnd);
    const afterImageSearch = fetchGSCImageSearchData(pageUrl, afterStart, afterEnd);

    // スプレッドシートに After データを記録
    writeDataRecord({
      changeDate: changeDate,
      pageUrl: pageUrl,
      periodType: 'After',
      startDate: formatDateYYYYMMDD(afterStart),
      endDate: formatDateYYYYMMDD(afterEnd),
      ga4Data: afterGA4,
      scrollData: null,  // スクロール指標は除外
      gscData: afterGSC,
      imageSearchData: afterImageSearch
    });

    // Before データを取得
    const beforeData = getBeforeData(pageUrl, changeDate);

    if (!beforeData) {
      throw new Error(`Before データが見つかりません: ${pageUrl}, ${changeDate}`);
    }

    // Before/After 比較（noData の場合はデフォルト値で正規化）
    const defaultGA4 = { sessions: 0, pageViews: 0, engagedSessions: 0, engagementRate: 0, avgSessionDuration: 0, bounceRate: 0, keyEvents: 0 };
    const defaultGSC = { clicks: 0, impressions: 0, ctr: 0, position: 0 };
    const defaultImageSearch = { imageClicks: 0, imageImpressions: 0 };

    const afterData = {
      ga4: (afterGA4 && !afterGA4.noData) ? afterGA4 : defaultGA4,
      scroll: null,  // スクロール指標は除外
      gsc: (afterGSC && !afterGSC.noData) ? afterGSC : defaultGSC,
      imageSearch: (afterImageSearch && !afterImageSearch.noData) ? afterImageSearch : defaultImageSearch
    };

    const comparison = compareData(beforeData, afterData);

    // 仮説生成 + 施策提案
    const hypothesisPageData = {
      pagePath: pagePath,
      sessionChangeRate: safeChangeRate(beforeData.ga4.sessions, afterData.ga4.sessions),
      currentGA4: afterData.ga4,
      previousGA4: beforeData.ga4,
      currentGSC: afterData.gsc,
      previousGSC: beforeData.gsc,
      currentImageSearch: afterData.imageSearch,
      previousImageSearch: beforeData.imageSearch
    };
    const hypotheses = generateHypotheses(hypothesisPageData, 'banner_change');
    const actions = proposeActions(hypotheses, hypothesisPageData);

    // 施策キューに書き込み
    if (actions.length > 0) {
      writeToQueue(pageUrl, actions, 'バナー差替え', hypotheses);
    }

    // レポートデータを構築
    const report = {
      pageUrl: pageUrl,
      changeDate: changeDate,
      before: beforeData,
      after: afterData,
      changes: comparison.changes,
      verdict: comparison.verdict,
      hypotheses: hypotheses,
      actions: actions
    };

    // Slack にレポート送信
    sendSlackReport(report);

    // 変更ログのステータスを更新
    updateLogStatus(triggerId, `完了 (${comparison.verdict})`);

    // トリガーのクリーンアップ
    const triggerToDelete = ScriptApp.getProjectTriggers().find(t => t.getUniqueId() === triggerId);
    if (triggerToDelete) {
      ScriptApp.deleteTrigger(triggerToDelete);
    }
    props.deleteProperty(triggerId);

    Logger.log(`[Report] レポート生成完了: ${comparison.verdict}`);

  } catch (error) {
    Logger.log(`[Report Error] ${error.message}\n${error.stack}`);
    sendSlackError(`レポート生成でエラー: ${error.message}`);

    // エラー時もトリガーは削除
    try {
      const trigger = ScriptApp.getProjectTriggers().find(t => t.getUniqueId() === triggerId);
      if (trigger) {
        ScriptApp.deleteTrigger(trigger);
      }
      updateLogStatus(triggerId, 'エラー');
    } catch (cleanupError) {
      Logger.log(`[Cleanup Error] ${cleanupError.message}`);
    }
  }
}

/**
 * 手動テスト用: フォーム送信をシミュレート
 *
 * GAS エディタから直接実行してテストする。
 */
function testFormSubmit() {
  const testEvent = {
    values: [
      new Date(),                              // [0] タイムスタンプ
      'https://jo-katsu.com/campus/26469',     // [1] ページURL
      '',                                       // [2] CTA遷移先URL（任意）
      'テスト: バナー画像を変更',                // [3] 変更内容メモ（任意）
      '',                                       // [4] 旧CTA画像URL（任意）
      ''                                        // [5] 新CTA画像URL（任意）
    ]
  };

  onFormSubmit(testEvent);
}

/**
 * 手動テスト用: レポート生成をシミュレート
 *
 * 既存のトリガーIDを指定して実行。
 * トリガーIDは listAllTriggers() で確認できる。
 */
function testGenerateReport() {
  const testTriggerId = 'XXXXXXXXX';  // 実際のトリガーIDに変更

  const testEvent = {
    triggerUid: testTriggerId
  };

  generateReport(testEvent);
}
