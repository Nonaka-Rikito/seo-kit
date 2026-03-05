"""
Ahrefs無料ツールから paytner.co.jp の競合・キーワードデータを取得するスクリプト v2
クッキー同意バナーに対応
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


def accept_cookies(page):
    """クッキー同意ボタンをクリック"""
    cookie_selectors = [
        'button:has-text("Accept All")',
        'button:has-text("Accept all")',
        'button:has-text("Accept")',
        'button:has-text("同意する")',
        'button:has-text("OK")',
        '[id*="accept"]',
        '[class*="accept"]',
        'button[data-testid*="accept"]',
    ]
    for sel in cookie_selectors:
        try:
            btn = page.query_selector(sel)
            if btn and btn.is_visible():
                btn.click()
                print(f"  クッキー同意: [{sel}]")
                time.sleep(2)
                return True
        except Exception:
            pass
    return False


def wait_for_results(page, timeout=15):
    """ページにコンテンツが読み込まれるまで待機"""
    time.sleep(timeout)


def get_page_text(page) -> str:
    return page.evaluate("() => document.body.innerText") or ""


def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-blink-features=AutomationControlled",
            ]
        )
        context = browser.new_context(
            viewport={"width": 1440, "height": 900},
            locale="en-US",
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/121.0.0.0 Safari/537.36"
            )
        )
        # JavaScriptによるwebdriver検出を回避
        context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
        """)
        page = context.new_page()

        # =========================================================
        # まずAhrefsのトップページにアクセスしてクッキーを設定
        # =========================================================
        print("\n=== 初期アクセス・クッキー同意処理 ===")
        page.goto("https://ahrefs.com/", wait_until="domcontentloaded", timeout=30000)
        time.sleep(3)
        take_screenshot(page, "00_initial_page")
        accept_cookies(page)
        take_screenshot(page, "00_after_cookie_accept")

        # =========================================================
        # STEP 1: 無料ツール一覧
        # =========================================================
        print("\n" + "="*60)
        print("STEP 1: 無料ツール一覧確認")
        print("="*60)
        page.goto("https://ahrefs.com/free-seo-tools", wait_until="domcontentloaded", timeout=30000)
        time.sleep(3)
        accept_cookies(page)
        take_screenshot(page, "01_free_tools_list")
        text = get_page_text(page)
        print(f"  ページテキスト（先頭500字）:\n{text[:500]}")

        # =========================================================
        # STEP 2: Website Authority Checker でDR確認
        # =========================================================
        print("\n" + "="*60)
        print("STEP 2: Website Authority Checker でpaytner.co.jpのDR確認")
        print("="*60)

        page.goto(
            "https://ahrefs.com/website-authority-checker?input=paytner.co.jp",
            wait_until="domcontentloaded", timeout=30000
        )
        time.sleep(3)
        accept_cookies(page)
        time.sleep(8)  # 結果読み込み待機
        take_screenshot(page, "02_authority_checker")

        text = get_page_text(page)
        print(f"  ページテキスト（先頭1500字）:\n{text[:1500]}")
        RESULTS["raw_notes"].append({"step": "authority_checker", "text": text[:4000]})

        # DRを抽出（0-100の数値）
        for sel in ['[class*="dr"]', '[data-metric="dr"]', '.metric-value', 'h2', 'h3',
                    '[class*="rating"]', '[class*="score"]', '.cell-metric', 'strong', 'b']:
            try:
                els = page.query_selector_all(sel)
                for el in els:
                    txt = el.inner_text().strip()
                    if txt and re.match(r'^\d+$', txt) and 0 <= int(txt) <= 100:
                        if RESULTS["dr"] is None:
                            RESULTS["dr"] = txt
                            print(f"  DR候補検出 [{sel}]: {txt}")
            except Exception:
                pass

        # テキストからDR抽出
        dr_match = re.search(r'Domain Rating[:\s]*(\d+)', text, re.IGNORECASE)
        if dr_match and RESULTS["dr"] is None:
            RESULTS["dr"] = dr_match.group(1)
            print(f"  DRテキスト抽出: {RESULTS['dr']}")

        # =========================================================
        # STEP 3: Keyword Generator でキーワード検索
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
                # URLエンコード（日本語はそのまま通る場合も多い）
                from urllib.parse import quote
                encoded = quote(kw)
                url = f"https://ahrefs.com/keyword-generator?input={encoded}&country=jp"
                print(f"  URL: {url}")

                page.goto(url, wait_until="domcontentloaded", timeout=30000)
                time.sleep(3)
                accept_cookies(page)
                time.sleep(8)  # データ読み込み待機

                ss_name = f"03_kw_{i+1:02d}"
                take_screenshot(page, ss_name)

                text = get_page_text(page)
                print(f"  ページテキスト（先頭1000字）:\n{text[:1000]}")

                # テーブルデータ抽出
                table_data = []
                try:
                    table_data = page.evaluate("""() => {
                        const rows = document.querySelectorAll('table tr, [class*="table"] [class*="row"]');
                        return Array.from(rows).map(row => {
                            const cells = row.querySelectorAll('td, th, [class*="cell"]');
                            return Array.from(cells).map(c => c.innerText.trim()).join(' | ');
                        }).filter(r => r.length > 1).slice(0, 30);
                    }""")
                except Exception:
                    pass

                # ボリューム抽出
                volume_patterns = [
                    r'(\d{1,3}(?:,\d{3})+)\s*(?:searches|/mo)',
                    r'Volume[:\s]+(\d[\d,KMk\.]*)',
                    r'(\d+[KMk])\s*/mo',
                    r'(\d{3,})',
                ]
                volume_info = None
                for pat in volume_patterns:
                    m = re.search(pat, text[:2000])
                    if m:
                        volume_info = m.group(1)
                        break

                kw_result = {
                    "keyword": kw,
                    "volume_extracted": volume_info,
                    "table_rows": table_data[:20],
                    "page_text": text[:2000]
                }
                RESULTS["keywords"].append(kw_result)

                if table_data:
                    print(f"  テーブル（{len(table_data)}行）:")
                    for row in table_data[:10]:
                        print(f"    {row}")
                else:
                    print(f"  テーブルデータなし")

                if volume_info:
                    print(f"  ボリューム候補: {volume_info}")

            except PWTimeoutError:
                print(f"  タイムアウト: {kw}")
                RESULTS["keywords"].append({"keyword": kw, "error": "timeout"})
            except Exception as e:
                print(f"  エラー: {e}")
                RESULTS["keywords"].append({"keyword": kw, "error": str(e)})

        # =========================================================
        # STEP 4: Traffic Checker
        # =========================================================
        print("\n" + "="*60)
        print("STEP 4: Traffic Checker でpaytner.co.jpのオーガニックトラフィック確認")
        print("="*60)
        try:
            page.goto(
                "https://ahrefs.com/traffic-checker?input=paytner.co.jp",
                wait_until="domcontentloaded", timeout=30000
            )
            time.sleep(3)
            accept_cookies(page)
            time.sleep(8)
            take_screenshot(page, "04_traffic_checker")

            text = get_page_text(page)
            print(f"  ページテキスト（先頭1500字）:\n{text[:1500]}")
            RESULTS["traffic_data"] = text[:4000]
        except Exception as e:
            print(f"  エラー: {e}")

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
            time.sleep(3)
            accept_cookies(page)
            time.sleep(8)
            take_screenshot(page, "05_backlink_checker")

            text = get_page_text(page)
            print(f"  ページテキスト（先頭1200字）:\n{text[:1200]}")
            RESULTS["backlinks"] = text[:4000]
        except Exception as e:
            print(f"  エラー: {e}")

        browser.close()

    # =========================================================
    # 結果保存
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
