import { createCommandHandler } from '../lib/command-handler.js';

export function register(app) {
  app.command('/seo-measure', createCommandHandler({
    label: '変更効果測定',
    requireArg: true,
    argHint: 'イベントIDを指定してください。例: `/seo-measure evt-001`',
    buildPrompt: (eventId) => [
      'あなたは /measure-change コマンドを実行します。',
      '`.claude/commands/measure-change.md` の手順に従って実行してください。',
      '',
      `イベントID: ${eventId}`,
    ].join('\n'),
  }));
}
