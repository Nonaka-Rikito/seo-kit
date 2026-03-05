/**
 * Slack.gs — Slack 通知
 *
 * Incoming Webhook を使った通知を管理する。
 */

/**
 * Slack に通知を送信（シンプル版）
 *
 * @param {string} text - 送信するテキスト
 */
function sendSlackSimple(text) {
  const webhookUrl = getConfig('SLACK_WEBHOOK_URL');

  if (!webhookUrl || webhookUrl.indexOf('https://hooks.slack.com') !== 0) {
    Logger.log('[Slack] Webhook URL が未設定です');
    return;
  }

  const payload = { text: text };

  try {
    UrlFetchApp.fetch(webhookUrl, {
      method: 'post',
      contentType: 'application/json',
      payload: JSON.stringify(payload)
    });

    Logger.log('[Slack] 通知送信成功');
  } catch (error) {
    Logger.log(`[Slack Error] ${error.message}`);
  }
}

/**
 * バナー差替え検知時の通知
 *
 * @param {Object} data
 */
function sendSlackDetection(data) {
  const text = `🔔 *バナー差替えを記録しました*\n` +
               `📄 記事: ${data.pageUrl}\n` +
               `🗓️ 変更日: ${formatDateJP(data.changeDate)}\n` +
               `⏰ ${getConfig('AFTER_DAYS') + getConfig('GSC_DELAY_BUFFER')}日後にレポートを送信します`;

  sendSlackSimple(text);
}

/**
 * Before/After 比較レポートの通知（リッチ版）
 *
 * @param {Object} report - 比較レポートデータ
 */
function sendSlackReport(report) {
  const webhookUrl = getConfig('SLACK_WEBHOOK_URL');

  if (!webhookUrl || webhookUrl.indexOf('https://hooks.slack.com') !== 0) {
    Logger.log('[Slack] Webhook URL が未設定です');
    return;
  }

  const { pageUrl, changeDate, before, after, changes, verdict } = report;

  // GSC データが存在しない場合のデフォルト値
  const bGSC = (before.gsc && !before.gsc.noData) ? before.gsc : { clicks: 0, impressions: 0, ctr: 0, position: 0 };
  const aGSC = (after.gsc && !after.gsc.noData) ? after.gsc : { clicks: 0, impressions: 0, ctr: 0, position: 0 };

  // 判定の絵文字
  const verdictEmoji = verdict === '改善' ? '✅' :
                       verdict === '悪化' ? '❌' :
                       '⚪';

  const payload = {
    blocks: [
      {
        type: 'header',
        text: {
          type: 'plain_text',
          text: '📊 バナー差替え検証レポート'
        }
      },
      {
        type: 'section',
        text: {
          type: 'mrkdwn',
          text: `*記事:* ${pageUrl}\n*差替え日:* ${formatDateJP(changeDate)}`
        }
      },
      {
        type: 'divider'
      },
      {
        type: 'section',
        fields: [
          {
            type: 'mrkdwn',
            text: `*セッション数*\n${before.ga4.sessions} → ${after.ga4.sessions} (${changes.sessions})`
          },
          {
            type: 'mrkdwn',
            text: `*PV数*\n${before.ga4.pageViews} → ${after.ga4.pageViews} (${changes.pageViews})`
          },
          {
            type: 'mrkdwn',
            text: `*直帰率*\n${(before.ga4.bounceRate * 100).toFixed(1)}% → ${(after.ga4.bounceRate * 100).toFixed(1)}% (${changes.bounceRate})`
          },
          {
            type: 'mrkdwn',
            text: `*エンゲージメント率*\n${(before.ga4.engagementRate * 100).toFixed(1)}% → ${(after.ga4.engagementRate * 100).toFixed(1)}% (${changes.engagementRate})`
          }
        ]
      },
      {
        type: 'section',
        fields: [
          {
            type: 'mrkdwn',
            text: `*クリック数 (GSC)*\n${bGSC.clicks} → ${aGSC.clicks} (${changes.clicks})`
          },
          {
            type: 'mrkdwn',
            text: `*CTR (GSC)*\n${(bGSC.ctr * 100).toFixed(2)}% → ${(aGSC.ctr * 100).toFixed(2)}% (${changes.ctr})`
          },
          {
            type: 'mrkdwn',
            text: `*平均掲載順位*\n${bGSC.position.toFixed(1)} → ${aGSC.position.toFixed(1)} (${changes.position})`
          },
          {
            type: 'mrkdwn',
            text: `*CV数*\n${before.ga4.keyEvents} → ${after.ga4.keyEvents} (${changes.keyEvents})`
          }
        ]
      },
      {
        type: 'divider'
      },
      {
        type: 'section',
        text: {
          type: 'mrkdwn',
          text: `*判定:* ${verdictEmoji} *${verdict}*`
        }
      }
    ]
  };

  // 仮説カードを追加
  if (report.hypotheses && report.hypotheses.length > 0) {
    const confidenceLabel = { high: '高', medium: '中', low: '低' };
    let hypothesisText = '🔍 *原因仮説:*\n';
    report.hypotheses.forEach((h, i) => {
      hypothesisText += `${i + 1}. ${h.text}（確信度: ${confidenceLabel[h.confidence] || h.confidence}）\n`;
      if (h.evidence) hypothesisText += `   _${h.evidence}_\n`;
    });

    payload.blocks.push({
      type: 'section',
      text: { type: 'mrkdwn', text: hypothesisText }
    });
  }

  // 施策提案を追加
  if (report.actions && report.actions.length > 0) {
    let actionText = '💡 *推奨施策:*\n';
    report.actions.slice(0, 3).forEach((a, i) => {
      actionText += `${i + 1}. *[${a.priority}優先/${a.effort}工数]* ${a.title}\n`;
      actionText += `   ${a.detail}\n`;
    });

    payload.blocks.push({
      type: 'section',
      text: { type: 'mrkdwn', text: actionText }
    });
  }

  // Claude Code での深掘り案内
  if ((report.hypotheses && report.hypotheses.length > 0) || (report.actions && report.actions.length > 0)) {
    payload.blocks.push({ type: 'divider' });
    payload.blocks.push({
      type: 'section',
      text: {
        type: 'mrkdwn',
        text: '💬 *詳細分析が必要な場合:* このレポートを Claude Code に貼り付けて「原因分析と施策提案をしてください」と依頼してください。'
      }
    });
  }

  try {
    UrlFetchApp.fetch(webhookUrl, {
      method: 'post',
      contentType: 'application/json',
      payload: JSON.stringify(payload)
    });

    Logger.log('[Slack] レポート送信成功');
  } catch (error) {
    Logger.log(`[Slack Error] ${error.message}`);
  }
}

/**
 * エラー通知
 *
 * @param {string} errorMessage
 */
function sendSlackError(errorMessage) {
  const text = `⚠️ *エラーが発生しました*\n\`\`\`${errorMessage}\`\`\``;
  sendSlackSimple(text);
}
