"""
GA4 Event Data CLI - jo-katsu.com CV指標・オーガニックセッション取得

Usage:
    python scripts/ga4_events.py event-daily <event_name> <start_date> <end_date>
    python scripts/ga4_events.py pageviews-daily <path_contains> <start_date> <end_date>
    python scripts/ga4_events.py organic-sessions <days> <limit>
    python scripts/ga4_events.py organic-sessions-compare <cur_start> <cur_end> <prev_start> <prev_end> <limit>
"""

import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dotenv import load_dotenv
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    DateRange,
    Dimension,
    Filter,
    FilterExpression,
    Metric,
    OrderBy,
    RunReportRequest,
)
from google.oauth2 import service_account


def init_client():
    load_dotenv(os.path.join(os.path.dirname(__file__), '..', 'data_sources', 'config', '.env'))
    property_id = os.getenv('GA4_PROPERTY_ID')
    credentials_path = os.getenv('GA4_CREDENTIALS_PATH')
    if not property_id or not credentials_path:
        print(json.dumps({"error": "GA4_PROPERTY_ID or GA4_CREDENTIALS_PATH not set"}), file=sys.stderr)
        sys.exit(1)
    credentials = service_account.Credentials.from_service_account_file(
        credentials_path,
        scopes=['https://www.googleapis.com/auth/analytics.readonly']
    )
    client = BetaAnalyticsDataClient(credentials=credentials)
    return client, property_id


def event_daily(client, property_id, event_name, start_date, end_date):
    """指定イベントの日別カウントを取得"""
    request = RunReportRequest(
        property=f"properties/{property_id}",
        date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
        dimensions=[Dimension(name="date")],
        metrics=[Metric(name="eventCount")],
        dimension_filter=FilterExpression(
            filter=Filter(
                field_name="eventName",
                string_filter=Filter.StringFilter(
                    match_type=Filter.StringFilter.MatchType.EXACT,
                    value=event_name
                )
            )
        ),
        order_bys=[OrderBy(dimension=OrderBy.DimensionOrderBy(dimension_name="date"))]
    )
    response = client.run_report(request)
    rows = []
    total = 0
    for row in response.rows:
        count = int(row.metric_values[0].value)
        rows.append({"date": row.dimension_values[0].value, "count": count})
        total += count
    return {
        "command": "event-daily",
        "event_name": event_name,
        "period": {"start": start_date, "end": end_date},
        "rows": rows,
        "total": total
    }


def pageviews_daily(client, property_id, path_contains, start_date, end_date):
    """指定パスを含むページのPV日別カウントを取得"""
    # Git Bash on Windows converts /path/ to C:/Program Files/Git/path/
    # Detect and fix this mangling
    if path_contains.startswith("C:/Program Files/Git/"):
        path_contains = "/" + path_contains.removeprefix("C:/Program Files/Git/")
    elif path_contains.startswith("C:\\Program Files\\Git\\"):
        path_contains = "/" + path_contains.removeprefix("C:\\Program Files\\Git\\")
    request = RunReportRequest(
        property=f"properties/{property_id}",
        date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
        dimensions=[Dimension(name="date")],
        metrics=[Metric(name="screenPageViews")],
        dimension_filter=FilterExpression(
            filter=Filter(
                field_name="pagePath",
                string_filter=Filter.StringFilter(
                    match_type=Filter.StringFilter.MatchType.CONTAINS,
                    value=path_contains
                )
            )
        ),
        order_bys=[OrderBy(dimension=OrderBy.DimensionOrderBy(dimension_name="date"))]
    )
    response = client.run_report(request)
    rows = []
    total = 0
    for row in response.rows:
        count = int(row.metric_values[0].value)
        rows.append({"date": row.dimension_values[0].value, "count": count})
        total += count
    return {
        "command": "pageviews-daily",
        "path_contains": path_contains,
        "period": {"start": start_date, "end": end_date},
        "rows": rows,
        "total": total
    }


def organic_sessions(client, property_id, days, limit):
    """オーガニックセッション数でページ別Top Nを取得"""
    request = RunReportRequest(
        property=f"properties/{property_id}",
        date_ranges=[DateRange(start_date=f"{days}daysAgo", end_date="today")],
        dimensions=[Dimension(name="pagePath")],
        metrics=[Metric(name="sessions")],
        dimension_filter=FilterExpression(
            filter=Filter(
                field_name="sessionDefaultChannelGroup",
                string_filter=Filter.StringFilter(
                    match_type=Filter.StringFilter.MatchType.EXACT,
                    value="Organic Search"
                )
            )
        ),
        order_bys=[OrderBy(metric=OrderBy.MetricOrderBy(metric_name="sessions"), desc=True)],
        limit=limit
    )
    response = client.run_report(request)
    rows = []
    for row in response.rows:
        rows.append({
            "page": row.dimension_values[0].value,
            "sessions": int(row.metric_values[0].value)
        })
    return {
        "command": "organic-sessions",
        "days": days,
        "limit": limit,
        "rows": rows,
        "total": sum(r["sessions"] for r in rows)
    }


def organic_sessions_compare(client, property_id, cur_start, cur_end, prev_start, prev_end, limit):
    """2期間のオーガニックセッションをページ別に比較"""
    def fetch_period(start, end):
        request = RunReportRequest(
            property=f"properties/{property_id}",
            date_ranges=[DateRange(start_date=start, end_date=end)],
            dimensions=[Dimension(name="pagePath")],
            metrics=[Metric(name="sessions")],
            dimension_filter=FilterExpression(
                filter=Filter(
                    field_name="sessionDefaultChannelGroup",
                    string_filter=Filter.StringFilter(
                        match_type=Filter.StringFilter.MatchType.EXACT,
                        value="Organic Search"
                    )
                )
            ),
            order_bys=[OrderBy(metric=OrderBy.MetricOrderBy(metric_name="sessions"), desc=True)],
            limit=500
        )
        response = client.run_report(request)
        result = {}
        for row in response.rows:
            result[row.dimension_values[0].value] = int(row.metric_values[0].value)
        return result

    current = fetch_period(cur_start, cur_end)
    previous = fetch_period(prev_start, prev_end)

    all_pages = set(list(current.keys())[:limit]) | set(list(previous.keys())[:limit])
    rows = []
    for page in all_pages:
        cur_val = current.get(page, 0)
        prev_val = previous.get(page, 0)
        if prev_val > 0:
            change_pct = round((cur_val - prev_val) / prev_val * 100, 1)
        elif cur_val > 0:
            change_pct = 100.0
        else:
            change_pct = 0.0
        rows.append({
            "page": page,
            "current": cur_val,
            "previous": prev_val,
            "change_pct": change_pct
        })

    rows.sort(key=lambda r: r["current"], reverse=True)
    rows = rows[:limit]

    return {
        "command": "organic-sessions-compare",
        "current_period": {"start": cur_start, "end": cur_end},
        "previous_period": {"start": prev_start, "end": prev_end},
        "rows": rows,
        "total_current": sum(r["current"] for r in rows),
        "total_previous": sum(r["previous"] for r in rows)
    }


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1]
    client, property_id = init_client()

    if cmd == "event-daily":
        if len(sys.argv) != 5:
            print("Usage: event-daily <event_name> <start_date> <end_date>", file=sys.stderr)
            sys.exit(1)
        result = event_daily(client, property_id, sys.argv[2], sys.argv[3], sys.argv[4])

    elif cmd == "pageviews-daily":
        if len(sys.argv) != 5:
            print("Usage: pageviews-daily <path_contains> <start_date> <end_date>", file=sys.stderr)
            sys.exit(1)
        result = pageviews_daily(client, property_id, sys.argv[2], sys.argv[3], sys.argv[4])

    elif cmd == "organic-sessions":
        if len(sys.argv) != 4:
            print("Usage: organic-sessions <days> <limit>", file=sys.stderr)
            sys.exit(1)
        result = organic_sessions(client, property_id, int(sys.argv[2]), int(sys.argv[3]))

    elif cmd == "organic-sessions-compare":
        if len(sys.argv) != 7:
            print("Usage: organic-sessions-compare <cur_start> <cur_end> <prev_start> <prev_end> <limit>", file=sys.stderr)
            sys.exit(1)
        result = organic_sessions_compare(
            client, property_id,
            sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], int(sys.argv[6])
        )

    else:
        print(f"Unknown command: {cmd}", file=sys.stderr)
        print(__doc__)
        sys.exit(1)

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
