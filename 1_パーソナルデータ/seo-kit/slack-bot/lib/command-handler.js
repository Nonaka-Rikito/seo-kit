import { runClaude } from './claude-runner.js';
import { markdownToSlack, splitMessage } from './slack-formatter.js';

/**
 * 共通のSlashコマンドハンドラを生成
 * @param {object} opts
 * @param {string} opts.label - 表示名（例: "CV指標レポート"）
 * @param {Function} opts.buildPrompt - (text) => string  プロンプト生成
 * @param {boolean} [opts.requireArg] - 引数必須かどうか
 * @param {string} [opts.argHint] - 引数未指定時のエラーメッセージ
 */
export function createCommandHandler({ label, buildPrompt, requireArg, argHint }) {
  return async ({ ack, command, client, respond }) => {
    await ack();

    const channelId = command.channel_id;
    const text = command.text?.trim() || '';
    const respondPublic = async (message) => {
      await respond({
        response_type: 'in_channel',
        text: message,
      });
    };

    // 引数バリデーション
    if (requireArg && !text) {
      await respondPublic(argHint || '引数を指定してください。');
      return;
    }

    // 「処理中」メッセージ — respond() で送信（チャンネル参加不要）
    await respondPublic(`${label}を処理中...`);

    // ボットをチャンネルに招待してもらう試み
    let canPostToChannel = true;
    let initialTs = null;
    try {
      // テスト投稿で確認
      const testMsg = await client.chat.postMessage({
        channel: channelId,
        text: `${label}を処理中...`,
      });
      // 成功したらこのメッセージを進捗更新用に使う
      initialTs = testMsg.ts;
    } catch (e) {
      canPostToChannel = false;
    }

    const prompt = buildPrompt(text);

    const output = await runClaude(prompt, {
      onProgress: async (progressText) => {
        if (!canPostToChannel) return;
        try {
          await client.chat.update({
            channel: channelId,
            ts: initialTs,
            text: progressText,
          });
        } catch (e) { /* rate limit */ }
      },
      onError: async (errText) => {
        if (canPostToChannel) {
          try {
            await client.chat.update({
              channel: channelId,
              ts: initialTs,
              text: `${label} エラー: ${errText}`,
            });
            return;
          } catch (e) { /* fall through */ }
        }
        await respondPublic(`${label} エラー: ${errText}`);
      },
    });

    if (output === null) return;

    if (!output.trim()) {
      if (canPostToChannel) {
        await client.chat.update({ channel: channelId, ts: initialTs, text: `${label} 完了（出力なし）` });
      } else {
        await respondPublic(`${label} 完了（出力なし）`);
      }
      return;
    }

    // Markdown → Slack変換 → 分割投稿
    const formatted = markdownToSlack(output);
    const chunks = splitMessage(formatted);

    if (canPostToChannel) {
      try {
        await client.chat.update({ channel: channelId, ts: initialTs, text: chunks[0] });
        for (let i = 1; i < chunks.length; i++) {
          await client.chat.postMessage({
            channel: channelId,
            thread_ts: initialTs,
            text: chunks[i],
          });
        }
      } catch (e) {
        // chat.update/postMessage 失敗時は respond にフォールバック
        for (const chunk of chunks) {
          try { await respondPublic(chunk); } catch (_) { /* exhausted */ }
        }
      }
    } else {
      for (const chunk of chunks) {
        try { await respondPublic(chunk); } catch (_) { /* exhausted */ }
      }
    }
  };
}
