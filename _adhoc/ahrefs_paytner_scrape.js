const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const SCREENSHOT_DIR = 'C:\\Users\\rikit\\Projects\\_adhoc\\ahrefs_paytner_screenshots';

async function sleep(ms) {
  return new Promise(r => setTimeout(r, ms));
}

async function main() {
  const results = {
    timestamp: new Date().toISOString(),
    domain: 'paytner.co.jp',
    dr: null,
    keywords: [],
    raw_notes: []
  };

  const browser = await chromium.launch({
    headless: false,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 },
    locale: 'ja-JP',
    userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
  });

  const page = await context.newPage();

  try {
    // ========== STEP 1: 無料ツール一覧の確認 ==========
    console.log('\n=== STEP 1: Ahrefs無料ツール一覧にアクセス ===');
    await page.goto('https://ahrefs.com/free-seo-tools', { waitUntil: 'networkidle', timeout: 30000 });
    await sleep(2000);
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '01_free_tools_list.png'), fullPage: true });
    console.log('スクリーンショット保存: 01_free_tools_list.png');

    // ページ内のツール名を収集
    const toolLinks = await page.$$eval('a[href]', links =>
      links
        .filter(a => a.href.includes('ahrefs.com') && !a.href.includes('#'))
        .map(a => ({ text: a.textContent.trim(), href: a.href }))
        .filter(l => l.text.length > 0)
        .slice(0, 30)
    );
    results.raw_notes.push({ step: 'free_tools_links', data: toolLinks });
    console.log('取得したリンク数:', toolLinks.length);

    // ========== STEP 2: Website Authority Checker でDR確認 ==========
    console.log('\n=== STEP 2: Website Authority Checker でpaytner.co.jpのDR確認 ===');
    await page.goto('https://ahrefs.com/website-authority-checker', { waitUntil: 'networkidle', timeout: 30000 });
    await sleep(2000);
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '02_authority_checker_initial.png') });
    console.log('スクリーンショット保存: 02_authority_checker_initial.png');

    // 入力フィールドを探す
    const inputSelectors = [
      'input[type="url"]',
      'input[name="target"]',
      'input[placeholder*="domain"]',
      'input[placeholder*="URL"]',
      'input[placeholder*="website"]',
      'input[class*="input"]',
      '.input input',
      'form input',
      'input[type="text"]'
    ];

    let inputFound = false;
    for (const sel of inputSelectors) {
      try {
        const el = await page.$(sel);
        if (el) {
          await el.click({ force: true });
          await el.fill('paytner.co.jp');
          console.log(`入力成功: セレクター "${sel}"`);
          inputFound = true;
          break;
        }
      } catch (e) {}
    }

    if (!inputFound) {
      console.log('入力フィールドが見つかりません。DOMを確認します...');
      const html = await page.content();
      const snippet = html.substring(0, 3000);
      results.raw_notes.push({ step: 'authority_checker_html_snippet', data: snippet });
    }

    await sleep(500);
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '03_authority_checker_filled.png') });

    // フォーム送信
    try {
      await page.keyboard.press('Enter');
      await sleep(5000);
    } catch (e) {
      console.log('Enter押下エラー:', e.message);
    }

    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '04_authority_checker_result.png'), fullPage: true });
    console.log('スクリーンショット保存: 04_authority_checker_result.png');

    // DRの数値を取得
    const drSelectors = [
      '.dr-value', '.domain-rating', '[class*="dr"]', '[class*="rating"]',
      '.metric-value', '.score', 'h2', 'h3', '.result-value'
    ];

    for (const sel of drSelectors) {
      try {
        const elements = await page.$$(sel);
        for (const el of elements) {
          const text = await el.textContent();
          if (text && /^\d+/.test(text.trim())) {
            results.dr = text.trim();
            console.log(`DR取得候補 (${sel}):`, text.trim());
          }
        }
      } catch (e) {}
    }

    // ページ全体のテキストからDR関連情報を抽出
    const pageText = await page.evaluate(() => document.body.innerText);
    results.raw_notes.push({ step: 'authority_checker_page_text', data: pageText.substring(0, 2000) });
    console.log('ページテキスト（先頭500字）:', pageText.substring(0, 500));

    // ========== STEP 3: Keyword Generator でキーワード確認 ==========
    console.log('\n=== STEP 3: Keyword Generator でキーワード確認 ===');

    const keywords = [
      'ファクタリング',
      'フリーランス 請求書',
      '確定申告 フリーランス',
      '個人事業主 経費',
      'インボイス制度',
      'フリーランス 税金',
      'ファクタリング 個人',
      '即日 資金調達'
    ];

    // Keyword Generatorにアクセス
    await page.goto('https://ahrefs.com/keyword-generator', { waitUntil: 'networkidle', timeout: 30000 });
    await sleep(2000);
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '05_keyword_generator_initial.png') });
    console.log('スクリーンショット保存: 05_keyword_generator_initial.png');

    // 最初のキーワードで試す
    const kw = keywords[0];
    console.log(`\nキーワード検索: "${kw}"`);

    let kwInputFound = false;
    for (const sel of inputSelectors) {
      try {
        const el = await page.$(sel);
        if (el) {
          await el.click({ force: true });
          await el.fill(kw);
          console.log(`キーワード入力成功: セレクター "${sel}"`);
          kwInputFound = true;
          break;
        }
      } catch (e) {}
    }

    if (kwInputFound) {
      // 国をJPに設定（ドロップダウンがある場合）
      try {
        const countrySelectors = [
          'select[name="country"]', 'select[name="language"]',
          '[class*="country"]', '[class*="lang"]',
          'select'
        ];
        for (const sel of countrySelectors) {
          const el = await page.$(sel);
          if (el) {
            await el.selectOption('JP');
            console.log('国設定: JP');
            break;
          }
        }
      } catch (e) {
        console.log('国設定スキップ:', e.message);
      }

      await page.keyboard.press('Enter');
      await sleep(6000);
    }

    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '06_keyword_generator_result1.png'), fullPage: true });
    console.log('スクリーンショット保存: 06_keyword_generator_result1.png');

    const kw1Text = await page.evaluate(() => document.body.innerText);
    results.raw_notes.push({ step: `keyword_${keywords[0]}`, data: kw1Text.substring(0, 3000) });
    console.log('キーワードページテキスト（先頭800字）:', kw1Text.substring(0, 800));

    // 残りのキーワードをURLパラメータで試す
    for (let i = 1; i < keywords.length; i++) {
      const kw = keywords[i];
      console.log(`\nキーワード検索: "${kw}"`);

      try {
        const encodedKw = encodeURIComponent(kw);
        await page.goto(
          `https://ahrefs.com/keyword-generator?input=${encodedKw}&country=jp`,
          { waitUntil: 'networkidle', timeout: 30000 }
        );
        await sleep(3000);

        await page.screenshot({
          path: path.join(SCREENSHOT_DIR, `07_keyword_${i + 1}_${kw.replace(/\s/g, '_')}.png`),
          fullPage: true
        });
        console.log(`スクリーンショット保存: keyword_${i + 1}`);

        const kwText = await page.evaluate(() => document.body.innerText);
        results.raw_notes.push({ step: `keyword_${kw}`, data: kwText.substring(0, 3000) });
        console.log(`テキスト（先頭600字）:`, kwText.substring(0, 600));

        // ボリューム情報をスクレイプ
        try {
          const tableData = await page.$$eval('table tr', rows =>
            rows.map(row => {
              const cells = Array.from(row.querySelectorAll('td, th'));
              return cells.map(c => c.textContent.trim()).join(' | ');
            })
          );
          if (tableData.length > 0) {
            results.keywords.push({ keyword: kw, table: tableData.slice(0, 20) });
            console.log('テーブルデータ:', tableData.slice(0, 5));
          }
        } catch (e) {}

      } catch (e) {
        console.log(`"${kw}" の取得エラー:`, e.message);
      }
    }

    // ========== STEP 4: Competitors確認（Website Traffic Checker） ==========
    console.log('\n=== STEP 4: paytner.co.jpのトラフィック・競合確認 ===');
    await page.goto('https://ahrefs.com/traffic-checker?input=paytner.co.jp', { waitUntil: 'networkidle', timeout: 30000 });
    await sleep(4000);
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '08_traffic_checker.png'), fullPage: true });
    console.log('スクリーンショット保存: 08_traffic_checker.png');

    const trafficText = await page.evaluate(() => document.body.innerText);
    results.raw_notes.push({ step: 'traffic_checker', data: trafficText.substring(0, 3000) });
    console.log('トラフィックページテキスト（先頭600字）:', trafficText.substring(0, 600));

  } catch (error) {
    console.error('エラー発生:', error.message);
    results.raw_notes.push({ step: 'error', data: error.message });
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, 'error_screenshot.png'), fullPage: true }).catch(() => {});
  }

  await browser.close();

  // 結果をJSONで保存
  const outputPath = 'C:\\Users\\rikit\\Projects\\_adhoc\\ahrefs_paytner_results.json';
  fs.writeFileSync(outputPath, JSON.stringify(results, null, 2), 'utf-8');
  console.log('\n=== 結果をJSONに保存しました:', outputPath, '===');
  console.log('結果サマリー:');
  console.log('  DR:', results.dr);
  console.log('  キーワード取得数:', results.keywords.length);
  console.log('  ノート数:', results.raw_notes.length);
}

main().catch(console.error);
