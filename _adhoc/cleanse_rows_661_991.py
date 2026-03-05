#!/usr/bin/env python3
"""
被リンク営業リスト クレンジングスクリプト（行661〜991）
- 除外すべきサイトの特定
- 社名の修正
"""
import csv
import json
import re

# ファイルパス
CONTACT_CSV = r"C:\Users\rikit\Projects\2_クライアントデータ\malna\nonaka\被リンク営業リスト_連絡先付き.csv"
ORIGINAL_CSV = r"C:\Users\rikit\Projects\2_クライアントデータ\malna\nonaka\被リンク営業リスト.csv"
OUTPUT_JSON = r"C:\Users\rikit\Projects\_adhoc\cleanse_result_3.json"

# 対象範囲（1-indexed, ヘッダー除く）
START_ROW = 661
END_ROW = 991

def load_csv(filepath):
    """CSVを読み込み、行番号付きで返す"""
    rows = []
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
        for i, row in enumerate(reader, start=1):
            rows.append((i, row))
    return header, rows

def get_title_map(original_csv):
    """元CSVからドメイン→リンクページタイトルのマップを作成"""
    title_map = {}
    with open(original_csv, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
        # リンクページタイトル列のインデックスを探す
        title_idx = None
        for i, h in enumerate(header):
            if "リンクページタイトル" in h:
                title_idx = i
                break
        if title_idx is None:
            return title_map
        for row in reader:
            if len(row) > title_idx:
                domain = row[0]
                title_map[domain] = row[title_idx]
    return title_map

def should_exclude(domain, company_name, ref_url, title, dr, traffic, status):
    """除外すべきサイトかどうか判定。除外理由を返す。Noneなら残す。"""
    domain_lower = domain.lower()
    name_lower = company_name.lower()
    title_lower = title.lower() if title else ""
    ref_lower = ref_url.lower() if ref_url else ""

    # 1. スパム/低品質サイト - madam72.xyz系（乱数ドメイン、DR=0、中国語映画サイト）
    if "madam72.xyz" in domain_lower:
        return "スパムサイト（madam72.xyz系中国語映画サイト）"

    # 2. 乱数文字列ドメイン（英数字の乱数 + 共通ドメイン）
    random_pattern = re.compile(r'^[a-z0-9]{8,}\.[a-z]+\.[a-z]+$')
    if random_pattern.match(domain_lower) and int(traffic) == 0:
        return f"スパムサイト（乱数ドメイン、トラフィック0）"

    # 3. 同一英語記事を持つハリケーンIrmaスパムサイト群
    hurricane_domains = [
        "webranksofworld.site", "howtorankfast.site", "worldwidetopweb.site",
        "99-best.site", "microlinkofworld.site"
    ]
    if domain_lower in hurricane_domains:
        return "スパムサイト（英語スパムコンテンツ群）"

    # 4. 外国語メインサイト
    if "directorycell.com" in domain_lower:
        return "外国語メインサイト（英語のみ）"

    if "redcoolmedia.net" in domain_lower:
        return "外国語メインサイト（英語コンテンツ）"

    # 5. 閉鎖・アクセス不能サイト（DNS解決失敗など）
    dns_fail_domains = []
    if status and "getaddrinfo failed" in status:
        # ただし一部はまだ判断が必要
        pass  # ステータスだけでは除外しない、他の条件と合わせて判断

    # 6. ペット関連EC/サービス（SEO・マーケティングに無関係）
    pet_ec_patterns = [
        ("erva-dog.com", "ドッグスリング専門店（ペット用品EC）"),
        ("pet-foodist.jp", "ペットフーディスト養成講座（ペット関連）"),
        ("t-oppo.jp", "ペット用品EC（OPPO）"),
        ("dog.ceramida.jp", "犬の臭い対策ブログ（ペット特化）"),
        ("dog-salon-mocomoco.com", "ドッグフード口コミサイト"),
        ("pelthia.jp", "ドッグフードEC（PELTHIA）"),
        ("pet-siiku.com", "ペット飼育情報サイト"),
        ("dogduca.com", "犬のしつけ教室（DOG DUCA）"),
        ("inutome.jp", "犬関連メディア（イヌトミィ）"),
        ("amarico.com", "ドッグフードEC（Amarico）"),
    ]
    for pat_domain, reason in pet_ec_patterns:
        if pat_domain in domain_lower:
            return reason

    # 7. 犬のしつけ教室
    if "study-dog-school.com" in domain_lower:
        return "犬のしつけ教室（完全無関係業種）"

    # 8. 動物病院
    animal_hospital_domains = [
        ("kinswith-vet.com", "動物病院（KINS WITH）"),
        ("roserose-ac.com", "動物病院（ローズローズアニマルクリニック）"),
        ("iogi-animal.com", "動物病院（井荻アニマルメディカルセンター）"),
        ("npo-la-vida.org", "動物保護NPO"),
    ]
    for pat_domain, reason in animal_hospital_domains:
        if pat_domain in domain_lower:
            return reason

    # 9. クリーニング/ハウスクリーニング
    if "al-on.com" in domain_lower:
        return "ハウスクリーニング業者（完全無関係業種）"
    if "makotoya-cleaning.jp" in domain_lower:
        return "クリーニング店（完全無関係業種）"

    # 10. 整骨院
    if "sakaguchi-seikotsuin.com" in domain_lower:
        return "整骨院（完全無関係業種）"

    # 11. 美容院/理容院
    if "hairsalon-mitsuishi-hp.com" in domain_lower:
        return "美容院・理容院（完全無関係業種）"

    # 12. 離乳食宅配
    if "shoku.zenhp.co.jp" in domain_lower:
        return "離乳食宅配サービス（完全無関係業種）"

    # 13. アダルトサイト
    if "av-sommelier.online" in domain_lower:
        return "アダルトサイト（エログの教科書）"

    # 14. サウナ系（明確にSEO/マーケティングと無関係）
    if "saunameetsgirl.com" in domain_lower:
        return "サウナ系個人ブログ（無関係業種）"

    # 15. ギャンブル/ベッティングサイト
    if "アイベット.com" in domain:
        return "海外ブックメーカー・ギャンブルサイト"

    # 16. 賃貸管理/不動産管理（SEOに無関係）
    if "hopehouse.co.jp" in domain_lower:
        return "賃貸管理会社（完全無関係業種）"

    # 17. 音楽/DTM系（無関係）
    if "synthsonic.net" in domain_lower:
        return "音楽・DTM系サイト（完全無関係業種）"

    # 18. フルート情報サイト
    if "fluteirassai.com" in domain_lower:
        return "フルート・音楽情報サイト（完全無関係業種）"

    # 19. ゲイライフスタイルマガジン
    if "kazukick.work" in domain_lower:
        return "ゲイライフスタイルブログ（無関係業種）"

    # 20. 宅食/食品サービス
    if "pal-blog.com" in domain_lower:
        return "食品宅配サービスブログ（パルシステム）"

    # 21. 家事代行
    if "en-job.jp" in domain_lower:
        return "家事代行サービス（完全無関係業種）"

    # 22. 災害リスク/防災
    if "daichi-risk.com" in domain_lower:
        return "災害リスク研究（ペット防災記事、完全無関係業種）"

    # 23. 子育てサロン
    if "salonstaff.mother-natures.com" in domain_lower:
        return "子育てサロンスタッフ求人（完全無関係業種）"

    # 24. 唐澤貴洋Wiki
    if "krsw-wiki.in" in domain_lower:
        return "2ちゃんねる系Wiki（低品質・不適切サイト）"

    # 25. ペット保険・飼い方
    # すでに pet-siiku.com は上で対処

    # 26. 食品レビュー
    if "kyomogochiso.com" in domain_lower:
        return "料理・食品レビューブログ（完全無関係業種）"

    # 27. トランクルーム比較
    if "sun-plazahome.com" in domain_lower:
        return "トランクルーム比較サイト（完全無関係業種）"

    # 28. 阿部梨園（農業）
    if "tips.abe-nashien.com" in domain_lower:
        return "農家の改善ブログ（完全無関係業種）"

    # 29. HSP系個人ブログ
    if "hsp.ryota-freedom.com" in domain_lower:
        return "HSP系個人ブログ（完全無関係業種）"

    # 30. バーレストラン（ただしSEO記事もある→SEO記事があるなら残す）
    # maxa.jp は SEO対策会社記事あり → 残す

    # 31. 文字化けサイト
    if "sipnstir.net" in domain_lower:
        return "文字化けサイト（低品質）"

    # 32. DNS解決不能 + トラフィック0 + スパム判定
    dns_fail_spam = [
        ("sozoinc.jp", None),  # これは企業サイトなので除外しない
        ("rurukblog.com", None),  # ブログなので除外しない
        ("nam-come.com", None),  # ホームページ情報サイト
        ("tmcdigital.jp", None),  # BtoBマーケティング
        ("yasukochi.jp", None),  # 教育系
    ]
    # DNS失敗でかつトラフィック0のものはケースバイケース

    # 33. moogry.com - Yahoo検索クローン的サイト
    if "moogry.com" in domain_lower:
        return "検索エンジンクローン/低品質サイト"

    # 34. news.pjdb.cc - HTTP 500エラー
    if "news.pjdb.cc" in domain_lower and status and "500" in status:
        return "サーバーエラー（HTTP 500）でアクセス不能"

    # 35. オフィス家具サブスク（fittingbox）- リンクページがCookieポリシー
    if "fittingbox.jp" in domain_lower:
        return "オフィス家具サブスク（リンクページがCookieポリシー、無関係）"

    # 36. 受付システム（receptiondesk）は企業サービスなので残す

    # 37. 一般社団法人はーとinはーとZR
    if "hinhzr.org" in domain_lower:
        return "動物保護系一般社団法人（完全無関係業種）"

    # 38. オフィスデザイン
    if "jimushodesign.com" in domain_lower:
        return "オフィスデザイン会社（無関係業種）"

    # 39. お役立ち.xyz - エンコードエラーでアクセス不能
    if "お役立ち.xyz" in domain:
        return "エンコードエラーでアクセス不能・個人ブログ"

    # 40. 個人の日記ブログ（SEO/ビジネスに無関係）
    if "blog.okashoi.net" in domain_lower:
        return "個人の技術日記ブログ（PHPカンファレンス参加記、無関係）"

    # 41. 農業
    # tips.abe-nashien.com は上で対処済み

    # 42. ゆとり世代の投資家jun - 投資ブログだがSEO/マーケティングには一応関連あり（サイト売買記事）
    # → 残す

    # 43. 暗号資産ブログ
    if "crypto-bear.net" in domain_lower:
        return "暗号資産個人ブログ（完全無関係業種）"

    # 44. アニメボックス
    if "animebox.jp" in domain_lower:
        return "アニメ情報サイト（完全無関係業種）"

    # 45. 大学共同研究（学術）
    if "aai.itri-apu.com" in domain_lower:
        return "大学共同研究プロジェクト（営業対象外）"

    # 46. ペット情報（toha2.fromation.co.jp - ペットカテゴリページ）
    if "toha2.fromation.co.jp" in domain_lower:
        # リンクページがペットカテゴリ + タイムアウトエラー
        return "ペット情報カテゴリページ＋アクセスタイムアウト"

    # 47. マクサ（バー＆グリル）- SEO記事もあるが本業は飲食店
    # → SEO記事があるので残す

    # 48. スポーツ系
    if "spo-gel.com" in domain_lower:
        return "スポーツ情報サイト（無関係業種）"

    # 49. 整骨院は対処済み

    # 50. ナイモノのオフショア開発は残す(IT系)

    # 51. システムパフォーマンス入門（ITだが営業対象外の個人ブログ）
    if "performance.oreda.net" in domain_lower:
        return "個人技術ブログ（Datadog監視記事、営業対象としてニッチすぎ）"

    # 52. コード関連の個人ブログ
    if "codenote.net" in domain_lower:
        # 英語で書かれている
        return "英語圏技術ブログ（日本語コンテンツなし）"

    return None  # 残す


def fix_company_name(company_name, domain, title):
    """社名が不適切な場合に修正する。修正不要ならNoneを返す。"""
    if not company_name or company_name.strip() == "":
        return domain  # 空欄ならドメイン

    name = company_name.strip()

    # ドメインがそのまま入っている場合
    if name == domain or name == f"www.{domain}":
        # タイトルから社名を推測
        if title:
            parts = re.split(r'[|｜\-–—]', title)
            # 最も短くて意味のある部分を選ぶ
            candidates = [p.strip() for p in parts if p.strip() and len(p.strip()) > 1]
            if candidates:
                # 最も短い部分（ただし2文字以上）
                shortest = min(candidates, key=len)
                if len(shortest) <= 50:
                    return shortest
        return None  # 修正不能、ドメインのまま

    # 長すぎる説明文が社名に入っている（50文字以上は怪しい）
    if len(name) > 50:
        # 区切り文字で分割して最短を取る
        parts = re.split(r'[|｜\-–—、。,.]', name)
        candidates = [p.strip() for p in parts if p.strip() and len(p.strip()) >= 2]
        if candidates:
            shortest = min(candidates, key=len)
            if len(shortest) <= 50 and shortest != name:
                return shortest
        # それでもダメならタイトルから
        if title:
            parts = re.split(r'[|｜\-–—]', title)
            candidates = [p.strip() for p in parts if p.strip() and len(p.strip()) >= 2]
            if candidates:
                shortest = min(candidates, key=len)
                if len(shortest) <= 50:
                    return shortest
        return None

    # 社名にURLが含まれている
    if "http" in name.lower() or "/" in name:
        if title:
            parts = re.split(r'[|｜\-–—]', title)
            candidates = [p.strip() for p in parts if p.strip() and len(p.strip()) >= 2]
            if candidates:
                shortest = min(candidates, key=len)
                if len(shortest) <= 50:
                    return shortest
        return domain

    # ページの説明文がそのまま入っている典型パターン
    description_patterns = [
        r'.*を.*する.*',
        r'.*のための.*',
        r'.*に関する.*情報.*',
    ]

    # 具体的に長い説明文チェック（30文字以上で、典型的な社名パターンでない）
    if len(name) > 30:
        # 株式会社/合同会社などが含まれていれば、それは社名の一部として妥当かもしれない
        if not re.search(r'(株式会社|合同会社|有限会社|一般社団法人|NPO法人)', name):
            parts = re.split(r'[|｜\-–—]', name)
            candidates = [p.strip() for p in parts if p.strip() and len(p.strip()) >= 2]
            if candidates and len(candidates) > 1:
                shortest = min(candidates, key=len)
                if len(shortest) <= 30 and shortest != name:
                    return shortest

    return None  # 修正不要


def main():
    print("Loading CSVs...")
    contact_header, contact_rows = load_csv(CONTACT_CSV)
    title_map = get_title_map(ORIGINAL_CSV)

    # 対象行を抽出
    target_rows = [(row_num, row) for row_num, row in contact_rows if START_ROW <= row_num <= END_ROW]
    print(f"Target rows: {len(target_rows)} (rows {START_ROW}-{END_ROW})")

    exclude_rows = []
    name_fixes = []

    for row_num, row in target_rows:
        domain = row[0] if len(row) > 0 else ""
        company_name = row[1] if len(row) > 1 else ""
        contact_url = row[2] if len(row) > 2 else ""
        dr = row[3] if len(row) > 3 else "0"
        traffic = row[4] if len(row) > 4 else "0"
        ref_url = row[8] if len(row) > 8 else ""
        status = row[9] if len(row) > 9 else ""

        title = title_map.get(domain, "")

        # 除外判定
        reason = should_exclude(domain, company_name, ref_url, title, dr, traffic, status)
        if reason:
            exclude_rows.append({
                "row": row_num,
                "domain": domain,
                "reason": reason
            })
            continue  # 除外サイトは社名修正不要

        # 社名修正判定
        new_name = fix_company_name(company_name, domain, title)
        if new_name and new_name != company_name:
            name_fixes.append({
                "row": row_num,
                "domain": domain,
                "old_name": company_name,
                "new_name": new_name
            })

    # 結果出力
    result = {
        "range": f"{START_ROW}-{END_ROW}",
        "exclude_rows": exclude_rows,
        "name_fixes": name_fixes,
        "summary": {
            "除外件数": len(exclude_rows),
            "社名修正件数": len(name_fixes)
        }
    }

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"\n=== 結果サマリー ===")
    print(f"除外件数: {len(exclude_rows)}")
    print(f"社名修正件数: {len(name_fixes)}")

    print(f"\n--- 除外理由の内訳 ---")
    reason_counts = {}
    for item in exclude_rows:
        # 理由のカテゴリを抽出
        r = item["reason"]
        # 括弧の前の部分をカテゴリとする
        cat = r.split("（")[0] if "（" in r else r
        reason_counts[cat] = reason_counts.get(cat, 0) + 1
    for reason, count in sorted(reason_counts.items(), key=lambda x: -x[1]):
        print(f"  {reason}: {count}件")

    print(f"\n--- 除外サイト一覧 ---")
    for item in exclude_rows:
        print(f"  行{item['row']}: {item['domain']} - {item['reason']}")

    print(f"\n--- 社名修正一覧 ---")
    for item in name_fixes:
        print(f"  行{item['row']}: {item['domain']}")
        print(f"    旧: {item['old_name']}")
        print(f"    新: {item['new_name']}")

    print(f"\n出力先: {OUTPUT_JSON}")

if __name__ == "__main__":
    main()
