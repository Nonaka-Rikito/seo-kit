#!/usr/bin/env python3
"""
cleanse_result_3.json の社名修正を手動で修正する
"""
import json

OUTPUT = r"C:\Users\rikit\Projects\_adhoc\cleanse_result_3.json"

with open(OUTPUT, "r", encoding="utf-8") as f:
    data = json.load(f)

# 手動修正マップ: row -> correct new_name (or None to remove the fix)
manual_fixes = {
    685: "アクセライト株式会社",  # accelainc.com - 中小企業向けメディア
    700: "株式会社シードアシスト",  # movie.seedassist.co.jp
    703: "株式会社モディッシュ",  # modish.co.jp
    723: "Career Ladder",  # careerladder.jp - M&A仲介転職エージェント
    742: "株式会社バースタイプ",  # verse-type.co.jp
    746: "プレア",  # plea-mm.com - 大分のweb制作
    748: "株式会社ナード",  # nerd.co.jp
    749: "株式会社SOZO",  # sozoinc.jp
    752: "ポラリスアカデミア",  # polaris-academia.co.jp
    775: "みつもり.com",  # mitu-mori.com
    778: "BNGパートナーズ",  # bngpartners.jp
    800: "KOBUSHI MARKETING",  # kobushi.marketing
    803: "Cast Me!",  # business.boujee.jp
    815: "インターンバイト",  # internbaito.com - 社名はウィルゲートではなくサービス名
    829: "Launch Studio",  # launchstudio.jp
    872: "suadd",  # suadd.com
    886: "B2Bマーケティング株式会社",  # b2b-marketing.co.jp
    903: "ArchRise",  # archrise-works.com
    912: "キャリコネ企業研究リサコ",  # corp-research.jp
    934: "なんばこめじるし",  # nam-come.com
    935: "TMCデジタル",  # tmcdigital.jp
    936: "安河内哲也",  # yasukochi.jp
    942: "民泊投資情報ナビ",  # blog.sogoseisaku.jp
}

# 削除すべきエントリ（修正が不要なもの）
remove_rows = set()

# 修正を適用
new_name_fixes = []
for item in data["name_fixes"]:
    row = item["row"]
    if row in remove_rows:
        continue
    if row in manual_fixes:
        item["new_name"] = manual_fixes[row]
    new_name_fixes.append(item)

data["name_fixes"] = new_name_fixes
data["summary"]["社名修正件数"] = len(new_name_fixes)

with open(OUTPUT, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"Updated {len(manual_fixes)} name fixes")
print(f"Total name fixes: {len(new_name_fixes)}")
print(f"Total excludes: {data['summary']['除外件数']}")
