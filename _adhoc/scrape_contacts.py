"""
被リンク営業リスト — 社名・問い合わせURL抽出スクリプト
対象: 被リンク営業リスト.csv の全ドメイン
出力: 被リンク営業リスト_連絡先付き.csv
"""

import csv
import ssl
import time
import urllib.request
import urllib.error
import concurrent.futures
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse
import os
import threading

# ---- 設定 ----
INPUT_CSV  = "C:/Users/rikit/Projects/2_クライアントデータ/malna/nonaka/被リンク営業リスト.csv"
OUTPUT_CSV = "C:/Users/rikit/Projects/2_クライアントデータ/malna/nonaka/被リンク営業リスト_連絡先付き.csv"
LOG_FILE   = "C:/Users/rikit/Projects/_adhoc/scrape_contacts_log.txt"
TIMEOUT    = 10   # 秒
MAX_WORKERS = 15  # 並列数
SAVE_EVERY  = 50  # N件ごとに途中保存

CONTACT_KEYWORDS = [
    "contact", "inquiry", "enquiry", "contact-us",
    "お問い合わせ", "問い合わせ", "お問合わせ", "お問合せ",
    "contact.html", "inquiry.html", "toiawase",
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0 Safari/537.36",
    "Accept-Language": "ja,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml",
}

ssl_ctx = ssl.create_default_context()
ssl_ctx.check_hostname = False
ssl_ctx.verify_mode = ssl.CERT_NONE

lock = threading.Lock()
results = {}      # domain -> dict
processed = 0


# ---- HTML パーサー ----
class SiteParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.og_site_name = ""
        self.title = ""
        self._in_title = False
        self.contact_links = []   # (href, text)
        self._current_a_href = ""
        self._current_a_text = ""
        self.base_url = ""

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        if tag == "meta":
            if attrs_dict.get("property") == "og:site_name":
                self.og_site_name = attrs_dict.get("content", "").strip()
        if tag == "title":
            self._in_title = True
        if tag == "a":
            href = attrs_dict.get("href", "")
            self._current_a_href = href
            self._current_a_text = ""

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False
        if tag == "a":
            href = self._current_a_href
            text = self._current_a_text.strip()
            if href and self._is_contact(href, text):
                full = urljoin(self.base_url, href)
                if full not in [l[0] for l in self.contact_links]:
                    self.contact_links.append((full, text))
            self._current_a_href = ""
            self._current_a_text = ""

    def handle_data(self, data):
        if self._in_title and not self.title:
            self.title = data.strip()
        if self._current_a_href:
            self._current_a_text += data

    def _is_contact(self, href, text):
        href_lower = href.lower()
        text_lower = text.lower()
        for kw in CONTACT_KEYWORDS:
            if kw in href_lower or kw in text_lower:
                return True
        return False

    def get_company_name(self):
        if self.og_site_name:
            return self.og_site_name
        # タイトルから会社名を推測（「|」「-」「–」で分割して末尾を取得）
        title = self.title
        for sep in [" | ", " ｜ ", " - ", " – ", " — ", "｜"]:
            if sep in title:
                parts = title.split(sep)
                return parts[-1].strip()
        return title.strip()[:50] if title else ""


# ---- スクレイプ関数 ----
def fetch(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=TIMEOUT, context=ssl_ctx) as resp:
        raw = resp.read(100000)  # 最大100KB
        ctype = resp.headers.get("Content-Type", "")
        # エンコード判定
        enc = "utf-8"
        if "charset=" in ctype.lower():
            enc = ctype.lower().split("charset=")[-1].split(";")[0].strip()
        try:
            html = raw.decode(enc, errors="replace")
        except (LookupError, ValueError):
            html = raw.decode("utf-8", errors="replace")
        return html, resp.url  # resp.url = リダイレクト後のURL


def scrape_domain(domain):
    global processed
    result = {
        "ドメイン": domain,
        "社名": "",
        "問い合わせURL": "",
        "ステータス": "OK",
    }
    for scheme in ["https", "http"]:
        url = f"{scheme}://{domain}/"
        try:
            html, final_url = fetch(url)
            parser = SiteParser()
            parser.base_url = final_url
            parser.feed(html)
            result["社名"] = parser.get_company_name()
            if parser.contact_links:
                result["問い合わせURL"] = parser.contact_links[0][0]
            break
        except urllib.error.HTTPError as e:
            result["ステータス"] = f"HTTP {e.code}"
        except urllib.error.URLError as e:
            result["ステータス"] = f"URLError: {str(e.reason)[:40]}"
        except Exception as e:
            result["ステータス"] = f"Error: {str(e)[:40]}"
    return result


def worker(item):
    global processed
    domain = item["ドメイン"]
    res = scrape_domain(domain)
    # 元データのカラムをマージ
    res.update({
        "DR": item.get("DR", ""),
        "トラフィック": item.get("トラフィック", ""),
        "競合リンク数": item.get("競合リンク数", ""),
        "競合実績": item.get("競合実績", ""),
        "優先度スコア": item.get("優先度スコア", ""),
        "参考リンクページURL": item.get("参考リンクページURL", ""),
    })
    with lock:
        results[domain] = res
        processed += 1
        if processed % 10 == 0:
            print(f"[{processed}/991] {domain} → 社名:{res['社名'][:20]} 問合:{res['問い合わせURL'][:40]}", flush=True)
    return res


def save_results():
    out_cols = ["ドメイン", "社名", "問い合わせURL", "DR", "トラフィック", "競合リンク数", "競合実績", "優先度スコア", "参考リンクページURL", "ステータス"]
    with open(OUTPUT_CSV, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=out_cols, extrasaction="ignore")
        writer.writeheader()
        # 元の優先度スコア順で保存
        sorted_results = sorted(results.values(), key=lambda x: float(x.get("優先度スコア", 0) or 0), reverse=True)
        writer.writerows(sorted_results)


# ---- メイン ----
def main():
    # 入力読み込み
    with open(INPUT_CSV, encoding="utf-8-sig") as f:
        items = list(csv.DictReader(f))

    total = len(items)
    print(f"開始: {total}件を並列{MAX_WORKERS}で処理", flush=True)
    start = time.time()

    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(worker, item): item for item in items}
        done_count = 0
        for future in concurrent.futures.as_completed(futures):
            done_count += 1
            try:
                future.result()
            except Exception as e:
                pass
            # 途中保存
            if done_count % SAVE_EVERY == 0:
                with lock:
                    save_results()
                print(f"  途中保存: {done_count}/{total}", flush=True)

    save_results()
    elapsed = time.time() - start
    ok = sum(1 for r in results.values() if r["ステータス"] == "OK")
    has_contact = sum(1 for r in results.values() if r["問い合わせURL"])
    has_name = sum(1 for r in results.values() if r["社名"])
    print(f"\n完了: {elapsed:.0f}秒")
    print(f"  成功: {ok}/{total}")
    print(f"  社名取得: {has_name}件")
    print(f"  問い合わせURL取得: {has_contact}件")
    print(f"保存先: {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
