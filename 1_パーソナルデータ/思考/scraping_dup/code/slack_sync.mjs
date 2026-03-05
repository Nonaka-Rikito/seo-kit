import 'dotenv/config';
import { WebClient } from '@slack/web-api';
import { writeFileSync, mkdirSync, existsSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const PROJECT_ROOT = join(__dirname, '..');
const OUTPUT_DIR = join(PROJECT_ROOT, '..', 'slack');

// --- 設定読み込み ---
const token = process.env.SLACK_USER_TOKEN;
const channelNames = (process.env.SLACK_CHANNELS || '').split(',').map(s => s.trim()).filter(Boolean);
const syncDays = parseInt(process.env.SYNC_DAYS || '3', 10);

if (!token || token.includes('ここに')) {
  console.error('エラー: .env ファイルに SLACK_USER_TOKEN を設定してください');
  process.exit(1);
}
if (channelNames.length === 0) {
  console.error('エラー: .env ファイルに SLACK_CHANNELS を設定してください（例: general,random）');
  process.exit(1);
}

const slack = new WebClient(token);

// --- レート制限回避用ディレイ ---
// conversations.replies は Tier 3 (50回/分) → 1.3秒間隔で制限を回避
const REPLY_DELAY_MS = 1300;
const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms));

// --- ユーザー名キャッシュ ---
const userCache = new Map();

async function getUserName(userId) {
  if (userCache.has(userId)) return userCache.get(userId);
  try {
    const res = await slack.users.info({ user: userId });
    const name = res.user.real_name || res.user.name || userId;
    userCache.set(userId, name);
    return name;
  } catch {
    userCache.set(userId, userId);
    return userId;
  }
}

// --- チャンネルID解決 ---
async function resolveChannelIds(names) {
  const resolved = [];

  // まず channels:read スコープでチャンネル一覧取得を試みる
  try {
    const channels = [];
    let cursor;
    do {
      const res = await slack.conversations.list({
        types: 'public_channel,private_channel',
        limit: 200,
        cursor,
      });
      channels.push(...(res.channels || []));
      cursor = res.response_metadata?.next_cursor;
    } while (cursor);

    for (const name of names) {
      const ch = channels.find(c => c.name === name);
      if (ch) {
        resolved.push({ id: ch.id, name: ch.name });
      } else {
        console.warn(`警告: チャンネル「${name}」が見つかりません（スキップ）`);
      }
    }
    return resolved;
  } catch (e) {
    // channels:read スコープがない場合
    if (e.data?.error === 'missing_scope') {
      console.log('注意: channels:read スコープがないため、チャンネルIDを直接指定してください');
      console.log('  .env の SLACK_CHANNELS にチャンネルID（Cから始まる文字列）を設定してください');
      console.log('  例: SLACK_CHANNELS=C01234ABCDE,C05678FGHIJ');
      console.log('');

      // チャンネルIDが直接指定されている場合はそのまま使う
      for (const name of names) {
        if (name.startsWith('C') && name.length > 8) {
          resolved.push({ id: name, name: name });
        }
      }
      if (resolved.length === 0) {
        console.error('エラー: チャンネルIDが指定されていません');
        process.exit(1);
      }
      return resolved;
    }
    throw e;
  }
}

// --- スレッド返信取得 ---
async function fetchThreadReplies(channelId, threadTs) {
  const replies = [];
  let cursor;
  do {
    const res = await slack.conversations.replies({
      channel: channelId,
      ts: threadTs,
      limit: 200,
      cursor,
    });
    replies.push(...(res.messages || []));
    cursor = res.response_metadata?.next_cursor;
  } while (cursor);
  // 最初の要素は親メッセージなので除外
  return replies.slice(1);
}

// --- メッセージ取得（スレッド返信含む） ---
async function fetchMessages(channelId, daysBack) {
  const oldest = Math.floor((Date.now() - daysBack * 24 * 60 * 60 * 1000) / 1000);
  const parentMessages = [];
  let cursor;

  do {
    const res = await slack.conversations.history({
      channel: channelId,
      oldest: String(oldest),
      limit: 200,
      cursor,
    });
    parentMessages.push(...(res.messages || []));
    cursor = res.response_metadata?.next_cursor;
  } while (cursor);

  // スレッド返信を取得して親メッセージに紐づける
  const threaded = parentMessages.filter(m => m.reply_count > 0);
  let threadReplyCount = 0;
  for (let i = 0; i < threaded.length; i++) {
    const msg = threaded[i];
    await sleep(REPLY_DELAY_MS);
    const replies = await fetchThreadReplies(channelId, msg.thread_ts || msg.ts);
    msg._replies = replies;
    threadReplyCount += replies.length;
    if ((i + 1) % 20 === 0) {
      console.log(`  スレッド取得中... ${i + 1}/${threaded.length}`);
    }
  }

  // 古い順にソート
  parentMessages.sort((a, b) => parseFloat(a.ts) - parseFloat(b.ts));

  const totalCount = parentMessages.length + threadReplyCount;
  return { parents: parentMessages, totalCount };
}

// --- Markdown変換（スレッド返信対応） ---
async function toMarkdown(channelName, { parents, totalCount }) {
  const lines = [
    `# Slack: #${channelName}`,
    `> 取得日時: ${new Date().toLocaleString('ja-JP')}  `,
    `> 対象期間: 直近${syncDays}日分  `,
    `> メッセージ数: ${totalCount}件（親: ${parents.length}件 + スレッド返信）`,
    '',
    '---',
    '',
  ];

  for (const msg of parents) {
    const userName = await getUserName(msg.user || 'unknown');
    const time = new Date(parseFloat(msg.ts) * 1000).toLocaleString('ja-JP');
    const text = (msg.text || '').replace(/<@(\w+)>/g, (_, id) => `@${userCache.get(id) || id}`);

    lines.push(`**${userName}** (${time})`);
    lines.push(text);

    // スレッド返信を字下げして表示
    if (msg._replies && msg._replies.length > 0) {
      lines.push('');
      for (const reply of msg._replies) {
        const replyUser = await getUserName(reply.user || 'unknown');
        const replyTime = new Date(parseFloat(reply.ts) * 1000).toLocaleString('ja-JP');
        const replyText = (reply.text || '').replace(/<@(\w+)>/g, (_, id) => `@${userCache.get(id) || id}`);
        lines.push(`> **${replyUser}** (${replyTime})`);
        lines.push(`> ${replyText.replace(/\n/g, '\n> ')}`);
        lines.push('');
      }
    }

    lines.push('');
  }

  return lines.join('\n');
}

// --- メイン ---
async function main() {
  console.log('=== Slack同期開始 ===');
  console.log(`対象チャンネル: ${channelNames.join(', ')}`);
  console.log(`取得期間: 直近${syncDays}日分`);
  console.log('');

  // 出力先ディレクトリ作成
  if (!existsSync(OUTPUT_DIR)) {
    mkdirSync(OUTPUT_DIR, { recursive: true });
  }

  // チャンネルID解決
  const channels = await resolveChannelIds(channelNames);
  console.log(`解決されたチャンネル: ${channels.map(c => `#${c.name}(${c.id})`).join(', ')}`);
  console.log('');

  // 各チャンネルのメッセージ取得＆保存
  for (const ch of channels) {
    console.log(`[#${ch.name}] メッセージ取得中（スレッド返信含む）...`);
    const result = await fetchMessages(ch.id, syncDays);
    console.log(`[#${ch.name}] ${result.totalCount}件のメッセージを取得（親: ${result.parents.length}件 + スレッド返信）`);

    const md = await toMarkdown(ch.name, result);
    const today = new Date().toISOString().split('T')[0];
    const filePath = join(OUTPUT_DIR, `${ch.name}_${today}.md`);
    writeFileSync(filePath, md, 'utf-8');
    console.log(`[#${ch.name}] 保存完了: ${filePath}`);
    console.log('');
  }

  console.log('=== Slack同期完了 ===');
}

main().catch(err => {
  console.error('エラーが発生しました:', err.message);
  process.exit(1);
});
