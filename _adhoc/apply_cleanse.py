"""
クレンジング結果をCSVに反映するスクリプト
- 除外すべき行を削除
- 社名を修正
"""

import csv
import json
import os

CSV_PATH = "C:/Users/rikit/Projects/2_クライアントデータ/malna/nonaka/被リンク営業リスト_連絡先付き.csv"
OUTPUT_PATH = "C:/Users/rikit/Projects/2_クライアントデータ/malna/nonaka/被リンク営業リスト_最終.csv"
CLEANSE_JSONS = [
    "C:/Users/rikit/Projects/_adhoc/cleanse_result_1.json",
    "C:/Users/rikit/Projects/_adhoc/cleanse_result_2.json",
    "C:/Users/rikit/Projects/_adhoc/cleanse_result_3.json",
]

# ---- クレンジング結果を読み込む ----
exclude_rows = set()   # row番号（1-indexed）
name_fixes = {}        # row番号 -> new_name

for path in CLEANSE_JSONS:
    if not os.path.exists(path):
        print(f"SKIP: {path}")
        continue
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    for item in data.get("exclude_rows", []):
        exclude_rows.add(item["row"])
    for item in data.get("name_fixes", []):
        name_fixes[item["row"]] = item["new_name"]

print(f"除外対象: {len(exclude_rows)}件")
print(f"社名修正: {len(name_fixes)}件")

# ---- CSV読み込み・修正 ----
with open(CSV_PATH, encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)
    fieldnames = reader.fieldnames
    rows = list(reader)

output_rows = []
excluded_count = 0
fixed_count = 0

for i, row in enumerate(rows):
    row_num = i + 1  # 1-indexed

    # 除外
    if row_num in exclude_rows:
        excluded_count += 1
        continue

    # 社名修正
    if row_num in name_fixes:
        row["社名"] = name_fixes[row_num]
        fixed_count += 1

    output_rows.append(row)

# ---- 保存 ----
with open(OUTPUT_PATH, "w", encoding="utf-8-sig", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(output_rows)

print(f"\n処理完了:")
print(f"  元の件数: {len(rows)}件")
print(f"  除外: {excluded_count}件")
print(f"  社名修正: {fixed_count}件")
print(f"  最終件数: {len(output_rows)}件")
print(f"保存先: {OUTPUT_PATH}")
