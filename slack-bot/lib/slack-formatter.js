const MAX_SLACK_LENGTH = 3000;

/**
 * Markdown → Slack mrkdwn 変換
 */
export function markdownToSlack(text) {
  if (!text) return '';

  let result = text;

  // テーブルをコードブロックに変換
  result = convertTables(result);

  // 見出し: # Heading → *Heading*
  result = result.replace(/^#{1,3}\s+(.+)$/gm, '*$1*');

  // 太字: **text** → *text*
  result = result.replace(/\*\*(.+?)\*\*/g, '*$1*');

  // リンク: [text](url) → <url|text>
  result = result.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<$2|$1>');

  return result;
}

/**
 * Markdownテーブルを ``` コードブロックで囲む
 */
function convertTables(text) {
  const lines = text.split('\n');
  const result = [];
  let inTable = false;

  for (const line of lines) {
    const trimmed = line.trim();
    const isTableRow = /^\|.+\|$/.test(trimmed);
    const isSeparator = /^\|[-:\s|]+\|$/.test(trimmed);

    if (isTableRow || isSeparator) {
      if (!inTable) {
        result.push('```');
        inTable = true;
      }
      result.push(line);
    } else {
      if (inTable) {
        result.push('```');
        inTable = false;
      }
      result.push(line);
    }
  }
  if (inTable) result.push('```');

  return result.join('\n');
}

/**
 * Slackメッセージ長制限で分割
 * セクション境界 > 改行 > 強制分割 の優先度
 */
export function splitMessage(text) {
  if (text.length <= MAX_SLACK_LENGTH) return [text];

  const chunks = [];
  let remaining = text;

  while (remaining.length > 0) {
    if (remaining.length <= MAX_SLACK_LENGTH) {
      chunks.push(remaining);
      break;
    }

    const region = remaining.substring(0, MAX_SLACK_LENGTH);

    // セクション境界（--- or 見出し）で分割
    let splitAt = region.lastIndexOf('\n---\n');
    if (splitAt < MAX_SLACK_LENGTH * 0.3) {
      splitAt = region.lastIndexOf('\n*');
    }
    // 改行で分割
    if (splitAt < MAX_SLACK_LENGTH * 0.3) {
      splitAt = region.lastIndexOf('\n');
    }
    // 強制分割
    if (splitAt < MAX_SLACK_LENGTH * 0.3) {
      splitAt = MAX_SLACK_LENGTH;
    }

    chunks.push(remaining.substring(0, splitAt));
    remaining = remaining.substring(splitAt).trimStart();
  }

  return chunks;
}
