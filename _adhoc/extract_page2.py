import asyncio
from playwright.async_api import async_playwright

JS_CSS = r"""
() => {
    let css = '';
    let styleTags = document.querySelectorAll('style');
    for (let i = 0; i < styleTags.length; i++) {
        css += '/* style tag ' + (i+1) + ' */\n';
        css += styleTags[i].textContent + '\n\n';
    }
    for (let i = 0; i < document.styleSheets.length; i++) {
        let sheet = document.styleSheets[i];
        try {
            let href = sheet.href ? sheet.href : 'inline';
            css += '/* Stylesheet: ' + href + ' */\n';
            let rules = sheet.cssRules;
            for (let j = 0; j < rules.length; j++) {
                css += rules[j].cssText + '\n';
            }
            css += '\n';
        } catch(e) {
            let href2 = sheet.href ? sheet.href : 'unknown';
            css += '/* Cannot access: ' + href2 + ' */\n\n';
        }
    }
    return css;
}
"""

JS_DOM = r"""
() => {
    return document.documentElement.outerHTML;
}
"""

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        url = "https://help.ninout.ai/ng/answers/account_form2/?___s=&___srk=003Q900001SvMpZIAV,006Q900001HST82IAH,005GC00000kynm3YAA"

        await page.goto(url, wait_until="networkidle", timeout=60000)

        # Wait for AngularJS to render the form
        # Look for visible form text that appears after rendering
        try:
            await page.wait_for_selector("text=契約更新のご案内", timeout=15000)
            print("AngularJS form rendered - found section A text")
        except Exception:
            print("WARNING: Could not find section A text, trying longer wait...")
            await asyncio.sleep(10)

        # Additional wait to ensure full rendering
        await asyncio.sleep(2)

        # Take screenshot first to see current state
        await page.screenshot(path="_adhoc/extracted_page.png", full_page=True)
        print("Screenshot saved")

        # Get rendered DOM via JS (captures AngularJS-rendered content)
        html_content = await page.evaluate(JS_DOM)
        html_content = "<!DOCTYPE html>\n<html" + html_content[5:]  # fix doctype
        with open("_adhoc/extracted_page.html", "w", encoding="utf-8") as f:
            f.write(html_content)

        # Also get page.content() for comparison
        page_content = await page.content()
        with open("_adhoc/extracted_page_raw.html", "w", encoding="utf-8") as f:
            f.write(page_content)

        # Get CSS
        css_data = await page.evaluate(JS_CSS)
        with open("_adhoc/extracted_page.css", "w", encoding="utf-8") as f:
            f.write(css_data)

        # Verify key content exists
        checks = [
            ("Section A - 契約更新", "契約更新" in html_content),
            ("Section B - 組織管理者", "組織管理者" in html_content),
            ("Section C - 請求先", "請求先" in html_content),
            ("Section D - サブドメイン", "サブドメイン" in html_content),
            ("Section E - IP制限", "IP" in html_content),
            ("Section F - Salesforce", "Salesforce" in html_content or "salesforce" in html_content.lower()),
            ("Section G - ロゴ", "ロゴ" in html_content),
            ("<input> tags", "<input" in html_content),
        ]
        print("\n=== Content verification ===")
        for label, found in checks:
            status = "OK" if found else "MISSING"
            print(f"  {status}: {label}")

        print(f"\nHTML saved: {len(html_content)} chars")
        print(f"CSS saved: {len(css_data)} chars")

        await browser.close()

asyncio.run(main())
