/**
 * Google Calendar API データ取得・登録スクリプト
 *
 * 使い方:
 *   node google-calendar.js <コマンド> [オプション]
 *
 * コマンド:
 *   list-calendars                カレンダー一覧を取得
 *   list-events                   イベント一覧を取得
 *   create-event                  イベント・タスクを作成
 *
 * 共通オプション:
 *   --calendar-id  カレンダーID (デフォルト: primary)
 *   --key          サービスアカウントJSONキーファイルのパス
 *   --impersonate  委任するユーザーのメールアドレス (Google Workspace の場合)
 *   --output       出力形式 (json, csv) デフォルト: json
 *
 * list-events オプション:
 *   --start        開始日時 YYYY-MM-DD (デフォルト: 今日)
 *   --end          終了日時 YYYY-MM-DD (デフォルト: 開始日の7日後)
 *   --limit        取得件数 (デフォルト: 50, 最大: 2500)
 *   --query        テキスト検索 (イベント名等)
 *
 * create-event オプション:
 *   --summary      イベント名（必須）
 *   --start        開始日時 YYYY-MM-DDTHH:MM または YYYY-MM-DD（終日）
 *   --end          終了日時 YYYY-MM-DDTHH:MM または YYYY-MM-DD
 *   --description  説明
 *   --location     場所
 *   --attendees    参加者メール（カンマ区切り）
 *   --reminder     リマインダー（分、デフォルト: 10）
 *
 * 例:
 *   node google-calendar.js list-calendars --impersonate rikito.nonaka@malna.co.jp
 *   node google-calendar.js list-events --impersonate rikito.nonaka@malna.co.jp --start 2026-02-01 --end 2026-02-28
 *   node google-calendar.js create-event --impersonate rikito.nonaka@malna.co.jp --summary "定例MTG" --start 2026-02-13T10:00 --end 2026-02-13T11:00
 *   node google-calendar.js create-event --impersonate rikito.nonaka@malna.co.jp --summary "締切" --start 2026-02-15
 *
 * 注意:
 *   サービスアカウントで他ユーザーのカレンダーにアクセスするには、
 *   Google Workspace 管理コンソールでドメイン全体の委任を設定し、
 *   --impersonate で対象ユーザーのメールを指定する必要があります。
 */

const { google } = require("googleapis");
const path = require("path");

const DEFAULT_KEY_PATH = path.resolve(
  __dirname,
  "rikito-nonaka-project-600939cd7cb6.json"
);

function parseArgs() {
  const args = process.argv.slice(2);
  const command = args[0] && !args[0].startsWith("--") ? args[0] : null;
  const parsed = { _command: command };
  for (let i = command ? 1 : 0; i < args.length; i++) {
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
使い方: node google-calendar.js <コマンド> [オプション]

コマンド:
  list-calendars   カレンダー一覧を取得
  list-events      イベント一覧を取得
  create-event     イベント・タスクを作成

共通オプション:
  --calendar-id    カレンダーID (デフォルト: primary)
  --key            サービスアカウントJSONキーファイルのパス
  --impersonate    委任するユーザーのメールアドレス
  --output         出力形式 (json, csv) デフォルト: json

list-events オプション:
  --start          開始日 YYYY-MM-DD (デフォルト: 今日)
  --end            終了日 YYYY-MM-DD (デフォルト: 開始日の7日後)
  --limit          取得件数 (デフォルト: 50)
  --query          テキスト検索

create-event オプション:
  --summary        イベント名（必須）
  --start          開始日時 YYYY-MM-DDTHH:MM または YYYY-MM-DD（終日）
  --end            終了日時
  --description    説明
  --location       場所
  --attendees      参加者メール（カンマ区切り）
  --reminder       リマインダー分数（デフォルト: 10）
  `);
}

async function getAuthClient(keyFile, impersonateEmail) {
  if (impersonateEmail) {
    // ドメイン全体の委任を使って特定ユーザーとして認証
    const keyData = require(keyFile);
    const jwtClient = new google.auth.JWT({
      email: keyData.client_email,
      key: keyData.private_key,
      scopes: ["https://www.googleapis.com/auth/calendar"],
      subject: impersonateEmail,
    });
    await jwtClient.authorize();
    return jwtClient;
  }

  return new google.auth.GoogleAuth({
    keyFile,
    scopes: ["https://www.googleapis.com/auth/calendar"],
  });
}

function formatDateTime(dt) {
  if (!dt) return "";
  // dateTime (時刻あり) または date (終日) のどちらかが入る
  return dt.dateTime || dt.date || "";
}

async function listCalendars(calendar, outputFormat) {
  const res = await calendar.calendarList.list();
  const items = res.data.items || [];

  if (items.length === 0) {
    console.log("カレンダーが見つかりませんでした。");
    return;
  }

  if (outputFormat === "csv") {
    console.log("id,summary,accessRole,primary");
    for (const cal of items) {
      console.log(
        `"${(cal.id || "").replace(/"/g, '""')}","${(cal.summary || "").replace(/"/g, '""')}",${cal.accessRole},${cal.primary || false}`
      );
    }
  } else {
    const result = {
      totalCalendars: items.length,
      calendars: items.map((cal) => ({
        id: cal.id,
        summary: cal.summary,
        description: cal.description || "",
        accessRole: cal.accessRole,
        primary: cal.primary || false,
        timeZone: cal.timeZone,
      })),
    };
    console.log(JSON.stringify(result, null, 2));
  }
}

async function listEvents(calendar, args) {
  const calendarId = args["calendar-id"] || "primary";
  const outputFormat = args.output || "json";
  const maxResults = parseInt(args.limit || "50", 10);

  const now = new Date();
  const startDate = args.start
    ? new Date(args.start + "T00:00:00")
    : now;
  const endDate = args.end
    ? new Date(args.end + "T23:59:59")
    : new Date(startDate.getTime() + 7 * 24 * 60 * 60 * 1000);

  const params = {
    calendarId,
    timeMin: startDate.toISOString(),
    timeMax: endDate.toISOString(),
    maxResults,
    singleEvents: true,
    orderBy: "startTime",
  };

  if (args.query) {
    params.q = args.query;
  }

  const res = await calendar.events.list(params);
  const items = res.data.items || [];

  if (items.length === 0) {
    console.log("イベントが見つかりませんでした。");
    return;
  }

  if (outputFormat === "csv") {
    console.log("start,end,summary,location,status");
    for (const event of items) {
      const start = formatDateTime(event.start);
      const end = formatDateTime(event.end);
      console.log(
        `${start},${end},"${(event.summary || "").replace(/"/g, '""')}","${(event.location || "").replace(/"/g, '""')}",${event.status}`
      );
    }
  } else {
    const result = {
      calendarId,
      period: {
        start: startDate.toISOString().split("T")[0],
        end: endDate.toISOString().split("T")[0],
      },
      totalEvents: items.length,
      events: items.map((event) => ({
        id: event.id,
        summary: event.summary || "",
        start: formatDateTime(event.start),
        end: formatDateTime(event.end),
        location: event.location || "",
        description: event.description || "",
        status: event.status,
        organizer: event.organizer ? event.organizer.email : "",
        attendees: (event.attendees || []).map((a) => ({
          email: a.email,
          responseStatus: a.responseStatus,
        })),
      })),
    };
    console.log(JSON.stringify(result, null, 2));
  }
}

async function createEvent(calendar, args) {
  if (!args.summary) {
    console.error("エラー: --summary（イベント名）は必須です。");
    process.exit(1);
  }

  const calendarId = args["calendar-id"] || "primary";

  const event = {
    summary: args.summary,
    description: args.description || "",
    location: args.location || "",
    start: {},
    end: {},
  };

  // 時刻付き or 終日イベント
  if (args.start && args.start.includes("T")) {
    event.start = {
      dateTime: new Date(args.start).toISOString(),
      timeZone: "Asia/Tokyo",
    };
    const endTime = args.end
      ? new Date(args.end)
      : new Date(new Date(args.start).getTime() + 60 * 60 * 1000);
    event.end = {
      dateTime: endTime.toISOString(),
      timeZone: "Asia/Tokyo",
    };
  } else if (args.start) {
    event.start = { date: args.start };
    event.end = { date: args.end || args.start };
  } else {
    console.error("エラー: --start（開始日時）は必須です。");
    process.exit(1);
  }

  if (args.attendees) {
    event.attendees = args.attendees
      .split(",")
      .map((e) => ({ email: e.trim() }));
  }

  if (args.reminder) {
    event.reminders = {
      useDefault: false,
      overrides: [{ method: "popup", minutes: parseInt(args.reminder, 10) }],
    };
  }

  const res = await calendar.events.insert({
    calendarId,
    requestBody: event,
    sendUpdates: args.attendees ? "all" : "none",
  });

  console.log(
    JSON.stringify(
      {
        status: "created",
        eventId: res.data.id,
        htmlLink: res.data.htmlLink,
        summary: res.data.summary,
        start: formatDateTime(res.data.start),
        end: formatDateTime(res.data.end),
      },
      null,
      2
    )
  );
}

async function main() {
  const args = parseArgs();

  if (args.help || !args._command) {
    printUsage();
    process.exit(args.help ? 0 : 1);
  }

  const keyFile = args.key || DEFAULT_KEY_PATH;
  const outputFormat = args.output || "json";

  try {
    const auth = await getAuthClient(keyFile, args.impersonate);
    const calendar = google.calendar({ version: "v3", auth });

    switch (args._command) {
      case "list-calendars":
        await listCalendars(calendar, outputFormat);
        break;
      case "list-events":
        await listEvents(calendar, args);
        break;
      case "create-event":
        await createEvent(calendar, args);
        break;
      default:
        console.error(`不明なコマンド: ${args._command}`);
        printUsage();
        process.exit(1);
    }
  } catch (err) {
    if (err.message && err.message.includes("unauthorized_client")) {
      console.error(
        "エラー: ドメイン全体の委任が設定されていません。\n" +
          "Google Workspace 管理コンソールで以下を設定してください:\n" +
          "  クライアント ID: 105996297510236551527\n" +
          "  スコープ: https://www.googleapis.com/auth/calendar"
      );
    } else {
      console.error("エラー:", err.message);
      if (err.response) {
        console.error("詳細:", JSON.stringify(err.response.data, null, 2));
      }
    }
    process.exit(1);
  }
}

main();
