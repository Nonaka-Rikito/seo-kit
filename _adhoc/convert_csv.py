import sys
filepath = r'C:\Users\rikit\Projects\2_クライアントデータ\lightmarks\vip-limo.jp-organic-keywords-subdomains-jp_2026-02-25_10-12-02.csv'
outpath = r'C:\Users\rikit\Projects\viplimo_keywords_utf8.csv'
with open(filepath, 'r', encoding='utf-16-le') as f:
    content = f.read()
if content.startswith('\ufeff'):
    content = content[1:]
with open(outpath, 'w', encoding='utf-8', newline='') as f:
    f.write(content)
# Also run analysis and write output
import csv, io
from urllib.parse import unquote
from collections import defaultdict

reader = csv.DictReader(io.StringIO(content), delimiter='\t', quotechar='"')
rows = []
for row in reader:
    cleaned = {}
    for k, v in row.items():
        if k:
            cleaned[k.strip()] = v.strip() if v else ''
    rows.append(cleaned)

def pn(val):
    if not val: return 0
    try: return float(val.replace(',',''))
    except: return 0

def pi(val):
    if not val: return 0
    try: return int(val.replace(',',''))
    except:
        try: return int(float(val.replace(',','')))
        except: return 0

for r in rows:
    r['_traffic'] = pn(r.get('Current organic traffic','0'))
    r['_volume'] = pi(r.get('Volume','0'))
    r['_kd'] = pi(r.get('KD','0'))
    r['_position'] = r.get('Current position','')
    r['_url'] = r.get('Current URL','')

rows_sorted = sorted(rows, key=lambda x: x['_traffic'], reverse=True)

out = r'C:\Users\rikit\Projects\viplimo_analysis_output.txt'
with open(out, 'w', encoding='utf-8') as f:
    f.write(f"AHREFS ORGANIC KEYWORDS ANALYSIS: vip-limo.jp\n")
    f.write(f"{'='*80}\n")
    f.write(f"Total keywords: {len(rows)}\n\n")

    f.write(f"{'='*80}\n")
    f.write(f"TOP 50 KEYWORDS BY CURRENT ORGANIC TRAFFIC\n")
    f.write(f"{'='*80}\n")
    for i, r in enumerate(rows_sorted[:50], 1):
        kw = r.get('Keyword','')
        vol = r['_volume']
        kd = r['_kd']
        pos = r['_position']
        traffic = r['_traffic']
        url = unquote(r['_url'])
        info = r.get('Informational','')
        comm = r.get('Commercial','')
        trans = r.get('Transactional','')
        intent_flags = []
        if info == 'true': intent_flags.append('Info')
        if comm == 'true': intent_flags.append('Comm')
        if trans == 'true': intent_flags.append('Trans')
        intent_str = '/'.join(intent_flags) if intent_flags else 'N/A'
        f.write(f"\n--- #{i} ---\n")
        f.write(f"  Keyword:  {kw}\n")
        f.write(f"  Volume:   {vol}\n")
        f.write(f"  KD:       {kd}\n")
        f.write(f"  Position: {pos}\n")
        f.write(f"  Traffic:  {traffic}\n")
        f.write(f"  Intent:   {intent_str}\n")
        f.write(f"  URL:      {url}\n")

    # Group by URL
    url_groups = defaultdict(list)
    for r in rows:
        url = unquote(r['_url'])
        url_groups[url].append(r)
    url_traffic = []
    for url, kws in url_groups.items():
        total_traffic = sum(k['_traffic'] for k in kws)
        url_traffic.append((url, kws, total_traffic))
    url_traffic.sort(key=lambda x: x[2], reverse=True)

    f.write(f"\n{'='*80}\n")
    f.write(f"KEYWORDS GROUPED BY URL\n")
    f.write(f"{'='*80}\n")
    for url, kws, total_traffic in url_traffic:
        kws_sorted = sorted(kws, key=lambda x: x['_traffic'], reverse=True)
        f.write(f"\n{'─'*70}\n")
        f.write(f"URL: {url}\n")
        f.write(f"  Keywords count: {len(kws)}\n")
        f.write(f"  Total organic traffic: {total_traffic}\n")
        f.write(f"  Top keywords:\n")
        for k in kws_sorted[:10]:
            kw = k.get('Keyword','')
            traffic = k['_traffic']
            vol = k['_volume']
            pos = k['_position']
            f.write(f"    - [{pos}位] {kw} (Vol:{vol}, Traffic:{traffic})\n")

    # Categorization
    parking_airport_patterns = ['駐車場','駐車','パーキング','parking','空港','airport',
                                '羽田','成田','関西国際','伊丹','中部国際','セントレア',
                                '混雑','料金比較','安い駐車']
    limo_vip_patterns = ['リムジン','limousine','limo','ハイヤー','hire','VIP','vip',
                         '送迎','タクシー','taxi','配車','貸切','チャーター',
                         'ウェディング','結婚式','ゴルフ','接待']

    def categorize(keyword, url):
        kw_lower = keyword.lower()
        url_lower = url.lower()
        combined = kw_lower + ' ' + url_lower
        is_pa = any(p.lower() in combined for p in parking_airport_patterns)
        is_lv = any(p.lower() in combined for p in limo_vip_patterns)
        if is_lv and not is_pa: return 'CORE_LIMO_VIP'
        elif is_pa and not is_lv: return 'PARKING_AIRPORT'
        elif is_pa and is_lv: return 'MIXED_AIRPORT_LIMO'
        else: return 'OTHER'

    categories = defaultdict(list)
    for r in rows:
        kw = r.get('Keyword','')
        url = unquote(r['_url'])
        cat = categorize(kw, url)
        categories[cat].append(r)

    f.write(f"\n{'='*80}\n")
    f.write(f"KEYWORD CATEGORIZATION\n")
    f.write(f"{'='*80}\n")
    for cat in ['CORE_LIMO_VIP','PARKING_AIRPORT','MIXED_AIRPORT_LIMO','OTHER']:
        kws = categories.get(cat, [])
        total_t = sum(k['_traffic'] for k in kws)
        kws_s = sorted(kws, key=lambda x: x['_traffic'], reverse=True)
        f.write(f"\n### {cat}\n")
        f.write(f"  Keywords: {len(kws)}\n")
        f.write(f"  Total traffic: {total_t}\n")
        if kws_s:
            f.write(f"  Top 15 keywords:\n")
            for k in kws_s[:15]:
                kw_text = k.get('Keyword','')
                traffic = k['_traffic']
                vol = k['_volume']
                pos = k['_position']
                url = unquote(k['_url'])
                f.write(f"    - [{pos}位] {kw_text} (Vol:{vol}, Traffic:{traffic})\n")
                f.write(f"      URL: {url}\n")

    # Summary
    total_t = sum(r['_traffic'] for r in rows)
    avg_pos = 0
    pos_cnt = 0
    for r in rows:
        try:
            p = float(r['_position'])
            avg_pos += p
            pos_cnt += 1
        except: pass
    if pos_cnt > 0: avg_pos = avg_pos / pos_cnt

    f.write(f"\n{'='*80}\n")
    f.write(f"SUMMARY STATISTICS\n")
    f.write(f"{'='*80}\n")
    f.write(f"Total keywords: {len(rows)}\n")
    f.write(f"Total organic traffic: {total_t}\n")
    f.write(f"Average position: {avg_pos:.1f}\n")
    f.write(f"Unique URLs: {len(url_groups)}\n")
    f.write(f"Position 1-3: {sum(1 for r in rows if r['_position'] and 0 < pn(r['_position']) <= 3)}\n")
    f.write(f"Position 4-10: {sum(1 for r in rows if r['_position'] and 4 <= pn(r['_position']) <= 10)}\n")
    f.write(f"Position 11-20: {sum(1 for r in rows if r['_position'] and 11 <= pn(r['_position']) <= 20)}\n")
    f.write(f"Position 21+: {sum(1 for r in rows if r['_position'] and pn(r['_position']) > 20)}\n")
    info_c = sum(1 for r in rows if r.get('Informational','') == 'true')
    comm_c = sum(1 for r in rows if r.get('Commercial','') == 'true')
    trans_c = sum(1 for r in rows if r.get('Transactional','') == 'true')
    nav_c = sum(1 for r in rows if r.get('Navigational','') == 'true')
    f.write(f"\nIntent Distribution:\n")
    f.write(f"  Informational: {info_c}\n")
    f.write(f"  Commercial: {comm_c}\n")
    f.write(f"  Transactional: {trans_c}\n")
    f.write(f"  Navigational: {nav_c}\n")
    f.write(f"\nDONE\n")

# Signal completion
with open(r'C:\Users\rikit\Projects\viplimo_done.flag', 'w') as f:
    f.write('done')
