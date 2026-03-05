/**
 * MonitorConfig.gs — 自動モニタリング専用設定
 *
 * 既存 Config.gs（バナー計測用）とは独立。
 * 追加コスト: なし（GAS + GA4/GSC API のみ使用）
 */

const MONITOR_CONFIG = {
  // === 変動検出しきい値 ===
  SESSION_CHANGE_THRESHOLD: 0.20,     // セッション数 20% 以上の変動で検出
  MIN_SESSIONS: 10,                   // 最低セッション数（ノイズ除外）
  MAX_FLAGGED_PAGES: 20,              // 1回の分析対象ページ上限

  // === 期間設定 ===
  CURRENT_WEEK_DAYS: 7,               // 直近 7 日間
  GSC_DELAY_DAYS: 3,                  // GSC データ遅延バッファ（日）
  GSC_QUERY_LIMIT: 10,                // ページ当たり上位クエリ数

  // === サイト情報 ===
  SITE_DOMAIN: 'jo-katsu.com',
  SITE_URL: 'https://jo-katsu.com',

  // === 仮説エンジン設定 ===
  HYPOTHESIS_THRESHOLDS: {
    RANKING_CHANGE: 1.5,        // 順位変動しきい値（ポイント）
    CTR_DROP_RATE: 0.20,        // CTR低下率 20%
    CTR_POSITION_STABLE: 1.0,   // 「順位横ばい」の範囲（ポイント）
    QUERY_CLICK_DROP: 0.50,     // クエリクリック減少率 50%
    NEW_QUERY_MIN_CLICKS: 5,    // 新規クエリ最低クリック数
    BOUNCE_SPIKE_PT: 0.10,      // 直帰率急増しきい値（10pt）
    IMAGE_SEARCH_CHANGE: 0.50   // 画像検索変動 50%
  },

  // === 季節性パターン（jo-katsu.com 就活サイト用） ===
  SEASONAL_PATTERNS: [
    { pathRegex: '(intern|campus|recruit)', peakMonths: [1,2,3,5,6], offMonths: [8,9,11,12] },
    { pathRegex: 'manner', peakMonths: [2,3,4], offMonths: [7,8,9] }
  ],

  // === スプレッドシート シート名 ===
  SHEET_MONITOR_WEEKLY: '週次モニタリング',
  SHEET_MONITOR_FLAGGED: 'フラグ付きページ',
  SHEET_QUEUE: '施策キュー',

  // === フェーズ管理キー（ScriptProperties） ===
  PHASE_KEY: 'MONITOR_CURRENT_PHASE',
  RUN_ID_KEY: 'MONITOR_RUN_ID'
};

/**
 * モニタリング設定値を取得
 * ScriptProperties → MONITOR_CONFIG のフォールバック
 */
function getMonitorConfig(key) {
  const prop = PropertiesService.getScriptProperties().getProperty(key);
  if (prop) {
    try {
      return JSON.parse(prop);
    } catch (e) {
      return prop;
    }
  }
  return MONITOR_CONFIG[key];
}
