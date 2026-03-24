"""
Data Verifier

AIが出力する数値を独立して再計算し、矛盾を検出する1次検証レイヤー。
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple


class DataVerifier:
    """SEO分析データの数値検証"""

    # メトリクス別の妥当範囲
    VALID_RANGES = {
        'ctr': (0, 100),              # %
        'position': (1, 200),          # GSC順位
        'impressions': (0, float('inf')),
        'clicks': (0, float('inf')),
        'sessions': (0, float('inf')),
        'bounce_rate': (0, 100),       # %
        'scroll_depth': (0, 100),      # %
        'engagement_time': (0, 3600),  # 秒（1時間上限）
    }

    def verify_percentage_change(
        self,
        before: float,
        after: float,
        claimed_change: float,
        tolerance: float = 0.5,
    ) -> Dict[str, Any]:
        """変化率の独立再計算と検証

        Args:
            before: 変更前の値
            after: 変更後の値
            claimed_change: AIが主張した変化率（%）
            tolerance: 許容誤差（%ポイント）
        """
        if before == 0:
            if after == 0:
                actual_change = 0.0
            else:
                actual_change = float('inf')
        else:
            actual_change = ((after - before) / before) * 100

        diff = abs(actual_change - claimed_change)
        is_valid = diff <= tolerance

        return {
            'check': 'percentage_change',
            'passed': is_valid,
            'before': before,
            'after': after,
            'actual_change': round(actual_change, 2) if actual_change != float('inf') else 'inf',
            'claimed_change': claimed_change,
            'difference': round(diff, 2) if diff != float('inf') else 'inf',
            'message': 'OK' if is_valid else f'変化率の不一致: 実測{actual_change:.2f}% vs 主張{claimed_change:.2f}%',
        }

    def verify_range(self, metric_name: str, value: float) -> Dict[str, Any]:
        """メトリクスの妥当範囲チェック"""
        if metric_name not in self.VALID_RANGES:
            return {
                'check': 'range',
                'passed': True,
                'metric': metric_name,
                'value': value,
                'message': f'未知のメトリクス: {metric_name}（範囲チェックをスキップ）',
            }

        min_val, max_val = self.VALID_RANGES[metric_name]
        is_valid = min_val <= value <= max_val

        return {
            'check': 'range',
            'passed': is_valid,
            'metric': metric_name,
            'value': value,
            'valid_range': (min_val, max_val),
            'message': 'OK' if is_valid else f'{metric_name}={value}は範囲外（{min_val}〜{max_val}）',
        }

    def verify_data_freshness(
        self, data_timestamp: str, max_age_hours: int = 96
    ) -> Dict[str, Any]:
        """データ鮮度チェック（GSCは通常3日遅延）"""
        try:
            ts = datetime.fromisoformat(data_timestamp.replace('Z', '+00:00'))
            now = datetime.now(ts.tzinfo) if ts.tzinfo else datetime.now()
            age = now - ts
            age_hours = age.total_seconds() / 3600

            is_fresh = age_hours <= max_age_hours
            # GSCの3日遅延は正常
            is_normal_delay = 48 <= age_hours <= 96

            return {
                'check': 'freshness',
                'passed': is_fresh,
                'timestamp': data_timestamp,
                'age_hours': round(age_hours, 1),
                'max_age_hours': max_age_hours,
                'is_normal_gsc_delay': is_normal_delay,
                'message': 'OK' if is_fresh else f'データが古い（{age_hours:.0f}時間前）',
            }
        except (ValueError, TypeError) as e:
            return {
                'check': 'freshness',
                'passed': False,
                'message': f'タイムスタンプの解析エラー: {e}',
            }

    def verify_sample_size(
        self, sessions: int, min_sessions: int = 30
    ) -> Dict[str, Any]:
        """統計的信頼性の最低サンプルサイズチェック"""
        is_sufficient = sessions >= min_sessions

        if sessions < 10:
            confidence = 'very_low'
        elif sessions < 30:
            confidence = 'low'
        elif sessions < 100:
            confidence = 'moderate'
        elif sessions < 1000:
            confidence = 'high'
        else:
            confidence = 'very_high'

        return {
            'check': 'sample_size',
            'passed': is_sufficient,
            'sessions': sessions,
            'min_required': min_sessions,
            'confidence': confidence,
            'message': 'OK' if is_sufficient else f'セッション数不足（{sessions}<{min_sessions}）。統計的信頼性が低い。',
        }

    def verify_clicks_vs_impressions(self, clicks: int, impressions: int) -> Dict[str, Any]:
        """クリック数がインプレッション数を超えていないかチェック"""
        is_valid = clicks <= impressions

        return {
            'check': 'clicks_impressions',
            'passed': is_valid,
            'clicks': clicks,
            'impressions': impressions,
            'message': 'OK' if is_valid else f'クリック数({clicks})がインプレッション数({impressions})を超過',
        }

    def run_all_checks(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """渡されたデータに対して全チェックを実行"""
        results = []

        # 範囲チェック
        for metric in ('ctr', 'position', 'impressions', 'clicks', 'sessions', 'bounce_rate'):
            if metric in data:
                results.append(self.verify_range(metric, data[metric]))

        # クリック vs インプレッション
        if 'clicks' in data and 'impressions' in data:
            results.append(self.verify_clicks_vs_impressions(data['clicks'], data['impressions']))

        # サンプルサイズ
        if 'sessions' in data:
            results.append(self.verify_sample_size(data['sessions']))

        # データ鮮度
        if 'timestamp' in data:
            results.append(self.verify_data_freshness(data['timestamp']))

        # 変化率
        if all(k in data for k in ('before', 'after', 'claimed_change')):
            results.append(self.verify_percentage_change(
                data['before'], data['after'], data['claimed_change']
            ))

        passed = sum(1 for r in results if r['passed'])
        total = len(results)
        failed = [r for r in results if not r['passed']]

        return {
            'total_checks': total,
            'passed': passed,
            'failed': total - passed,
            'all_passed': total == passed,
            'results': results,
            'failed_checks': failed,
            'confidence_score': round((passed / total * 100) if total > 0 else 0, 1),
        }
