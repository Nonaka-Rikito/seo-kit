import csv
import io
import os
from urllib.parse import unquote
from collections import defaultdict

filepath = r'C:\Users\rikit\Projects\2_クライアントデータ\lightmarks\vip-limo.jp-organic-keywords-subdomains-jp_2026-02-25_10-12-02.csv'
outpath = r'C:\Users\rikit\Projects\ahrefs_analysis_output.txt'

# Read the file with UTF-16LE encoding
with open(filepath, 'r', encoding='utf-16-le') as f:
    content = f.read()

# Remove BOM if present
if content.startswith('\ufeff'):
    content = content[1:]

# Parse as TSV
reader = csv.DictReader(io.StringIO(content), delimiter='\t', quotechar='"')

# Collect all data
article_urls = defaultdict(lambda: {"traffic": 0, "keywords": []})
non_article_urls = defaultdict(lambda: {"traffic": 0, "keywords": []})
total_rows = 0

for row in reader:
    total_rows += 1
    current_url = row.get("Current URL", "").strip()
    traffic_str = row.get("Current organic traffic", "").strip()
    keyword = row.get("Keyword", "").strip()

    # Parse traffic (may be empty)
    try:
        traffic = float(traffic_str) if traffic_str else 0
    except ValueError:
        traffic = 0

    if not current_url:
        continue

    if "/articles/" in current_url:
        article_urls[current_url]["traffic"] += traffic
        article_urls[current_url]["keywords"].append((keyword, traffic))
    else:
        non_article_urls[current_url]["traffic"] += traffic
        non_article_urls[current_url]["keywords"].append((keyword, traffic))

lines = []
lines.append(f"Total data rows: {total_rows}")
lines.append(f"Total unique /articles/ URLs: {len(article_urls)}")
lines.append(f"Total unique non-/articles/ URLs: {len(non_article_urls)}")
lines.append("")

# Sort articles by traffic descending
sorted_articles = sorted(article_urls.items(), key=lambda x: x[1]["traffic"], reverse=True)

total_article_traffic = sum(d["traffic"] for d in article_urls.values())
total_non_article_traffic = sum(d["traffic"] for d in non_article_urls.values())

lines.append(f"TOTAL /articles/ traffic sum: {total_article_traffic:.0f}")
lines.append(f"TOTAL non-/articles/ traffic sum: {total_non_article_traffic:.0f}")
lines.append("")

lines.append("=" * 120)
lines.append("ALL UNIQUE /articles/ URLs - SORTED BY TOTAL TRAFFIC (DESCENDING)")
lines.append("=" * 120)

for rank, (url, data) in enumerate(sorted_articles, 1):
    decoded_url = unquote(url)
    slug = decoded_url.split("/articles/")[1].rstrip("/") if "/articles/" in decoded_url else decoded_url
    top_keywords = sorted(data["keywords"], key=lambda x: x[1], reverse=True)[:5]

    lines.append(f"")
    lines.append(f"#{rank} | Traffic: {data['traffic']:.0f} | Keywords: {len(data['keywords'])}")
    lines.append(f"  Decoded Title: {slug}")
    lines.append(f"  Top Keywords:")
    for kw, tr in top_keywords:
        lines.append(f"    - [{tr:.0f}] {kw}")

lines.append("")
lines.append("=" * 120)
lines.append("NON-ARTICLE URLs - SORTED BY TRAFFIC (DESCENDING)")
lines.append("=" * 120)

sorted_non_articles = sorted(non_article_urls.items(), key=lambda x: x[1]["traffic"], reverse=True)
for rank, (url, data) in enumerate(sorted_non_articles, 1):
    decoded = unquote(url)
    lines.append(f"  #{rank} | Traffic: {data['traffic']:.0f} | Keywords: {len(data['keywords'])} | {decoded}")

with open(outpath, 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))

# Signal completion
with open(r'C:\Users\rikit\Projects\ahrefs_done.txt', 'w') as f:
    f.write('done')
