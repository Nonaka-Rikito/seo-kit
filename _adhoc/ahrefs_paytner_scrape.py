"""
Ahrefs無料ツールから paytner.co.jp の競合・キーワードデータを取得するスクリプト
"""

import json
import time
import re
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeoutError

SCREENSHOT_DIR = Path(r"C:\Users\rikit\Projects\_adhoc\ahrefs_paytner_screenshots")
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

RESULTS = {
    "domain": "paytner.co.jp",
    "dr": None,
    "backlinks": None,
    "keywords": [],
    "traffic_data": None,
    "raw_notes": []
}

def take_screenshot(page, name: str):
    path = SCREENSHOT_DIR / f"{name}.png"
    try:
        page.screenshot(path=str(path), full_page=True)
        print(f"  [SS] {path.name}")
    except Exception as e:
        print(f"  [SS ERROR] {name}: {e}")

def fill_input(page, value: str) -> bool:
    """入力フィールドを探して値を入力"""
    selectors = [
        'input[type="url"]',
        'input[type="text"]',
        'input[name="target"]',
        'input[name="input"]',
        'input[placeholder*="domain"]',
        'input[placeholder*="URL"]',
        'input[placeholder*="keyword"]',
        'input[class*="input"]',
        'form input',
        'input',
    ]
    for sel in selectors:
        try:
            els = page.query_selector_all(sel)
            for el in els:
                if el.is_visible():
                    el.click(force=True)
                    time.sleep(0.3)
                    el.fill(value)
                    print(f"  入力成功: [{sel}] = '{value}'")
                    return True
        except Exception:
            pass
    return False


def extract_numbers_from_text(text: str) -> list:
    """テキストから数値情報を抽出"""
    # ボリューム・DR等の数値パターン
    patterns = [
        r'(\d{1,3}(?:,\d{3})*(?:\.\d+)?[KMB]?)',
        r'DR[:\s]+(\d+)',
        r'Domain Rating[:\s]+(\d+)',
    ]
    found = []
    for pat in patterns:
        found.extend(re.findall(pat, text))
    return found[:20]


def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=["--no-sandbox", "--disable-setuid-sandbox", "--start-maximized"]
        )
        context = browser.new_context(
            viewport={"width": 1440, "height": 900},
            locale="ja-JP",
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/121.0.0.0 Safari/537.36"
            )
        )
        page = context.new_page()
        page.set_default_timeout(30000)

        # =========================================================
        # STEP 1: 無料ツール一覧
        # =========================================================
        print("\n" + "="*60)
        print("STEP 1: Ahrefs無料ツール一覧を確認")
        print("="*60)
        try:
            page.goto("https://ahrefs.com/free-seo-tools", wait_until="domcontentloaded", timeout=30000)
            time.sleep(3)
            take_screenshot(page, "01_free_tools_list")

            links = page.evaluate("""() => {
                return Array.from(document.querySelectorAll('a[href]'))
                    .filter(a => a.href.includes('ahrefs.com') && !a.href.includes('#'))
                    .map(a => ({text: a.textContent.trim(), href: a.href}))
                    .filter(l => l.text.length > 2 && l.text.length < 80)
                    .slice(0, 40);
            }""")
            print(f"  取得リンク数: {len(links)}")
            for l in links[:15]:
                print(f"  - {l['text']}: {l['href']}")
            RESULTS["raw_notes"].append({"step": "free_tools_links", "data": links})
        except Exception as e:
            print(f"  エラー: {e}")

        # =========================================================
        # STEP 2: Website Authority Checker でDR確認
        # =========================================================
        print("\n" + "="*60)
        print("STEP 2: Website Authority Checker でpaytner.co.jpのDR確認")
        print("="*60)
        try:
            page.goto(
                "https://ahrefs.com/website-authority-checker?input=paytner.co.jp",
                wait_until="domcontentloaded", timeout=30000
            )
            time.sleep(5)
            take_screenshot(page, "02_authority_checker_result")

            body_text = page.evaluate("() => document.body.innerText")
            print(f"  ページテキスト（先頭800字）:\n{body_text[:800]}")
            RESULTS["raw_notes"].append({"step": "authority_checker", "text": body_text[:3000]})

            # DRを抽出
            numbers = extract_numbers_from_text(body_text[:500])
            print(f"  抽出数値: {numbers}")

            # DR専用セレクター
            dr_candidates = []
            for sel in ['.cell-metric-value', '.dr', '[class*="dr-"]', 'h2', 'h3', '.metric', '.score', 'strong']:
                try:
                    els = page.query_selector_all(sel)
                    for el in els:
                        txt = el.inner_text().strip()
                        if txt and re.match(r'^\d+$', txt) and int(txt) <= 100:
                            dr_candidates.append({"sel": sel, "value": txt})
                except Exception:
                    pass

            print(f"  DR候補: {dr_candidates}")
            if dr_candidates:
                RESULTS["dr"] = dr_candidates[0]["value"]

        except Exception as e:
            print(f"  エラー: {e}")
            take_screenshot(page, "02_authority_checker_error")

        # =========================================================
        # STEP 3: Keyword Generator でキーワードごとに検索
        # =========================================================
        print("\n" + "="*60)
        print("STEP 3: Keyword Generator でキーワード検索")
        print("="*60)

        keywords_to_check = [
            "ファクタリング",
            "フリーランス 請求書",
            "確定申告 フリーランス",
            "個人事業主 経費",
            "インボイス制度",
            "フリーランス 税金",
            "ファクタリング 個人",
            "即日 資金調達"
        ]

        for i, kw in enumerate(keywords_to_check):
            print(f"\n  [{i+1}/{len(keywords_to_check)}] キーワード: 「{kw}」")
            try:
                encoded = kw.replace(" ", "+")
                url = f"https://ahrefs.com/keyword-generator?input={encoded}&country=jp"
                page.goto(url, wait_until="domcontentloaded", timeout=30000)
                time.sleep(5)

                ss_name = f"03_kw_{i+1:02d}_{kw.replace(' ', '_')}"
                take_screenshot(page, ss_name)

                body_text = page.evaluate("() => document.body.innerText")
                print(f"  ページテキスト（先頭600字）:\n{body_text[:600]}")

                # テーブルデータの抽出
                table_data = []
                try:
                    table_data = page.evaluate("""() => {
                        const rows = document.querySelectorAll('table tr');
                        return Array.from(rows).map(row => {
                            const cells = row.querySelectorAll('td, th');
                            return Array.from(cells).map(c => c.innerText.trim()).join(' | ');
                        }).filter(r => r.length > 0).slice(0, 30);
                    }""")
                except Exception:
                    pass

                # ボリューム情報をリストから抽出
                volume_info = None
                volume_patterns = [
                    r'(\d{1,3}(?:,\d{3})*)\s*(?:searches|月間)',
                    r'Volume[:\s]+(\d[\d,KMk]*)',
                    r'(\d+[KMk]?)\s*/\s*mo',
                ]
                for pat in volume_patterns:
                    m = re.search(pat, body_text[:2000])
                    if m:
                        volume_info = m.group(1)
                        break

                kw_result = {
                    "keyword": kw,
                    "url": url,
                    "volume_extracted": volume_info,
                    "table_rows": table_data[:15],
                    "page_text_snippet": body_text[:1500]
                }
                RESULTS["keywords"].append(kw_result)
                print(f"  テーブル行数: {len(table_data)}")
                if table_data:
                    for row in table_data[:8]:
                        print(f"    {row}")
                if volume_info:
                    print(f"  ボリューム: {volume_info}")

            except PWTimeoutError:
                print(f"  タイムアウト: {kw}")
                RESULTS["keywords"].append({"keyword": kw, "error": "timeout"})
            except Exception as e:
                print(f"  エラー: {kw} - {e}")
                RESULTS["keywords"].append({"keyword": kw, "error": str(e)})

        # =========================================================
        # STEP 4: Traffic Checker でpaytner.co.jpのオーガニック概要
        # =========================================================
        print("\n" + "="*60)
        print("STEP 4: Traffic Checker でpaytner.co.jpのトラフィック確認")
        print("="*60)
        try:
            page.goto(
                "https://ahrefs.com/traffic-checker?input=paytner.co.jp",
                wait_until="domcontentloaded", timeout=30000
            )
            time.sleep(5)
            take_screenshot(page, "04_traffic_checker")

            body_text = page.evaluate("() => document.body.innerText")
            print(f"  ページテキスト（先頭1000字）:\n{body_text[:1000]}")
            RESULTS["traffic_data"] = body_text[:3000]

        except Exception as e:
            print(f"  エラー: {e}")
            take_screenshot(page, "04_traffic_checker_error")

        # =========================================================
        # STEP 5: Backlink Checker
        # =========================================================
        print("\n" + "="*60)
        print("STEP 5: Backlink Checker でpaytner.co.jpの被リンク確認")
        print("="*60)
        try:
            page.goto(
                "https://ahrefs.com/backlink-checker?input=paytner.co.jp",
                wait_until="domcontentloaded", timeout=30000
            )
            time.sleep(5)
            take_screenshot(page, "05_backlink_checker")

            body_text = page.evaluate("() => document.body.innerText")
            print(f"  ページテキスト（先頭800字）:\n{body_text[:800]}")
            RESULTS["backlinks"] = body_text[:3000]

        except Exception as e:
            print(f"  エラー: {e}")

        browser.close()

    # =========================================================
    # 結果をJSONに保存
    # =========================================================
    output_path = Path(r"C:\Users\rikit\Projects\_adhoc\ahrefs_paytner_results.json")
    output_path.write_text(json.dumps(RESULTS, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n{'='*60}")
    print(f"結果をJSONに保存: {output_path}")
    print(f"  DR: {RESULTS['dr']}")
    print(f"  キーワード取得数: {len(RESULTS['keywords'])}")
    print(f"{'='*60}")


if __name__ == "__main__":
    run()
