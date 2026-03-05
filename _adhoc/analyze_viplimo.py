#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Analyze Ahrefs organic keywords CSV for vip-limo.jp"""

import csv
import io
import sys
from urllib.parse import unquote
from collections import defaultdict

# Write output to file instead of stdout
output_path = r'C:\Users\rikit\Projects\viplimo_analysis_output.txt'
sys.stdout = open(output_path, 'w', encoding='utf-8')

filepath = r'C:\Users\rikit\Projects\2_クライアントデータ\lightmarks\vip-limo.jp-organic-keywords-subdomains-jp_2026-02-25_10-12-02.csv'

# Read UTF-16LE file
with open(filepath, 'r', encoding='utf-16-le') as f:
    content = f.read()

# Remove BOM if present
if content.startswith('\ufeff'):
    content = content[1:]

# Parse as TSV
reader = csv.DictReader(io.StringIO(content), delimiter='\t', quotechar='"')

rows = []
for row in reader:
    # Strip whitespace from keys and values
    cleaned = {}
    for k, v in row.items():
        if k:
            cleaned[k.strip()] = v.strip() if v else ''
    rows.append(cleaned)

print(f"=" * 80)
print(f"AHREFS ORGANIC KEYWORDS ANALYSIS: vip-limo.jp")
print(f"=" * 80)
print(f"\n## 総キーワード数: {len(rows)}")

# Parse traffic as number
def parse_num(val):
    if not val:
        return 0
    try:
        return float(val.replace(',', ''))
    except:
        return 0

def parse_int(val):
    if not val:
        return 0
    try:
        return int(val.replace(',', ''))
    except:
        try:
            return int(float(val.replace(',', '')))
        except:
            return 0

# Sort by current organic traffic
for r in rows:
    r['_traffic'] = parse_num(r.get('Current organic traffic', '0'))
    r['_volume'] = parse_int(r.get('Volume', '0'))
    r['_kd'] = parse_int(r.get('KD', '0'))
    r['_position'] = r.get('Current position', '')
    r['_url'] = r.get('Current URL', '')

rows_sorted = sorted(rows, key=lambda x: x['_traffic'], reverse=True)

# Decode URL-encoded URLs
def decode_url(url):
    try:
        return unquote(url)
    except:
        return url

print(f"\n{'=' * 80}")
print(f"TOP 50 KEYWORDS BY CURRENT ORGANIC TRAFFIC")
print(f"{'=' * 80}")

for i, r in enumerate(rows_sorted[:50], 1):
    kw = r.get('Keyword', '')
    vol = r['_volume']
    kd = r['_kd']
    pos = r['_position']
    traffic = r['_traffic']
    url = decode_url(r['_url'])
    info = r.get('Informational', '')
    comm = r.get('Commercial', '')
    trans = r.get('Transactional', '')

    intent_flags = []
    if info == 'true': intent_flags.append('Info')
    if comm == 'true': intent_flags.append('Comm')
    if trans == 'true': intent_flags.append('Trans')
    intent_str = '/'.join(intent_flags) if intent_flags else 'N/A'

    print(f"\n--- #{i} ---")
    print(f"  Keyword:  {kw}")
    print(f"  Volume:   {vol}")
    print(f"  KD:       {kd}")
    print(f"  Position: {pos}")
    print(f"  Traffic:  {traffic}")
    print(f"  Intent:   {intent_str}")
    print(f"  URL:      {url}")

# Group by URL
print(f"\n{'=' * 80}")
print(f"KEYWORDS GROUPED BY URL")
print(f"{'=' * 80}")

url_groups = defaultdict(list)
for r in rows:
    url = decode_url(r['_url'])
    url_groups[url].append(r)

# Sort URL groups by total traffic
url_traffic = []
for url, kws in url_groups.items():
    total_traffic = sum(k['_traffic'] for k in kws)
    url_traffic.append((url, kws, total_traffic))

url_traffic.sort(key=lambda x: x[2], reverse=True)

for url, kws, total_traffic in url_traffic:
    kws_sorted = sorted(kws, key=lambda x: x['_traffic'], reverse=True)
    print(f"\n{'─' * 70}")
    print(f"URL: {url}")
    print(f"  Keywords count: {len(kws)}")
    print(f"  Total organic traffic: {total_traffic}")
    print(f"  Top keywords:")
    for k in kws_sorted[:10]:
        kw = k.get('Keyword', '')
        traffic = k['_traffic']
        vol = k['_volume']
        pos = k['_position']
        print(f"    - [{pos}位] {kw} (Vol:{vol}, Traffic:{traffic})")

# Categorization: Core VIP/Limo services vs Parking/Airport content
print(f"\n{'=' * 80}")
print(f"KEYWORD CATEGORIZATION")
print(f"{'=' * 80}")

# Define category patterns
parking_airport_patterns = ['駐車場', '駐車', 'パーキング', 'parking', '空港', 'airport',
                            '羽田', '成田', '関西国際', '伊丹', '中部国際', 'セントレア',
                            '混雑', '料金比較', '安い駐車']
limo_vip_patterns = ['リムジン', 'limousine', 'limo', 'ハイヤー', 'hire', 'VIP', 'vip',
                     '送迎', 'タクシー', 'taxi', '配車', '貸切', 'チャーター',
                     'ウェディング', '結婚式', 'ゴルフ', '接待']

def categorize(keyword, url):
    kw_lower = keyword.lower()
    url_lower = url.lower()
    combined = kw_lower + ' ' + url_lower

    is_parking_airport = any(p in combined for p in parking_airport_patterns)
    is_limo_vip = any(p in combined for p in limo_vip_patterns)

    if is_limo_vip and not is_parking_airport:
        return 'CORE_LIMO_VIP'
    elif is_parking_airport and not is_limo_vip:
        return 'PARKING_AIRPORT'
    elif is_parking_airport and is_limo_vip:
        return 'MIXED (Airport+Limo/Taxi)'
    else:
        return 'OTHER'

categories = defaultdict(list)
for r in rows:
    kw = r.get('Keyword', '')
    url = decode_url(r['_url'])
    cat = categorize(kw, url)
    categories[cat].append(r)

for cat in ['CORE_LIMO_VIP', 'PARKING_AIRPORT', 'MIXED (Airport+Limo/Taxi)', 'OTHER']:
    kws = categories.get(cat, [])
    total_traffic = sum(k['_traffic'] for k in kws)
    kws_sorted = sorted(kws, key=lambda x: x['_traffic'], reverse=True)

    print(f"\n### {cat}")
    print(f"  Keywords: {len(kws)}")
    print(f"  Total traffic: {total_traffic}")
    if kws_sorted:
        print(f"  Top 15 keywords:")
        for k in kws_sorted[:15]:
            kw_text = k.get('Keyword', '')
            traffic = k['_traffic']
            vol = k['_volume']
            pos = k['_position']
            url = decode_url(k['_url'])
            print(f"    - [{pos}位] {kw_text} (Vol:{vol}, Traffic:{traffic})")
            print(f"      URL: {url}")

# Summary statistics
print(f"\n{'=' * 80}")
print(f"SUMMARY STATISTICS")
print(f"{'=' * 80}")

total_traffic = sum(r['_traffic'] for r in rows)
total_volume = sum(r['_volume'] for r in rows)
avg_position = 0
pos_count = 0
for r in rows:
    try:
        p = float(r['_position'])
        avg_position += p
        pos_count += 1
    except:
        pass
if pos_count > 0:
    avg_position = avg_position / pos_count

print(f"Total keywords: {len(rows)}")
print(f"Total organic traffic: {total_traffic}")
print(f"Total search volume (all KWs): {total_volume}")
print(f"Average position: {avg_position:.1f}")
print(f"Unique URLs: {len(url_groups)}")
print(f"Keywords with position 1-3: {sum(1 for r in rows if r['_position'] and parse_num(r['_position']) <= 3 and parse_num(r['_position']) > 0)}")
print(f"Keywords with position 4-10: {sum(1 for r in rows if r['_position'] and 4 <= parse_num(r['_position']) <= 10)}")
print(f"Keywords with position 11-20: {sum(1 for r in rows if r['_position'] and 11 <= parse_num(r['_position']) <= 20)}")
print(f"Keywords with position 21+: {sum(1 for r in rows if r['_position'] and parse_num(r['_position']) > 20)}")

# Intent distribution
info_count = sum(1 for r in rows if r.get('Informational', '') == 'true')
comm_count = sum(1 for r in rows if r.get('Commercial', '') == 'true')
trans_count = sum(1 for r in rows if r.get('Transactional', '') == 'true')
nav_count = sum(1 for r in rows if r.get('Navigational', '') == 'true')
print(f"\nIntent Distribution:")
print(f"  Informational: {info_count}")
print(f"  Commercial: {comm_count}")
print(f"  Transactional: {trans_count}")
print(f"  Navigational: {nav_count}")

print(f"\n{'=' * 80}")
print(f"ANALYSIS COMPLETE")
print(f"{'=' * 80}")
