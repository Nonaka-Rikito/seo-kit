"""
被リンク営業リスト — 検証結果に基づく一括修正スクリプト

修正内容:
1. 外部ドメイン不正 → https://{domain}/ に差し替え
2. 社名異常（長すぎ/titleタグ全文） → 区切り文字で再切り出し
3. 社名空欄 → ドメイン名を充填
"""

import csv
import json
import os
import re

CSV_PATH = "C:/Users/rikit/Projects/2_クライアントデータ/malna/nonaka/被リンク営業リスト_連絡先付き.csv"
VERIFY_JSONS = [
    "C:/Users/rikit/Projects/_adhoc/verify_result_1.json",
    "C:/Users/rikit/Projects/_adhoc/verify_result_2.json",
    "C:/Users/rikit/Projects/_adhoc/verify_result_3.json",
]

# 外部フォームサービスとして許容するドメイン
ALLOWED_EXTERNAL = [
    "forms.gle", "docs.google.com", "tayori.com", "typeform.com",
    "tally.so", "formrun.me", "mailchimp.com", "hubspot.com",
    "zendesk.com", "intercom.io", "larksuite.com", "lark.suite",
    "connpass.com", "eventregist.com",
]

# issue_type の正規化（エンコード違いに対応）
EXTERNAL_DOMAIN_TYPES = [
    "許容外外部ドメイン", "外部ドメイン不正", "外部ドメイン（非フォームサービス）",
    "外部ドメイン（非フォームサービス)", "外部ドメイン不正", "外部ドメインs",
]
NAME_LONG_TYPES = [
    "社名が極端に長い（60文字超）", "社名が極端に長い(60文字超)",
    "社名異常", "社名異常（長すぎ・短すぎ・ドメイン名そのまま）",
    "社名異常（長すぎ/短すぎ/ドメイン名そのまま）",
]
NAME_EMPTY_TYPES = ["社名空欄", "社名空白"]

def is_external_domain_issue(issue_type):
    return any(t in issue_type for t in ["外部ドメイン", "許容外", "不正"])

def is_name_abnormal(issue_type):
    return any(t in issue_type for t in ["社名異常", "長すぎ", "長い", "ドメイン名そのまま", "短すぎ"])

def is_name_empty(issue_type):
    return "社名空欄" in issue_type or "社名空白" in issue_type

def is_allowed_external(url):
    for allowed in ALLOWED_EXTERNAL:
        if allowed in url:
            return True
    return False

def clean_company_name(name, domain):
    """社名の再切り出し"""
    if not name:
        return domain
    # 区切り文字で分割して末尾（会社名）を取得
    for sep in [" | ", " ｜ ", "｜", " - ", " – ", " — ", "：", ": "]:
        if sep in name:
            parts = [p.strip() for p in name.split(sep) if p.strip()]
            if parts:
                # 末尾が短すぎる場合は先頭を使う
                candidate = parts[-1]
                if len(candidate) >= 3:
                    return candidate[:60]
                elif len(parts) >= 2:
                    return parts[0][:60]
    # 60文字超の場合は60文字で切る
    if len(name) > 60:
        return name[:60]
    return name

# ---- 検証結果を読み込む ----
all_issues = {}  # row番号(1-indexed) -> list of issue_type

for json_path in VERIFY_JSONS:
    if not os.path.exists(json_path):
        print(f"SKIP (not found): {json_path}")
        continue
    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)
    for issue in data.get("issues", []):
        row_num = issue.get("row")
        issue_type = issue.get("issue_type", "")
        if row_num not in all_issues:
            all_issues[row_num] = []
        all_issues[row_num].append(issue_type)

print(f"検証結果: {len(all_issues)}行に問題あり")

# ---- CSV読み込み ----
with open(CSV_PATH, encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)
    fieldnames = reader.fieldnames
    rows = list(reader)

print(f"CSV読み込み: {len(rows)}行")

# ---- 修正適用 ----
stats = {
    "外部ドメイン修正": 0,
    "社名長すぎ修正": 0,
    "社名空欄補完": 0,
    "変更なし": 0,
}

for i, row in enumerate(rows):
    row_num = i + 1  # 1-indexed
    domain = row["ドメイン"]
    issue_types = all_issues.get(row_num, [])

    changed = False

    # 1. 外部ドメイン不正 → トップページに差し替え
    for issue_type in issue_types:
        if is_external_domain_issue(issue_type):
            contact_url = row.get("問い合わせURL", "")
            if contact_url and not is_allowed_external(contact_url):
                row["問い合わせURL"] = f"https://{domain}/"
                stats["外部ドメイン修正"] += 1
                changed = True
            break

    # 2. 社名異常（長すぎ・ドメイン名等）→ 再切り出し
    for issue_type in issue_types:
        if is_name_abnormal(issue_type):
            original_name = row.get("社名", "")
            fixed_name = clean_company_name(original_name, domain)
            if fixed_name != original_name:
                row["社名"] = fixed_name
                stats["社名長すぎ修正"] += 1
                changed = True
            break

    # 3. 社名空欄 → ドメイン名を充填
    for issue_type in issue_types:
        if is_name_empty(issue_type):
            if not row.get("社名", "").strip():
                row["社名"] = domain
                stats["社名空欄補完"] += 1
                changed = True
            break

    # 社名が空欄（issueに関係なく）
    if not row.get("社名", "").strip():
        row["社名"] = domain
        stats["社名空欄補完"] += 1

    if not changed:
        stats["変更なし"] += 1

# ---- 保存 ----
with open(CSV_PATH, "w", encoding="utf-8-sig", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print("\n修正完了:")
for k, v in stats.items():
    print(f"  {k}: {v}件")
print(f"\n保存先: {CSV_PATH}")
