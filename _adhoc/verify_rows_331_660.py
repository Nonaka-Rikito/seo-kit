import csv
import json
import re
from urllib.parse import urlparse

CSV_PATH = r"C:/Users/rikit/Projects/2_クライアントデータ/malna/nonaka/被リンク営業リスト_連絡先付き.csv"
OUTPUT_PATH = r"C:/Users/rikit/Projects/_adhoc/verify_result_2.json"

# 許容する外部フォームサービスドメイン
ALLOWED_FORM_DOMAINS = {
    "tayori.com", "forms.gle", "docs.google.com", "form.run",
    "formrun.com", "formzu.net", "questant.jp", "typeform.com",
    "hubspot.com", "mailchimp.com", "ssl.form-mailer.jp",
    "business.form-mailer.jp", "ws.formzu.net", "form.k3r.jp",
    "krs.bz", "pro.form-mailer.jp", "sgfm.jp", "formbridge.com",
    "f.msgs.jp", "bit.ly", "contact.because-web.com"
}

CONTACT_KEYWORDS = [
    "contact", "inquiry", "inquire", "お問い合わせ", "toiawase",
    "otoiawase", "form", "consulting", "support", "ask",
    "相談", "soudan", "mail", "entry"
]

def is_top_page_only(url, domain):
    """URLがトップページのみかどうか判定"""
    parsed = urlparse(url)
    path = parsed.path.rstrip("/")
    # パスが空またはルートのみで、queryもfragmentもない
    if path == "" and not parsed.query and not parsed.fragment:
        return True
    return False

def is_external_domain(url, domain):
    """URLが元ドメインと異なる外部ドメインかどうか判定"""
    parsed = urlparse(url)
    url_host = parsed.hostname or ""
    # 元ドメインを含んでいれば内部
    if domain in url_host or url_host in domain:
        return False, url_host
    # 許容フォームサービスか判定
    for allowed in ALLOWED_FORM_DOMAINS:
        if allowed in url_host:
            return False, url_host  # 許容
    return True, url_host

def has_contact_keyword(url):
    """URLにcontact系キーワードが含まれているか"""
    url_lower = url.lower()
    for kw in CONTACT_KEYWORDS:
        if kw in url_lower:
            return True
    return False

def check_company_name(name, domain):
    """社名の妥当性チェック"""
    issues = []
    if not name or name.strip() == "":
        issues.append("社名空欄")
    else:
        name_stripped = name.strip()
        # ドメイン名そのままか
        domain_base = domain.replace("www.", "")
        if name_stripped == domain or name_stripped == domain_base:
            issues.append("社名がドメイン名そのまま")
        # 極端に短い
        if len(name_stripped) <= 2:
            issues.append("社名が極端に短い（2文字以下）")
        # 極端に長い
        if len(name_stripped) > 60:
            issues.append("社名が極端に長い（60文字超）")
    return issues

# CSV読み込み
with open(CSV_PATH, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    all_rows = list(reader)

# 行331〜660（0-indexed: 330〜659）
target_rows = all_rows[330:660]

issues = []
summary = {
    "トップページフォールバック件数": 0,
    "外部フォームサービス件数": 0,
    "外部ドメイン（非フォームサービス）件数": 0,
    "社名空欄件数": 0,
    "社名異常件数": 0,
    "contact_keyword_なし件数": 0
}

for i, row in enumerate(target_rows):
    row_num = 331 + i  # 1-indexed (ヘッダー除き)
    domain = row.get("ドメイン", "").strip()
    company = row.get("社名", "").strip()
    contact_url = row.get("問い合わせURL", "").strip()

    # 1. トップページフォールバック
    if contact_url and is_top_page_only(contact_url, domain):
        issues.append({
            "row": row_num,
            "domain": domain,
            "issue_type": "トップページフォールバック",
            "detail": "問い合わせURLがトップページのみ",
            "現在の値": contact_url,
            "社名": company
        })
        summary["トップページフォールバック件数"] += 1

    # 2. 外部ドメインチェック
    if contact_url:
        is_ext, url_host = is_external_domain(contact_url, domain)
        if is_ext:
            issues.append({
                "row": row_num,
                "domain": domain,
                "issue_type": "外部ドメイン（非フォームサービス）",
                "detail": f"問い合わせURLが外部ドメイン: {url_host}",
                "現在の値": contact_url,
                "社名": company
            })
            summary["外部ドメイン（非フォームサービス）件数"] += 1
        else:
            # 外部だが許容フォームサービスの場合
            parsed = urlparse(contact_url)
            url_host_check = parsed.hostname or ""
            if domain not in url_host_check and url_host_check not in domain:
                summary["外部フォームサービス件数"] += 1

    # 3. contact系キーワードチェック
    if contact_url and not is_top_page_only(contact_url, domain):
        if not has_contact_keyword(contact_url):
            issues.append({
                "row": row_num,
                "domain": domain,
                "issue_type": "contact_keywordなし",
                "detail": "URLにcontact/inquiry等のキーワードが含まれていない",
                "現在の値": contact_url,
                "社名": company
            })
            summary["contact_keyword_なし件数"] += 1

    # 4. 社名チェック
    name_issues = check_company_name(company, domain)
    for ni in name_issues:
        if "空欄" in ni:
            summary["社名空欄件数"] += 1
        else:
            summary["社名異常件数"] += 1
        issues.append({
            "row": row_num,
            "domain": domain,
            "issue_type": ni,
            "detail": ni,
            "現在の値": company if company else "(空)",
            "社名": company
        })

result = {
    "range": "331-660",
    "total_checked": len(target_rows),
    "issues": issues,
    "summary": summary
}

with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print(f"検証完了: {len(target_rows)}行チェック, {len(issues)}件の問題検出")
print(f"出力先: {OUTPUT_PATH}")
print(json.dumps(summary, ensure_ascii=False, indent=2))
