/**
 * Google Drive 同期スクリプト（MTG 議事録の自動取得）
 *
 * 使い方:
 *   node google-drive-sync.js --impersonate <メールアドレス> [オプション]
 *
 * 必須:
 *   --impersonate  委任するユーザーのメールアドレス
 *
 * オプション:
 *   --folder-id    Google Drive フォルダ ID（デフォルト: マイドライブ全体）
 *   --query        ファイル名フィルタ（例: "議事録", "transcript"）
 *   --full-sync    前回同期時刻を無視して全ファイルを取得
 *   --days         取得対象の日数（full-sync時、デフォルト: 30）
 *   --output-dir   出力先ディレクトリ
 *   --key          サービスアカウントJSONキーファイルのパス
 *   --output       ログ出力形式 (json, text) デフォルト: text
 *
 * 例:
 *   node google-drive-sync.js --impersonate rikito.nonaka@malna.co.jp
 *   node google-drive-sync.js --impersonate rikito.nonaka@malna.co.jp --query "議事録" --full-sync
 *   node google-drive-sync.js --impersonate rikito.nonaka@malna.co.jp --folder-id 1ABC... --days 7
 */

const { google } = require("googleapis");
const path = require("path");
const fs = require("fs");

const DEFAULT_KEY_PATH = path.resolve(
  __dirname,
  "rikito-nonaka-project-600939cd7cb6.json"
);

const DEFAULT_OUTPUT_DIR = path.resolve(
  __dirname,
  "../../raw-data/mtg-transcripts"
);

const STATE_FILE = path.resolve(__dirname, ".drive-sync-state.json");

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
使い方: node google-drive-sync.js --impersonate <メールアドレス> [オプション]

必須:
  --impersonate  委任するユーザーのメールアドレス

オプション:
  --folder-id    Google Drive フォルダ ID (デフォルト: マイドライブ全体)
  --query        ファイル名フィルタ (例: "議事録")
  --full-sync    前回同期時刻を無視して全ファイルを取得
  --days         full-sync 時の対象日数 (デフォルト: 30)
  --output-dir   出力先ディレクトリ
  --key          サービスアカウントJSONキーファイルのパス
  --output       ログ出力形式 (json, text) デフォルト: text
  `);
}

function loadState() {
  try {
    if (fs.existsSync(STATE_FILE)) {
      return JSON.parse(fs.readFileSync(STATE_FILE, "utf-8"));
    }
  } catch (e) {
    // 読み込み失敗時は初期状態
  }
  return { lastSyncTime: null };
}

function saveState(lastSyncTime) {
  fs.writeFileSync(
    STATE_FILE,
    JSON.stringify({ lastSyncTime, updatedAt: new Date().toISOString() }, null, 2),
    "utf-8"
  );
}

async function getAuthClient(keyFile, impersonateEmail) {
  const keyData = require(keyFile);
  const jwtClient = new google.auth.JWT({
    email: keyData.client_email,
    key: keyData.private_key,
    scopes: ["https://www.googleapis.com/auth/drive.readonly"],
    subject: impersonateEmail,
  });
  await jwtClient.authorize();
  return jwtClient;
}

async function withRetry(fn, maxRetries = 3) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await fn();
    } catch (err) {
      if (i === maxRetries - 1) throw err;
      const delay = Math.pow(2, i) * 1000;
      console.log(`  リトライ中... (${i + 1}/${maxRetries}, ${delay}ms待機)`);
      await new Promise((r) => setTimeout(r, delay));
    }
  }
}

async function findFiles(drive, options) {
  const { folderId, query, sinceTime } = options;
  const conditions = [];

  conditions.push(
    "(mimeType='application/vnd.google-apps.document' or mimeType='text/plain' or mimeType='application/pdf')"
  );
  conditions.push("trashed=false");

  if (folderId && folderId !== "root") {
    conditions.push(`'${folderId}' in parents`);
  }

  if (sinceTime) {
    conditions.push(`modifiedTime > '${sinceTime}'`);
  }

  if (query) {
    conditions.push(`name contains '${query}'`);
  }

  const q = conditions.join(" and ");
  const allFiles = [];
  let pageToken = null;

  do {
    const res = await withRetry(() =>
      drive.files.list({
        q,
        fields: "nextPageToken, files(id, name, mimeType, modifiedTime, size)",
        pageSize: 100,
        orderBy: "modifiedTime desc",
        pageToken,
      })
    );
    allFiles.push(...(res.data.files || []));
    pageToken = res.data.nextPageToken;
  } while (pageToken);

  return allFiles;
}

function sanitizeFileName(name) {
  return name.replace(/[<>:"/\\|?*]/g, "_").replace(/\s+/g, " ").trim();
}

async function downloadFile(drive, file, outputDir) {
  const dateStr = new Date(file.modifiedTime).toISOString().split("T")[0];
  const baseName = sanitizeFileName(file.name);
  const ext =
    file.mimeType === "application/vnd.google-apps.document" ? ".txt" : "";
  const fileName = `${baseName}_${dateStr}${ext}`;
  const filePath = path.join(outputDir, fileName);

  let content;

  if (file.mimeType === "application/vnd.google-apps.document") {
    const res = await withRetry(() =>
      drive.files.export({ fileId: file.id, mimeType: "text/plain" })
    );
    content = res.data;
  } else {
    const res = await withRetry(() =>
      drive.files.get(
        { fileId: file.id, alt: "media" },
        { responseType: "arraybuffer" }
      )
    );
    content = Buffer.from(res.data);
  }

  fs.writeFileSync(
    filePath,
    content,
    typeof content === "string" ? "utf-8" : undefined
  );
  return { fileName, filePath, size: Buffer.byteLength(content) };
}

async function main() {
  const args = parseArgs();

  if (args.help || !args.impersonate) {
    printUsage();
    process.exit(args.help ? 0 : 1);
  }

  const keyFile = args.key || DEFAULT_KEY_PATH;
  const outputDir = args["output-dir"] || DEFAULT_OUTPUT_DIR;
  const folderId = args["folder-id"] || "root";
  const isFullSync = args["full-sync"] === true;
  const days = parseInt(args.days || "30", 10);
  const outputFormat = args.output || "text";

  if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
  }

  const state = loadState();
  let sinceTime;

  if (isFullSync || !state.lastSyncTime) {
    const since = new Date();
    since.setDate(since.getDate() - days);
    sinceTime = since.toISOString();
  } else {
    sinceTime = state.lastSyncTime;
  }

  const syncStartTime = new Date().toISOString();

  try {
    if (outputFormat === "text") {
      console.log(`=== Google Drive 同期 ===`);
      console.log(`対象ユーザー: ${args.impersonate}`);
      console.log(`同期対象: ${sinceTime} 以降の更新`);
      console.log(`出力先: ${outputDir}`);
      console.log("");
    }

    const auth = await getAuthClient(keyFile, args.impersonate);
    const drive = google.drive({ version: "v3", auth });

    const files = await findFiles(drive, { folderId, query: args.query, sinceTime });

    if (files.length === 0) {
      const msg = "新しいファイルはありませんでした。";
      if (outputFormat === "json") {
        console.log(JSON.stringify({ status: "no_updates", message: msg }));
      } else {
        console.log(msg);
      }
      saveState(syncStartTime);
      return;
    }

    if (outputFormat === "text") {
      console.log(`${files.length} 件のファイルが見つかりました。ダウンロード中...`);
      console.log("");
    }

    const results = [];
    const errors = [];

    for (let i = 0; i < files.length; i++) {
      const file = files[i];
      try {
        const result = await downloadFile(drive, file, outputDir);
        results.push({ ...result, originalName: file.name, id: file.id });
        if (outputFormat === "text") {
          console.log(`  [${i + 1}/${files.length}] ${result.fileName}`);
        }
      } catch (err) {
        errors.push({ fileName: file.name, error: err.message });
        if (outputFormat === "text") {
          console.log(
            `  [${i + 1}/${files.length}] エラー: ${file.name} - ${err.message}`
          );
        }
      }
    }

    saveState(syncStartTime);

    if (outputFormat === "json") {
      console.log(
        JSON.stringify(
          {
            status: "completed",
            syncTime: syncStartTime,
            totalFound: files.length,
            downloaded: results.length,
            failed: errors.length,
            files: results,
            errors,
          },
          null,
          2
        )
      );
    } else {
      console.log("");
      console.log(`=== 同期完了 ===`);
      console.log(`ダウンロード: ${results.length}/${files.length} 件`);
      if (errors.length > 0) {
        console.log(`エラー: ${errors.length} 件`);
      }
    }
  } catch (err) {
    if (err.message && err.message.includes("unauthorized_client")) {
      console.error(
        "エラー: ドメイン全体の委任が設定されていません。\n" +
          "Google Workspace 管理コンソールで以下を設定してください:\n" +
          "  クライアント ID: 105996297510236551527\n" +
          "  スコープ: https://www.googleapis.com/auth/drive.readonly"
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
