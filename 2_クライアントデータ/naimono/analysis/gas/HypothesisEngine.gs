/**
 * HypothesisEngine.gs — ルールベース因果仮説生成エンジン
 *
 * GA4/GSC の数値変動パターンからルールマッチングで仮説を生成する。
 * Claude API 不要（追加コスト0円）。
 *
 * 10ルール:
 *   RANKING_LOSS, RANKING_GAIN, CTR_DROP, QUERY_LOSS, NEW_QUERY,
 *   BOUNCE_SPIKE, SEASONAL, CTA_POSITIVE, CTA_NEGATIVE, IMAGE_SEARCH
 */

/**
 * メイン関数: データを受け取り、該当する仮説を全て返す
 *
 * @param {Object} pageData - ページデータ
 *   { pagePath, sessionChangeRate, currentGA4, previousGA4,
 *     currentGSC, previousGSC, currentImageSearch, previousImageSearch,
 *     queryChanges }
 * @param {string} context - 'monitoring' | 'banner_change'
 * @return {Array<Object>} 仮説配列 [{ ruleId, confidence, text, evidence }, ...]
 */
function generateHypotheses(pageData, context) {
  const hypotheses = [];

  // 共通ルール（monitoring / banner_change 両方で実行）
  const rankingResult = checkRankingChange(pageData);
  if (rankingResult) hypotheses.push(rankingResult);

  const ctrResult = checkCTRDrop(pageData);
  if (ctrResult) hypotheses.push(ctrResult);

  const queryResults = checkQueryChanges(pageData);
  hypotheses.push(...queryResults);

  const bounceResult = checkBounceSpike(pageData);
  if (bounceResult) hypotheses.push(bounceResult);

  const seasonalResult = checkSeasonalPattern(pageData);
  if (seasonalResult) hypotheses.push(seasonalResult);

  const imageResult = checkImageSearch(pageData);
  if (imageResult) hypotheses.push(imageResult);

  // banner_change 専用ルール
  if (context === 'banner_change') {
    const ctaResult = checkCTAEffect(pageData);
    if (ctaResult) hypotheses.push(ctaResult);
  }

  // 確信度の高い順にソート
  const confidenceOrder = { high: 3, medium: 2, low: 1 };
  hypotheses.sort((a, b) => (confidenceOrder[b.confidence] || 0) - (confidenceOrder[a.confidence] || 0));

  Logger.log(`[Hypothesis] ${pageData.pagePath}: ${hypotheses.length} 件の仮説を生成`);
  return hypotheses;
}

// ========================================
// 個別ルール関数
// ========================================

/**
 * 順位変動チェック（RANKING_LOSS / RANKING_GAIN）
 */
function checkRankingChange(pageData) {
  const threshold = getMonitorConfig('HYPOTHESIS_THRESHOLDS').RANKING_CHANGE;
  const cGSC = pageData.currentGSC || {};
  const pGSC = pageData.previousGSC || {};

  if (!pGSC.position || !cGSC.position) return null;

  const positionDelta = cGSC.position - pGSC.position;

  // 順位悪化（数値が大きくなる = 順位が下がる）
  if (positionDelta >= threshold) {
    return {
      ruleId: 'RANKING_LOSS',
      confidence: positionDelta >= 3 ? 'high' : 'medium',
      text: '検索順位の下落によるトラフィック減少の可能性',
      evidence: `平均順位: ${pGSC.position.toFixed(1)} → ${cGSC.position.toFixed(1)} (${positionDelta >= 0 ? '+' : ''}${positionDelta.toFixed(1)})`
    };
  }

  // 順位改善（数値が小さくなる = 順位が上がる）
  if (positionDelta <= -threshold) {
    return {
      ruleId: 'RANKING_GAIN',
      confidence: positionDelta <= -3 ? 'high' : 'medium',
      text: '検索順位の改善によるトラフィック増加の可能性',
      evidence: `平均順位: ${pGSC.position.toFixed(1)} → ${cGSC.position.toFixed(1)} (${positionDelta.toFixed(1)})`
    };
  }

  return null;
}

/**
 * CTR低下チェック（CTR_DROP）
 * 順位はほぼ横ばいなのにCTRが下がっている → SERP表示の変化（AI Overview等）
 */
function checkCTRDrop(pageData) {
  const thresholds = getMonitorConfig('HYPOTHESIS_THRESHOLDS');
  const cGSC = pageData.currentGSC || {};
  const pGSC = pageData.previousGSC || {};

  if (!pGSC.ctr || pGSC.ctr === 0) return null;

  const ctrChangeRate = (cGSC.ctr - pGSC.ctr) / pGSC.ctr;
  const positionDelta = Math.abs((cGSC.position || 0) - (pGSC.position || 0));

  // CTRが大きく低下 & 順位はほぼ横ばい
  if (ctrChangeRate <= -thresholds.CTR_DROP_RATE && positionDelta <= thresholds.CTR_POSITION_STABLE) {
    return {
      ruleId: 'CTR_DROP',
      confidence: ctrChangeRate <= -0.4 ? 'high' : 'medium',
      text: 'SERP表示の変化（AI Overview・リッチリザルト等）によるCTR低下の可能性',
      evidence: `CTR: ${(pGSC.ctr * 100).toFixed(2)}% → ${(cGSC.ctr * 100).toFixed(2)}% (${(ctrChangeRate * 100).toFixed(1)}%) / 順位変動: ${positionDelta.toFixed(1)}pt`
    };
  }

  return null;
}

/**
 * クエリ変動チェック（QUERY_LOSS / NEW_QUERY）
 */
function checkQueryChanges(pageData) {
  const thresholds = getMonitorConfig('HYPOTHESIS_THRESHOLDS');
  const queryChanges = pageData.queryChanges || [];
  const results = [];

  queryChanges.forEach(q => {
    // クエリ消失: 主要クエリのクリックが大幅減少
    if (!q.isNew && q.previousClicks > 0) {
      const dropRate = (q.currentClicks - q.previousClicks) / q.previousClicks;
      if (dropRate <= -thresholds.QUERY_CLICK_DROP && q.previousClicks >= 3) {
        results.push({
          ruleId: 'QUERY_LOSS',
          confidence: dropRate <= -0.8 ? 'high' : 'medium',
          text: `主要検索クエリ「${q.query}」でのクリック減少`,
          evidence: `クリック: ${q.previousClicks} → ${q.currentClicks} / 順位: ${(q.previousPosition || 0).toFixed(1)} → ${(q.currentPosition || 0).toFixed(1)}`
        });
      }
    }

    // 新規クエリ発見
    if (q.isNew && q.currentClicks >= thresholds.NEW_QUERY_MIN_CLICKS) {
      results.push({
        ruleId: 'NEW_QUERY',
        confidence: q.currentClicks >= 10 ? 'high' : 'medium',
        text: `新規クエリ「${q.query}」からの流入開始`,
        evidence: `クリック: 0 → ${q.currentClicks} / 順位: ${(q.currentPosition || 0).toFixed(1)}`
      });
    }
  });

  return results;
}

/**
 * 直帰率急増チェック（BOUNCE_SPIKE）
 */
function checkBounceSpike(pageData) {
  const threshold = getMonitorConfig('HYPOTHESIS_THRESHOLDS').BOUNCE_SPIKE_PT;
  const cGA4 = pageData.currentGA4 || {};
  const pGA4 = pageData.previousGA4 || {};

  if (pGA4.bounceRate === undefined || cGA4.bounceRate === undefined) return null;

  const bounceDelta = cGA4.bounceRate - pGA4.bounceRate;

  if (bounceDelta >= threshold) {
    return {
      ruleId: 'BOUNCE_SPIKE',
      confidence: bounceDelta >= 0.20 ? 'high' : 'medium',
      text: 'コンテンツとユーザー検索意図のミスマッチの可能性',
      evidence: `直帰率: ${(pGA4.bounceRate * 100).toFixed(1)}% → ${(cGA4.bounceRate * 100).toFixed(1)}% (+${(bounceDelta * 100).toFixed(1)}pt)`
    };
  }

  return null;
}

/**
 * 季節性パターンチェック（SEASONAL）
 */
function checkSeasonalPattern(pageData) {
  const patterns = getMonitorConfig('SEASONAL_PATTERNS');
  const currentMonth = new Date().getMonth() + 1;  // 1-12
  const pagePath = pageData.pagePath || '';
  const changeRate = pageData.sessionChangeRate || 0;

  for (const pattern of patterns) {
    const regex = new RegExp(pattern.pathRegex);
    if (!regex.test(pagePath)) continue;

    // オフシーズンで減少 → 季節変動
    if (pattern.offMonths.indexOf(currentMonth) !== -1 && changeRate < -0.15) {
      return {
        ruleId: 'SEASONAL',
        confidence: 'medium',
        text: '就活シーズンに連動した季節的なトラフィック減少の可能性',
        evidence: `${currentMonth}月はオフシーズン / セッション変化: ${(changeRate * 100).toFixed(1)}%`
      };
    }

    // ピークシーズンで増加 → 季節変動
    if (pattern.peakMonths.indexOf(currentMonth) !== -1 && changeRate > 0.15) {
      return {
        ruleId: 'SEASONAL',
        confidence: 'medium',
        text: '就活シーズンに連動した季節的なトラフィック増加の可能性',
        evidence: `${currentMonth}月はピークシーズン / セッション変化: +${(changeRate * 100).toFixed(1)}%`
      };
    }
  }

  return null;
}

/**
 * CTA効果チェック（CTA_POSITIVE / CTA_NEGATIVE）— banner_change 専用
 */
function checkCTAEffect(pageData) {
  const changeRate = pageData.sessionChangeRate || 0;
  const cGA4 = pageData.currentGA4 || {};
  const pGA4 = pageData.previousGA4 || {};

  // キーイベント（CV）の変化を重視
  const cvBefore = pGA4.keyEvents || 0;
  const cvAfter = cGA4.keyEvents || 0;
  const cvChange = cvBefore > 0 ? (cvAfter - cvBefore) / cvBefore : (cvAfter > 0 ? 1 : 0);

  // エンゲージメント率の変化
  const engDelta = (cGA4.engagementRate || 0) - (pGA4.engagementRate || 0);

  // 複合スコア: セッション変化 + CV変化 + エンゲージメント変化
  const compositeScore = changeRate * 0.3 + cvChange * 0.5 + engDelta * 0.2;

  if (compositeScore >= 0.05) {
    return {
      ruleId: 'CTA_POSITIVE',
      confidence: compositeScore >= 0.15 ? 'high' : 'medium',
      text: 'CTA変更による正の効果が見られます',
      evidence: `セッション: ${(changeRate * 100).toFixed(1)}% / CV: ${cvBefore}→${cvAfter} / エンゲージメント: ${(engDelta * 100).toFixed(1)}pt`
    };
  }

  if (compositeScore <= -0.05) {
    return {
      ruleId: 'CTA_NEGATIVE',
      confidence: compositeScore <= -0.15 ? 'high' : 'medium',
      text: 'CTA変更による負の効果の可能性。旧バナーへの差し戻しを検討してください',
      evidence: `セッション: ${(changeRate * 100).toFixed(1)}% / CV: ${cvBefore}→${cvAfter} / エンゲージメント: ${(engDelta * 100).toFixed(1)}pt`
    };
  }

  return null;
}

/**
 * 画像検索変動チェック（IMAGE_SEARCH）
 */
function checkImageSearch(pageData) {
  const threshold = getMonitorConfig('HYPOTHESIS_THRESHOLDS').IMAGE_SEARCH_CHANGE;
  const cImg = pageData.currentImageSearch || {};
  const pImg = pageData.previousImageSearch || {};

  const prevClicks = pImg.imageClicks || 0;
  const currClicks = cImg.imageClicks || 0;

  if (prevClicks === 0 && currClicks === 0) return null;

  let changeRate;
  if (prevClicks === 0) {
    changeRate = currClicks >= 3 ? 1.0 : 0;
  } else {
    changeRate = (currClicks - prevClicks) / prevClicks;
  }

  if (Math.abs(changeRate) >= threshold) {
    const direction = changeRate > 0 ? '増加' : '減少';
    return {
      ruleId: 'IMAGE_SEARCH',
      confidence: Math.abs(changeRate) >= 1.0 ? 'high' : 'medium',
      text: `画像検索からのトラフィック${direction}`,
      evidence: `画像検索クリック: ${prevClicks} → ${currClicks} (${(changeRate * 100).toFixed(1)}%)`
    };
  }

  return null;
}
