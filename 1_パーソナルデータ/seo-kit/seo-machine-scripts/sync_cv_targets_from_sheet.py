"""
スプレッドシートのCV目標を config/cv-targets.json に同期するスクリプト。

使い方:
  .venv\\Scripts\\python scripts/sync_cv_targets_from_sheet.py [スプレッドシートURL] [--sheet "シート名"] [--layout table|matrix]
  URL省略時は config/cv-targets.json の spreadsheet_url を使用。

レイアウト:
  table  - 1行目: 月, pre_register_cta_click, dl_material_page_view / 2行目〜: YYYY-MM, 数値, 数値
  matrix - 行＝指標・列＝日付の日次目標表（「日次目標」シート形式）。仮登録数・資料DL系の行を月で合計して目標に使用

事前準備:
  1. Google Cloud Console で Google Sheets API を有効化
  2. スプレッドシートをサービスアカウントに共有（閲覧者で可）
  3. .env の GA4_CREDENTIALS_PATH（または GOOGLE_APPLICATION_CREDENTIALS）が有効
"""

import argparse
import json
import os
import re
import sys
from collections import defaultdict
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Optional

# プロジェクトルートをパスに追加
REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

# data_sources/config/.env を読む
env_path = REPO_ROOT / "data_sources" / "config" / ".env"
if env_path.exists():
    from dotenv import load_dotenv
    load_dotenv(env_path)

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


LABELS = {
    "pre_register_cta_click": "会員登録",
    "dl_material_page_view": "資料DL申し込み",
}

# 固定参照行（スプレッドシートの1始まり行番号）
# ユーザー指定:
# - dl_material_page_view: 5行目
# - pre_register_cta_click: 9行目
DL_ROW_1BASED = 5
PRE_ROW_1BASED = 9


def get_sheet_client():
    cred_path = os.getenv("GA4_CREDENTIALS_PATH") or os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if not cred_path or not os.path.exists(cred_path):
        raise SystemExit("GA4_CREDENTIALS_PATH または GOOGLE_APPLICATION_CREDENTIALS が未設定かファイルがありません。")
    creds = service_account.Credentials.from_service_account_file(
        cred_path,
        scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"],
    )
    return build("sheets", "v4", credentials=creds)


def spreadsheet_id_from_url(url: str) -> str:
    m = re.search(r"/d/([a-zA-Z0-9_-]+)", url)
    if not m:
        raise ValueError(f"スプレッドシートURLからIDを取得できません: {url}")
    return m.group(1)


def parse_header(row: list) -> dict:
    """ヘッダー行から列インデックスを返す。"""
    col = {}
    for i, cell in enumerate(row):
        s = (cell or "").strip().lower()
        if s in ("月", "month", "yyyy-mm"):
            col["month"] = i
        elif s in ("pre_register_cta_click", "会員登録", "会員登録目標"):
            col["pre_register_cta_click"] = i
        elif s in ("dl_material_page_view", "資料dl", "資料dl目標", "資料dl申し込み"):
            col["dl_material_page_view"] = i
    if "month" not in col or "pre_register_cta_click" not in col or "dl_material_page_view" not in col:
        raise ValueError(
            "ヘッダーに 月 / pre_register_cta_click(会員登録) / dl_material_page_view(資料DL) が必要です。"
        )
    return col


def safe_int(val, default: int = 0) -> int:
    if val is None or val == "":
        return default
    try:
        return int(float(str(val).replace(",", "").strip()))
    except (ValueError, TypeError):
        return default


def safe_float(val, default: float = 0.0) -> float:
    """小数を含むセル値を数値に。日次目標の合計用。"""
    if val is None or val == "":
        return default
    try:
        return float(str(val).replace(",", "").strip())
    except (ValueError, TypeError):
        return default


def safe_decimal(val, default: Decimal = Decimal("0")) -> Decimal:
    """小数を正確に扱うため Decimal で返す。"""
    if val is None or val == "":
        return default
    try:
        return Decimal(str(val).replace(",", "").strip())
    except (InvalidOperation, ValueError, TypeError):
        return default


def fetch_values_from_sheet(sheets_api, spreadsheet_id: str, sheet_title: Optional[str] = None):
    """指定シート（省略時は1枚目）を取得（A〜Z列）。"""
    try:
        meta = sheets_api.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
        sheets_list = meta.get("sheets", [])
        if not sheets_list:
            raise SystemExit("スプレッドシートにシートがありません。")
        if sheet_title:
            sheet = next((s for s in sheets_list if s.get("properties", {}).get("title") == sheet_title), None)
            if not sheet:
                names = [s.get("properties", {}).get("title", "?") for s in sheets_list]
                raise SystemExit(f"シート「{sheet_title}」が見つかりません。存在するシート: {names}")
            name = sheet_title
        else:
            name = sheets_list[0].get("properties", {}).get("title", "Sheet1")
        range_name = f"'{name}'!A:Z"
        result = sheets_api.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range=range_name,
            valueRenderOption="UNFORMATTED_VALUE",
        ).execute()
        return result.get("values", [])
    except HttpError as e:
        if e.resp.status == 404:
            raise SystemExit("スプレッドシートが見つかりません。URLを確認するか、サービスアカウントに共有してください。")
        raise


def parse_date_cell(s: str) -> Optional[tuple]:
    """'2026/02/01' or '2026-02-01' -> (2026, 2). 解釈できない場合は None."""
    if s is None or s == "":
        return None
    # Google Sheets のシリアル日付（UNFORMATTED_VALUE）
    if isinstance(s, (int, float)):
        try:
            base = datetime(1899, 12, 30)
            dt = base + timedelta(days=float(s))
            return (dt.year, dt.month)
        except Exception:
            pass
    s = str(s).strip()
    # 数値文字列のシリアル日付
    if re.match(r"^\d+(\.\d+)?$", s):
        try:
            base = datetime(1899, 12, 30)
            dt = base + timedelta(days=float(s))
            return (dt.year, dt.month)
        except Exception:
            pass
    for sep in ("/", "-", "."):
        if sep in s:
            parts = s.split(sep)
            if len(parts) >= 2:
                try:
                    y = int(parts[0])
                    m = int(parts[1])
                    if 2000 <= y <= 2100 and 1 <= m <= 12:
                        return (y, m)
                except (ValueError, IndexError):
                    pass
    return None


def parse_date_cell_full(s: str) -> Optional[tuple]:
    """'2026/02/01' or '2026-02-01' -> (2026, 2, 1)。日付として解釈できない場合は None."""
    if s is None or s == "":
        return None
    # Google Sheets のシリアル日付（UNFORMATTED_VALUE）
    if isinstance(s, (int, float)):
        try:
            base = datetime(1899, 12, 30)
            dt = base + timedelta(days=float(s))
            return (dt.year, dt.month, dt.day)
        except Exception:
            pass
    s = str(s).strip()
    # 数値文字列のシリアル日付
    if re.match(r"^\d+(\.\d+)?$", s):
        try:
            base = datetime(1899, 12, 30)
            dt = base + timedelta(days=float(s))
            return (dt.year, dt.month, dt.day)
        except Exception:
            pass
    for sep in ("/", "-", "."):
        if sep in s:
            parts = s.split(sep)
            if len(parts) >= 3:
                try:
                    y = int(parts[0])
                    m = int(parts[1])
                    d = int(parts[2])
                    if 2000 <= y <= 2100 and 1 <= m <= 12 and 1 <= d <= 31:
                        return (y, m, d)
                except (ValueError, IndexError):
                    pass
    return None


def build_cv_targets_from_matrix(values: list, spreadsheet_url: str, metric_col: int = 2) -> dict:
    """
    行＝指標・列＝日付の日次目標表から月別目標を集計する。
    - 1行目（または最初に日付が並ぶ行）を日付ヘッダーとして扱う
    - metric_col 列（0始まり、C列=2）に指標名。'仮登録数' -> 会員登録、'資料CIA DL…'/'資料DL' 等 -> 資料DL
    - 日付列の値を月ごとに合計して target にする
    """
    if not values:
        raise ValueError("スプレッドシートにデータがありません。")
    # 日付が並ぶ行を探す（先頭数行のうち、日付らしいセルが3個以上ある行）
    date_row_idx = 0
    col_to_ym: dict[int, tuple[int, int]] = {}
    for ri, row in enumerate(values[:20]):
        count = 0
        col_to_ym = {}
        for ci, cell in enumerate(row):
            ym = parse_date_cell(cell)
            if ym:
                col_to_ym[ci] = ym
                count += 1
        if count >= 3:
            date_row_idx = ri
            break
    if not col_to_ym:
        raise ValueError("日付の列が見つかりません。1行目付近に 2026/02/01 形式の日付を置いてください。")
    # 指標行は固定参照（1始まり）
    pre_row_idx = PRE_ROW_1BASED - 1
    dl_row_idx = DL_ROW_1BASED - 1
    if pre_row_idx >= len(values) or dl_row_idx >= len(values):
        raise ValueError(
            f"固定参照行がシート範囲外です。pre_register={PRE_ROW_1BASED}行目, "
            f"dl_material={DL_ROW_1BASED}行目, 総行数={len(values)}"
        )
    # 月ごとに列をグループ化
    month_columns: dict = defaultdict(list)
    for ci, ym in col_to_ym.items():
        month_columns[ym].append(ci)
    # 月ごとに合計（小数対応: 0.3, 5.9 等を合算して四捨五入）
    month_targets: dict = {}
    for (y, m), cols in sorted(month_columns.items()):
        month_key = f"{y}-{m:02d}"
        pre_sum = Decimal("0")
        dl_sum = Decimal("0")
        for ci in cols:
            if pre_row_idx < len(values):
                row = values[pre_row_idx]
                pre_sum += safe_decimal(row[ci] if ci < len(row) else None)
            if dl_row_idx < len(values):
                row = values[dl_row_idx]
                dl_sum += safe_decimal(row[ci] if ci < len(row) else None)
        month_targets[month_key] = {
            "pre_register_cta_click": {"label": LABELS["pre_register_cta_click"], "target": float(pre_sum)},
            "dl_material_page_view": {"label": LABELS["dl_material_page_view"], "target": float(dl_sum)},
        }
    if not month_targets:
        raise ValueError("有効な月のデータがありません。")
    # defaults は直近月または最初の月の値
    first_month = min(month_targets.keys())
    out = {
        "_note": "目標値はスプシで管理。このファイルは sync_cv_targets_from_sheet.py でスプシから同期可能。",
        "spreadsheet_url": spreadsheet_url,
        "defaults": month_targets[first_month],
        **month_targets,
    }
    return out


def target_through_date_from_matrix(
    values: list, through_ymd: tuple, metric_col: int = 2
) -> dict:
    """指定日までの日次目標の累計を返す。through_ymd = (2026, 2, 10)。"""
    if not values:
        return {"pre_register_cta_click": 0, "dl_material_page_view": 0}
    date_row_idx = 0
    col_to_ymd: dict = {}
    for ri, row in enumerate(values[:20]):
        col_to_ymd = {}
        for ci, cell in enumerate(row):
            ymd = parse_date_cell_full(cell)
            if ymd:
                col_to_ymd[ci] = ymd
        if len(col_to_ymd) >= 3:
            date_row_idx = ri
            break
    if not col_to_ymd:
        return {"pre_register_cta_click": 0, "dl_material_page_view": 0}
    pre_row_idx = PRE_ROW_1BASED - 1
    dl_row_idx = DL_ROW_1BASED - 1
    if pre_row_idx >= len(values) or dl_row_idx >= len(values):
        return {"pre_register_cta_click": 0, "dl_material_page_view": 0}
    pre_sum = Decimal("0")
    dl_sum = Decimal("0")
    for ci, ymd in col_to_ymd.items():
        if ymd <= through_ymd:
            if pre_row_idx < len(values) and ci < len(values[pre_row_idx]):
                pre_sum += safe_decimal(values[pre_row_idx][ci])
            if dl_row_idx < len(values) and ci < len(values[dl_row_idx]):
                dl_sum += safe_decimal(values[dl_row_idx][ci])
    return {
        "pre_register_cta_click": float(pre_sum),
        "dl_material_page_view": float(dl_sum),
    }


def build_cv_targets_json(values: list, spreadsheet_url: str) -> dict:
    if not values:
        raise ValueError("スプレッドシートにデータがありません。")
    header = values[0]
    col = parse_header(header)
    out = {
        "_note": "目標値はスプシで管理。このファイルは sync_cv_targets_from_sheet.py でスプシから同期可能。",
        "spreadsheet_url": spreadsheet_url,
        "defaults": {
            "pre_register_cta_click": {"label": LABELS["pre_register_cta_click"], "target": 0},
            "dl_material_page_view": {"label": LABELS["dl_material_page_view"], "target": 0},
        },
    }
    for row in values[1:]:
        while len(row) <= max(col.values()):
            row.append("")
        month_key = (row[col["month"]] or "").strip()
        pre = safe_int(row[col["pre_register_cta_click"]])
        dl = safe_int(row[col["dl_material_page_view"]])
        if month_key.lower() == "default":
            out["defaults"] = {
                "pre_register_cta_click": {"label": LABELS["pre_register_cta_click"], "target": pre},
                "dl_material_page_view": {"label": LABELS["dl_material_page_view"], "target": dl},
            }
            continue
        if not month_key:
            continue
        # YYYY-MM 形式でない行はスキップ（コメント行など）
        if not re.match(r"^\d{4}-\d{2}$", month_key):
            continue
        out[month_key] = {
            "pre_register_cta_click": {"label": LABELS["pre_register_cta_click"], "target": pre},
            "dl_material_page_view": {"label": LABELS["dl_material_page_view"], "target": dl},
        }
    return out


def main():
    parser = argparse.ArgumentParser(description="スプレッドシートのCV目標を config/cv-targets.json に同期")
    parser.add_argument("url", nargs="?", help="スプレッドシートURL（省略時は cv-targets.json の spreadsheet_url を使用）")
    parser.add_argument("--sheet", default=None, help="読み込むシート名（例: [2026/02/06更新] 日次目標）。省略時は1枚目")
    parser.add_argument("--layout", choices=("table", "matrix"), default="matrix",
                        help="table=月・会員登録・資料DLの3列表。matrix=行が指標・列が日付の日次目標表（デフォルト）")
    parser.add_argument("--target-through", metavar="YYYY-MM-DD", default=None,
                        help="指定日までのスプシ日次目標の累計を表示して終了（例: 2026-02-10）")
    args = parser.parse_args()

    config_path = REPO_ROOT / "config" / "cv-targets.json"
    spreadsheet_url = (args.url or "").strip()
    if not spreadsheet_url and config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            existing = json.load(f)
        spreadsheet_url = (existing.get("spreadsheet_url") or "").strip()
    if not spreadsheet_url:
        print("使い方: python scripts/sync_cv_targets_from_sheet.py <スプレッドシートURL> [--sheet \"シート名\"] [--layout table|matrix]")
        print("または config/cv-targets.json の spreadsheet_url を設定してから再度実行してください。")
        sys.exit(1)
    spreadsheet_id = spreadsheet_id_from_url(spreadsheet_url)
    sheets = get_sheet_client()
    values = fetch_values_from_sheet(sheets, spreadsheet_id, sheet_title=args.sheet)
    # 指定日までの目標累計のみ表示
    if args.target_through:
        m = re.match(r"^(\d{4})-(\d{2})-(\d{2})$", args.target_through.strip())
        if not m:
            print("--target-through は YYYY-MM-DD 形式で指定してください（例: 2026-02-10）")
            sys.exit(1)
        through_ymd = (int(m.group(1)), int(m.group(2)), int(m.group(3)))
        result = target_through_date_from_matrix(values, through_ymd)
        print(f"{args.target_through} までのスプシ日次目標の累計:")
        print(f"  会員登録（pre_register_cta_click）: {result['pre_register_cta_click']}")
        print(f"  資料DL申し込み（dl_material_page_view）: {result['dl_material_page_view']}")
        sys.exit(0)
    if args.layout == "table":
        data = build_cv_targets_json(values, spreadsheet_url)
    else:
        data = build_cv_targets_from_matrix(values, spreadsheet_url)
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"更新しました: {config_path}")
    months = [k for k in data if k not in ("_note", "spreadsheet_url", "defaults")]
    print(f"反映した月: {', '.join(sorted(months)) or '(なし)'}")


if __name__ == "__main__":
    main()
