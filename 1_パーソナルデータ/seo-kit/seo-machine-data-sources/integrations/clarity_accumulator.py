"""
Clarity Data Accumulator

Clarity MCPの制約を回避するためのデータ蓄積ジョブ。
毎日6リクエストを実行し、JSONファイルに保存して履歴を蓄積する。

制約:
- 1日10リクエストまで
- 直近1-3日のデータのみ
- 1リクエスト最大3ディメンション

対策:
- 毎日6リクエスト（4リクエストはオンデマンド用に温存）
- data/clarity/YYYY-MM-DD/ にJSON保存
"""

import os
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional


class ClarityAccumulator:
    """Clarityデータの日次蓄積"""

    DAILY_QUERIES = [
        {
            'name': 'device_sessions',
            'description': 'デバイス別セッション・エンゲージメント',
            'dimensions': ['DeviceType'],
        },
        {
            'name': 'page_traffic',
            'description': 'ページ別トラフィック',
            'dimensions': ['URL'],
        },
        {
            'name': 'scroll_depth',
            'description': 'ページ別スクロールデプス',
            'dimensions': ['URL'],
        },
        {
            'name': 'click_issues',
            'description': 'Dead Click / Rage Click検出',
            'dimensions': ['URL', 'DeviceType'],
        },
        {
            'name': 'js_errors',
            'description': 'JavaScriptエラー検出',
            'dimensions': ['URL'],
        },
        {
            'name': 'source_quality',
            'description': '流入元別セッション品質',
            'dimensions': ['Channel', 'Source'],
        },
    ]

    def __init__(self, data_dir: Optional[str] = None):
        self.data_dir = Path(data_dir or os.path.join(
            os.path.dirname(__file__), '..', '..', 'data', 'clarity'
        ))
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def save_snapshot(self, date: str, query_name: str, data: Any) -> str:
        """日次スナップショットをJSONに保存"""
        day_dir = self.data_dir / date
        day_dir.mkdir(parents=True, exist_ok=True)

        file_path = day_dir / f'{query_name}.json'
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump({
                'date': date,
                'query': query_name,
                'fetched_at': datetime.now().isoformat(),
                'data': data,
            }, f, ensure_ascii=False, indent=2)

        return str(file_path)

    def load_snapshot(self, date: str, query_name: str) -> Optional[Dict]:
        """保存済みスナップショットを読み込み"""
        file_path = self.data_dir / date / f'{query_name}.json'
        if not file_path.exists():
            return None

        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def load_historical(self, query_name: str, days: int = 30) -> List[Dict]:
        """過去N日分のデータを時系列で読み込み"""
        results = []
        today = datetime.now()

        for i in range(days):
            date = (today - timedelta(days=i)).strftime('%Y-%m-%d')
            data = self.load_snapshot(date, query_name)
            if data:
                results.append(data)

        return sorted(results, key=lambda x: x.get('date', ''))

    def get_available_dates(self) -> List[str]:
        """蓄積済みの日付一覧を取得"""
        if not self.data_dir.exists():
            return []

        dates = []
        for item in self.data_dir.iterdir():
            if item.is_dir() and len(item.name) == 10:  # YYYY-MM-DD format
                dates.append(item.name)

        return sorted(dates)

    def get_daily_summary(self, date: str) -> Dict[str, Any]:
        """指定日のデータ概要を取得"""
        day_dir = self.data_dir / date
        if not day_dir.exists():
            return {'date': date, 'available': False}

        queries = {}
        for f in day_dir.glob('*.json'):
            queries[f.stem] = True

        return {
            'date': date,
            'available': True,
            'queries_collected': list(queries.keys()),
            'total_queries': len(queries),
        }

    def generate_trend_report(self, query_name: str, days: int = 14) -> Dict[str, Any]:
        """指定クエリの過去N日間トレンドレポートを生成"""
        historical = self.load_historical(query_name, days)

        if not historical:
            return {'error': f'{query_name}のデータが見つかりません'}

        return {
            'query': query_name,
            'period': f'過去{days}日間',
            'data_points': len(historical),
            'first_date': historical[0].get('date') if historical else None,
            'last_date': historical[-1].get('date') if historical else None,
            'snapshots': historical,
        }
