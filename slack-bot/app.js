import pkg from '@slack/bolt';
const { App } = pkg;
import 'dotenv/config';
import { stopCurrentProcess } from './lib/claude-runner.js';
import { register as registerLogChange } from './commands/log-change.js';
import { register as registerCvReport } from './commands/cv-report.js';
import { register as registerOrganicTop100 } from './commands/organic-top100.js';
import { register as registerWeeklyReport } from './commands/weekly-report.js';
import { register as registerVerifyData } from './commands/verify-data.js';
import { register as registerMeasureChange } from './commands/measure-change.js';
import { register as registerExecutiveDashboard } from './commands/executive-dashboard.js';
import { register as registerSeoAnalytics } from './commands/seo-analytics.js';

// --- Slack Bolt 初期化 (Socket Mode) ---
const app = new App({
  token: process.env.SLACK_BOT_TOKEN,
  signingSecret: process.env.SLACK_SIGNING_SECRET,
  socketMode: true,
  appToken: process.env.SLACK_APP_TOKEN,
  clientOptions: {
    pingPongLoopIntervalMS: 30000,
    serverPingTimeoutMS: 15000,
  },
});

// --- ユーザー認可ミドルウェア ---
const allowedUsers = (process.env.SLACK_ALLOWED_USER_IDS || '')
  .split(',')
  .map(s => s.trim())
  .filter(Boolean);

if (allowedUsers.length > 0) {
  app.use(async ({ next, body }) => {
    const userId = body?.user_id || body?.user?.id || body?.event?.user;
    if (userId && !allowedUsers.includes(userId)) {
      return; // 無許可ユーザーは無視
    }
    await next();
  });
}

// --- コマンド登録 ---
registerLogChange(app);
registerCvReport(app);
registerOrganicTop100(app);
registerWeeklyReport(app);
registerVerifyData(app);
registerMeasureChange(app);
registerExecutiveDashboard(app);
registerSeoAnalytics(app);

// /seo-stop: 実行中のClaude処理を停止
app.command('/seo-stop', async ({ ack, respond }) => {
  await ack();
  const stopped = stopCurrentProcess();
  await respond({
    response_type: 'in_channel',
    text: stopped ? '処理を停止しました。' : '現在実行中の処理はありません。',
  });
});

// --- グレースフルシャットダウン ---
function shutdown() {
  console.log('シャットダウン中...');
  stopCurrentProcess();
  process.exit(0);
}
process.on('SIGINT', shutdown);
process.on('SIGTERM', shutdown);

// --- 起動 ---
(async () => {
  process.on('unhandledRejection', (error) => {
    console.error('[FATAL] Unhandled rejection:', error);
  });

  if (!process.env.SLACK_BOT_TOKEN) {
    console.error('SLACK_BOT_TOKEN が .env に設定されていません');
    process.exit(1);
  }
  if (!process.env.SLACK_APP_TOKEN) {
    console.error('SLACK_APP_TOKEN が .env に設定されていません');
    process.exit(1);
  }

  await app.start();
  console.log('SEO Machine Slack Bot 起動完了');
  console.log(`コマンド: /seo-log, /seo-cv, /seo-top100, /seo-weekly, /seo-verify, /seo-measure, /seo-dashboard, /seo-analytics, /seo-stop`);
})();
