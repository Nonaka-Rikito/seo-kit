/**
 * ActionProposer.gs — 仮説→施策マッピング + 優先度スコアリング
 *
 * HypothesisEngine が生成した仮説に基づき、具体的な施策を提案する。
 * 各施策に優先度と工数を付与し、費用対効果スコアで並べ替える。
 */

/**
 * 仮説→施策マッピングテーブル
 *
 * priority: 高=3, 中=2, 低=1
 * effort:   低=1, 中=2, 高=3
 */
const ACTION_MAP = {
  RANKING_LOSS: [
    { title: 'コンテンツリライト', detail: '検索意図に合わせた見出し構成の見直し、情報の更新、網羅性の強化', priority: '中', effort: '高' },
    { title: '内部リンク強化', detail: '関連記事からの内部リンクを追加し、ページ評価を底上げ', priority: '中', effort: '低' }
  ],
  RANKING_GAIN: [
    { title: '成功要因の横展開', detail: '順位改善の要因を分析し、類似ページにも同様の最適化を適用', priority: '中', effort: '中' }
  ],
  CTR_DROP: [
    { title: 'タイトル・メタディスクリプション見直し', detail: 'AI Overview との差別化を意識した、クリックしたくなるタイトルへ変更', priority: '高', effort: '低' },
    { title: '構造化データ追加', detail: 'FAQ・HowTo等の構造化データでリッチリザルト表示を狙う', priority: '中', effort: '中' }
  ],
  QUERY_LOSS: [
    { title: '失ったクエリのセクション強化', detail: 'クリック減少したクエリに直接答えるセクションを追加・強化', priority: '高', effort: '中' },
    { title: '関連記事からの内部リンク追加', detail: '失ったクエリに関連する記事から内部リンクを設置', priority: '中', effort: '低' }
  ],
  NEW_QUERY: [
    { title: '新規クエリ向けセクション追加', detail: '新たに流入しているクエリに対応するコンテンツセクションを拡充', priority: '中', effort: '中' }
  ],
  BOUNCE_SPIKE: [
    { title: 'コンテンツ冒頭の改善', detail: '記事冒頭で検索意図に即座に答える構成に変更（結論ファースト）', priority: '高', effort: '中' },
    { title: '目次・CTA配置の見直し', detail: 'ユーザーが求める情報にたどり着きやすいナビゲーションを設置', priority: '中', effort: '低' }
  ],
  SEASONAL: [
    { title: '経過観察', detail: '季節的な変動のため、対応は不要。次の該当シーズンまで経過観察', priority: '低', effort: '低' }
  ],
  CTA_POSITIVE: [
    { title: '成功パターンを他ページに横展開', detail: '効果のあったCTAデザイン・配置を同カテゴリの他ページにも適用', priority: '中', effort: '中' }
  ],
  CTA_NEGATIVE: [
    { title: '旧CTAに差し戻し', detail: '数値が悪化しているため、前回のCTAバナーに一旦戻す', priority: '高', effort: '低' },
    { title: '別デザインでA/Bテスト', detail: '差し戻し後、新しい別デザインで再度テストを実施', priority: '中', effort: '中' }
  ],
  IMAGE_SEARCH: [
    { title: '画像alt・ファイル名の最適化', detail: '主要キーワードを含むalt属性と説明的なファイル名に変更', priority: '中', effort: '低' }
  ]
};

/**
 * 仮説配列から施策提案を生成
 *
 * @param {Array<Object>} hypotheses - generateHypotheses() の出力
 * @param {Object} pageData - ページデータ（将来的なカスタマイズ用）
 * @return {Array<Object>} 施策配列（スコア降順）
 *   [{ title, detail, priority, effort, score, sourceRuleId }, ...]
 */
function proposeActions(hypotheses, pageData) {
  const actions = [];
  const seenTitles = {};

  hypotheses.forEach(h => {
    const templates = ACTION_MAP[h.ruleId];
    if (!templates) return;

    templates.forEach(template => {
      // 同じ施策タイトルが複数仮説から重複提案されるのを防ぐ
      if (seenTitles[template.title]) return;
      seenTitles[template.title] = true;

      const score = calculateActionScore(template.priority, template.effort);

      actions.push({
        title: template.title,
        detail: template.detail,
        priority: template.priority,
        effort: template.effort,
        score: score,
        sourceRuleId: h.ruleId
      });
    });
  });

  // スコア降順（費用対効果が高い順）
  actions.sort((a, b) => b.score - a.score);

  Logger.log(`[ActionProposer] ${actions.length} 件の施策を提案`);
  return actions;
}

/**
 * 費用対効果スコアを計算
 *
 * @param {string} priority - '高' | '中' | '低'
 * @param {string} effort - '低' | '中' | '高'
 * @return {number} スコア（priority数値 / effort数値）
 */
function calculateActionScore(priority, effort) {
  const priorityMap = { '高': 3, '中': 2, '低': 1 };
  const effortMap = { '低': 1, '中': 2, '高': 3 };

  const p = priorityMap[priority] || 1;
  const e = effortMap[effort] || 1;

  return p / e;
}
