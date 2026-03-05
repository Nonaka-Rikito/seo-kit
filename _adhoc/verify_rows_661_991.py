"""被リンク営業リストの検証スクリプト（行661〜991）"""
import csv
import json
import re
from urllib.parse import urlparse

CSV_PATH = r"C:/Users/rikit/Projects/2_クライアントデータ/malna/nonaka/被リンク営業リスト_連絡先付き.csv"
OUTPUT_PATH = r"C:/Users/rikit/Projects/_adhoc/verify_result_3.json"

# Column indices
COL_DOMAIN = 0
COL_COMPANY = 1
COL_CONTACT_URL = 2

# 許容する外部フォームサービスのドメイン
ALLOWED_FORM_SERVICES = [
    "tayori.com", "forms.gle", "google.com", "googleforms.com",
    "formrun.com", "form.run", "typeform.com", "hubspot.com",
    "mailchimp.com", "kintone.com", "cybozu.com", "chatwork.com",
    "line.me", "secure.force.com", "salesforce.com",
    "formzu.net", "formmailer.jp", "enquete.ne.jp",
    "business.form-mailer.jp", "ssl.form-mailer.jp",
    "docs.google.com", "bit.ly", "ws.formzu.net",
    "pro.form-mailer.jp", "smoothcontact.jp", "formbridge.com",
    "forms.office.com", "survey.zohopublic.com",
]

# 問い合わせ系キーワード
CONTACT_KEYWORDS = [
    "contact", "inquiry", "enquiry", "toiawase", "otoiawase",
    "ask", "form", "mail", "support", "soudan", "request",
    "apply", "entry", "mailto:",
]

def is_top_page_only(url, domain):
    """URLがトップページフォールバック（ドメイン直下のみ）かどうか判定"""
    parsed = urlparse(url)
    path = parsed.path.rstrip("/")
    return path == "" or path == "/"

def is_external_domain(url, domain):
    """URLが元ドメインと異なる外部ドメインか判定（フォームサービスは許容）"""
    parsed = urlparse(url)
    url_host = parsed.netloc.lower().replace("www.", "")
    domain_clean = domain.lower().replace("www.", "")

    # mailto: の場合はスキップ
    if url.startswith("mailto:"):
        return False, None

    if not url_host or not domain_clean:
        return False, None

    if url_host == domain_clean:
        return False, None
    if url_host.endswith("." + domain_clean):
        return False, None
    if domain_clean.endswith("." + url_host):
        return False, None

    # サブドメイン違いの同一ルートドメイン チェック
    # e.g., domain=web-analytics.eitapapa-fire.com, url_host=eb-analytics.eitapapa-fire.com
    # 共通の親ドメインを持つか
    domain_parts = domain_clean.split(".")
    url_parts = url_host.split(".")
    if len(domain_parts) >= 2 and len(url_parts) >= 2:
        domain_root = ".".join(domain_parts[-2:])
        url_root = ".".join(url_parts[-2:])
        if domain_root == url_root:
            return False, None

    # フォームサービスチェック
    for service in ALLOWED_FORM_SERVICES:
        if service in url_host:
            return False, "form_service"

    return True, url_host

def has_contact_keyword(url):
    """URLにcontact系キーワードが含まれるか"""
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
        return issues

    name_stripped = name.strip()

    # ドメイン名そのままチェック
    domain_clean = domain.lower().replace("www.", "")
    if name_stripped.lower() == domain_clean or name_stripped.lower() == domain_clean.split(".")[0]:
        issues.append("社名がドメイン名そのまま")

    # 極端に短い
    if len(name_stripped) <= 2:
        issues.append("社名が極端に短い（2文字以下）")

    # 極端に長い
    if len(name_stripped) > 60:
        issues.append("社名が極端に長い（60文字超）")

    return issues

def main():
    issues = []
    summary = {
        "トップページフォールバック件数": 0,
        "外部フォームサービス件数": 0,
        "外部ドメイン不正件数": 0,
        "社名空欄件数": 0,
        "社名異常件数": 0,
        "contact_keyword_なし件数": 0,
    }

    with open(CSV_PATH, "r", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        header = next(reader)  # skip header
        all_rows = list(reader)

    # Data rows 661-991 = index 660-990 (0-based)
    start_idx = 660
    end_idx = 991  # exclusive
    target_rows = all_rows[start_idx:end_idx]
    total_checked = len(target_rows)

    for i, row in enumerate(target_rows):
        data_row_num = start_idx + i + 1  # 1-based data row number (661, 662, ...)
        csv_row_num = data_row_num + 1     # CSV line number (header=1, so data row 661 = line 662)

        domain = row[COL_DOMAIN].strip() if len(row) > COL_DOMAIN else ""
        company = row[COL_COMPANY].strip() if len(row) > COL_COMPANY else ""
        contact_url = row[COL_CONTACT_URL].strip() if len(row) > COL_CONTACT_URL else ""

        # 1. トップページフォールバックチェック
        if contact_url and not contact_url.startswith("mailto:") and is_top_page_only(contact_url, domain):
            issues.append({
                "row": data_row_num,
                "domain": domain,
                "issue_type": "トップページフォールバック",
                "detail": "問い合わせURLがトップページのみ",
                "現在の値": contact_url,
                "社名": company
            })
            summary["トップページフォールバック件数"] += 1

        # 2. 外部ドメインチェック
        if contact_url:
            is_external, ext_info = is_external_domain(contact_url, domain)
            if is_external:
                issues.append({
                    "row": data_row_num,
                    "domain": domain,
                    "issue_type": "外部ドメイン不正",
                    "detail": f"問い合わせURLが外部ドメイン: {ext_info}",
                    "現在の値": contact_url,
                    "社名": company
                })
                summary["外部ドメイン不正件数"] += 1
            elif ext_info == "form_service":
                summary["外部フォームサービス件数"] += 1

        # 3. contact keywordチェック（トップページフォールバック以外で）
        if contact_url and not contact_url.startswith("mailto:") and not is_top_page_only(contact_url, domain):
            if not has_contact_keyword(contact_url):
                issues.append({
                    "row": data_row_num,
                    "domain": domain,
                    "issue_type": "contact_keywordなし",
                    "detail": "URLにcontact/inquiry等のキーワードが含まれない",
                    "現在の値": contact_url,
                    "社名": company
                })
                summary["contact_keyword_なし件数"] += 1

        # 4. 社名チェック
        name_issues = check_company_name(company, domain)
        for ni in name_issues:
            if "空欄" in ni:
                summary["社名空欄件数"] += 1
                issue_type = "社名空欄"
            else:
                summary["社名異常件数"] += 1
                issue_type = "社名異常"
            issues.append({
                "row": data_row_num,
                "domain": domain,
                "issue_type": issue_type,
                "detail": ni,
                "現在の値": company if company else "(空)",
                "社名": company if company else "(空)"
            })

    result = {
        "range": "661-991",
        "total_checked": total_checked,
        "issues": issues,
        "summary": summary
    }

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    # Print summary to stdout
    print(f"Verification complete: {total_checked} rows checked")
    print(f"Issues found: {len(issues)}")
    print(f"Summary:")
    for k, v in summary.items():
        print(f"  {k}: {v}")

if __name__ == "__main__":
    main()
