/**
 * MonitorSlack.gs — モニタリング専用 Slack レポート整形
 *
 * 数値データを見やすく整形して Slack に送信する。
 * 深い分析が必要な場合は、このレポートを Claude Code に貼り付けて分析する。
 */

/**
 * 週次モニタリングレポートを Slack に送信（データレポート版）
 *
 * @param {Array<Object>} flaggedPages - フラグ付きページデータ
 * @param {Object} runMeta - { runId, runDate, totalPages, flaggedCount, dates }
 */
function sendSlackMonitoringReport(flaggedPages, runMeta) {
  const webhookUrl = getConfig('SLACK_WEBHOOK_URL');

  if (!webhookUrl || webhookUrl.indexOf('https://hooks.slack.com') !== 0) {
    Logger.log('[MonitorSlack] Webhook URL が未設定です');
    return;
  }

  const blocks = [];

  // ヘッダー
  blocks.push({
    type: 'header',
    text: { type: 'plain_text', text: '📊 週次 SEO モニタリングレポート' }
  });

  // メタ情報
  const dates = runMeta.dates;
  blocks.push({
    type: 'section',
    text: {
      type: 'mrkdwn',
      text: [
        `📅 *対象期間:* ${formatDateJP(dates.currentStart)}〜${formatDateJP(dates.currentEnd)} vs ${formatDateJP(dates.previousStart)}〜${formatDateJP(dates.previousEnd)}`,
        `🔍 *スキャン対象:* ${runMeta.totalPages} ページ（Organic Search）`,
        `⚠️ *変動検出:* ${runMeta.flaggedCount} 件の記事でセッション数に大きな変化`
      ].join('\n')
    }
  });

  blocks.push({ type: 'divider' });

  // 個別ページデータ（上位5件まで）
  const displayPages = flaggedPages.slice(0, 5);

  displayPages.forEach((page, i) => {
    const changeRate = page.sessionChangeRate || 0;
    const icon = changeRate > 0 ? '🟢' : changeRate < -0.3 ? '🔴' : '🟠';

    let pageText = `${icon} *${i + 1}. ${page.pagePath}*\n`;

    // GA4 データ
    const cGA4 = page.currentGA4;
    const pGA4 = page.previousGA4;
    pageText += `*セッション:* ${pGA4.sessions}→${cGA4.sessions} (${changeRate >= 0 ? '+' : ''}${(changeRate * 100).toFixed(1)}%)\n`;
    pageText += `*PV:* ${pGA4.pageViews}→${cGA4.pageViews}`;
    pageText += ` | *直帰率:* ${(pGA4.bounceRate * 100).toFixed(1)}%→${(cGA4.bounceRate * 100).toFixed(1)}%`;
    pageText += ` | *CV:* ${pGA4.keyEvents}→${cGA4.keyEvents}`;

    // GSC データ
    const cGSC = page.currentGSC || {};
    const pGSC = page.previousGSC || {};
    if (pGSC.position || cGSC.position) {
      pageText += `\n*GSC順位:* ${(pGSC.position || 0).toFixed(1)}→${(cGSC.position || 0).toFixed(1)}`;
      pageText += ` | *CTR:* ${((pGSC.ctr || 0) * 100).toFixed(2)}%→${((cGSC.ctr || 0) * 100).toFixed(2)}%`;
      pageText += ` | *クリック:* ${pGSC.clicks || 0}→${cGSC.clicks || 0}`;
    }

    // クエリ変動（上位3件）
    if (page.queryChanges && page.queryChanges.length > 0) {
      pageText += '\n📉 *主要クエリ:*';
      page.queryChanges.slice(0, 3).forEach(q => {
        const posStr = q.previousPosition ? `順位${q.previousPosition.toFixed(1)}→${q.currentPosition.toFixed(1)}` : '(新規)';
        const clickStr = `クリック${q.previousClicks}→${q.currentClicks}`;
        pageText += `\n  「${q.query}」 ${posStr} ${clickStr}`;
      });
    }

    // 仮説表示
    if (page.hypotheses && page.hypotheses.length > 0) {
      const confidenceLabel = { high: '高', medium: '中', low: '低' };
      page.hypotheses.slice(0, 2).forEach(h => {
        pageText += `\n🔍 *仮説:* ${h.text}（確信度: ${confidenceLabel[h.confidence] || h.confidence}）`;
      });
    }

    // 施策提案表示
    if (page.actions && page.actions.length > 0) {
      pageText += '\n💡 *施策:*';
      page.actions.slice(0, 3).forEach((a, j) => {
        pageText += `\n  ${j + 1}. [${a.priority}優先/${a.effort}工数] ${a.title}`;
      });
    }

    blocks.push({
      type: 'section',
      text: { type: 'mrkdwn', text: pageText }
    });
  });

  // 残りのページがある場合
  if (flaggedPages.length > 5) {
    blocks.push({
      type: 'section',
      text: {
        type: 'mrkdwn',
        text: `📊 他 ${flaggedPages.length - 5} 件はスプレッドシートを参照してください。`
      }
    });
  }

  blocks.push({ type: 'divider' });

  // フッター: Claude Code での分析案内
  blocks.push({
    type: 'section',
    text: {
      type: 'mrkdwn',
      text: '💡 *詳細分析が必要な場合:* このレポートの内容を Claude Code に貼り付けて「原因分析と施策提案をしてください」と依頼してください。'
    }
  });

  // 送信
  try {
    UrlFetchApp.fetch(webhookUrl, {
      method: 'post',
      contentType: 'application/json',
      payload: JSON.stringify({ blocks: blocks })
    });
    Logger.log('[MonitorSlack] レポート送信成功');
  } catch (error) {
    Logger.log(`[MonitorSlack Error] ${error.message}`);
  }
}

/**
 * フラグ付きページがゼロの場合の「異常なし」通知
 */
function sendSlackNoChanges(runMeta) {
  const dates = runMeta.dates;
  const text = [
    '📊 *週次 SEO モニタリングレポート*',
    `📅 対象期間: ${formatDateJP(dates.currentStart)}〜${formatDateJP(dates.currentEnd)} vs ${formatDateJP(dates.previousStart)}〜${formatDateJP(dates.previousEnd)}`,
    `🔍 スキャン対象: ${runMeta.totalPages} ページ（Organic Search）`,
    '✅ 変動検出: 0 件 — すべてのページが安定しています。'
  ].join('\n');

  sendSlackSimple(text);
}

/**
 * モニタリングエラー通知
 */
function sendSlackMonitoringError(phase, errorMessage) {
  const text = `⚠️ *週次モニタリングでエラー*\nフェーズ: ${phase}\n\`\`\`${errorMessage}\`\`\``;
  sendSlackSimple(text);
}
