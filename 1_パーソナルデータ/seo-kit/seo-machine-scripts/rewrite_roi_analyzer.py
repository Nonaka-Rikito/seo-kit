#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
リライト費用対効果分析ツール
GSC + GA4 データから最適なリライト候補記事を算出
"""
import json
import math
from typing import Dict, List, Tuple

# GSCデータ (サンプル - 実際のデータに差し替えてください)
gsc_data = {
    'https://example-media.com/blog/article-001/': {'clicks': 2500, 'impressions': 40000, 'ctr': 6.25, 'position': 4.2},
    'https://example-media.com/blog/article-002/': {'clicks': 1600, 'impressions': 60000, 'ctr': 2.67, 'position': 3.9},
    'https://example-media.com/blog/article-003/': {'clicks': 1500, 'impressions': 20000, 'ctr': 7.50, 'position': 4.5},
    'https://example-media.com/blog/article-004/': {'clicks': 1400, 'impressions': 200000, 'ctr': 0.70, 'position': 8.0},
    'https://example-media.com/blog/article-005/': {'clicks': 1300, 'impressions': 13000, 'ctr': 10.00, 'position': 5.5},
    'https://example-media.com/blog/article-006/': {'clicks': 1200, 'impressions': 25000, 'ctr': 4.80, 'position': 3.2},
    'https://example-media.com/blog/article-007/': {'clicks': 1000, 'impressions': 5000, 'ctr': 20.00, 'position': 4.8},
    'https://example-media.com/blog/article-008/': {'clicks': 900, 'impressions': 20000, 'ctr': 4.50, 'position': 5.0},
    'https://example-media.com/blog/article-009/': {'clicks': 800, 'impressions': 70000, 'ctr': 1.14, 'position': 3.5},
    'https://example-media.com/blog/article-010/': {'clicks': 700, 'impressions': 10000, 'ctr': 7.00, 'position': 6.0},
}

# GSC期間比較データ（サンプル）
gsc_compare_data = {
    'https://example-media.com/blog/article-004/': {'change_clicks': 680, 'change_pct': 95.0, 'pos_delta': -0.5},
    'https://example-media.com/blog/article-005/': {'change_clicks': -400, 'change_pct': -23.0, 'pos_delta': -0.1},
    'https://example-media.com/blog/article-006/': {'change_clicks': 390, 'change_pct': 42.0, 'pos_delta': 0.8},
    'https://example-media.com/blog/article-001/': {'change_clicks': -340, 'change_pct': -12.0, 'pos_delta': -0.2},
    'https://example-media.com/blog/article-009/': {'change_clicks': 350, 'change_pct': 55.0, 'pos_delta': 1.0},
}

# GA4データ（サンプル）
ga4_data = {
    '/blog/article-001/': {'current': 3800, 'previous': 4100, 'change_pct': -7.3},
    '/blog/article-002/': {'current': 1700, 'previous': 1500, 'change_pct': 13.3},
    '/blog/article-003/': {'current': 2000, 'previous': 2100, 'change_pct': -4.8},
    '/blog/article-004/': {'current': 1500, 'previous': 900, 'change_pct': 66.7},
    '/blog/article-005/': {'current': 1800, 'previous': 2300, 'change_pct': -21.7},
    '/blog/article-006/': {'current': 1900, 'previous': 1400, 'change_pct': 35.7},
    '/blog/article-007/': {'current': 1200, 'previous': 1100, 'change_pct': 9.1},
    '/blog/article-008/': {'current': 1000, 'previous': 1100, 'change_pct': -9.1},
    '/blog/article-009/': {'current': 1400, 'previous': 950, 'change_pct': 47.4},
    '/blog/article-010/': {'current': 900, 'previous': 700, 'change_pct': 28.6},
}

def normalize_url(gsc_url: str) -> str:
    """GSCのURLからGA4のパス形式に変換"""
    if gsc_url.startswith('https://example-media.com'):
        return gsc_url.replace('https://example-media.com', '')
    return gsc_url

def calculate_expected_ctr(position: float) -> float:
    """順位に対する期待CTR（業界平均）を計算"""
    ctr_map = {
        1: 28.0, 2: 15.0, 3: 11.0, 4: 8.0, 5: 7.0,
        6: 5.0, 7: 4.0, 8: 3.5, 9: 3.0, 10: 2.5,
        11: 2.0, 12: 1.8, 13: 1.6, 14: 1.4, 15: 1.2
    }

    if position <= 1:
        return ctr_map[1]
    elif position >= 15:
        return ctr_map[15]
    else:
        # 線形補間
        lower_pos = int(position)
        upper_pos = lower_pos + 1
        if lower_pos in ctr_map and upper_pos in ctr_map:
            ratio = position - lower_pos
            return ctr_map[lower_pos] * (1 - ratio) + ctr_map[upper_pos] * ratio
        elif lower_pos in ctr_map:
            return ctr_map[lower_pos]
        else:
            return 1.0

def calculate_rewrite_roi_score(url: str, gsc_data: dict, ga4_data: dict, gsc_compare: dict) -> dict:
    """リライト費用対効果スコアを計算"""

    # URL正規化
    path = normalize_url(url)

    # データ取得
    gsc = gsc_data.get(url, {})
    ga4 = ga4_data.get(path, {})
    compare = gsc_compare.get(url, {})

    if not gsc:
        return None

    clicks = gsc.get('clicks', 0)
    impressions = gsc.get('impressions', 0)
    ctr = gsc.get('ctr', 0) / 100  # パーセントからレートに変換
    position = gsc.get('position', 20)
    sessions = ga4.get('current', 0)

    # リライト対象外条件
    if position < 3 or position > 15:  # 3位以上または15位以下は対象外
        return None
    if impressions < 1000:  # 月間1000インプレッション未満は対象外
        return None

    # スコア要素計算

    # 1. 順位改善可能性 (25%) - 3-15位で上位ほど高スコア
    position_score = max(0, (15 - position) / 12 * 100)

    # 2. インプレッション規模 (20%) - ログスケールで正規化
    impression_score = min(100, math.log10(impressions) * 25)

    # 3. セッション規模 (15%)
    session_score = min(100, sessions / 50)

    # 4. CTR改善余地 (20%)
    expected_ctr = calculate_expected_ctr(position) / 100
    ctr_gap = max(0, expected_ctr - ctr)
    ctr_score = min(100, ctr_gap * 1000)

    # 5. 順位トレンド (10%) - 最近下がっているほど改善余地大
    pos_delta = compare.get('pos_delta', 0)
    trend_score = max(0, min(100, -pos_delta * 20 + 50))

    # 6. セッション安定性 (10%) - 大きな変動がない方が良い
    ga4_change = ga4.get('change_pct', 0)
    stability_score = max(0, 100 - abs(ga4_change) * 2)

    # 重み付き合計スコア
    total_score = (
        position_score * 0.25 +
        impression_score * 0.20 +
        session_score * 0.15 +
        ctr_score * 0.20 +
        trend_score * 0.10 +
        stability_score * 0.10
    )

    # 期待効果計算
    target_position = max(3, position - 2)  # 2ランクアップ目標
    target_ctr = calculate_expected_ctr(target_position) / 100
    expected_click_increase = impressions * (target_ctr - ctr)
    estimated_hours = 4.0  # 平均リライト時間
    roi_index = expected_click_increase / estimated_hours if estimated_hours > 0 else 0

    return {
        'url': url,
        'path': path,
        'total_score': round(total_score, 1),
        'position': position,
        'clicks': clicks,
        'impressions': impressions,
        'ctr': round(ctr * 100, 2),
        'expected_ctr': round(expected_ctr * 100, 2),
        'sessions': sessions,
        'ga4_change_pct': ga4_change,
        'expected_click_increase': round(expected_click_increase),
        'estimated_hours': estimated_hours,
        'roi_index': round(roi_index, 1),
        'scores': {
            'position': round(position_score, 1),
            'impression': round(impression_score, 1),
            'session': round(session_score, 1),
            'ctr_gap': round(ctr_score, 1),
            'trend': round(trend_score, 1),
            'stability': round(stability_score, 1)
        }
    }

def main():
    """メイン処理"""
    results = []

    # 全URLでROI分析実行
    all_urls = set(gsc_data.keys())

    for url in all_urls:
        score_data = calculate_rewrite_roi_score(url, gsc_data, ga4_data, gsc_compare_data)
        if score_data:
            results.append(score_data)

    # スコア順でソート
    results.sort(key=lambda x: x['total_score'], reverse=True)

    # Top20を出力
    print("# リライト費用対効果 Top20 分析結果")
    print("=" * 80)
    print()
    print("| # | URL | スコア | 順位 | セッション | CTR | 期待効果 | ROI指数 |")
    print("|---|-----|--------|------|-----------|-----|----------|---------|")

    for i, result in enumerate(results[:20], 1):
        url_short = result['path'].replace('/blog/', '').replace('/', '')[:10]
        print(f"| {i:2d} | {url_short:10s} | {result['total_score']:6.1f} | {result['position']:4.1f} | {result['sessions']:5d} | {result['ctr']:4.1f}% | +{result['expected_click_increase']:4d} | {result['roi_index']:5.1f} |")

    print()
    print("## 詳細分析（Top5）")
    print("=" * 80)

    for i, result in enumerate(results[:5], 1):
        print(f"\n### {i}位: {result['url']}")
        print(f"- **総合スコア**: {result['total_score']:.1f}/100")
        print(f"- **現在の順位**: {result['position']:.1f}位")
        print(f"- **月間インプレッション**: {result['impressions']:,}")
        print(f"- **現在のCTR**: {result['ctr']:.2f}% (期待値: {result['expected_ctr']:.2f}%)")
        print(f"- **現在のセッション**: {result['sessions']:,} (前期比: {result['ga4_change_pct']:+.1f}%)")
        print(f"- **期待クリック増**: +{result['expected_click_increase']:,} clicks/月")
        print(f"- **推定作業時間**: {result['estimated_hours']:.1f}時間")
        print(f"- **ROI指数**: {result['roi_index']:.1f} (クリック増/時間)")
        print(f"- **スコア内訳**:")
        for key, value in result['scores'].items():
            print(f"  - {key}: {value:.1f}")

    # 結果をJSONで保存
    with open('rewrite_roi_analysis.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\n詳細結果を rewrite_roi_analysis.json に保存しました（{len(results)}件）")

    return results[:20]

if __name__ == "__main__":
    top20 = main()
