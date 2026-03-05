/**
 * Google Search Console API データ取得スクリプト
 *
 * 使い方:
 *   node google-search-console.js --site <サイトURL> --start <開始日> --end <終了日> [オプション]
 *
 * 必須:
 *   --site        対象サイトURL (例: https://example.com)
 *   --start       開始日 YYYY-MM-DD
 *   --end         終了日 YYYY-MM-DD
 *
 * オプション:
 *   --dimensions   ディメンション (カンマ区切り: query,page,country,device,date)
 *   --limit        取得行数 (デフォルト: 25, 最大: 25000)
 *   --filter-query クエリフィルタ (部分一致)
 *   --filter-page  ページフィルタ (部分一致)
 *   --type         検索タイプ (web, image, video, news, discover, googleNews)
 *   --output       出力形式 (json, csv) デフォルト: json
 *   --key          サービスアカウントJSONキーファイルのパス
 *
 * 例:
 *   node google-search-console.js --site https://example.com --start 2026-01-01 --end 2026-01-31 --dimensions query,page --limit 100
 *   node google-search-console.js --site https://example.com --start 2026-01-01 --end 2026-01-31 --filter-query "SEO" --output csv
 */

const { google } = require("googleapis");
const path = require("path");

// デフォルトのサービスアカウントキーのパス
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
使い方: node google-search-console.js --site <URL> --start <YYYY-MM-DD> --end <YYYY-MM-DD> [オプション]

必須:
  --site        対象サイトURL (例: https://example.com)
  --start       開始日 (YYYY-MM-DD)
  --end         終了日 (YYYY-MM-DD)

オプション:
  --dimensions   ディメンション (カンマ区切り: query,page,country,device,date)
  --limit        取得行数 (デフォルト: 25, 最大: 25000)
  --filter-query クエリフィルタ (部分一致)
  --filter-page  ページフィルタ (部分一致)
  --type         検索タイプ (web, image, video, news, discover, googleNews)
  --output       出力形式 (json, csv) デフォルト: json
  --key          サービスアカウントJSONキーファイルのパス
  `);
}

async function main() {
  const args = parseArgs();

  if (args.help || !args.site || !args.start || !args.end) {
    printUsage();
    process.exit(args.help ? 0 : 1);
  }

  const keyFile = args.key || DEFAULT_KEY_PATH;
  const dimensions = args.dimensions ? args.dimensions.split(",") : ["query"];
  const rowLimit = parseInt(args.limit || "25", 10);
  const searchType = args.type || "web";
  const outputFormat = args.output || "json";

  // 認証
  const auth = new google.auth.GoogleAuth({
    keyFile,
    scopes: ["https://www.googleapis.com/auth/webmasters.readonly"],
  });

  const searchconsole = google.searchconsole({ version: "v1", auth });

  // リクエストボディの構築
  const requestBody = {
    startDate: args.start,
    endDate: args.end,
    dimensions,
    rowLimit,
    type: searchType,
  };

  // フィルタの追加
  const dimensionFilters = [];
  if (args["filter-query"]) {
    dimensionFilters.push({
      dimension: "query",
      operator: "contains",
      expression: args["filter-query"],
    });
  }
  if (args["filter-page"]) {
    dimensionFilters.push({
      dimension: "page",
      operator: "contains",
      expression: args["filter-page"],
    });
  }
  if (dimensionFilters.length > 0) {
    requestBody.dimensionFilterGroups = [{ filters: dimensionFilters }];
  }

  try {
    const res = await searchconsole.searchanalytics.query({
      siteUrl: args.site,
      requestBody,
    });

    const rows = res.data.rows || [];

    if (rows.length === 0) {
      console.log("データが見つかりませんでした。");
      return;
    }

    if (outputFormat === "csv") {
      // CSV 出力
      const header = [...dimensions, "clicks", "impressions", "ctr", "position"].join(",");
      console.log(header);
      for (const row of rows) {
        const dims = row.keys.map((k) => `"${k.replace(/"/g, '""')}"`).join(",");
        console.log(`${dims},${row.clicks},${row.impressions},${row.ctr.toFixed(4)},${row.position.toFixed(1)}`);
      }
    } else {
      // JSON 出力
      const result = {
        site: args.site,
        period: { start: args.start, end: args.end },
        dimensions,
        totalRows: rows.length,
        rows: rows.map((row) => {
          const entry = {};
          dimensions.forEach((dim, i) => {
            entry[dim] = row.keys[i];
          });
          entry.clicks = row.clicks;
          entry.impressions = row.impressions;
          entry.ctr = parseFloat(row.ctr.toFixed(4));
          entry.position = parseFloat(row.position.toFixed(1));
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
