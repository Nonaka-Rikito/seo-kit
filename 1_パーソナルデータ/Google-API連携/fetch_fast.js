const { spawn } = require('child_process');
const fs = require('fs');

const GA4_SCRIPT = 'google-analytics.js';
const GSC_SCRIPT = 'google-search-console.js';
const PROPERTY_ID = '356839446';
const SITE_URL = 'https://jo-katsu.com/campus/';

// Dates
const CURRENT_START = '2026-01-14';
const CURRENT_END = '2026-02-13';
const PREV_START = '2025-01-14';
const PREV_END = '2025-02-13';

// Helper to run command as promise with stdout capture
function runCommand(cmd, args) {
    return new Promise((resolve, reject) => {
        const proc = spawn('node', [cmd, ...args]); // Using 'node' explicitly
        let stdout = '';
        let stderr = '';

        proc.stdout.on('data', data => stdout += data);
        proc.stderr.on('data', data => stderr += data);

        proc.on('close', code => {
            if (code === 0) resolve(stdout);
            else resolve(null); // Return null on error (no data)
        });

        proc.on('error', err => resolve(null));
    });
}

async function main() {
    console.log('=== Starting SEO Analysis (Parallel) ===');

    // 1. Fetch GA4 Current
    console.log(`[1/4] Fetching GA4 Current...`);
    // Using execSync for GA4 is fine as it's one call
    // But let's use our helper
    const ga4CurrentRaw = await runCommand(GA4_SCRIPT, ['--property', PROPERTY_ID, '--start', CURRENT_START, '--end', CURRENT_END, '--dimensions', 'pagePath', '--limit', '1000']);
    const ga4Current = ga4CurrentRaw ? JSON.parse(ga4CurrentRaw) : { rows: [] };

    // 2. Fetch GA4 Previous
    console.log(`[2/4] Fetching GA4 Previous...`);
    const ga4PrevRaw = await runCommand(GA4_SCRIPT, ['--property', PROPERTY_ID, '--start', PREV_START, '--end', PREV_END, '--dimensions', 'pagePath', '--limit', '1000']);
    const ga4Prev = ga4PrevRaw ? JSON.parse(ga4PrevRaw) : { rows: [] };

    // 3. Merge & Analyze
    console.log('[3/4] Merging and Analyzing Data...');
    const map = new Map();

    ga4Prev.rows.forEach(row => {
        const path = row.pagePath;
        if (!map.has(path)) map.set(path, { path, prev: 0, current: 0 });
        map.get(path).prev = row.sessions;
    });

    ga4Current.rows.forEach(row => {
        const path = row.pagePath;
        if (!map.has(path)) map.set(path, { path, prev: 0, current: 0 });
        map.get(path).current = row.sessions;
    });

    const analyzed = Array.from(map.values()).map(item => {
        item.delta = item.current - item.prev;
        return item;
    });

    const drops = analyzed
        .filter(item => item.delta < 0)
        .sort((a, b) => a.delta - b.delta);

    const topDrops = drops.slice(0, 60); // Top 60
    console.log(`Identified ${topDrops.length} pages with traffic decline.`);

    // 4. Fetch GSC Data (Parallel)
    console.log('[4/4] Fetching GSC Data (Concurrency: 5)...');

    // Chunk array for concurrency
    const concurrency = 5;
    const results = [];

    for (let i = 0; i < topDrops.length; i += concurrency) {
        const chunk = topDrops.slice(i, i + concurrency);
        console.log(`  Processing chunk ${i / concurrency + 1}/${Math.ceil(topDrops.length / concurrency)}...`);

        const promises = chunk.map(async (page) => {
            const filterPath = page.path;
            const gscRaw = await runCommand(GSC_SCRIPT, ['--site', SITE_URL, '--start', CURRENT_START, '--end', CURRENT_END, '--dimensions', 'query', '--filter-page', filterPath, '--limit', '5']);

            let queries = [];
            if (gscRaw) {
                try {
                    const gscData = JSON.parse(gscRaw);
                    queries = gscData.rows || [];
                } catch (e) { }
            }
            page.gsc_queries = queries;
            return page;
        });

        const chunkResults = await Promise.all(promises);
        results.push(...chunkResults);
    }

    // 5. Output
    const OutputFile = 'seo_analysis_result_parallel.json';
    fs.writeFileSync(OutputFile, JSON.stringify(results, null, 2));

    // Markdown
    let md = "# SEO再分析: リライト候補記事リスト (Top 60)\n\n";
    md += "| 順位 | URL | 昨年セッション | 今期セッション | 増減数 | 主な検索クエリ (Click/Imp/Pos) |\n";
    md += "|---|---|---|---|---|---|\n";

    results.forEach((item, idx) => {
        const queries = item.gsc_queries ? item.gsc_queries.slice(0, 3).map(q => `${q.query} (${q.clicks}/${q.impressions}/${q.position})`).join('<br>') : '';
        md += "| " + (idx + 1) + " | " + item.path + " | " + item.prev + " | " + item.current + " | **" + item.delta + "** | " + queries + " |\n";
    });

    fs.writeFileSync('seo_analysis_summary_parallel.md', md);
    console.log('Analysis completed.');
}

main();
