import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        url = "https://help.ninout.ai/ng/answers/account_form2/?___s=&___srk=003Q900001SvMpZIAV,006Q900001HST82IAH,005GC00000kynm3YAA"

        await page.goto(url, wait_until="networkidle", timeout=30000)
        await asyncio.sleep(3)

        html_content = await page.content()
        with open("_adhoc/extracted_page.html", "w", encoding="utf-8") as f:
            f.write(html_content)

        css_js = (
            '() => {'
            '  let css = "";'
            '  const styleTags = document.querySelectorAll("style");'
            '  styleTags.forEach((tag, i) => {'
            '    css += "/* === style tag #" + (i+1) + " === */\n";'
            '    css += tag.textContent + "\n\n";'
            '  });'
            '  for (let sheet of document.styleSheets) {'
            '    try {'
            '      css += "/* === Stylesheet: " + (sheet.href || "inline") + " === */\n";'
            '      for (let rule of sheet.cssRules) {'
            '        css += rule.cssText + "\n";'
            '      }'
            '      css += "\n";'
            '    } catch(e) {'
            '      css += "/* Cannot access: " + (sheet.href || "unknown") + " (CORS) */\n\n";'
            '    }'
            '  }'
            '  return css;'
            '}'
        )
        css_data = await page.evaluate(css_js)
        with open("_adhoc/extracted_page.css", "w", encoding="utf-8") as f:
            f.write(css_data)

        await page.screenshot(path="_adhoc/extracted_page.png", full_page=True)

        print("HTML saved: " + str(len(html_content)) + " chars")
        print("CSS saved: " + str(len(css_data)) + " chars")
        print("Screenshot saved")

        await browser.close()

asyncio.run(main())
