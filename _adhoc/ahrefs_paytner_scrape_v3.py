"""
Ahrefs無料ツールから paytner.co.jp の競合・キーワードデータを取得するスクリプト v3
クッキー同意対応 + Windowsエンコードエラー修正
"""

import json
import time
import re
import sys
from pathlib import Path
from urllib.parse import quote
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeoutError

# stdout/stderrをUTF-8に強制
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

SCREENSHOT_DIR = Path(r"C:\Users\rikit\Projects\_adhoc\ahrefs_paytner_screenshots")
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

LOG_PATH = Path(r"C:\Users\rikit\Projects\_adhoc\ahrefs_paytner_log.txt")
log_file = open(str(LOG_PATH), 'w', encoding='utf-8')

RESULTS = {
    "domain": "paytner.co.jp",
    "dr": None,
    "backlinks": None,
    "keywords": [],
    "traffic_data": None,
    "raw_notes": []
}


def log(msg: str):
    """ログを画面とファイルに出力"""
    clean = msg.replace('\xa0', ' ').replace('\u200b', '')
    print(clean)
    log_file.write(clean + '\n')
    log_file.flush()


def take_screenshot(page, name: str):
    path = SCREENSHOT_DIR / f"{name}.png"
    try:
        page.screenshot(path=str(path), full_page=True)
        log(f"  [SS] {path.name}")
    except Exception as e:
        log(f"  [SS ERROR] {name}: {e}")


def accept_cookies(page):
    """クッキー同意ボタンをクリック"""
    cookie_selectors = [
        'button:has-text("Accept All")',
        'button:has-text("Accept all")',
        'button:has-text("Accept")',
        '[id*="accept"]',
        '[class*="accept"]',
    ]
    for sel in cookie_selectors:
        try:
            btn = page.query_selector(sel)
            if btn and btn.is_visible():
                btn.click()
                log(f"  クッキー同意OK: [{sel}]")
                time.sleep(2)
                return True
        except Exception:
            pass
    return False


def clean_text(text: str) -> str:
    """特殊文字を除去"""
    return text.replace('\xa0', ' ').replace('\u200b', '').replace('\u00ad', '')


def save_text_to_file(name: str, text: str):
    """テキストをファイルに保存（エンコード問題回避）"""
    path = SCREENSHOT_DIR / f"{name}.txt"
    path.write_text(text, encoding='utf-8')
    log(f"  [TXT] {path.name}")


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
        context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
        """)
        page = context.new_page()

        # ==========================================================
        # 初期アクセス・クッキー同意
        # ==========================================================
        log("\n=== 初期アクセス・クッキー同意処理 ===")
        page.goto("https://ahrefs.com/", wait_until="domcontentloaded", timeout=30000)
        time.sleep(3)
        accept_cookies(page)
        take_screenshot(page, "00_initial")

        # ==========================================================
        # STEP 1: 無料ツール一覧
        # ==========================================================
        log("\n" + "="*60)
        log("STEP 1: 無料ツール一覧確認")
        log("="*60)
        page.goto("https://ahrefs.com/free-seo-tools", wait_until="domcontentloaded", timeout=30000)
        time.sleep(3)
        accept_cookies(page)
        take_screenshot(page, "01_free_tools_list")
        raw = page.evaluate("() => document.body.innerText") or ""
        text = clean_text(raw)
        save_text_to_file("01_free_tools_text", text)
        log(f"  テキスト先頭300字:\n{text[:300]}")

        # ==========================================================
        # STEP 2: Website Authority Checker (DR確認)
        # ==========================================================
        log("\n" + "="*60)
        log("STEP 2: Website Authority Checker - paytner.co.jpのDR確認")
        log("="*60)
        page.goto(
            "https://ahrefs.com/website-authority-checker?input=paytner.co.jp",
            wait_until="domcontentloaded", timeout=30000
        )
        time.sleep(3)
        accept_cookies(page)
        time.sleep(10)
        take_screenshot(page, "02_authority_checker")

        raw = page.evaluate("() => document.body.innerText") or ""
        text = clean_text(raw)
        save_text_to_file("02_authority_text", text)
        log(f"  テキスト先頭2000字:\n{text[:2000]}")
        RESULTS["raw_notes"].append({"step": "authority_checker", "text": text[:5000]})

        # DRを数値セレクターで抽出
        for sel in [
            '.dr-value', '[class*="dr"]', '[data-metric="dr"]',
            '.metric-value', '[class*="rating"]', '[class*="score"]',
            'h2', 'h3', 'strong', 'b', '.value'
        ]:
            try:
                els = page.query_selector_all(sel)
                for el in els:
                    txt = el.inner_text().strip()
                    if txt and re.match(r'^\d+$', txt) and 0 <= int(txt) <= 100:
                        if RESULTS["dr"] is None:
                            RESULTS["dr"] = txt
                            log(f"  DR検出 [{sel}]: {txt}")
            except Exception:
                pass

        # テキスト正規表現でDR抽出
        for pat in [
            r'Domain Rating[:\s]*(\d+)',
            r'DR[:\s]+(\d+)',
            r'Authority Score[:\s]*(\d+)',
        ]:
            m = re.search(pat, text, re.IGNORECASE)
            if m and RESULTS["dr"] is None:
                RESULTS["dr"] = m.group(1)
                log(f"  DRテキスト抽出: {RESULTS['dr']}")

        # ==========================================================
        # STEP 3: Keyword Generator
        # ==========================================================
        log("\n" + "="*60)
        log("STEP 3: Keyword Generator でキーワード検索")
        log("="*60)

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
            log(f"\n  [{i+1}/{len(keywords_to_check)}] キーワード: {kw}")
            try:
                encoded = quote(kw)
                url = f"https://ahrefs.com/keyword-generator?input={encoded}&country=jp"
                log(f"  URL: {url}")

                page.goto(url, wait_until="domcontentloaded", timeout=30000)
                time.sleep(3)
                accept_cookies(page)
                time.sleep(10)

                ss_name = f"03_kw_{i+1:02d}"
                take_screenshot(page, ss_name)

                raw = page.evaluate("() => document.body.innerText") or ""
                text = clean_text(raw)
                save_text_to_file(f"03_kw_{i+1:02d}_text", text)
                log(f"  テキスト先頭1500字:\n{text[:1500]}")

                # テーブルデータ抽出
                table_data = []
                try:
                    table_data = page.evaluate("""() => {
                        const rows = document.querySelectorAll('table tr');
                        return Array.from(rows).map(row => {
                            const cells = row.querySelectorAll('td, th');
                            return Array.from(cells).map(c => c.innerText.replace(/\\u00a0/g, ' ').trim()).join(' | ');
                        }).filter(r => r.trim().length > 1).slice(0, 30);
                    }""")
                except Exception as te:
                    log(f"  テーブル抽出エラー: {te}")

                # リスト形式のデータ抽出
                list_data = []
                try:
                    list_data = page.evaluate("""() => {
                        const items = document.querySelectorAll('[class*="row"], [class*="item"], li');
                        return Array.from(items)
                            .map(el => el.innerText.replace(/\\u00a0/g, ' ').trim())
                            .filter(t => t.length > 3 && t.length < 200)
                            .slice(0, 30);
                    }""")
                except Exception:
                    pass

                # 数値ボリューム抽出
                volume_info = None
                for pat in [
                    r'(\d{1,3}(?:,\d{3})+)\s*(?:searches|/mo|per month)',
                    r'Volume[:\s]+(\d[\d,\.KMk]*)',
                    r'(\d+[KMk])\s*/mo',
                    r'Monthly searches[:\s]*(\d[\d,KMk\.]*)',
                ]:
                    m = re.search(pat, text[:3000], re.IGNORECASE)
                    if m:
                        volume_info = m.group(1)
                        log(f"  ボリューム候補: {volume_info}")
                        break

                kw_result = {
                    "keyword": kw,
                    "volume": volume_info,
                    "table_rows": [clean_text(r) for r in table_data[:20]],
                    "list_items": [clean_text(r) for r in list_data[:20]],
                    "page_text": text[:3000]
                }
                RESULTS["keywords"].append(kw_result)

                if table_data:
                    log(f"  テーブルデータ ({len(table_data)}行):")
                    for row in table_data[:12]:
                        log(f"    {clean_text(row)}")
                elif list_data:
                    log(f"  リストデータ ({len(list_data)}件):")
                    for item in list_data[:12]:
                        log(f"    {clean_text(item)}")
                else:
                    log(f"  構造化データなし（テキストに保存済み）")

            except PWTimeoutError:
                log(f"  タイムアウト: {kw}")
                RESULTS["keywords"].append({"keyword": kw, "error": "timeout"})
            except Exception as e:
                log(f"  エラー: {e}")
                RESULTS["keywords"].append({"keyword": kw, "error": str(e)})

        # ==========================================================
        # STEP 4: Traffic Checker
        # ==========================================================
        log("\n" + "="*60)
        log("STEP 4: Traffic Checker でpaytner.co.jpの概要確認")
        log("="*60)
        try:
            page.goto(
                "https://ahrefs.com/traffic-checker?input=paytner.co.jp",
                wait_until="domcontentloaded", timeout=30000
            )
            time.sleep(3)
            accept_cookies(page)
            time.sleep(10)
            take_screenshot(page, "04_traffic_checker")

            raw = page.evaluate("() => document.body.innerText") or ""
            text = clean_text(raw)
            save_text_to_file("04_traffic_text", text)
            log(f"  テキスト先頭2000字:\n{text[:2000]}")
            RESULTS["traffic_data"] = text[:5000]
        except Exception as e:
            log(f"  エラー: {e}")

        # ==========================================================
        # STEP 5: Backlink Checker
        # ==========================================================
        log("\n" + "="*60)
        log("STEP 5: Backlink Checker でpaytner.co.jpの被リンク確認")
        log("="*60)
        try:
            page.goto(
                "https://ahrefs.com/backlink-checker?input=paytner.co.jp",
                wait_until="domcontentloaded", timeout=30000
            )
            time.sleep(3)
            accept_cookies(page)
            time.sleep(10)
            take_screenshot(page, "05_backlink_checker")

            raw = page.evaluate("() => document.body.innerText") or ""
            text = clean_text(raw)
            save_text_to_file("05_backlink_text", text)
            log(f"  テキスト先頭2000字:\n{text[:2000]}")
            RESULTS["backlinks"] = text[:5000]
        except Exception as e:
            log(f"  エラー: {e}")

        browser.close()

    log_file.close()

    # 結果保存
    output_path = Path(r"C:\Users\rikit\Projects\_adhoc\ahrefs_paytner_results.json")
    output_path.write_text(json.dumps(RESULTS, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n結果JSON保存: {output_path}")
    print(f"  DR: {RESULTS['dr']}")
    print(f"  キーワード数: {len(RESULTS['keywords'])}")


if __name__ == "__main__":
    run()
