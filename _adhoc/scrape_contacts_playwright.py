"""
被リンク営業リスト — Playwright版 問い合わせURL再取得
対象: scrape_contacts_log で問い合わせURLが空だったドメイン（342件）
出力: 既存CSVの該当行を上書き更新
"""

import asyncio
import csv
import os
import re
import sys

# Playwrightチェック
try:
    from playwright.async_api import async_playwright
except ImportError:
    print("ERROR: playwright not installed.")
    print("Run: pip install playwright && playwright install chromium")
    sys.exit(1)

INPUT_CSV  = "C:/Users/rikit/Projects/2_クライアントデータ/malna/nonaka/被リンク営業リスト_連絡先付き.csv"
OUTPUT_CSV = INPUT_CSV  # 同じファイルを上書き
DOMAINS_FILE = "C:/Users/rikit/Projects/_adhoc/no_contact_domains.txt"
LOG_FILE = "C:/Users/rikit/Projects/_adhoc/scrape_playwright_log.txt"

TIMEOUT = 15000   # ms
MAX_CONCURRENT = 5
SAVE_EVERY = 30

CONTACT_KEYWORDS_HREF = [
    "contact", "inquiry", "enquiry", "toiawase",
    "お問い合わせ", "問い合わせ", "お問合わせ", "お問合せ",
]
CONTACT_KEYWORDS_TEXT = [
    "お問い合わせ", "問い合わせ", "お問合わせ", "お問合せ",
    "contact", "inquiry", "お気軽に", "ご相談",
]

results_patch = {}  # domain -> {"問い合わせURL": ..., "社名": ...}
sem = None
done_count = 0
total_target = 0


def is_contact_link(href: str, text: str) -> bool:
    href_l = href.lower()
    text_l = text.lower().strip()
    for kw in CONTACT_KEYWORDS_HREF:
        if kw in href_l:
            return True
    for kw in CONTACT_KEYWORDS_TEXT:
        if kw in text_l:
            return True
    return False


async def scrape_domain(domain: str, browser) -> dict:
    result = {"ドメイン": domain, "問い合わせURL": "", "社名": "", "ステータス": "OK"}
    url = f"https://{domain}/"
    context = None
    try:
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0 Safari/537.36",
            ignore_https_errors=True,
            locale="ja-JP",
        )
        page = await context.new_page()
        await page.goto(url, timeout=TIMEOUT, wait_until="domcontentloaded")

        # 社名（og:site_name → title）
        og = await page.evaluate("() => { const m = document.querySelector('meta[property=\"og:site_name\"]'); return m ? m.content : ''; }")
        if og:
            result["社名"] = og.strip()
        else:
            title = await page.title()
            for sep in [" | ", " ｜ ", " - ", " – ", "｜"]:
                if sep in title:
                    result["社名"] = title.split(sep)[-1].strip()
                    break
            else:
                result["社名"] = title.strip()[:50]

        # 問い合わせリンクを探す
        links = await page.evaluate("""() => {
            const anchors = Array.from(document.querySelectorAll('a[href]'));
            return anchors.map(a => ({ href: a.href, text: a.textContent.trim() }));
        }""")

        for link in links:
            href = link.get("href", "")
            text = link.get("text", "")
            if href and is_contact_link(href, text):
                result["問い合わせURL"] = href
                break

        # 見つからない場合: nav/footer 限定で再探索
        if not result["問い合わせURL"]:
            nav_links = await page.evaluate("""() => {
                const selectors = ['nav a[href]', 'footer a[href]', 'header a[href]', '.nav a[href]', '.footer a[href]'];
                const found = [];
                for (const sel of selectors) {
                    found.push(...Array.from(document.querySelectorAll(sel)).map(a => ({ href: a.href, text: a.textContent.trim() })));
                }
                return found;
            }""")
            for link in nav_links:
                href = link.get("href", "")
                text = link.get("text", "")
                if href and is_contact_link(href, text):
                    result["問い合わせURL"] = href
                    break

    except Exception as e:
        result["ステータス"] = f"PW Error: {str(e)[:50]}"
    finally:
        if context:
            await context.close()
    return result


async def worker(domain: str, browser):
    global done_count
    async with sem:
        res = await scrape_domain(domain, browser)
        results_patch[domain] = res
        done_count += 1
        if done_count % 10 == 0:
            print(f"[{done_count}/{total_target}] {domain} → 社名:{res['社名'][:20]} 問合:{res['問い合わせURL'][:50]}", flush=True)
        return res


def merge_and_save():
    """既存CSVを読み込んでresults_patchで上書き保存"""
    rows = []
    with open(INPUT_CSV, encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))

    for row in rows:
        domain = row["ドメイン"]
        if domain in results_patch:
            patch = results_patch[domain]
            if patch["問い合わせURL"]:
                row["問い合わせURL"] = patch["問い合わせURL"]
            if patch["社名"] and not row["社名"]:
                row["社名"] = patch["社名"]
            row["ステータス"] = patch["ステータス"]

    with open(OUTPUT_CSV, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()), extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


async def main():
    global sem, total_target

    # 対象ドメイン読み込み
    with open(DOMAINS_FILE) as f:
        domains = [line.strip() for line in f if line.strip()]
    total_target = len(domains)
    print(f"開始: {total_target}件をPlaywright並列{MAX_CONCURRENT}で処理", flush=True)

    sem = asyncio.Semaphore(MAX_CONCURRENT)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        tasks = [worker(d, browser) for d in domains]

        done = 0
        for coro in asyncio.as_completed(tasks):
            await coro
            done += 1
            if done % SAVE_EVERY == 0:
                merge_and_save()
                print(f"  途中保存: {done}/{total_target}", flush=True)

        await browser.close()

    merge_and_save()

    # 最終集計
    got = sum(1 for r in results_patch.values() if r["問い合わせURL"])
    errors = sum(1 for r in results_patch.values() if "Error" in r.get("ステータス", ""))
    print(f"\n完了: {total_target}件処理")
    print(f"  問い合わせURL新規取得: {got}件")
    print(f"  エラー: {errors}件")
    print(f"保存先: {OUTPUT_CSV}")


if __name__ == "__main__":
    asyncio.run(main())
