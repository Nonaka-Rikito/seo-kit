import { runClaude } from '../lib/claude-runner.js';
import { markdownToSlack, splitMessage } from '../lib/slack-formatter.js';

export function register(app) {
  // スラッシュコマンド → モーダル表示
  app.command('/seo-log', async ({ ack, body, client }) => {
    await ack();

    await client.views.open({
      trigger_id: body.trigger_id,
      view: {
        type: 'modal',
        callback_id: 'log_change_modal',
        private_metadata: body.channel_id,
        title: { type: 'plain_text', text: 'SEO変更記録' },
        submit: { type: 'plain_text', text: '記録する' },
        close: { type: 'plain_text', text: 'キャンセル' },
        blocks: [
          {
            type: 'input',
            block_id: 'url_block',
            label: { type: 'plain_text', text: '変更した記事のURL' },
            element: {
              type: 'url_text_input',
              action_id: 'url_input',
              placeholder: { type: 'plain_text', text: 'https://example-media.com/campus/26469' },
            },
          },
          {
            type: 'input',
            block_id: 'type_block',
            label: { type: 'plain_text', text: '変更の種類' },
            element: {
              type: 'static_select',
              action_id: 'type_select',
              options: [
                { text: { type: 'plain_text', text: 'CTAバナー' }, value: 'cta_banner' },
                { text: { type: 'plain_text', text: 'タイトル' }, value: 'title' },
                { text: { type: 'plain_text', text: 'メタディスクリプション' }, value: 'meta_description' },
                { text: { type: 'plain_text', text: 'コンテンツ' }, value: 'content' },
                { text: { type: 'plain_text', text: '画像' }, value: 'image' },
                { text: { type: 'plain_text', text: 'レイアウト' }, value: 'layout' },
              ],
            },
          },
          {
            type: 'input',
            block_id: 'desc_block',
            label: { type: 'plain_text', text: '変更内容' },
            element: {
              type: 'plain_text_input',
              action_id: 'desc_input',
              multiline: true,
              placeholder: { type: 'plain_text', text: 'CTAボタンの色を青から赤に変更' },
            },
          },
          {
            type: 'input',
            block_id: 'hypo_block',
            label: { type: 'plain_text', text: '変更の理由/仮説' },
            element: {
              type: 'plain_text_input',
              action_id: 'hypo_input',
              multiline: true,
              placeholder: { type: 'plain_text', text: '赤いCTAの方がクリック率が上がるという仮説' },
            },
            optional: true,
          },
        ],
      },
    });
  });

  // モーダル送信 → Claude CLI実行
  app.view('log_change_modal', async ({ ack, view, client }) => {
    await ack();

    const channelId = view.private_metadata;
    const v = view.state.values;
    const url = v.url_block.url_input.value;
    const changeType = v.type_block.type_select.selected_option.value;
    const description = v.desc_block.desc_input.value;
    const hypothesis = v.hypo_block.hypo_input?.value || '(未記入)';

    let initialTs = null;
    try {
      const initialMsg = await client.chat.postMessage({
        channel: channelId,
        text: `変更記録を処理中...\nURL: ${url}\n種類: ${changeType}`,
      });
      initialTs = initialMsg.ts;
    } catch (e) {
      // チャンネルにボット未参加の場合は進捗更新なしで実行
    }

    const prompt = [
      'あなたは /log-change コマンドを実行します。',
      '`.claude/commands/log-change.md` の手順に従ってください。',
      '',
      'ユーザーから以下の情報が提供されています（質問不要）:',
      `1. 変更した記事のURL: ${url}`,
      `2. 変更の種類: ${changeType}`,
      `3. 変更内容: ${description}`,
      `4. 変更の理由/仮説: ${hypothesis}`,
      '',
      'この情報を使って手順2以降を実行してください。',
    ].join('\n');

    const output = await runClaude(prompt, {
      onProgress: async (text) => {
        if (!initialTs) return;
        try {
          await client.chat.update({ channel: channelId, ts: initialTs, text });
        } catch (e) { /* rate limit */ }
      },
      onError: async (text) => {
        if (initialTs) {
          try {
            await client.chat.update({ channel: channelId, ts: initialTs, text: `変更記録エラー: ${text}` });
            return;
          } catch (e) { /* fall through */ }
        }
        try {
          await client.chat.postMessage({ channel: channelId, text: `変更記録エラー: ${text}` });
        } catch (e) { /* can't reach channel */ }
      },
    });

    if (output === null) return;

    const formatted = markdownToSlack(output || '変更記録完了（出力なし）');
    const chunks = splitMessage(formatted);

    if (initialTs) {
      try {
        await client.chat.update({ channel: channelId, ts: initialTs, text: chunks[0] });
        for (let i = 1; i < chunks.length; i++) {
          await client.chat.postMessage({ channel: channelId, thread_ts: initialTs, text: chunks[i] });
        }
      } catch (e) {
        for (const chunk of chunks) {
          try { await client.chat.postMessage({ channel: channelId, text: chunk }); } catch (_) { /* can't reach channel */ }
        }
      }
    } else {
      for (const chunk of chunks) {
        try {
          await client.chat.postMessage({ channel: channelId, text: chunk });
        } catch (e) { /* can't reach channel */ }
      }
    }
  });
}
