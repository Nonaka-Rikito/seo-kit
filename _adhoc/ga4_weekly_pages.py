"""
GA4 ページ別×週次PVデータ取得 - jo-katsu.com
直近8週間のページ別PV内訳を週単位で集計（週ごとにAPIコール）
"""

import json
import sys
import os
from datetime import datetime, timedelta
from collections import defaultdict

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '1_パーソナルデータ', 'seo-machine'))

from dotenv import load_dotenv
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    DateRange, Dimension, Metric, OrderBy, RunReportRequest,
)
from google.oauth2 import service_account


def init_client():
    load_dotenv(os.path.join(
        os.path.dirname(__file__), '..', '1_パーソナルデータ', 'seo-machine',
        'data_sources', 'config', '.env'
    ))
    property_id = os.getenv('GA4_PROPERTY_ID')
    credentials_path = os.getenv('GA4_CREDENTIALS_PATH')
    credentials = service_account.Credentials.from_service_account_file(
        credentials_path,
        scopes=['https://www.googleapis.com/auth/analytics.readonly']
    )
    client = BetaAnalyticsDataClient(credentials=credentials)
    return client, property_id


def fetch_week(client, property_id, start, end):
    """1週間分のページ別PVを取得"""
    request = RunReportRequest(
        property=f"properties/{property_id}",
        date_ranges=[DateRange(start_date=start, end_date=end)],
        dimensions=[Dimension(name="pagePath")],
        metrics=[Metric(name="screenPageViews")],
        order_bys=[
            OrderBy(metric=OrderBy.MetricOrderBy(metric_name="screenPageViews"), desc=True)
        ],
        limit=500,
    )
    response = client.run_report(request)
    result = {}
    for row in response.rows:
        page = row.dimension_values[0].value
        pv = int(row.metric_values[0].value)
        result[page] = pv
    return result


def main():
    client, property_id = init_client()

    today = datetime.now()
    this_monday = today - timedelta(days=today.weekday())

    # 8週分の週区間を生成（先週日曜まで）
    weeks = []
    for i in range(8, 0, -1):
        week_start = this_monday - timedelta(weeks=i)
        week_end = week_start + timedelta(days=6)
        weeks.append({
            "label": week_start.strftime("%m/%d"),
            "start": week_start.strftime("%Y-%m-%d"),
            "end": week_end.strftime("%Y-%m-%d"),
        })

    print(f"取得期間: {weeks[0]['start']} ~ {weeks[-1]['end']}", file=sys.stderr)

    # 週ごとにAPI呼び出し
    page_weekly = defaultdict(lambda: defaultdict(int))
    page_total = defaultdict(int)

    for w in weeks:
        print(f"  取得中: {w['label']} ({w['start']} ~ {w['end']})...", file=sys.stderr)
        data = fetch_week(client, property_id, w["start"], w["end"])
        for page, pv in data.items():
            page_weekly[page][w["label"]] = pv
            page_total[page] += pv

    # PV合計Top 50
    week_labels = [w["label"] for w in weeks]
    top_pages = sorted(page_total.items(), key=lambda x: x[1], reverse=True)[:50]

    # JSON出力
    result = {
        "period": {"start": weeks[0]["start"], "end": weeks[-1]["end"]},
        "weeks": week_labels,
        "total_pages": len(page_total),
        "top50": []
    }
    for page, total in top_pages:
        weekly = {w: page_weekly[page].get(w, 0) for w in week_labels}
        result["top50"].append({"page": page, "total": total, "weekly": weekly})

    output_path = os.path.join(os.path.dirname(__file__), "ga4_weekly_pages_result.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    # TSV出力
    tsv_path = os.path.join(os.path.dirname(__file__), "ga4_weekly_pages_result.tsv")
    with open(tsv_path, "w", encoding="utf-8") as f:
        f.write("ページパス\t合計PV\t" + "\t".join(week_labels) + "\n")
        for item in result["top50"]:
            row = f"{item['page']}\t{item['total']}"
            for w in week_labels:
                row += f"\t{item['weekly'].get(w, 0)}"
            f.write(row + "\n")

    print(f"\nJSON: {output_path}", file=sys.stderr)
    print(f"TSV: {tsv_path}", file=sys.stderr)

    # コンソール表示（Top 20）
    print(f"\n=== jo-katsu.com ページ別×週次PV (Top 20 / {len(page_total)}ページ) ===")
    print(f"期間: {weeks[0]['start']} ~ {weeks[-1]['end']}\n")

    # ヘッダー
    print(f"{'#':>2} {'ページパス':<55} {'合計':>6}  " + "  ".join(f"{w:>5}" for w in week_labels))
    print("-" * (70 + 8 * len(week_labels)))

    for i, item in enumerate(result["top50"][:20], 1):
        path = item["page"][:55]
        weekly_str = "  ".join(f"{item['weekly'].get(w, 0):>5}" for w in week_labels)
        print(f"{i:>2} {path:<55} {item['total']:>6}  {weekly_str}")


if __name__ == "__main__":
    main()
