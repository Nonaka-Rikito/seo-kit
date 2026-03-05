#!/usr/bin/env python3
"""
被リンク営業リスト クレンジング v2: 行331〜660
- 除外すべきサイトの特定
- 社名の修正
"""

import csv
import json
import re
import sys
import io

# Windows cp932 エラー回避
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# ファイルパス
CONTACT_CSV = r"C:\Users\rikit\Projects\2_クライアントデータ\malna\nonaka\被リンク営業リスト_連絡先付き.csv"
ORIGINAL_CSV = r"C:\Users\rikit\Projects\2_クライアントデータ\malna\nonaka\被リンク営業リスト.csv"
OUTPUT_JSON = r"C:\Users\rikit\Projects\_adhoc\cleanse_result_2.json"

# 連絡先CSVを読み込み (行331〜660, 1-indexed, ヘッダー除く)
with open(CONTACT_CSV, "r", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)
    contact_rows = []
    for i, row in enumerate(reader, start=2):  # ヘッダーが行1なのでデータは行2から
        if 332 <= i <= 661:  # 行331〜660 (data row番号)
            contact_rows.append((i - 1, row))  # i-1 で実際のデータ行番号

# 元CSVからリンクページタイトル・カテゴリーをドメインで引ける辞書を作成
title_by_domain = {}
category_by_domain = {}
with open(ORIGINAL_CSV, "r", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)
    for row in reader:
        domain = row.get("ドメイン", "").strip()
        title = row.get("リンクページタイトル", "").strip()
        cat = row.get("カテゴリー", "").strip()
        if domain:
            if title:
                title_by_domain[domain] = title
            if cat:
                category_by_domain[domain] = cat

print(f"連絡先CSV 読み込み行数: {len(contact_rows)}")
print(f"元CSV タイトル辞書エントリ数: {len(title_by_domain)}")

# --- 除外判定 ---

# 除外キーワード（ドメインで判定 - サブドメイン含む全体チェック）
EXCLUDE_DOMAIN_PATTERNS = [
    # ペット関連
    (r'\bpet[\.\-]', "ペット関連サイト"),
    (r'\bdogfood', "ドッグフード関連"),
    (r'\bcatfood', "キャットフード関連"),
    (r'\bdog\.', "ペット（犬）関連サイト"),
    (r'\bcat\.', "ペット（猫）関連サイト"),
    (r'naturaldogfood', "ドッグフード関連"),
    (r'nelsonsdogfood', "ドッグフード関連"),
    # クリーニング（SEO/マーケ無関係）
    (r'[\.\-]cleaning\.', "クリーニング業"),
    (r'^cleaning\.', "クリーニング業"),
]

EXCLUDE_KEYWORDS_NAME_TITLE = [
    # ペット関連
    ("ドッグフード", "ペットフード販売"),
    ("キャットフード", "ペットフード販売"),
    ("ペットフード", "ペットフード販売"),
    ("ペットショップ", "ペットショップ"),
    ("トリミング", "ペットトリミング"),
    ("ペットホテル", "ペットホテル"),
    ("ペット葬儀", "ペット関連"),
    ("ペット火葬", "ペット関連"),
    ("動物病院", "動物病院"),
    ("獣医", "動物病院"),
    # 美容・ヘルスケア（無関係業種）
    ("美容院", "美容院"),
    ("美容室", "美容室"),
    ("ヘアサロン", "美容室"),
    ("ネイルサロン", "ネイルサロン"),
    ("エステサロン", "エステ"),
    ("整体院", "整体院"),
    ("整骨院", "整骨院"),
    ("鍼灸", "鍼灸院"),
    ("歯科", "歯科"),
    ("歯医者", "歯科"),
    # 飲食
    ("レストラン", "飲食店"),
    ("居酒屋", "飲食店"),
    # 冠婚葬祭
    ("葬儀", "葬儀関連"),
    ("葬祭", "葬儀関連"),
    ("墓石", "葬儀関連"),
    ("仏壇", "葬儀関連"),
    ("ウェディング", "ウェディング"),
    ("ブライダル", "ブライダル"),
    ("結婚式場", "ブライダル"),
    # その他無関係
    ("害虫駆除", "害虫駆除"),
    ("害獣駆除", "害獣駆除"),
    ("外壁塗装", "塗装業"),
    ("水道工事", "水道工事"),
]

# ポジティブキーワード（これがある場合は除外しない）
POSITIVE_KEYWORDS = [
    "seo", "marketing", "マーケティング", "コンテンツ", "広告", "web制作",
    "デジタル", "メディア", "人材", "採用", "キャリア", "就活", "転職",
    "saas", "ツール", "crm", "it", "テック", "tech", "dx",
    "コンサル", "ビジネス", "経営", "スタートアップ",
    "ニュース", "エンジニア", "プログラミング", "開発",
    "アフィリエイト", "データ分析", "analytics",
    "ホームページ制作", "webデザイン",
    "sns", "動画制作", "セキュリティ",
    "クラウド", "ai", "機械学習",
    "コピーライティング", "ライティング",
    "会計", "人事", "法務", "営業", "リード",
    "ブランディング", "pr", "広報", "研修", "教育",
    "金融", "fintech", "法律", "弁護士", "補助金",
]


def is_spam_domain(domain):
    """スパム/乱数ドメインの判定"""
    name_part = domain.split(".")[0]
    if len(name_part) > 15 and not any(c in name_part for c in ["-", "_"]):
        consonants = sum(1 for c in name_part.lower() if c in "bcdfghjklmnpqrstvwxyz")
        if consonants / max(len(name_part), 1) > 0.75:
            return True
    return False


def should_exclude(row_num, domain, company_name, ref_url, title, status, dr_str):
    """除外すべきかどうか判定。除外理由を返す（除外しない場合はNone）"""

    domain_lower = domain.lower()
    name_lower = company_name.lower() if company_name else ""
    title_lower = title.lower() if title else ""
    ref_lower = ref_url.lower() if ref_url else ""
    all_text = f"{domain_lower} {name_lower} {title_lower} {ref_lower}"

    # DR=0 のスパムチェック
    try:
        dr_val = int(dr_str) if dr_str else 0
    except (ValueError, TypeError):
        dr_val = 0

    if dr_val == 0 and is_spam_domain(domain):
        return "DR=0のスパムドメイン"

    # ドメインパターンチェック
    for pattern, reason in EXCLUDE_DOMAIN_PATTERNS:
        if re.search(pattern, domain_lower):
            # ポジティブキーワードチェック
            has_positive = any(pk in all_text for pk in POSITIVE_KEYWORDS)
            if not has_positive:
                return f"{reason}（ドメイン: {domain}）"

    # 社名・タイトルキーワードチェック
    for kw, reason in EXCLUDE_KEYWORDS_NAME_TITLE:
        if kw in name_lower or kw in title_lower:
            has_positive = any(pk in all_text for pk in POSITIVE_KEYWORDS)
            if not has_positive:
                return f"{reason}"

    # 外国語メインサイト判定
    if domain_lower.endswith((".com", ".net", ".org", ".io")):
        if company_name and re.match(r'^[a-zA-Z0-9\s\.\-\_\&\|\/\:\#]+$', company_name):
            if title and not re.search(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]', title):
                if not any(pk in all_text for pk in ["seo", "marketing", "japan", "japanese", "tokyo", ".jp", ".co.jp"]):
                    return "外国語メインサイト（日本語コンテンツなし）"

    # スパム的な社名パターン（ハートマーク等）
    if company_name and re.search(r'[❤️💗💕]', company_name):
        return "スパムサイト"
    if title and re.search(r'[❤️💗💕]', title):
        return "スパムサイト"

    return None


def extract_best_name(text, domain=None, title=None):
    """テキストからサイト名/社名を抽出する"""
    if not text:
        return None

    # 区切り文字で分割
    separators = [" | ", "｜", " - ", " – ", " — ", "│", " / "]
    parts = [text]
    for sep in separators:
        new_parts = []
        for p in parts:
            new_parts.extend(p.split(sep))
        parts = new_parts

    parts = [p.strip() for p in parts if p.strip() and len(p.strip()) >= 2]

    if not parts:
        return None

    # 「株式会社」等を含む部分を最優先
    corp_keywords = ["株式会社", "（株）", "(株)", "合同会社", "有限会社", "一般社団法人", "一般財団法人"]
    corp_parts = [p for p in parts if any(k in p for k in corp_keywords) and len(p) <= 50]
    if corp_parts:
        # 株式会社名を含む最も短い合理的なもの
        return min(corp_parts, key=len)

    # サービス名として適切な長さの部分を探す（短すぎず長すぎず）
    good_parts = [p for p in parts if 2 <= len(p) <= 30]

    if not good_parts:
        good_parts = [p for p in parts if 2 <= len(p) <= 50]

    if not good_parts:
        return parts[0] if parts else None

    # ドメイン名に近いものを優先
    if domain:
        domain_name = domain.split(".")[0].lower().replace("-", "").replace("_", "")
        for p in good_parts:
            p_normalized = p.lower().replace(" ", "").replace("　", "")
            if domain_name in p_normalized or p_normalized in domain_name:
                return p

    # 最初のパート（メインタイトル側）を返す
    # ただし、最初のパートが記事タイトルっぽく長い場合は最後のパート（サイト名）
    first = good_parts[0]
    last = good_parts[-1]

    # 最後のパートにサイト名っぽい特徴があれば採用
    if len(good_parts) >= 2:
        # 日本語のサイト名パターン: 「〜サイト」「〜メディア」「〜ブログ」
        if len(last) < len(first) and len(last) <= 25:
            return last

    return first


def fix_company_name(company_name, domain, title):
    """社名を修正。修正不要ならNoneを返す"""
    if not company_name or company_name.strip() == "":
        if title:
            extracted = extract_best_name(title, domain)
            if extracted:
                return extracted
        return domain

    name = company_name.strip()

    # ドメインがそのまま入っている場合
    is_domain_name = (name == domain or
                      name == f"www.{domain}" or
                      name.startswith("http://") or
                      name.startswith("https://") or
                      (re.match(r'^[a-z0-9\-\.]+\.[a-z]{2,}$', name, re.IGNORECASE) and name == domain))

    if is_domain_name:
        # タイトルから社名を抽出
        if title:
            extracted = extract_best_name(title, domain)
            if extracted:
                return extracted
        return None  # ドメインのままでOK

    # 明らかに長い説明文が入っている場合（80文字以上）
    if len(name) > 80:
        extracted = extract_best_name(name, domain, title)
        if extracted and extracted != name and len(extracted) < len(name) * 0.7:
            return extracted

    # 区切り文字を含む場合 → 分割して適切な部分を抽出
    has_separator = any(sep in name for sep in [" | ", "｜", " - ", " – ", " — ", "│"])
    if has_separator and len(name) > 30:
        extracted = extract_best_name(name, domain, title)
        if extracted and extracted != name and len(extracted) < len(name):
            return extracted

    return None  # 修正不要


# メイン処理
exclude_rows = []
name_fixes = []

for row_num, row in contact_rows:
    domain = row.get("ドメイン", "").strip()
    company_name = row.get("社名", "").strip()
    ref_url = row.get("参考リンクページURL", "").strip()
    status = row.get("ステータス", "").strip()
    dr_str = row.get("DR", "0").strip()
    title = title_by_domain.get(domain, "")

    # 除外判定
    reason = should_exclude(row_num, domain, company_name, ref_url, title, status, dr_str)
    if reason:
        exclude_rows.append({
            "row": row_num,
            "domain": domain,
            "reason": reason
        })

    # 社名修正判定
    new_name = fix_company_name(company_name, domain, title)
    if new_name is not None:
        name_fixes.append({
            "row": row_num,
            "domain": domain,
            "old_name": company_name,
            "new_name": new_name
        })

# --- 手動で確認して修正が必要なケースを補正 ---
# extract_best_nameの結果を手動検証して問題のある結果を修正

manual_overrides = {
    # row: (old_name_check, correct_new_name)  - old_name_checkは検証用
}

# 社名修正の品質チェック: 明らかにおかしい結果をフィルタ
cleaned_name_fixes = []
for fix in name_fixes:
    new = fix["new_name"]
    old = fix["old_name"]

    # 新しい名前が2文字以下の場合はスキップ（品質不足）
    if len(new) <= 2:
        continue

    # 新しい名前が年号だけの場合はスキップ
    if re.match(r'^\d{4}$', new):
        continue

    # 新しい名前が「最短で」のように文の途中で切れている場合
    if new.endswith(("で", "の", "を", "に", "が", "は", "と", "も", "から", "まで", "より", "へ")):
        # タイトルから再抽出を試みる
        domain = fix["domain"]
        title = title_by_domain.get(domain, "")
        if title:
            re_extracted = extract_best_name(title, domain)
            if re_extracted and len(re_extracted) > 2 and not re_extracted.endswith(("で", "の", "を", "に", "が", "は", "と")):
                fix["new_name"] = re_extracted
            else:
                continue  # どうしようもなければスキップ
        else:
            continue

    # 「/ 」で始まる場合は除去
    if new.startswith("/ ") or new.startswith("／ "):
        fix["new_name"] = new.lstrip("/ ／").strip()

    cleaned_name_fixes.append(fix)

name_fixes = cleaned_name_fixes

# 結果出力
result = {
    "range": "331-660",
    "exclude_rows": exclude_rows,
    "name_fixes": name_fixes,
    "summary": {
        "対象行数": len(contact_rows),
        "除外件数": len(exclude_rows),
        "社名修正件数": len(name_fixes)
    }
}

with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print(f"\n=== クレンジング結果 ===")
print(f"対象行数: {len(contact_rows)}")
print(f"除外件数: {len(exclude_rows)}")
print(f"社名修正件数: {len(name_fixes)}")

print(f"\n--- 除外サイト ---")
for ex in exclude_rows:
    print(f"  行{ex['row']}: {ex['domain']} - {ex['reason']}")

print(f"\n--- 社名修正 ---")
for fix in name_fixes:
    print(f"  行{fix['row']}: {fix['domain']}: 「{fix['old_name'][:40]}...」→「{fix['new_name']}」" if len(fix['old_name']) > 40 else f"  行{fix['row']}: {fix['domain']}: 「{fix['old_name']}」→「{fix['new_name']}」")

# 除外理由の集計
reason_counts = {}
for ex in exclude_rows:
    # 理由からカッコ内のドメイン情報を除去して集計
    r = re.sub(r'（ドメイン:.*?）', '', ex['reason']).strip()
    reason_counts[r] = reason_counts.get(r, 0) + 1

print(f"\n--- 除外理由の集計 ---")
for reason, count in sorted(reason_counts.items(), key=lambda x: -x[1]):
    print(f"  {reason}: {count}件")

print(f"\n結果保存先: {OUTPUT_JSON}")
