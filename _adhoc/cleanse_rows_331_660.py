#!/usr/bin/env python3
"""
被リンク営業リスト クレンジング: 行331〜660
- 除外すべきサイトの特定
- 社名の修正
"""

import csv
import json
import re

# ファイルパス
CONTACT_CSV = r"C:\Users\rikit\Projects\2_クライアントデータ\malna\nonaka\被リンク営業リスト_連絡先付き.csv"
ORIGINAL_CSV = r"C:\Users\rikit\Projects\2_クライアントデータ\malna\nonaka\被リンク営業リスト.csv"
OUTPUT_JSON = r"C:\Users\rikit\Projects\_adhoc\cleanse_result_2.json"

# 連絡先CSVを読み込み (行331〜660, 1-indexed, ヘッダー除く)
with open(CONTACT_CSV, "r", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)
    contact_rows = []
    for i, row in enumerate(reader, start=2):  # ヘッダーが行1なのでデータは行2から
        if 332 <= i <= 661:  # 行331〜660 (0-indexed: 330〜659, 1-indexed data rows: 331〜660)
            contact_rows.append((i - 1, row))  # i-1 で実際の行番号 (ヘッダー除く1-indexed)

# 元CSVからリンクページタイトルをドメインで引ける辞書を作成
title_by_domain = {}
with open(ORIGINAL_CSV, "r", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)
    for row in reader:
        domain = row.get("ドメイン", "").strip()
        title = row.get("リンクページタイトル", "").strip()
        if domain and title:
            title_by_domain[domain] = title

print(f"連絡先CSV 読み込み行数: {len(contact_rows)}")
print(f"元CSV タイトル辞書エントリ数: {len(title_by_domain)}")

# --- 除外判定 ---

# 除外キーワード（ドメイン、社名、タイトルで判定）
EXCLUDE_KEYWORDS_DOMAIN = [
    "pet.", "pets.", "dog.", "cat.", "vet.", "veterinary",
    "beauty.", "salon.", "nail.", "hair.", "esthe.",
    "restaurant.", "food.", "recipe.", "cooking.", "cafe.", "bakery.",
    "cleaning.", "laundry.", "wash.",
    "flower.", "florist.", "garden.",
    "dental.", "clinic.", "hospital.",
    "fishing.", "travel.",
]

EXCLUDE_KEYWORDS_NAME_TITLE = [
    "ペットフード", "ドッグフード", "キャットフード", "犬", "猫", "ペット用品",
    "動物病院", "獣医",
    "美容院", "美容室", "ヘアサロン", "ネイルサロン", "エステ",
    "レストラン", "飲食店", "料理教室",
    "クリーニング", "洗濯",
    "花屋", "フラワー",
    "歯科", "歯医者",
    "釣り具", "釣具",
    "葬儀", "葬祭", "墓石", "仏壇",
    "ウェディング", "ブライダル", "結婚式場",
    "ゴルフ場", "ゴルフスクール",
    "整体院", "整骨院", "鍼灸", "マッサージ",
    "不動産賃貸", "賃貸物件",
    "着物レンタル", "振袖",
    "ペットショップ", "トリミング",
    "自動車修理", "板金塗装", "車検",
    "ハウスクリーニング",
    "害虫駆除", "害獣駆除",
    "水回り修理", "水道工事",
    "引越し",
    "エアコン取付",
    "リフォーム施工",
    "塗装工事", "外壁塗装",
]

# SEO/マーケ/ビジネス関連のポジティブキーワード
KEEP_KEYWORDS = [
    "seo", "marketing", "マーケティング", "コンテンツ", "広告", "web制作",
    "デジタル", "メディア", "hr", "人材", "採用", "キャリア", "就活", "転職",
    "saas", "ツール", "crm", "ma ", "it", "テック", "tech", "dx",
    "コンサル", "ビジネス", "経営", "スタートアップ", "startup",
    "ニュース", "news", "メディア", "media", "ブログ",
    "エンジニア", "プログラミング", "開発",
    "リスティング", "アフィリエイト", "affiliate",
    "データ分析", "analytics", "アクセス解析",
    "ホームページ制作", "webデザイン", "ui", "ux",
    "ec", "eコマース", "通販", "ネットショップ",
    "sns", "ソーシャル", "動画",
    "セキュリティ", "security",
    "クラウド", "cloud", "aws", "azure",
    "ai", "機械学習", "chatgpt",
    "コピーライティング", "ライティング",
    "会計", "経理", "人事", "労務", "法務", "総務",
    "営業", "sales", "リード",
    "ブランディング", "pr", "広報",
    "研修", "教育", "eラーニング",
    "物流", "ロジスティクス",
    "金融", "fintech", "保険",
    "法律", "弁護士", "士業",
    "補助金", "助成金",
]


def is_spam_domain(domain):
    """スパム/乱数ドメインの判定"""
    name_part = domain.split(".")[0]
    # 長い乱数文字列
    if len(name_part) > 15 and not any(c in name_part for c in ["-", "_"]):
        consonants = sum(1 for c in name_part.lower() if c in "bcdfghjklmnpqrstvwxyz")
        if consonants / max(len(name_part), 1) > 0.75:
            return True
    return False


def should_exclude(row_num, domain, company_name, ref_url, title, status):
    """除外すべきかどうか判定。除外理由を返す（除外しない場合はNone）"""

    domain_lower = domain.lower()
    name_lower = company_name.lower()
    title_lower = title.lower() if title else ""
    ref_lower = ref_url.lower() if ref_url else ""
    all_text = f"{domain_lower} {name_lower} {title_lower} {ref_lower}"

    # DR=0 のスパムチェック
    dr = row.get("DR", "0")
    try:
        dr_val = int(dr)
    except (ValueError, TypeError):
        dr_val = 0

    if dr_val == 0 and is_spam_domain(domain):
        return "DR=0のスパムドメイン"

    # ステータスチェック（閉鎖・アクセス不能）- ただしHTTP 403は除外しない（問い合わせURLの問題の可能性）
    # 完全にアクセス不能なもののみ除外

    # ドメインキーワードチェック
    for kw in EXCLUDE_KEYWORDS_DOMAIN:
        if kw in domain_lower:
            # ただし pet.laetitien のようなサブドメインの場合のみ
            # marketing.pet.com のようなケースは除外しない
            return f"ドメインに除外キーワード「{kw}」を含む"

    # 社名・タイトルキーワードチェック
    for kw in EXCLUDE_KEYWORDS_NAME_TITLE:
        if kw in name_lower or kw in title_lower:
            # ポジティブキーワードも含む場合はスキップ（例：「SEOコンサルのペット業界事例」は残す）
            has_positive = any(pk in all_text for pk in KEEP_KEYWORDS[:20])  # 上位のポジティブKWのみ
            if not has_positive:
                return f"社名/タイトルに除外キーワード「{kw}」を含む"

    # 外国語メインサイト判定（ドメインが .com/.net/.org で社名がアルファベットのみ、タイトルも英語のみ）
    if domain_lower.endswith((".com", ".net", ".org", ".io")):
        # 社名が完全に英字で、タイトルも日本語を含まない場合
        if company_name and re.match(r'^[a-zA-Z0-9\s\.\-\_\&\|]+$', company_name):
            if title and not re.search(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]', title):
                # ただしSEO/マーケ関連の英語サイトは残す
                if not any(pk in all_text for pk in ["seo", "marketing", "japan", "japanese", "tokyo"]):
                    return "外国語メインサイト（日本語コンテンツなし）"

    return None


def fix_company_name(company_name, domain, title):
    """社名を修正。修正不要ならNoneを返す"""
    if not company_name or company_name.strip() == "":
        return domain  # 空欄ならドメイン名

    name = company_name.strip()

    # ドメインがそのまま入っている場合
    if name == domain or name == f"www.{domain}" or name == f"https://{domain}" or name == f"http://{domain}":
        # タイトルから社名を抽出してみる
        if title:
            extracted = extract_site_name_from_title(title)
            if extracted:
                return extracted
        return None  # ドメインのままでOK（修正不要として扱う）

    # 明らかに長い説明文が入っている場合（60文字以上）
    if len(name) > 60:
        extracted = extract_site_name_from_title(name)
        if extracted and extracted != name:
            return extracted

    # 区切り文字で分割して最も適切な部分を抽出
    separators = [" | ", " - ", " – ", " — ", "｜", "│", " / "]
    for sep in separators:
        if sep in name:
            parts = [p.strip() for p in name.split(sep) if p.strip()]
            if len(parts) >= 2:
                # 最も短くて意味のある部分を選ぶ
                candidates = [p for p in parts if 2 <= len(p) <= 40]
                if candidates:
                    # 「株式会社」「（株）」を含む部分を優先
                    corp_parts = [p for p in candidates if any(k in p for k in ["株式会社", "（株）", "合同会社", "有限会社"])]
                    if corp_parts:
                        best = min(corp_parts, key=len)
                        if best != name:
                            return best
                    # なければ最も短い部分
                    best = min(candidates, key=len)
                    if best != name and len(best) < len(name) * 0.8:
                        return best

    # URLパターンが含まれている場合
    if re.search(r'https?://', name) or re.search(r'www\.', name):
        if title:
            extracted = extract_site_name_from_title(title)
            if extracted:
                return extracted
        return domain

    return None  # 修正不要


def extract_site_name_from_title(text):
    """タイトルや長い文字列からサイト名/社名を抽出"""
    if not text:
        return None

    # 区切り文字で分割
    separators = [" | ", " - ", " – ", " — ", "｜", "│", " / "]
    parts = [text]
    for sep in separators:
        new_parts = []
        for p in parts:
            new_parts.extend(p.split(sep))
        parts = new_parts

    parts = [p.strip() for p in parts if p.strip()]

    if not parts:
        return None

    # 「株式会社」等を含む部分を優先
    corp_parts = [p for p in parts if any(k in p for k in ["株式会社", "（株）", "合同会社", "有限会社", "一般社団法人", "一般財団法人"])]
    if corp_parts:
        return min(corp_parts, key=len)

    # 最後の部分がサイト名であることが多い（「記事タイトル | サイト名」パターン）
    if len(parts) >= 2:
        last = parts[-1]
        if 2 <= len(last) <= 40:
            return last

    # 最も短い部分
    candidates = [p for p in parts if 2 <= len(p) <= 40]
    if candidates:
        return min(candidates, key=len)

    return None


# メイン処理
exclude_rows = []
name_fixes = []

for row_num, row in contact_rows:
    domain = row.get("ドメイン", "").strip()
    company_name = row.get("社名", "").strip()
    ref_url = row.get("参考リンクページURL", "").strip()
    status = row.get("ステータス", "").strip()
    title = title_by_domain.get(domain, "")

    # 除外判定
    reason = should_exclude(row_num, domain, company_name, ref_url, title, status)
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
    print(f"  行{fix['row']}: {fix['domain']}: 「{fix['old_name']}」→「{fix['new_name']}」")

print(f"\n結果保存先: {OUTPUT_JSON}")
