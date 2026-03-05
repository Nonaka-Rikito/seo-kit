/**
 * Google Analytics (GA4) Data API データ取得スクリプト
 *
 * 使い方:
 *   node google-analytics.js --property <プロパティID> --start <開始日> --end <終了日> [オプション]
 *
 * 必須:
 *   --property    GA4 プロパティ ID (例: 123456789)
 *   --start       開始日 YYYY-MM-DD
 *   --end         終了日 YYYY-MM-DD
 *
 * オプション:
 *   --dimensions   ディメンション (カンマ区切り)
 *   --metrics      メトリクス (カンマ区切り、デフォルト: sessions,activeUsers,screenPageViews)
 *   --limit        取得行数 (デフォルト: 25, 最大: 100000)
 *   --order-by     ソートするメトリクス名 (デフォルト: sessions)
 *   --order-desc   降順ソート (デフォルト: true)
 *   --filter-dim   フィルタするディメンション名
 *   --filter-val   フィルタ値 (部分一致)
 *   --output       出力形式 (json, csv) デフォルト: json
 *   --key          サービスアカウントJSONキーファイルのパス
 *
 * よく使うディメンション:
 *   date, pagePath, pageTitle, sessionSource, sessionMedium,
 *   sessionCampaignName, country, city, deviceCategory, browser,
 *   landingPage, sessionDefaultChannelGroup
 *
 * よく使うメトリクス:
 *   sessions, activeUsers, newUsers, screenPageViews, engagedSessions,
 *   averageSessionDuration, bounceRate, conversions, totalRevenue,
 *   engagementRate, sessionsPerUser, screenPageViewsPerSession
 *
 * 例:
 *   node google-analytics.js --property 123456789 --start 2026-01-01 --end 2026-01-31 --dimensions pagePath --metrics screenPageViews,sessions --limit 50
 *   node google-analytics.js --property 123456789 --start 2026-01-01 --end 2026-01-31 --dimensions sessionSource,sessionMedium --output csv
 *   node google-analytics.js --property 123456789 --start 2026-01-01 --end 2026-01-31 --dimensions pagePath --filter-dim pagePath --filter-val "/blog"
 */

const { google } = require("googleapis");
const path = require("path");

const DEFAULT_KEY_PATH = path.resolve(
  __dirname,
  "../feisty-gasket-487202-k7-992b8b630483.json"
);

function parseArgs() {
  const args = process.argv.slice(2);
  const parsed = {};
  for (let i = 0; i < args.length; i++) {
    if (args[i].startsWith("--")) {
      const key = args[i].slice(2);
      const val = args[i + 1] && !args[i + 1].startsWith("--") ? args[i + 1] : true;
      parsed[key] = val;
      if (val !== true) i++;
    }
  }
  return parsed;
}

function printUsage() {
  console.log(`
使い方: node google-analytics.js --property <ID> --start <YYYY-MM-DD> --end <YYYY-MM-DD> [オプション]

必須:
  --property    GA4 プロパティ ID (数値)
  --start       開始日 (YYYY-MM-DD)
  --end         終了日 (YYYY-MM-DD)

オプション:
  --dimensions   ディメンション (カンマ区切り)
  --metrics      メトリクス (カンマ区切り、デフォルト: sessions,activeUsers,screenPageViews)
  --limit        取得行数 (デフォルト: 25)
  --order-by     ソートするメトリクス名 (デフォルト: sessions)
  --order-desc   降順ソート (デフォルト: true)
  --filter-dim   フィルタするディメンション名
  --filter-val   フィルタ値 (部分一致)
  --output       出力形式 (json, csv) デフォルト: json
  --key          サービスアカウントJSONキーファイルのパス

よく使うディメンション:
  date, pagePath, pageTitle, sessionSource, sessionMedium,
  sessionDefaultChannelGroup, country, city, deviceCategory, landingPage

よく使うメトリクス:
  sessions, activeUsers, newUsers, screenPageViews, engagedSessions,
  averageSessionDuration, bounceRate, engagementRate, conversions
  `);
}

async function main() {
  const args = parseArgs();

  if (args.help || !args.property || !args.start || !args.end) {
    printUsage();
    process.exit(args.help ? 0 : 1);
  }

  const keyFile = args.key || DEFAULT_KEY_PATH;
  const dimensions = args.dimensions ? args.dimensions.split(",") : [];
  const metrics = args.metrics
    ? args.metrics.split(",")
    : ["sessions", "activeUsers", "screenPageViews"];
  const rowLimit = parseInt(args.limit || "25", 10);
  const orderBy = args["order-by"] || metrics[0];
  const orderDesc = args["order-desc"] !== "false";
  const outputFormat = args.output || "json";

  // 認証
  const auth = new google.auth.GoogleAuth({
    keyFile,
    scopes: ["https://www.googleapis.com/auth/analytics.readonly"],
  });

  const analyticsdata = google.analyticsdata({ version: "v1beta", auth });

  // リクエストの構築
  const request = {
    property: `properties/${args.property}`,
    requestBody: {
      dateRanges: [{ startDate: args.start, endDate: args.end }],
      dimensions: dimensions.map((d) => ({ name: d })),
      metrics: metrics.map((m) => ({ name: m })),
      limit: rowLimit,
      orderBys: [
        {
          metric: { metricName: orderBy },
          desc: orderDesc,
        },
      ],
    },
  };

  // ディメンションフィルタ
  if (args["filter-dim"] && args["filter-val"]) {
    request.requestBody.dimensionFilter = {
      filter: {
        fieldName: args["filter-dim"],
        stringFilter: {
          matchType: "CONTAINS",
          value: args["filter-val"],
          caseSensitive: false,
        },
      },
    };
  }

  try {
    const res = await analyticsdata.properties.runReport(request);

    const rows = res.data.rows || [];
    const dimHeaders = (res.data.dimensionHeaders || []).map((h) => h.name);
    const metricHeaders = (res.data.metricHeaders || []).map((h) => h.name);

    if (rows.length === 0) {
      console.log("データが見つかりませんでした。");
      return;
    }

    if (outputFormat === "csv") {
      // CSV 出力
      const header = [...dimHeaders, ...metricHeaders].join(",");
      console.log(header);
      for (const row of rows) {
        const dims = (row.dimensionValues || [])
          .map((v) => `"${(v.value || "").replace(/"/g, '""')}"`)
          .join(",");
        const mets = (row.metricValues || []).map((v) => v.value).join(",");
        const parts = [dims, mets].filter(Boolean);
        console.log(parts.join(","));
      }
    } else {
      // JSON 出力
      const totals = {};
      if (res.data.totals && res.data.totals[0]) {
        res.data.totals[0].metricValues.forEach((v, i) => {
          totals[metricHeaders[i]] = parseFloat(v.value);
        });
      }

      const result = {
        property: args.property,
        period: { start: args.start, end: args.end },
        dimensions: dimHeaders,
        metrics: metricHeaders,
        totals,
        totalRows: rows.length,
        rows: rows.map((row) => {
          const entry = {};
          (row.dimensionValues || []).forEach((v, i) => {
            entry[dimHeaders[i]] = v.value;
          });
          (row.metricValues || []).forEach((v, i) => {
            entry[metricHeaders[i]] = parseFloat(v.value);
          });
          return entry;
        }),
      };
      console.log(JSON.stringify(result, null, 2));
    }
  } catch (err) {
    console.error("エラー:", err.message);
    if (err.response) {
      console.error("詳細:", JSON.stringify(err.response.data, null, 2));
    }
    process.exit(1);
  }
}

main();
