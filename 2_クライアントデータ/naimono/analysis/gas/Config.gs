/**
 * Config.gs — 設定・定数
 *
 * ここだけ書き換えれば全体が動く。
 * GAS エディタの「プロジェクトの設定」→「スクリプトプロパティ」でも管理可能。
 */

const CONFIG = {
  // === GA4 ===
  GA4_PROPERTY_ID: 'XXXXXXXXX',  // GA4 プロパティ ID（数字のみ）

  // === Google Search Console ===
  GSC_SITE_URL: 'https://example.com/',  // GSC に登録しているサイトURL（末尾スラッシュ注意）
  // sc-domain: 形式の場合は 'sc-domain:example.com'

  // === スプレッドシート ===
  SPREADSHEET_ID: 'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX',

  // シート名
  SHEET_LOG:       '変更ログ',
  SHEET_DATA:      'データ',

  // === Slack ===
  SLACK_WEBHOOK_URL: 'https://hooks.slack.com/services/XXXXX/XXXXX/XXXXX',

  // === 比較期間（日数） ===
  BEFORE_DAYS: 14,       // 変更前: 何日分のデータを取るか
  AFTER_DAYS:  14,       // 変更後: 何日分のデータを取るか
  GSC_DELAY_BUFFER: 3,   // GSC データ遅延バッファ（日）
  REPORT_DELAY_MS: 17 * 24 * 60 * 60 * 1000,  // AFTER_DAYS + GSC_DELAY_BUFFER 日後にレポート実行

  // === 判定しきい値 ===
  VERDICT_IMPROVED_THRESHOLD:  0.05,   // +5% 以上で「改善」
  VERDICT_DEGRADED_THRESHOLD: -0.05,   // -5% 以下で「悪化」

  // === 計測指標の重み（スクロール指標を除外した12指標版） ===
  // 重み付きスコアの計算に使用（合計100%）
  METRIC_WEIGHTS: {
    // Tier 1: トラフィック指標（50%）
    sessions: 0.20,           // セッション数
    ctr: 0.30,                // CTR（GSC）

    // Tier 2: エンゲージメント指標（30%）
    avgSessionDuration: 0.10, // 平均セッション時間
    engagementRate: 0.10,     // エンゲージメント率
    bounceRate: 0.10,         // 直帰率

    // Tier 3: コンバージョン指標（20%）
    keyEvents: 0.20            // キーイベント数（旧conversions）
  },

  // === その他の監視指標（重みなし） ===
  // レポートに表示するが、判定には使用しない
  MONITORING_METRICS: [
    'pageviews',     // ページビュー数
    'users',         // ユーザー数
    'newUsers',      // 新規ユーザー数
    'clicks',        // クリック数（GSC）
    'impressions',   // 表示回数（GSC）
    'position'       // 平均掲載順位（GSC）
  ]
};

/**
 * スクリプトプロパティから設定値を取得するヘルパー。
 * GAS エディタのスクリプトプロパティに設定があればそちらを優先。
 */
function getConfig(key) {
  const prop = PropertiesService.getScriptProperties().getProperty(key);
  if (prop) {
    try {
      return JSON.parse(prop);
    } catch (e) {
      return prop;
    }
  }
  return CONFIG[key];
}
