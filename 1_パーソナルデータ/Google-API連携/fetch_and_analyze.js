const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const GA4_SCRIPT = 'google-analytics.js';
const GSC_SCRIPT = 'google-search-console.js';
const PROPERTY_ID = '356839446';
const SITE_URL = 'https://jo-katsu.com/campus/';

// Dates
const CURRENT_START = '2026-01-14';
const CURRENT_END = '2026-02-13';
const PREV_START = '2025-01-14';
const PREV_END = '2025-02-13';

function runCommand(cmd) {
    try {
        return execSync(cmd, { maxBuffer: 1024 * 1024 * 50, encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'] });
    } catch (e) {
        // GSC script returns exit code 1 if no data, which implies empty rows for us
        return null;
    }
}

console.log('=== Starting SEO Analysis ===');

// 1. Fetch GA4 Current
console.log(`[1/4] Fetching GA4 Current (${CURRENT_START} ~ ${CURRENT_END})...`);
const cmd1 = `node ${GA4_SCRIPT} --property ${PROPERTY_ID} --start ${CURRENT_START} --end ${CURRENT_END} --dimensions pagePath --limit 1000`;
const ga4CurrentRaw = runCommand(cmd1);
const ga4Current = ga4CurrentRaw ? JSON.parse(ga4CurrentRaw) : { rows: [] };

// 2. Fetch GA4 Previous
console.log(`[2/4] Fetching GA4 Previous (${PREV_START} ~ ${PREV_END})...`);
const cmd2 = `node ${GA4_SCRIPT} --property ${PROPERTY_ID} --start ${PREV_START} --end ${PREV_END} --dimensions pagePath --limit 1000`;
const ga4PrevRaw = runCommand(cmd2);
const ga4Prev = ga4PrevRaw ? JSON.parse(ga4PrevRaw) : { rows: [] };

// 3. Merge & Analyze
console.log('[3/4] Merging and Analyzing Data...');
const map = new Map();

// Process Previous Data (Benchmark)
ga4Prev.rows.forEach(row => {
    const path = row.pagePath;
    if (!map.has(path)) map.set(path, { path, prev: 0, current: 0 });
    map.get(path).prev = row.sessions;
});

// Process Current Data
ga4Current.rows.forEach(row => {
    const path = row.pagePath;
    if (!map.has(path)) map.set(path, { path, prev: 0, current: 0 });
    map.get(path).current = row.sessions;
});

// Calculate Delta
const analyzed = Array.from(map.values()).map(item => {
    item.delta = item.current - item.prev;
    item.growth = item.prev > 0 ? (item.current - item.prev) / item.prev : (item.current > 0 ? 1 : 0);
    return item;
});

// Filter: Only pages with decrease AND significant volume (prev > 100 or current > 100)
// Or just top drops.
const drops = analyzed
    .filter(item => item.delta < 0)
    .sort((a, b) => a.delta - b.delta); // Ascending (largest negative first)

const topDrops = drops.slice(0, 80); // Top 80 drops
console.log(`Identified ${topDrops.length} pages with traffic decline.`);

// 4. Fetch GSC Data for Top Drops
console.log('[4/4] Fetching GSC Data for target pages...');
const finalResults = [];

for (const [index, page] of topDrops.entries()) {
    // Determine path for GSC filter
    // GSC often stores path as /campus/xxx/
    // GA4 might have /campus/xxx
    const filterPath = page.path;

    console.log(`  [${index + 1}/${topDrops.length}] GSC for ${filterPath} (Delta: ${page.delta})`);

    // Fetch top queries
    const cmdGsc = `node ${GSC_SCRIPT} --site ${SITE_URL} --start ${CURRENT_START} --end ${CURRENT_END} --dimensions query --filter-page "${filterPath}" --limit 5`;
    const gscRaw = runCommand(cmdGsc);

    if (gscRaw) {
        try {
            const gscData = JSON.parse(gscRaw);
            page.gsc_queries = gscData.rows || [];
        } catch (e) {
            page.gsc_queries = [];
        }
    } else {
        page.gsc_queries = [];
    }
    finalResults.push(page);
}

// 5. Output
const OutputFile = 'seo_analysis_result_20260215.json';
fs.writeFileSync(OutputFile, JSON.stringify(finalResults, null, 2));
console.log(`Analysis saved to ${OutputFile}`);

// Generate Markdown Summary
let md = "# SEO再分析: リライト候補記事リスト (50-100選)\n\n";
md += "| 順位 | URL | 昨年セッション | 今期セッション | 増減数 | 主な検索クエリ (Click/Imp/Pos) |\n";
md += "|---|---|---|---|---|---|\n";

finalResults.forEach((item, idx) => {
    const queries = item.gsc_queries.slice(0, 3).map(q => `${q.query} (${q.clicks}/${q.impressions}/${q.position})`).join('<br>');
    md += `| ${idx + 1} | ${item.path} | ${item.prev} | ${item.current} | **${item.delta}** | ${queries} |\n`;
});

fs.writeFileSync('seo_analysis_summary.md', md);
console.log('Markdown summary saved to seo_analysis_summary.md');
