# -*- coding: utf-8 -*-
"""
vip-limo.jp トピックKW（親キーワード）分析スクリプト
出力: topic_analysis_output.txt
"""
import os, sys, csv, io
from collections import defaultdict, Counter

BASE = os.path.dirname(os.path.abspath(__file__))
OUTPUT = os.path.join(BASE, "topic_analysis_output.txt")

# ─── ファイル定義 ───
EXPLORER_FILES = {
    "SegA_overview": os.path.join(BASE, "google_us_hire-car-japan-with-driver_overview_2026-02-25_21-12-58.csv"),
    "SegA_airport": os.path.join(BASE, "google_us_japan-airport-transfer_フレーズ一致_2026-02-25_21-13-23.csv"),
    "SegA_taxi": os.path.join(BASE, "google_us_japan-taxi_関連用語_2026-02-25_21-15-08.csv"),
    "SegBC_related": os.path.join(BASE, "google_jp_vip-送迎-ゲスト-送迎-コンシェルジュ-手配_関連用語_2026-02-25_21-15-57.csv"),
    "SegB_suggest1": os.path.join(BASE, "google_jp_ゲスト-送迎-コンシェルジュ-手配-ホテル-ハ_検索候補（サジェスト）_2026-02-25_21-17-33.csv"),
    "SegB_suggest2": os.path.join(BASE, "google_jp_ゲスト-送迎-コンシェルジュ-手配-ホテル-ハ_検索候補（サジェスト）_2026-02-25_21-18-24.csv"),
}
COMP_DIR = os.path.join(BASE, "競合オーガニックkw")
OWN_FILE = os.path.join(BASE, "自社kw", "vip-limo.jp-organic-keywords-subdomains-jp_2026-02-25_21-27-34.csv")

def read_csv(filepath):
    for enc in ['utf-16', 'utf-16-le', 'utf-8-sig', 'utf-8', 'cp932']:
        try:
            with open(filepath, 'r', encoding=enc) as f:
                content = f.read()
            delim = '\t' if '\t' in content.split('\n')[0] else ','
            reader = csv.DictReader(io.StringIO(content), delimiter=delim, quotechar='"')
            rows = []
            for row in reader:
                cleaned = {k.strip().strip('"').strip(): (v.strip().strip('"').strip() if v else '') for k, v in row.items()}
                rows.append(cleaned)
            if rows:
                return rows
        except:
            continue
    return []

def safe_int(val):
    if not val: return 0
    try: return int(val.strip().replace(',', ''))
    except:
        try: return int(float(val.strip().replace(',', '')))
        except: return 0

def is_english(text):
    if not text: return False
    alpha = [c for c in text if c.isalpha()]
    if not alpha: return False
    return sum(1 for c in alpha if ord(c) < 128) / len(alpha) > 0.7

# ─── データ構造 ───
parent_data = defaultdict(lambda: {
    'vol': 0, 'kd': 999, 'gvol': 0, 'tp': 0,
    'children': set(), 'child_vols': {}, 'cluster_vol': 0,
    'sources': set(), 'country': '', 'segment': None
})
comp_kws = defaultdict(set)  # kw -> set of competitor domains
own_kws = {}  # kw -> {vol, position, traffic, url}

out = open(OUTPUT, 'w', encoding='utf-8')
def p(text=''):
    print(text)
    out.write(text + '\n')

p("=" * 100)
p("vip-limo.jp トピックKW（親キーワード）分析")
p("=" * 100)

# ─── 1. Keywords Explorer ───
p("\n## 1. Keywords Explorer データ読み込み")
for label, fpath in EXPLORER_FILES.items():
    if not os.path.exists(fpath):
        p(f"  MISSING: {label}")
        continue
    rows = read_csv(fpath)
    p(f"  {label}: {len(rows)} KW")
    for row in rows:
        kw = row.get('Keyword', '')
        if not kw: continue
        parent = row.get('Parent Keyword', '').strip() or kw
        vol = safe_int(row.get('Volume', ''))
        kd = safe_int(row.get('Difficulty', ''))
        gvol = safe_int(row.get('Global volume', ''))
        tp = max(safe_int(row.get('Traffic potential', '')), safe_int(row.get('Global traffic potential', '')))
        country = row.get('Country', '').strip()

        pd = parent_data[parent]
        pd['vol'] = max(pd['vol'], vol if kw == parent else pd['vol'])
        if kw == parent and vol > 0:
            pd['vol'] = max(pd['vol'], vol)
        if kd > 0: pd['kd'] = min(pd['kd'], kd)
        pd['gvol'] = max(pd['gvol'], gvol if kw == parent else pd['gvol'])
        if kw == parent and gvol > 0:
            pd['gvol'] = max(pd['gvol'], gvol)
        pd['tp'] = max(pd['tp'], tp)
        pd['children'].add(kw)
        pd['child_vols'][kw] = max(pd['child_vols'].get(kw, 0), vol)
        pd['cluster_vol'] += vol
        pd['sources'].add(label)
        if country: pd['country'] = country

# ─── 2. 競合オーガニックKW ───
p("\n## 2. 競合オーガニックKW読み込み")
if os.path.exists(COMP_DIR):
    for fname in sorted(os.listdir(COMP_DIR)):
        if not fname.endswith('.csv'): continue
        fpath = os.path.join(COMP_DIR, fname)
        rows = read_csv(fpath)
        domain = fname.split('-organic')[0] if '-organic' in fname else fname[:30]
        p(f"  {domain}: {len(rows)} KW")
        for row in rows:
            kw = row.get('Keyword', '')
            if not kw: continue
            vol = safe_int(row.get('Volume', ''))
            kd_val = safe_int(row.get('KD', '') or row.get('Difficulty', ''))
            parent = row.get('Parent Keyword', '').strip() or kw
            comp_kws[kw].add(domain)
            # 親KWデータに追加
            if vol >= 10:
                cpd = parent_data[parent]
                cpd['vol'] = max(cpd['vol'], vol if kw == parent else cpd['vol'])
                if kw == parent: cpd['vol'] = max(cpd['vol'], vol)
                if kd_val > 0: cpd['kd'] = min(cpd['kd'], kd_val)
                cpd['children'].add(kw)
                cpd['child_vols'][kw] = max(cpd['child_vols'].get(kw, 0), vol)
                cpd['sources'].add(f'comp_{domain}')

# ─── 3. 自社KW ───
p("\n## 3. 自社（vip-limo.jp）KW読み込み")
if os.path.exists(OWN_FILE):
    rows = read_csv(OWN_FILE)
    p(f"  vip-limo.jp: {len(rows)} KW")
    for row in rows:
        kw = row.get('Keyword', '')
        if not kw: continue
        own_kws[kw] = {
            'vol': safe_int(row.get('Volume', '')),
            'pos': safe_int(row.get('Current position', '') or row.get('Position', '')),
            'traffic': safe_int(row.get('Traffic', '') or row.get('Current organic traffic', '')),
            'url': row.get('URL', '') or row.get('Current URL', ''),
        }

# ─── 4. セグメント分類 ───
def classify(kw):
    if is_english(kw):
        return 'A'
    # 日本語
    seg_c = ['ハイヤー', '役員', '秘書', '法人', '社用車', 'タクシー', '料金', '配車', '運転手', '黒塗り', '月極']
    seg_b = ['ホテル', '旅館', 'コンシェルジュ', 'ゲスト', '結婚式', 'ウェディング', '宿泊', '送迎バス', 'ブライダル']
    for s in seg_c:
        if s in kw: return 'C'
    for s in seg_b:
        if s in kw: return 'B'
    if '送迎' in kw or '手配' in kw or '外注' in kw or '貸切' in kw:
        return 'B'
    if '空港' in kw or '観光' in kw:
        return 'B'
    return '?'

for pk, pd in parent_data.items():
    seg = classify(pk)
    if seg == '?':
        # 子KWから推測
        child_segs = [classify(c) for c in pd['children']]
        child_segs = [s for s in child_segs if s != '?']
        if child_segs:
            seg = Counter(child_segs).most_common(1)[0][0]
    pd['segment'] = seg

# ─── 5. セグメント別分析 ───
def print_segment(seg_label, seg_name):
    p(f"\n\n{'#'*100}")
    p(f"## セグメント{seg_label}: {seg_name}")
    p(f"{'#'*100}")

    items = [(pk, pd) for pk, pd in parent_data.items() if pd['segment'] == seg_label and (pd['vol'] > 0 or pd['gvol'] > 0)]
    items.sort(key=lambda x: (x[1]['gvol'] or x[1]['vol'], x[1]['vol']), reverse=True)

    p(f"\n親KW数（Vol>0）: {len(items)}")
    p(f"\n{'Rank':<5} {'親キーワード':<50} {'Vol':>7} {'KD':>4} {'GVol':>7} {'TP':>7} {'子KW':>5} {'自社':>6}")
    p("-" * 95)

    candidates = []
    for i, (pk, pd) in enumerate(items[:50]):
        kd = str(pd['kd']) if pd['kd'] < 999 else '-'
        own = '-'
        if pk in own_kws:
            own = f"P{own_kws[pk]['pos']}"
        elif any(c in own_kws for c in pd['children']):
            for c in pd['children']:
                if c in own_kws:
                    own = f"P{own_kws[c]['pos']}"
                    break

        pk_d = pk[:48] if len(pk) > 48 else pk
        p(f"{i+1:<5} {pk_d:<50} {pd['vol']:>7,} {kd:>4} {pd['gvol']:>7,} {pd['tp']:>7,} {len(pd['children']):>5} {own:>6}")
        candidates.append((pk, pd))

    # トピックKW候補（ブランドKW除外、KD<40）
    p(f"\n{'='*80}")
    p(f"★ トピックKW候補（Vol>=50, KD<40, 非ブランド）")
    p(f"{'='*80}")

    branded = ['日本交通', '帝都', '国際自動車', 'mk ', 'uber', 'lyft', 'go app', 'app.go',
               'didi', 's.ride', 'visit japan', 'fullcast', 'フルキャスト', 'toyota',
               'nihon kotsu', 'km ', '東都', 'japantaxi']

    filtered = []
    for pk, pd in items:
        if pd['vol'] < 50 and pd['gvol'] < 100: continue
        kd = pd['kd'] if pd['kd'] < 999 else 0
        if kd >= 40: continue
        if any(b.lower() in pk.lower() for b in branded): continue
        filtered.append((pk, pd))

    p(f"\n{'#':<4} {'親KW':<50} {'Vol':>7} {'KD':>4} {'GVol':>7} {'TP':>7} {'子KW':>5}")
    p("-" * 90)
    for i, (pk, pd) in enumerate(filtered[:30]):
        kd = str(pd['kd']) if pd['kd'] < 999 else '-'
        pk_d = pk[:48] if len(pk) > 48 else pk
        p(f"{i+1:<4} {pk_d:<50} {pd['vol']:>7,} {kd:>4} {pd['gvol']:>7,} {pd['tp']:>7,} {len(pd['children']):>5}")

    # クラスター詳細（上位5）
    p(f"\n{'='*80}")
    p(f"★ 上位候補のクラスター詳細")
    p(f"{'='*80}")
    for pk, pd in filtered[:8]:
        p(f"\n  ■ {pk}  (Vol:{pd['vol']:,} KD:{pd['kd'] if pd['kd']<999 else '-'} GVol:{pd['gvol']:,} TP:{pd['tp']:,})")
        sorted_children = sorted(pd['child_vols'].items(), key=lambda x: x[1], reverse=True)
        for child, vol in sorted_children[:15]:
            marks = []
            if child in own_kws: marks.append(f"自社P{own_kws[child]['pos']}")
            if child in comp_kws: marks.append(f"競合{len(comp_kws[child])}社")
            mark_str = f" [{', '.join(marks)}]" if marks else ''
            p(f"    - {child} (vol:{vol:,}){mark_str}")
        if len(sorted_children) > 15:
            p(f"    ... 他{len(sorted_children)-15}件")

    return filtered

p("\n")
seg_a = print_segment('A', '海外旅行会社（英語）')
seg_b = print_segment('B', '宿泊業者（日本語）')
seg_c = print_segment('C', '法人・総務・秘書（日本語）')

# ─── 6. 自社の既存順位 ───
p(f"\n\n{'#'*100}")
p("## 自社（vip-limo.jp）既存順位トップ30（Traffic順）")
p(f"{'#'*100}")
own_sorted = sorted(own_kws.items(), key=lambda x: x[1]['traffic'], reverse=True)
p(f"\n{'KW':<50} {'Vol':>7} {'Pos':>5} {'Traffic':>8} {'URL':<50}")
p("-" * 125)
for kw, d in own_sorted[:30]:
    kw_d = kw[:48] if len(kw) > 48 else kw
    url_d = d['url'][-48:] if len(d['url']) > 48 else d['url']
    p(f"{kw_d:<50} {d['vol']:>7,} {d['pos']:>5} {d['traffic']:>8,} {url_d:<50}")

p("\n\n[分析完了]")
out.close()
print(f"\n出力ファイル: {OUTPUT}")
print("完了！")
