import { createCommandHandler } from '../lib/command-handler.js';

export function register(app) {
  app.command('/seo-dashboard', createCommandHandler({
    label: '月次エグゼクティブダッシュボード',
    buildPrompt: () => [
      'あなたは /executive-dashboard コマンドを実行します。',
      '`.claude/commands/executive-dashboard.md` の手順に従って実行してください。',
      '',
      '【重要: 出力ルール】',
      'output/ への保存と同時に、レポートの全文を標準出力してください。',
      'MDファイルに書き込む内容と完全に同一の全文を標準出力すること。サマリーのみ・要約のみの出力は不可。',
      '',
      '【重要: 根拠明記ルール】',
      '分析・判断・提案には必ず「定量データ（ソースレポート名+数値）」または「参照ソースURL」を付記すること。根拠なしの記述は禁止。',
    ].join('\n'),
  }));
}
