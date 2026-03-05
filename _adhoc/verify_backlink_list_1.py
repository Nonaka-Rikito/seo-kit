"""被リンク営業リスト検証スクリプト（行1〜330）"""
import csv
import json
import re
from urllib.parse import urlparse

INPUT_FILE = r"C:/Users/rikit/Projects/2_クライアントデータ/malna/nonaka/被リンク営業リスト_連絡先付き.csv"
OUTPUT_FILE = r"C:/Users/rikit/Projects/_adhoc/verify_result_1.json"

# 許容する外部フォームサービスドメイン
ALLOWED_FORM_DOMAINS = {
    "tayori.com", "forms.gle", "form.run", "formrun.jp",
    "docs.google.com", "typeform.com", "hubspot.com",
    "mailchimp.com", "jotform.com", "wufoo.com",
    "formzu.net", "formmailer.jp", "ssl-form.jp",
    "secure-link.jp", "business-form.com", "f.msgs.jp",
    "form.kintoneapp.com", "enquete.ne.jp",
}

# 問い合わせ関連キーワード
CONTACT_KEYWORDS = [
    "contact", "inquiry", "enquiry", "form", "toiawase",
    "お問い合わせ", "問い合わせ", "問合せ", "お問合せ",
    "otoiawase", "ask", "support", "request",
    "mail", "soudan", "相談",
]

def is_top_page_only(url, domain):
    """URLがトップページだけかチェック"""
    parsed = urlparse(url)
    path = parsed.path.rstrip("/")
    return path == "" or path == "/"

def is_external_form_service(url, domain):
    """外部フォームサービスかチェック"""
    parsed = urlparse(url)
    url_domain = parsed.netloc.lower()
    # ドメインが元のドメインと異なるか
    if domain.lower() in url_domain:
        return False
    # 許容リストに含まれるか
    for allowed in ALLOWED_FORM_DOMAINS:
        if allowed in url_domain:
            return True
    return False

def is_unexpected_external(url, domain):
    """許容外の外部ドメインかチェック"""
    parsed = urlparse(url)
    url_domain = parsed.netloc.lower()
    if not url_domain:
        return False
    if domain.lower() in url_domain:
        return False
    # 許容フォームサービスならOK
    for allowed in ALLOWED_FORM_DOMAINS:
        if allowed in url_domain:
            return False
    return True

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
    else:
        name_stripped = name.strip()
        # ドメイン名そのまま
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

def main():
    issues = []
    summary = {
        "トップページフォールバック件数": 0,
        "外部フォームサービス件数": 0,
        "許容外外部ドメイン件数": 0,
        "社名空欄件数": 0,
        "社名異常件数": 0,
        "contact_keyword_なし件数": 0,
    }

    with open(INPUT_FILE, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader, start=1):
            if i > 330:
                break

            domain = row.get("ドメイン", "").strip()
            company = row.get("社名", "").strip()
            contact_url = row.get("問い合わせURL", "").strip()

            # --- 問い合わせURL チェック ---
            if contact_url:
                # トップページフォールバック
                if is_top_page_only(contact_url, domain):
                    summary["トップページフォールバック件数"] += 1
                    issues.append({
                        "row": i,
                        "domain": domain,
                        "issue_type": "トップページフォールバック",
                        "detail": "問い合わせURLがトップページのみ",
                        "現在の値": contact_url,
                        "社名": company,
                    })

                # 外部フォームサービス（情報として記録）
                if is_external_form_service(contact_url, domain):
                    summary["外部フォームサービス件数"] += 1
                    issues.append({
                        "row": i,
                        "domain": domain,
                        "issue_type": "外部フォームサービス利用",
                        "detail": "外部フォームサービスを利用（許容範囲）",
                        "現在の値": contact_url,
                        "社名": company,
                    })

                # 許容外の外部ドメイン
                if is_unexpected_external(contact_url, domain):
                    summary["許容外外部ドメイン件数"] += 1
                    issues.append({
                        "row": i,
                        "domain": domain,
                        "issue_type": "許容外外部ドメイン",
                        "detail": "問い合わせURLが許容外の外部ドメインを指している",
                        "現在の値": contact_url,
                        "社名": company,
                    })

                # contact キーワードチェック
                if not is_top_page_only(contact_url, domain) and not has_contact_keyword(contact_url):
                    summary["contact_keyword_なし件数"] += 1
                    issues.append({
                        "row": i,
                        "domain": domain,
                        "issue_type": "contact_keywordなし",
                        "detail": "URLにcontact/inquiry等のキーワードが含まれない",
                        "現在の値": contact_url,
                        "社名": company,
                    })

            # --- 社名チェック ---
            name_issues = check_company_name(company, domain)
            for ni in name_issues:
                if "空欄" in ni:
                    summary["社名空欄件数"] += 1
                else:
                    summary["社名異常件数"] += 1
                issues.append({
                    "row": i,
                    "domain": domain,
                    "issue_type": ni,
                    "detail": ni,
                    "現在の値": company if company else "(空欄)",
                    "社名": company if company else "(空欄)",
                })

    result = {
        "range": "1-330",
        "total_checked": min(i, 330),
        "issues": issues,
        "summary": summary,
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"検証完了: {result['total_checked']}行をチェック")
    print(f"問題件数: {len(issues)}件")
    print("サマリー:")
    for k, v in summary.items():
        print(f"  {k}: {v}")

if __name__ == "__main__":
    main()
