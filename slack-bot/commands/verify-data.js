import { createCommandHandler } from '../lib/command-handler.js';

export function register(app) {
  app.command('/seo-verify', createCommandHandler({
    label: 'データ検証',
    buildPrompt: (target) => {
      if (target) {
        return [
          'あなたは /verify-data コマンドを実行します。',
          '`.claude/commands/verify-data.md` の手順に従って実行してください。',
          '',
          `検証対象: ${target}`,
        ].join('\n');
      }
      return [
        'あなたは /verify-data コマンドを実行します。',
        '`.claude/commands/verify-data.md` の手順に従って実行してください。',
        '',
        'output/ ディレクトリにある最新のレポートファイルを検証してください。',
      ].join('\n');
    },
  }));
}
