"""
Ahrefs無料ツール - フォーム入力方式でデータを取得
URLパラメータではなくフォームに実際に入力して結果を取得する
"""

import json
import time
import re
import sys
from pathlib import Path
from urllib.parse import quote
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeoutError

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

SCREENSHOT_DIR = Path(r"C:\Users\rikit\Projects\_adhoc\ahrefs_paytner_screenshots")
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

LOG_FILE = open(str(Path(r"C:\Users\rikit\Projects\_adhoc\ahrefs_paytner_log2.txt")), 'w', encoding='utf-8')

RESULTS = {
    "domain": "paytner.co.jp",
    "dr": None,
    "authority_data": {},
    "backlink_data": {},
    "keywords": {},
    "traffic_data": {}
}


def log(msg: str):
    clean = str(msg).replace('\xa0', ' ').replace('\u200b', '')
    print(clean)
    LOG_FILE.write(clean + '\n')
    LOG_FILE.flush()


def ss(page, name: str):
    p = SCREENSHOT_DIR / f"{name}.png"
    try:
        page.screenshot(path=str(p), full_page=True)
        log(f"  [SS] {p.name}")
    except Exception as e:
        log(f"  [SS ERROR] {name}: {e}")


def txt(page, name: str) -> str:
    raw = page.evaluate("() => document.body.innerText") or ""
    clean = raw.replace('\xa0', ' ').replace('\u200b', '')
    path = SCREENSHOT_DIR / f"{name}.txt"
    path.write_text(clean, encoding='utf-8')
    return clean


def accept_cookies(page):
    for sel in ['button:has-text("Accept All")', 'button:has-text("Accept")', '[id*="accept"]']:
        try:
            btn = page.query_selector(sel)
            if btn and btn.is_visible():
                btn.click()
                time.sleep(1.5)
                return True
        except Exception:
            pass
    return False


def find_and_fill_input(page, value: str) -> bool:
    """可視状態のinputに値を入力"""
    selectors = [
        'input[type="url"]',
        'input[type="text"]',
        'input[placeholder]',
        'input',
    ]
    for sel in selectors:
        try:
            els = page.query_selector_all(sel)
            for el in els:
                if el.is_visible():
                    el.triple_click()
                    time.sleep(0.2)
                    el.fill(value)
                    log(f"  入力: [{sel}] = {value}")
                    return True
        except Exception:
            pass
    return False


def extract_table(page) -> list:
    try:
        return page.evaluate("""() => {
            const rows = document.querySelectorAll('table tr');
            return Array.from(rows).map(row => {
                const cells = row.querySelectorAll('td, th');
                return Array.from(cells)
                    .map(c => c.innerText.replace(/\\u00a0/g,' ').trim())
                    .join(' | ');
            }).filter(r => r.trim().length > 1).slice(0, 40);
        }""")
    except Exception:
        return []


def extract_metrics_from_text(text: str, keyword: str = "") -> dict:
    """テキストからメトリクスを抽出"""
    result = {}

    # ボリューム（月間検索数）
    for pat in [
        r'(\d{1,3}(?:,\d{3})+)\s*(?:searches|/mo)',
        r'Volume[:\s]+(\d[\d,\.KMk]*)',
        r'(\d+[KMk])\s*/mo',
        r'Monthly[:\s]+(\d[\d,KMk\.]*)',
    ]:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            result['volume'] = m.group(1)
            break

    # KD (Keyword Difficulty)
    for pat in [r'KD[:\s]+(\d+)', r'Difficulty[:\s]+(\d+)', r'(\d+)%?\s*(?:difficulty|KD)']:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            result['kd'] = m.group(1)
            break

    # CPC
    m = re.search(r'CPC[:\s]+\$?([0-9\.]+)', text, re.IGNORECASE)
    if m:
        result['cpc'] = m.group(1)

    # DR
    for pat in [r'Domain Rating[:\s]*(\d+)', r'DR[:\s]+(\d+)']:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            result['dr'] = m.group(1)
            break

    # Traffic
    for pat in [r'Traffic[:\s]+(\d[\d,KMk\.]*)', r'(\d{3,})\s+organic']:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            result['traffic'] = m.group(1)
            break

    return result


def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            slow_mo=100,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-blink-features=AutomationControlled",
                "--start-maximized"
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
        context.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"
        )
        page = context.new_page()

        # ============================================================
        # 初期アクセス + クッキー同意
        # ============================================================
        log("=== 初期アクセス ===")
        page.goto("https://ahrefs.com/", wait_until="domcontentloaded", timeout=30000)
        time.sleep(3)
        accepted = accept_cookies(page)
        log(f"  クッキー同意: {accepted}")
        ss(page, "00_initial")

        # ============================================================
        # STEP 1: Website Authority Checker - フォーム入力
        # ============================================================
        log("\n" + "="*60)
        log("STEP 1: Website Authority Checker")
        log("="*60)

        page.goto("https://ahrefs.com/website-authority-checker", wait_until="domcontentloaded", timeout=30000)
        time.sleep(3)
        accept_cookies(page)
        ss(page, "01a_authority_before_input")

        # フォームに入力
        filled = find_and_fill_input(page, "paytner.co.jp")
        time.sleep(0.5)
        ss(page, "01b_authority_filled")

        if filled:
            # Enterキーで送信
            page.keyboard.press("Enter")
            log("  フォーム送信（Enter）")
            time.sleep(12)
        else:
            log("  入力フィールドが見つからない - ボタンを探す")
            for sel in ['button[type="submit"]', 'button:has-text("Check")', 'button']:
                try:
                    btn = page.query_selector(sel)
                    if btn and btn.is_visible():
                        btn.click()
                        log(f"  ボタンクリック: [{sel}]")
                        time.sleep(12)
                        break
                except Exception:
                    pass

        ss(page, "01c_authority_result")
        page_text = txt(page, "01c_authority_result")
        log(f"\n  ページテキスト（全文）:\n{page_text[:3000]}")

        # DR抽出
        metrics = extract_metrics_from_text(page_text)
        if 'dr' in metrics:
            RESULTS["dr"] = metrics['dr']
        RESULTS["authority_data"] = {"text": page_text[:5000], "metrics": metrics}
        log(f"  抽出メトリクス: {metrics}")

        # DOMから数値を直接取得
        log("  DOM要素から数値を探す...")
        try:
            numbers = page.evaluate("""() => {
                const all = document.querySelectorAll('*');
                const found = [];
                for(const el of all) {
                    if(el.children.length === 0) {  // テキストノードのみ
                        const t = el.innerText;
                        if(t && /^\\d+$/.test(t.trim()) && parseInt(t) <= 100 && parseInt(t) >= 0) {
                            found.push({
                                text: t.trim(),
                                tag: el.tagName,
                                class: el.className,
                                id: el.id
                            });
                        }
                    }
                }
                return found.slice(0, 20);
            }""")
            log(f"  0-100の数値要素: {json.dumps(numbers, ensure_ascii=False)}")
        except Exception as e:
            log(f"  DOM探索エラー: {e}")

        # ============================================================
        # STEP 2: Backlink Checker
        # ============================================================
        log("\n" + "="*60)
        log("STEP 2: Backlink Checker")
        log("="*60)

        page.goto("https://ahrefs.com/backlink-checker", wait_until="domcontentloaded", timeout=30000)
        time.sleep(3)
        accept_cookies(page)

        filled = find_and_fill_input(page, "paytner.co.jp")
        time.sleep(0.5)
        if filled:
            page.keyboard.press("Enter")
            log("  フォーム送信")
            time.sleep(12)

        ss(page, "02_backlink_result")
        page_text = txt(page, "02_backlink_result")
        log(f"\n  ページテキスト:\n{page_text[:3000]}")
        RESULTS["backlink_data"] = {"text": page_text[:5000]}

        # テーブル抽出
        table = extract_table(page)
        if table:
            RESULTS["backlink_data"]["table"] = table
            log(f"  テーブル ({len(table)}行):")
            for row in table[:10]:
                log(f"    {row}")

        # ============================================================
        # STEP 3: Keyword Generator - 各キーワードを検索
        # ============================================================
        log("\n" + "="*60)
        log("STEP 3: Keyword Generator")
        log("="*60)

        keywords = [
            "ファクタリング",
            "フリーランス 請求書",
            "確定申告 フリーランス",
            "個人事業主 経費",
            "インボイス制度",
            "フリーランス 税金",
            "ファクタリング 個人",
            "即日 資金調達"
        ]

        # まず一度Keyword Generatorにアクセス
        page.goto("https://ahrefs.com/keyword-generator", wait_until="domcontentloaded", timeout=30000)
        time.sleep(3)
        accept_cookies(page)
        ss(page, "03_kw_generator_initial")

        for i, kw in enumerate(keywords):
            log(f"\n  [{i+1}/{len(keywords)}] 「{kw}」")

            try:
                # ページ内のinputに入力
                time.sleep(2)
                filled = find_and_fill_input(page, kw)
                time.sleep(0.5)

                if not filled:
                    log("  直接URLアクセスを試みる")
                    page.goto(
                        f"https://ahrefs.com/keyword-generator?input={quote(kw)}&country=jp",
                        wait_until="domcontentloaded", timeout=30000
                    )
                    time.sleep(3)
                    accept_cookies(page)
                    time.sleep(8)
                else:
                    # 国をJPに設定
                    try:
                        country_sel = page.query_selector('select, [class*="country"], [class*="lang"]')
                        if country_sel:
                            country_sel.select_option(value="jp")
                            log("  国: JP設定")
                    except Exception:
                        pass

                    page.keyboard.press("Enter")
                    log("  Enter送信")
                    time.sleep(12)

                ss(page, f"03_kw_{i+1:02d}_{kw.replace(' ','_')[:20]}")
                page_text = txt(page, f"03_kw_{i+1:02d}_text")
                log(f"  テキスト（先頭2000字）:\n{page_text[:2000]}")

                # テーブル/構造データ
                table = extract_table(page)

                # メトリクス抽出
                metrics = extract_metrics_from_text(page_text, kw)

                kw_data = {
                    "keyword": kw,
                    "metrics": metrics,
                    "table": table[:20],
                    "text_snippet": page_text[:3000]
                }
                RESULTS["keywords"][kw] = kw_data

                if metrics:
                    log(f"  メトリクス: {metrics}")
                if table:
                    log(f"  テーブル ({len(table)}行):")
                    for row in table[:8]:
                        log(f"    {row}")

                # 次のキーワードのためにinputをクリア
                try:
                    input_el = page.query_selector('input[type="text"], input[type="url"], input')
                    if input_el and input_el.is_visible():
                        input_el.triple_click()
                        time.sleep(0.3)
                except Exception:
                    pass

            except PWTimeoutError:
                log(f"  タイムアウト")
                RESULTS["keywords"][kw] = {"error": "timeout"}
            except Exception as e:
                log(f"  エラー: {e}")
                RESULTS["keywords"][kw] = {"error": str(e)}

        # ============================================================
        # STEP 4: Traffic Checker
        # ============================================================
        log("\n" + "="*60)
        log("STEP 4: Traffic Checker - paytner.co.jp")
        log("="*60)

        page.goto("https://ahrefs.com/traffic-checker", wait_until="domcontentloaded", timeout=30000)
        time.sleep(3)
        accept_cookies(page)

        filled = find_and_fill_input(page, "paytner.co.jp")
        if filled:
            time.sleep(0.5)
            page.keyboard.press("Enter")
            log("  フォーム送信")
            time.sleep(12)

        ss(page, "04_traffic_result")
        page_text = txt(page, "04_traffic_result")
        log(f"  テキスト:\n{page_text[:3000]}")
        table = extract_table(page)
        metrics = extract_metrics_from_text(page_text)
        RESULTS["traffic_data"] = {
            "text": page_text[:5000],
            "metrics": metrics,
            "table": table[:20]
        }
        if table:
            log(f"  テーブル ({len(table)}行):")
            for row in table[:10]:
                log(f"    {row}")

        browser.close()

    LOG_FILE.close()

    output_path = Path(r"C:\Users\rikit\Projects\_adhoc\ahrefs_paytner_results2.json")
    output_path.write_text(json.dumps(RESULTS, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f"\n結果JSON保存: {output_path}")
    print(f"  DR: {RESULTS['dr']}")
    print(f"  キーワード数: {len(RESULTS['keywords'])}")


if __name__ == "__main__":
    run()
