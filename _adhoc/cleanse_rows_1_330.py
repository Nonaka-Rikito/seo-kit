#!/usr/bin/env python3
"""
被リンク営業リスト クレンジングスクリプト（行1〜330）
- 除外すべきサイトの特定
- 社名の修正
"""
import csv
import json
import re

# ファイルパス
CONTACT_CSV = r"C:\Users\rikit\Projects\2_クライアントデータ\malna\nonaka\被リンク営業リスト_連絡先付き.csv"
ORIGINAL_CSV = r"C:\Users\rikit\Projects\2_クライアントデータ\malna\nonaka\被リンク営業リスト.csv"
OUTPUT_JSON = r"C:\Users\rikit\Projects\_adhoc\cleanse_result_1.json"

# 連絡先付きCSV読み込み
with open(CONTACT_CSV, encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)
    contact_rows = list(reader)

# 元CSV読み込み（リンクページタイトル・カテゴリー取得）
with open(ORIGINAL_CSV, encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)
    original_rows = list(reader)

# ドメインでインデックス
original_by_domain = {}
for row in original_rows:
    domain = row.get("ドメイン", "").strip()
    if domain:
        original_by_domain[domain] = row

# 対象: 行1〜330（0-indexed: 0〜329）
target_rows = contact_rows[:330]

# ============================================================
# 除外対象ドメイン
# ============================================================
EXCLUDE_DOMAINS = {
    # ペットフード・ペット系EC
    "pet.laetitien.co.jp": "ペットフード販売EC（レティシアン）",
    "laetitienpet.com": "ペットフード販売EC（レティシアン）",
    "staging-pet.laetitien.co.jp": "ペットフード販売EC（レティシアンステージング環境）",
    "konokototomoni.com": "ペットフード販売EC（このこのごはん）",
    "dogfood.jpn.org": "ドッグフード比較サイト",
    "mogwandogfood.co.jp": "ペットフード販売EC（モグワン）",
    "canagandogfood.co.jp": "ペットフード販売EC（カナガン）",
    "petfamilyins.co.jp": "ペット保険会社（SEO/マーケティングに無関係）",
    "petlife.asia": "ペット情報サイト（SEO/マーケティングに無関係）",

    # クリーニング・修理系
    "downjacket.pro": "ダウンジャケットクリーニング専門店",
    "bag-repair.pro": "高級バッグ修理専門店",
    "house-cleaning.heteml.net": "ハウスクリーニング比較サイト",
    "osoujikakumei.jp": "おそうじ革命（ハウスクリーニング業者）",
    "xs036891.xsrv.jp": "ハウスクリーニング比較サイト（SEO/マーケティングに無関係）",

    # 巨大プラットフォーム（営業先として不適切）
    "ja.wikipedia.org": "Wikipedia（営業先として不適切な巨大プラットフォーム）",
    "en.wikipedia.org": "Wikipedia英語版（営業先として不適切、外国語メイン）",
    "youtube.com": "YouTube（営業先として不適切な巨大プラットフォーム）",
    "ameblo.jp": "アメーバブログ（営業先として不適切な巨大プラットフォーム）",
    "medium.com": "Medium（営業先として不適切な巨大プラットフォーム）",
    "gist.github.com": "GitHub Gist（営業先として不適切な巨大プラットフォーム）",
    "d.hatena.ne.jp": "はてなブログタグ（営業先として不適切な巨大プラットフォーム）",
    "b.hatena.ne.jp": "はてなブックマーク（営業先として不適切な巨大プラットフォーム）",
    "blog.hatena.ne.jp": "はてなブログ（営業先として不適切な巨大プラットフォーム）",
    "jbbs.shitaraba.net": "したらば掲示板（営業先として不適切な巨大プラットフォーム）",
    "speakerdeck.com": "Speaker Deck（営業先として不適切な巨大プラットフォーム）",
    "creators.spotify.com": "Spotify（営業先として不適切な巨大プラットフォーム）",
    "developers.google.com": "Google for Developers（営業先として不適切な巨大プラットフォーム）",
    "qiita.com": "Qiita（営業先として不適切な巨大プラットフォーム）",
    "zenn.dev": "Zenn（営業先として不適切な巨大プラットフォーム）",
    "crowdworks.jp": "クラウドワークス（営業先として不適切な巨大プラットフォーム）",
    "pitta.me": "Pitta（カジュアル面談プラットフォーム、営業先として不適切）",

    # 個人ブログ（SEO/ビジネスに無関係）
    "highdy-pc.hatenablog.com": "個人日記ブログ（PC関連の個人ブログ）",
    "ab10.hatenablog.com": "個人日記ブログ",
    "gw3wgw.hatenablog.com": "テクノロジー犯罪研究所（個人ブログ、無関係テーマ）",
    "souta-k.hatenadiary.jp": "個人日記ブログ（寝そべり族）",
    "computational-sediment-hyd.hatenablog.jp": "個人技術ブログ（計算流砂水理、無関係分野）",
    "kanji.hatenablog.jp": "個人技術ブログ（かんちゃんの備忘録）",
    "error-daizenn.hatenablog.com": "個人ブログ（エラー大全集）",
    "tvrock69.cloudfree.jp": "個人PC活用サイト（文字化け、低品質）",

    # 外国語メインサイト
    "glints.com": "外国語メインサイト（ベトナム語求人サイト）",
    "kingranks.com": "外国語SEOサイト（英語、DR0トラフィック0）",
    "topseos.com": "外国語SEOランキングサイト（英語メイン）",
    "jetrank.com": "外国語SEOサービスサイト（英語、HTTP 403）",

    # スパム/低品質/ツール系
    "subdomainfinder.c99.nl": "サブドメインスキャンツール（スパム的サイト）",
    "siteprice.org": "トラフィックチェッカー（SEOツールサイト、営業先として不適切）",
    "sitelike.org": "類似サイト検索ツール（営業先として不適切）",

    # 自社サイト
    "malna.co.jp": "自社サイト（malna株式会社）",

    # 閉鎖・アクセス不能
    "softwareworld.co": "HTTP 403（アクセス不能、外国語サイト）",
    "hatenablogmedia.zendesk.com": "はてなブログメディアヘルプ（Zendesk、HTTP 403、営業先として不適切）",

    # 完全無関係業種
    "gc-yukizaki.jp": "ブランド時計・ジュエリー通販（完全無関係業種）",
    "ink-revolution.com": "プリンターインク通販（完全無関係業種）",
    "yattara.skr.jp": "こどもえん（保育施設、完全無関係業種）",
    "ebisu-fudousan.com": "不動産会社（完全無関係業種）",
    "reform.ebisu-fudousan.com": "リフォーム会社（完全無関係業種）",
    "koekisha.co.jp": "葬儀社（公益社、完全無関係業種）",
    "ryukyuasteeda.jp": "琉球アスティーダ（卓球チーム、完全無関係業種）",
}

# ============================================================
# 社名手動修正マップ（自動抽出より優先）
# ============================================================
MANUAL_NAME_FIXES = {
    "keywordmap.jp": "Keywordmap",
    "wacul-ai.com": "WACUL",
    "aidma-hd.jp": "アイドマ・ホールディングス",
    "hatarakigai.info": "働きがいのある会社研究所",
    "gmg.cloudcircus.jp": "クラウドサーカス",
    "ferret-plus.com": "ferret",
    "marketingnative.jp": "Marketing Native",
    "syukatsu-kaigi.jp": "就活会議",
    "muuuuu.org": "MUUUUU.ORG",
    "synergy-career.co.jp": "シナジーキャリア",
    "nttdata-strategy.com": "NTTデータ経営研究所",
    "cm.marke-media.net": "マーケメディア",
    "prizma-link.com": "プリズマリンク",
    "switchitmaker2.com": "switchitmaker2",
    "fortee.jp": "fortee",
    "lmi.ne.jp": "リンクアンドモチベーション",
    "sateraito.jp": "サテライトオフィス",
    "sedesign.co.jp": "SEデザイン",
    "tokyo-cci.or.jp": "東京商工会議所",
    "example3.com": "example3.com",
    "coki.jp": "coki",
    "kagemusya.biz-samurai.com": "CROCO",
    "japan-ai.geniee.co.jp": "Japan AI（ジーニー）",
    "break-marketing-program.jp": "Break Marketing Program",
    "webmarks.jp": "WEBMARKS",
    "blogs.bizmakoto.jp": "オルタナティブ・ブログ",
    "intloop.com": "INTLOOP",
    "x-i.co.jp": "クロスアイ",
    "ferret-one.com": "ferret One",
    "cone-c-slide.com": "c-slide",
    "so-labo.co.jp": "株式会社SoLabo",
    "kinabal.co.jp": "Kinabal",
    "yuryoweb.com": "優良WEB",
    "webwriter-pro.co.jp": "Webライタープロ",
}

# ============================================================
# 社名修正ロジック
# ============================================================
def fix_company_name(name, domain, orig_row):
    """社名を修正する。修正不要ならNoneを返す"""
    if not name or not name.strip():
        return domain

    name = name.strip()

    # ドメインがそのまま入っている場合
    if name == domain or name == f"www.{domain}" or name.startswith("http"):
        if orig_row:
            title = orig_row.get("リンクページタイトル", "")
            if title:
                extracted = extract_site_name_from_title(title)
                if extracted:
                    return extracted
        return domain

    # 長すぎる名前（説明文がそのまま入っている）: 40文字以上
    if len(name) > 40:
        extracted = extract_site_name_from_long_text(name)
        if extracted and extracted != name:
            return extracted

    return None


def extract_site_name_from_title(title):
    """タイトルからサイト名部分を抽出"""
    separators = [" | ", " - ", "｜", " — ", " – "]
    for sep in separators:
        if sep in title:
            parts = title.split(sep)
            last = parts[-1].strip()
            if 2 <= len(last) <= 30:
                return last
            first = parts[0].strip()
            if 2 <= len(first) <= 30:
                return first
    return None


def extract_site_name_from_long_text(text):
    """長いテキストからサイト名を抽出"""
    separators = [" | ", " - ", "｜", " — ", " – "]
    for sep in separators:
        if sep in text:
            parts = text.split(sep)
            first = parts[0].strip()
            if 2 <= len(first) <= 30:
                return first

    # 「は、」「を」等の助詞で切る
    for sep in ["は、", "は "]:
        if sep in text:
            parts = text.split(sep)
            first = parts[0].strip()
            if 2 <= len(first) <= 30:
                return first

    # 句読点や記号で切る
    for i, c in enumerate(text):
        if c in "。（(「【":
            if 2 <= i <= 30:
                return text[:i]

    return text[:30] if len(text) > 30 else None


# ============================================================
# メイン処理
# ============================================================
exclude_rows = []
name_fixes = []

for idx, row in enumerate(target_rows):
    row_num = idx + 1
    domain = row.get("ドメイン", "").strip()
    company_name = row.get("社名", "").strip()

    orig_row = original_by_domain.get(domain, {})

    # === 除外判定 ===
    if domain in EXCLUDE_DOMAINS:
        exclude_rows.append({
            "row": row_num,
            "domain": domain,
            "reason": EXCLUDE_DOMAINS[domain]
        })
        continue

    # === 社名修正判定（手動 > 自動） ===
    if domain in MANUAL_NAME_FIXES:
        new_name = MANUAL_NAME_FIXES[domain]
        if new_name != company_name:
            name_fixes.append({
                "row": row_num,
                "domain": domain,
                "old_name": company_name[:60] + ("..." if len(company_name) > 60 else ""),
                "new_name": new_name
            })
    else:
        new_name = fix_company_name(company_name, domain, orig_row)
        if new_name is not None:
            name_fixes.append({
                "row": row_num,
                "domain": domain,
                "old_name": company_name[:60] + ("..." if len(company_name) > 60 else ""),
                "new_name": new_name
            })

# ソート
name_fixes = sorted(name_fixes, key=lambda x: x["row"])

# 結果出力
result = {
    "range": "1-330",
    "exclude_rows": sorted(exclude_rows, key=lambda x: x["row"]),
    "name_fixes": name_fixes,
    "summary": {
        "除外件数": len(exclude_rows),
        "社名修正件数": len(name_fixes)
    }
}

with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print(f"Done: {OUTPUT_JSON}")
print(f"Exclude: {len(exclude_rows)}")
print(f"Name fixes: {len(name_fixes)}")
print()

# Summarize exclude reasons
reason_counts = {}
for er in exclude_rows:
    reason = er["reason"]
    if "ペット" in reason or "ドッグフード" in reason:
        cat = "Pet/DogFood"
    elif "プラットフォーム" in reason:
        cat = "Platform"
    elif "個人" in reason:
        cat = "Personal blog"
    elif "外国語" in reason or "英語" in reason:
        cat = "Foreign lang"
    elif "スパム" in reason or "ツール" in reason:
        cat = "Spam/Tool"
    elif "自社" in reason:
        cat = "Own site"
    elif "クリーニング" in reason or "修理" in reason or "ハウス" in reason:
        cat = "Cleaning/Repair"
    elif "無関係" in reason:
        cat = "Irrelevant biz"
    elif "403" in reason or "アクセス不能" in reason or "Zendesk" in reason:
        cat = "Inaccessible/Help"
    else:
        cat = "Other"
    reason_counts[cat] = reason_counts.get(cat, 0) + 1

for cat, count in sorted(reason_counts.items(), key=lambda x: -x[1]):
    print(f"  {cat}: {count}")
