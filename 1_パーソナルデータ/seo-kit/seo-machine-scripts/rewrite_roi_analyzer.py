#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
リライト費用対効果分析ツール
GSC + GA4 データから最適なリライト候補記事を算出
"""
import json
import math
from typing import Dict, List, Tuple

# GSCデータ (クリック順)
gsc_data = {
    'https://jo-katsu.com/campus/6271/': {'clicks': 2586, 'impressions': 40436, 'ctr': 6.40, 'position': 4.1},
    'https://jo-katsu.com/campus/24216/': {'clicks': 1621, 'impressions': 62491, 'ctr': 2.59, 'position': 3.8},
    'https://jo-katsu.com/campus/6288/': {'clicks': 1557, 'impressions': 19246, 'ctr': 8.09, 'position': 4.2},
    'https://jo-katsu.com/campus/10673/': {'clicks': 1387, 'impressions': 205190, 'ctr': 0.68, 'position': 8.1},
    'https://jo-katsu.com/campus/5423/': {'clicks': 1345, 'impressions': 12966, 'ctr': 10.37, 'position': 5.9},
    'https://jo-katsu.com/campus/6380/': {'clicks': 1323, 'impressions': 27304, 'ctr': 4.85, 'position': 3.1},
    'https://jo-katsu.com/campus/6359/': {'clicks': 1192, 'impressions': 4716, 'ctr': 25.28, 'position': 4.8},
    'https://jo-katsu.com/campus/18292/': {'clicks': 1057, 'impressions': 21124, 'ctr': 5.00, 'position': 4.8},
    'https://jo-katsu.com/campus/6369/': {'clicks': 980, 'impressions': 73094, 'ctr': 1.34, 'position': 3.1},
    'https://jo-katsu.com/campus/9837/': {'clicks': 939, 'impressions': 9631, 'ctr': 9.75, 'position': 6.3},
    'https://jo-katsu.com/campus/10304/': {'clicks': 780, 'impressions': 7762, 'ctr': 10.05, 'position': 11.2},
    'https://jo-katsu.com/campus/1637/': {'clicks': 738, 'impressions': 23592, 'ctr': 3.13, 'position': 7.8},
    'https://jo-katsu.com/campus/6289/': {'clicks': 683, 'impressions': 15398, 'ctr': 4.44, 'position': 4.0},
    'https://jo-katsu.com/campus/23869/': {'clicks': 625, 'impressions': 3543, 'ctr': 17.64, 'position': 6.2},
    'https://jo-katsu.com/campus/1696/': {'clicks': 583, 'impressions': 15050, 'ctr': 3.87, 'position': 13.3},
    'https://jo-katsu.com/campus/4980/': {'clicks': 566, 'impressions': 7502, 'ctr': 7.54, 'position': 6.9},
    'https://jo-katsu.com/campus/37257/': {'clicks': 538, 'impressions': 7471, 'ctr': 7.20, 'position': 3.4},
    'https://jo-katsu.com/campus/11626/': {'clicks': 527, 'impressions': 18045, 'ctr': 2.92, 'position': 4.4},
    'https://jo-katsu.com/campus/23598/': {'clicks': 523, 'impressions': 6518, 'ctr': 8.02, 'position': 5.0},
    'https://jo-katsu.com/campus/13760/': {'clicks': 521, 'impressions': 8738, 'ctr': 5.96, 'position': 5.5},
    'https://jo-katsu.com/campus/37241/': {'clicks': 499, 'impressions': 4726, 'ctr': 10.56, 'position': 4.2},
    'https://jo-katsu.com/campus/10330/': {'clicks': 487, 'impressions': 8844, 'ctr': 5.51, 'position': 4.1},
    'https://jo-katsu.com/campus/5922/': {'clicks': 479, 'impressions': 9293, 'ctr': 5.15, 'position': 6.9},
    'https://jo-katsu.com/campus/12287/': {'clicks': 441, 'impressions': 5526, 'ctr': 7.98, 'position': 5.6},
    'https://jo-katsu.com/campus/25667/': {'clicks': 429, 'impressions': 6262, 'ctr': 6.85, 'position': 4.7},
    'https://jo-katsu.com/campus/15729/': {'clicks': 418, 'impressions': 6590, 'ctr': 6.34, 'position': 4.0},
    'https://jo-katsu.com/campus/6106/': {'clicks': 418, 'impressions': 9279, 'ctr': 4.50, 'position': 4.5},
    'https://jo-katsu.com/campus/6278/': {'clicks': 400, 'impressions': 8953, 'ctr': 4.47, 'position': 4.6},
    'https://jo-katsu.com/campus/37264/': {'clicks': 392, 'impressions': 8323, 'ctr': 4.71, 'position': 5.2},
    'https://jo-katsu.com/campus/5504/': {'clicks': 384, 'impressions': 34778, 'ctr': 1.10, 'position': 3.9},
    'https://jo-katsu.com/campus/10300/': {'clicks': 351, 'impressions': 249026, 'ctr': 0.14, 'position': 1.3},
    'https://jo-katsu.com/campus/37221/': {'clicks': 346, 'impressions': 6262, 'ctr': 5.53, 'position': 3.5},
    'https://jo-katsu.com/campus/9993/': {'clicks': 337, 'impressions': 6805, 'ctr': 4.95, 'position': 6.1},
    'https://jo-katsu.com/campus/6279/': {'clicks': 335, 'impressions': 5996, 'ctr': 5.59, 'position': 6.8},
    'https://jo-katsu.com/campus/10318/': {'clicks': 333, 'impressions': 7961, 'ctr': 4.18, 'position': 6.2},
    'https://jo-katsu.com/campus/37255/': {'clicks': 332, 'impressions': 6004, 'ctr': 5.53, 'position': 3.6},
    'https://jo-katsu.com/campus/26404/': {'clicks': 329, 'impressions': 7039, 'ctr': 4.67, 'position': 6.9},
    'https://jo-katsu.com/campus/23876/': {'clicks': 322, 'impressions': 16211, 'ctr': 1.99, 'position': 2.2},
    'https://jo-katsu.com/campus/16508/': {'clicks': 321, 'impressions': 5022, 'ctr': 6.39, 'position': 6.4},
    'https://jo-katsu.com/campus/24333/': {'clicks': 321, 'impressions': 7058, 'ctr': 4.55, 'position': 4.1},
    'https://jo-katsu.com/campus/25569/': {'clicks': 320, 'impressions': 14626, 'ctr': 2.19, 'position': 2.9},
    'https://jo-katsu.com/campus/6194/': {'clicks': 320, 'impressions': 44036, 'ctr': 0.73, 'position': 3.2},
    'https://jo-katsu.com/campus/20321/': {'clicks': 317, 'impressions': 15615, 'ctr': 2.03, 'position': 2.2},
    'https://jo-katsu.com/campus/26869/': {'clicks': 317, 'impressions': 6448, 'ctr': 4.92, 'position': 4.0},
    'https://jo-katsu.com/campus/18788/': {'clicks': 312, 'impressions': 6684, 'ctr': 4.67, 'position': 5.2},
    'https://jo-katsu.com/campus/13762/': {'clicks': 308, 'impressions': 6827, 'ctr': 4.51, 'position': 7.0},
    'https://jo-katsu.com/campus/15728/': {'clicks': 307, 'impressions': 11746, 'ctr': 2.61, 'position': 4.1},
    'https://jo-katsu.com/campus/6245/': {'clicks': 303, 'impressions': 33798, 'ctr': 0.90, 'position': 8.4},
    'https://jo-katsu.com/campus/10756/': {'clicks': 296, 'impressions': 10294, 'ctr': 2.88, 'position': 4.5},
    'https://jo-katsu.com/campus/10507/': {'clicks': 294, 'impressions': 15369, 'ctr': 1.91, 'position': 5.6},
    'https://jo-katsu.com/campus/24193/': {'clicks': 288, 'impressions': 2847, 'ctr': 10.12, 'position': 4.4}
}

# GSC期間比較データ（変化量順）
gsc_compare_data = {
    'https://jo-katsu.com/campus/10673/': {'change_clicks': 681, 'change_pct': 96.5, 'pos_delta': -0.6},
    'https://jo-katsu.com/campus/10507/': {'change_clicks': -606, 'change_pct': -67.3, 'pos_delta': 1.4},
    'https://jo-katsu.com/campus/5423/': {'change_clicks': -400, 'change_pct': -22.9, 'pos_delta': -0.1},
    'https://jo-katsu.com/campus/6380/': {'change_clicks': 388, 'change_pct': 41.5, 'pos_delta': 0.9},
    'https://jo-katsu.com/campus/25569/': {'change_clicks': -388, 'change_pct': -54.8, 'pos_delta': 0.4},
    'https://jo-katsu.com/campus/6369/': {'change_clicks': 356, 'change_pct': 57.1, 'pos_delta': 0.9},
    'https://jo-katsu.com/campus/6271/': {'change_clicks': -337, 'change_pct': -11.5, 'pos_delta': -0.2},
    'https://jo-katsu.com/campus/10304/': {'change_clicks': 331, 'change_pct': 73.7, 'pos_delta': 6.8},
    'https://jo-katsu.com/campus/23598/': {'change_clicks': 265, 'change_pct': 102.7, 'pos_delta': 2.0},
    'https://jo-katsu.com/campus/37241/': {'change_clicks': 250, 'change_pct': 100.4, 'pos_delta': 0.9},
    'https://jo-katsu.com/campus/1696/': {'change_clicks': 228, 'change_pct': 64.2, 'pos_delta': 1.1},
    'https://jo-katsu.com/campus/24216/': {'change_clicks': 190, 'change_pct': 13.3, 'pos_delta': -0.1},
    'https://jo-katsu.com/campus/9837/': {'change_clicks': 187, 'change_pct': 24.9, 'pos_delta': 1.8},
    'https://jo-katsu.com/campus/25667/': {'change_clicks': 159, 'change_pct': 58.9, 'pos_delta': 1.9},
    'https://jo-katsu.com/campus/37257/': {'change_clicks': 156, 'change_pct': 40.8, 'pos_delta': 0.6},
    'https://jo-katsu.com/campus/6289/': {'change_clicks': -139, 'change_pct': -16.9, 'pos_delta': 0.1},
    'https://jo-katsu.com/campus/6278/': {'change_clicks': -131, 'change_pct': -24.7, 'pos_delta': 0.0},
    'https://jo-katsu.com/campus/6288/': {'change_clicks': -129, 'change_pct': -7.7, 'pos_delta': -0.2},
    'https://jo-katsu.com/campus/37264/': {'change_clicks': 122, 'change_pct': 45.2, 'pos_delta': 0.2},
    'https://jo-katsu.com/campus/12287/': {'change_clicks': 114, 'change_pct': 34.9, 'pos_delta': 0.6}
}

# GA4データ（セッション数）
ga4_data = {
    '/campus/6271/': {'current': 3873, 'previous': 4103, 'change_pct': -5.6},
    '/campus/6288/': {'current': 2084, 'previous': 2128, 'change_pct': -2.1},
    '/campus/6380/': {'current': 1948, 'previous': 1441, 'change_pct': 35.2},
    '/campus/5423/': {'current': 1824, 'previous': 2342, 'change_pct': -22.1},
    '/campus/24216/': {'current': 1689, 'previous': 1535, 'change_pct': 10.0},
    '/campus/18292/': {'current': 1519, 'previous': 1276, 'change_pct': 19.0},
    '/campus/10673/': {'current': 1485, 'previous': 901, 'change_pct': 64.8},
    '/campus/6369/': {'current': 1428, 'previous': 952, 'change_pct': 50.0},
    '/campus/9837/': {'current': 1400, 'previous': 1084, 'change_pct': 29.2},
    '/campus/1637/': {'current': 1314, 'previous': 1255, 'change_pct': 4.7},
    '/campus/6359/': {'current': 1218, 'previous': 1111, 'change_pct': 9.6},
    '/campus/6289/': {'current': 1134, 'previous': 1244, 'change_pct': -8.8},
    '/campus/10330/': {'current': 935, 'previous': 922, 'change_pct': 1.4},
    '/campus/10304/': {'current': 897, 'previous': 509, 'change_pct': 76.2},
    '/campus/11626/': {'current': 891, 'previous': 670, 'change_pct': 33.0},
    '/campus/13760/': {'current': 841, 'previous': 901, 'change_pct': -6.7},
    '/campus/23869/': {'current': 822, 'previous': 818, 'change_pct': 0.5},
    '/campus/1696/': {'current': 733, 'previous': 488, 'change_pct': 50.2},
    '/campus/37257/': {'current': 691, 'previous': 503, 'change_pct': 37.4},
    '/campus/10507/': {'current': 685, 'previous': 1752, 'change_pct': -60.9},
    '/campus/23598/': {'current': 602, 'previous': 357, 'change_pct': 68.6},
    '/campus/37241/': {'current': 590, 'previous': 314, 'change_pct': 87.9},
    '/campus/6278/': {'current': 579, 'previous': 738, 'change_pct': -21.5},
    '/campus/4980/': {'current': 578, 'previous': 497, 'change_pct': 16.3},
    '/campus/15729/': {'current': 551, 'previous': 407, 'change_pct': 35.4},
    '/campus/25569/': {'current': 551, 'previous': 1081, 'change_pct': -49.0},
    '/campus/5922/': {'current': 546, 'previous': 447, 'change_pct': 22.1},
    '/campus/25667/': {'current': 544, 'previous': 352, 'change_pct': 54.5},
    '/campus/5504/': {'current': 517, 'previous': 403, 'change_pct': 28.3},
    '/campus/12287/': {'current': 506, 'previous': 387, 'change_pct': 30.7},
    '/campus/37264/': {'current': 503, 'previous': 326, 'change_pct': 54.3},
    '/campus/37255/': {'current': 501, 'previous': 421, 'change_pct': 19.0},
    '/campus/6106/': {'current': 490, 'previous': 479, 'change_pct': 2.3},
    '/campus/23620/': {'current': 489, 'previous': 422, 'change_pct': 15.9},
    '/campus/23876/': {'current': 475, 'previous': 227, 'change_pct': 109.3},
    '/campus/16508/': {'current': 471, 'previous': 572, 'change_pct': -17.7},
    '/campus/6245/': {'current': 453, 'previous': 596, 'change_pct': -24.0},
    '/campus/37221/': {'current': 431, 'previous': 290, 'change_pct': 48.6},
    '/campus/6279/': {'current': 429, 'previous': 527, 'change_pct': -18.6},
    '/campus/25669/': {'current': 429, 'previous': 458, 'change_pct': -6.3}
}

def normalize_url(gsc_url: str) -> str:
    """GSCのURLからGA4のパス形式に変換"""
    if gsc_url.startswith('https://jo-katsu.com'):
        return gsc_url.replace('https://jo-katsu.com', '')
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
        url_short = result['path'].replace('/campus/', '').replace('/', '')[:10]
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