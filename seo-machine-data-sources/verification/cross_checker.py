"""
Cross Checker

複数データソース間の整合性を検証する2次検証レイヤー。
GSC, GA4, Clarityのデータを突き合わせて矛盾を検出する。
"""

from typing import Dict, Any, List, Optional


class CrossChecker:
    """データソース間のクロスチェック"""

    def check_gsc_vs_ga4(
        self,
        gsc_clicks: int,
        ga4_sessions: int,
        tolerance_ratio: float = 2.0,
    ) -> Dict[str, Any]:
        """GSCクリック数 vs GA4セッション数の整合性

        通常: GSCクリック >= GA4オーガニックセッション * 0.5
        大きなずれ(2倍以上)は警告
        """
        if ga4_sessions == 0 and gsc_clicks == 0:
            return {
                'check': 'gsc_vs_ga4',
                'passed': True,
                'message': '両方ゼロ（データ未取得の可能性）',
            }

        if ga4_sessions == 0:
            ratio = float('inf')
        else:
            ratio = gsc_clicks / ga4_sessions

        is_consistent = 0.3 <= ratio <= tolerance_ratio

        return {
            'check': 'gsc_vs_ga4',
            'passed': is_consistent,
            'gsc_clicks': gsc_clicks,
            'ga4_sessions': ga4_sessions,
            'ratio': round(ratio, 2) if ratio != float('inf') else 'inf',
            'message': 'OK' if is_consistent else
                f'GSCクリック({gsc_clicks})とGA4セッション({ga4_sessions})の比率が異常（{ratio:.1f}x）',
        }

    def check_ahrefs_vs_gsc(
        self,
        ahrefs_position: float,
        gsc_position: float,
        tolerance: float = 5.0,
    ) -> Dict[str, Any]:
        """Ahrefs順位 vs GSC平均順位の照合

        Ahrefsはクロールベースの推定順位、GSCは実測期間平均値のため差異は許容。
        5位以上のずれは警告。
        """
        diff = abs(ahrefs_position - gsc_position)
        is_consistent = diff <= tolerance

        return {
            'check': 'ahrefs_vs_gsc',
            'passed': is_consistent,
            'ahrefs_position': ahrefs_position,
            'gsc_position': gsc_position,
            'difference': round(diff, 1),
            'message': 'OK' if is_consistent else
                f'順位データの不一致: Ahrefs={ahrefs_position} vs GSC={gsc_position}（差{diff:.1f}）',
            'note': 'Ahrefs=クロール推定 / GSC=期間平均 のため±3位程度の差は正常',
        }

    def check_trend_consistency(
        self,
        ga4_trend: str,
        gsc_trend: str,
    ) -> Dict[str, Any]:
        """GA4トレンドとGSCトレンドの方向性一致チェック

        GA4セッション減少 + GSCクリック増加 = 矛盾 → 警告
        """
        contradictions = {
            ('decreasing', 'increasing'): 'GA4セッション減少なのにGSCクリック増加',
            ('increasing', 'decreasing'): 'GA4セッション増加なのにGSCクリック減少',
        }

        key = (ga4_trend, gsc_trend)
        is_consistent = key not in contradictions

        return {
            'check': 'trend_consistency',
            'passed': is_consistent,
            'ga4_trend': ga4_trend,
            'gsc_trend': gsc_trend,
            'message': 'OK' if is_consistent else contradictions.get(key, '不明な矛盾'),
            'note': '短期的なタイムラグによる一時的なずれの場合もあり' if not is_consistent else '',
        }

    def check_clarity_vs_ga4_sessions(
        self,
        clarity_sessions: int,
        ga4_sessions: int,
        tolerance_ratio: float = 1.5,
    ) -> Dict[str, Any]:
        """ClarityセッションとGA4セッションの照合"""
        if ga4_sessions == 0:
            ratio = float('inf') if clarity_sessions > 0 else 1.0
        else:
            ratio = clarity_sessions / ga4_sessions

        is_consistent = 0.5 <= ratio <= tolerance_ratio

        return {
            'check': 'clarity_vs_ga4',
            'passed': is_consistent,
            'clarity_sessions': clarity_sessions,
            'ga4_sessions': ga4_sessions,
            'ratio': round(ratio, 2) if ratio != float('inf') else 'inf',
            'message': 'OK' if is_consistent else
                f'Clarity({clarity_sessions})とGA4({ga4_sessions})のセッション数に乖離',
        }

    def generate_confidence_score(self, check_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """全チェック結果から信頼度スコア(0-100)を算出"""
        if not check_results:
            return {'score': 0, 'level': 'unknown', 'message': 'チェック結果なし'}

        passed = sum(1 for r in check_results if r['passed'])
        total = len(check_results)
        score = round((passed / total) * 100)

        if score >= 90:
            level = 'high'
        elif score >= 70:
            level = 'moderate'
        elif score >= 50:
            level = 'low'
        else:
            level = 'very_low'

        failed = [r for r in check_results if not r['passed']]

        return {
            'score': score,
            'level': level,
            'passed': passed,
            'total': total,
            'failed_checks': failed,
            'message': f'信頼度スコア: {score}/100（{level}）',
        }

    def run_full_cross_check(
        self,
        gsc_data: Optional[Dict] = None,
        ga4_data: Optional[Dict] = None,
        ahrefs_data: Optional[Dict] = None,
        clarity_data: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """全データソースのクロスチェックを実行"""
        results = []

        # GSC vs GA4
        if gsc_data and ga4_data:
            gsc_clicks = gsc_data.get('clicks', 0)
            ga4_sessions = ga4_data.get('organic_sessions', ga4_data.get('sessions', 0))
            results.append(self.check_gsc_vs_ga4(gsc_clicks, ga4_sessions))

            # トレンド一致
            gsc_trend = gsc_data.get('trend')
            ga4_trend = ga4_data.get('trend')
            if gsc_trend and ga4_trend:
                results.append(self.check_trend_consistency(ga4_trend, gsc_trend))

        # Ahrefs vs GSC
        if ahrefs_data and gsc_data:
            ah_pos = ahrefs_data.get('position')
            gsc_pos = gsc_data.get('position')
            if ah_pos and gsc_pos:
                results.append(self.check_ahrefs_vs_gsc(ah_pos, gsc_pos))

        # Clarity vs GA4
        if clarity_data and ga4_data:
            clarity_sessions = clarity_data.get('sessions', 0)
            ga4_sessions = ga4_data.get('sessions', 0)
            if clarity_sessions and ga4_sessions:
                results.append(self.check_clarity_vs_ga4_sessions(clarity_sessions, ga4_sessions))

        confidence = self.generate_confidence_score(results)

        return {
            'checks': results,
            'confidence': confidence,
            'summary': self._build_summary(results, confidence),
        }

    def _build_summary(self, results: List[Dict], confidence: Dict) -> str:
        """人間が読めるサマリーを生成"""
        lines = [f'--- データ信頼度 ---', f'信頼度スコア: {confidence["score"]}/100']

        for r in results:
            status = '[OK]' if r['passed'] else '[WARNING]'
            lines.append(f'  {status} {r["check"]}: {r["message"]}')

        return '\n'.join(lines)
