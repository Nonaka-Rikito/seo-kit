import { createCommandHandler } from '../lib/command-handler.js';

export function register(app) {
  app.command('/seo-analytics', createCommandHandler({
    label: 'SEO Analytics分析',
    requireArg: true,
    argHint: '分析したい内容を入力してください。例: `/seo-analytics 今月のCV低下要因を仮説付きで分析`',
    buildPrompt: (requestText) => [
      'あなたは /seo-analytics コマンドを実行します。',
      '以下のユーザー依頼を満たす分析を実行してください。',
      '',
      `依頼内容: ${requestText}`,
      '',
      '実行方針:',
      '- 必要に応じて GSC/GA4/Ahrefs/Clarity のデータを取得して根拠を示す',
      '- 数値は可能な限り検証し、期間と比較対象を明記する',
      '- 重要な示唆は「事実」「解釈」「次アクション」に分けて提示する',
      '- すぐ着手できる優先アクションを3つ以上提示する',
      '',
      'レポート本文を標準出力してください。必要なら output/ への保存も行ってください。',
    ].join('\n'),
  }));
}
