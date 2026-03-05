# Write Command

Use this command to create comprehensive, SEO-optimized long-form blog content.

## Usage
`/write [topic or research brief]`

## What This Command Does
1. Creates complete, well-structured long-form articles (10,000文字以上)
2. Optimizes content for target keywords and SEO best practices
3. Maintains your brand voice and messaging throughout
4. Integrates internal and external links strategically
5. Includes all meta elements for publishing

## Process

### Pre-Writing Review
- **Research Brief**: Review research brief from `/research` command if available
- **Brand Voice**: Check @context/brand-voice.md for tone and messaging
- **Writing Examples**: Study @context/writing-examples.md for style consistency
- **Style Guide**: Follow formatting rules from @context/style-guide.md
- **SEO Guidelines**: Apply requirements from @context/seo-guidelines.md
- **Target Keywords**: Integrate keywords from @context/target-keywords.md naturally

### Content Structure

#### 1. Headline (H1)
- Include primary keyword naturally
- Create compelling, click-worthy title
- Keep under 60 characters for SERP display
- Promise clear value to reader

#### 2. Introduction (150-200 words)

**CRITICAL: The Hook (First 1-2 Sentences)**

The opening hook is the most important element. A strong hook can boost reader retention by 30%. NEVER open with a generic definition or statement like "X is..." or "When it comes to..."

**Choose ONE hook type for each article:**

| Hook Type | Example | Best For |
|-----------|---------|----------|
| **Provocative Question** | "What if the 'free' plan is actually costing you $500/month in lost opportunities?" | Challenging assumptions |
| **Specific Scenario** | "Last Tuesday, Sarah checked her dashboard and discovered something alarming: her site had been invisible to Google for three weeks." | Creating emotional connection |
| **Surprising Statistic** | "73% of SaaS users who switch platforms do so within 18 months, and most cite the same three reasons." | Data-driven topics |
| **Bold Statement** | "Your current tool is lying to you about your numbers." | Controversial takes |
| **Counterintuitive Claim** | "The cheapest option might be the most expensive decision you make this year." | Comparison content |

**After the hook, follow the APP Formula:**
- **Agree**: Acknowledge something the reader already believes/feels
- **Promise**: Tell them exactly what they'll learn or gain
- **Preview**: Brief overview of what's coming (can include mini table of contents for long posts)

- **Keyword**: Include primary keyword in first 100 words
- **Credibility**: Establish why you/this article is authoritative

#### 3. Main Body (8,000〜12,000文字)
- **Logical Flow**: Organize sections in clear, progressive order
- **H2 Sections**: 4-7 main sections covering comprehensive topic scope
- **H3 Subsections**: Break complex sections into digestible pieces
- **Keyword Integration**: Use primary keyword 1-2% density, variations throughout
- **Depth**: Provide thorough, actionable information at each point
- **Data**: Reference statistics and studies to support claims
- **Visuals**: Note where images, screenshots, or graphics enhance understanding
- **Lists**: Use bulleted or numbered lists for scannability
- **Formatting**: Bold key concepts, use short paragraphs (2-4 sentences MAX)

**REQUIRED: Mini-Stories (2-3 per article)**

Research shows we're 22x more likely to remember facts wrapped in stories. Every article MUST include 2-3 mini-scenarios with:
- A **specific person** (use names, even if fictional: "Sarah," "Mike," "The team at Acme Corp")
- A **concrete situation** with details (dates, numbers, specifics)
- A **clear outcome** that illustrates the point

**Example mini-story (aim for 50-150 words each):**
> "When Marcus launched his SaaS product in March 2024, he chose the cheapest hosting plan he could find, $5/month seemed like a no-brainer. Six months later, his app hit 10,000 active users. That's when he discovered the hidden bandwidth fees buried in his provider's terms. His $5/month plan suddenly became $89/month. Worse, migrating mid-growth meant a 3-week gap in analytics that cost him a $2,000 partnership deal. The 'savings' from cheap hosting cost him over $3,000."

**Place mini-stories:**
- One in the introduction or early section (to hook readers)
- One in the middle (to re-engage skimmers)
- One near the conclusion (to reinforce the main point)

**REQUIRED: CTA配置設計（1記事あたり2〜3箇所）**

文中にいきなりバナーを置かない。CTAは必ず「見出し → 接続本文 → バナー画像」の3点セットで構成する。

**CTA 3点セット構成:**

```
### [CTA見出し — セクション内容と自然につながるH3]

[接続本文 — 直前の本文内容を受けて、読者の課題・欲求とCTAの提供価値を橋渡しする1〜3文。
「ここまで読んで〜と感じた方は」「〜を今すぐ試したい方は」のように、
読者の心理状態に寄り添った導線文を書く。]

[CTAバナー画像 — ![alt text](バナー画像URL)]
```

**CTA配置戦略:**

| 配置箇所 | タイミング | 訴求の方向性 | 接続本文の例 |
|----------|-----------|-------------|-------------|
| 序盤（最初のH2セクション後） | 課題認識が深まった直後 | 共感型（「まずは無料で試す」「詳しく知る」） | 「〜という課題を感じている方は、まず○○から始めてみてください。」 |
| 中盤（比較・事例セクション後） | 解決策への納得感が出たタイミング | 証拠型（「実績を見る」「事例を確認」） | 「A社のように成果を出すには、○○の導入が第一歩です。」 |
| 終盤（まとめ直前） | 行動意欲が最も高い | 行動喚起型（「無料トライアル」「相談予約」） | 「本記事で紹介した○○を実践するなら、今すぐ始められます。」 |

**CTA設計ルール:**
- CTAバナーの前に必ず接続本文を入れる（バナー単体での挿入禁止）
- 接続本文は直前セクションの内容と自然につながること
- 訴求文言はセクションごとに変える（同じ文言の繰り返し禁止）
- 最初のCTAは記事冒頭から2,000文字以内に配置
- 「詳しくはこちら」「クリックしてください」等の汎用文言は使わない
- CTAクリック数・CTR最大化を意識した訴求設計を行う

#### 4. Conclusion (150-200 words)
- **Recap**: Summarize 3-5 key takeaways
- **Action**: Provide clear next steps for reader
- **CTA**: Include relevant call-to-action (free trial, resource download, etc.)
- **Encouragement**: End on empowering, forward-looking note

### SEO Optimization

#### Keyword Placement
- H1 headline
- First paragraph (within first 100 words)
- At least 2-3 H2 headings
- Naturally throughout body (1-2% density)
- Meta title and description
- URL slug

#### Internal Linking (3-5+ links)
- Reference @context/internal-links-map.md for key pages
- Link to relevant pillar content from your site
- Link to related blog articles
- Link to product/service pages where natural
- Use descriptive anchor text with keywords

#### External Linking (2-3 links)
- Link to authoritative sources for statistics
- Reference industry research or studies
- Link to tools or resources mentioned
- Build credibility with quality sources

#### Readability
- Keep sentences under 25 words average
- Use transition words between sections
- Vary sentence length for rhythm
- Write at 8th-10th grade reading level
- Use active voice predominantly
- Break up text with subheadings every 300-400 words

### Target Audience Focus
- **Audience Perspective**: Write for your target audience (defined in @context/brand-voice.md)
- **Practical Application**: Show how information applies to their specific challenges
- **Product Integration**: Naturally mention how your features solve problems (reference @context/features.md)
- **Industry Context**: Reference relevant trends and best practices
- **Technical Accuracy**: Ensure terminology and processes are correct for your industry

### Brand Voice Consistency
- Maintain your brand tone (reference @context/brand-voice.md for specifics)
- Follow your established voice pillars
- Use messaging framework from your context files
- Apply terminology preferences consistently
- Match tone to content type (how-to, strategy, news, etc.)

## Output
Provides a complete, publish-ready article including:

### 1. Article Content
Full markdown-formatted article with:
- H1 headline
- Introduction
- Body sections with H2/H3 structure
- Conclusion with CTA
- Proper formatting and styling

### 2. Meta Elements
```
---
Meta Title: [50-60 character optimized title]
Meta Description: [150-160 character compelling description]
Primary Keyword: [main target keyword]
Secondary Keywords: [keyword1, keyword2, keyword3]
URL Slug: /blog/[optimized-slug]
Internal Links: [list of pages linked from your site]
External Links: [list of external sources]
Word Count: [actual word count]
---
```

### 3. SEO Checklist
- [ ] Primary keyword in H1
- [ ] Primary keyword in first 100 words
- [ ] Primary keyword in 2+ H2 headings
- [ ] Keyword density 1-2%
- [ ] 3-5+ internal links included
- [ ] 2-3 external authority links
- [ ] Meta title 50-60 characters
- [ ] Meta description 150-160 characters
- [ ] Article 10,000文字以上
- [ ] Proper H2/H3 hierarchy
- [ ] Readability optimized

### 4. Engagement Checklist
- [ ] **Hook**: Opens with question, scenario, statistic, or bold statement (NOT generic definition)
- [ ] **APP Formula**: Introduction includes Agree, Promise, Preview elements
- [ ] **Mini-stories**: 2-3 specific scenarios with names, details, and outcomes
- [ ] **CTA 3点セット**: 見出し + 接続本文 + バナー画像の構成で2-3箇所配置
- [ ] **CTA接続本文**: 各CTAに直前内容と繋がる導線文あり
- [ ] **First CTA**: 記事冒頭から2,000文字以内に配置
- [ ] **Paragraph length**: No paragraphs exceed 4 sentences
- [ ] **Sentence rhythm**: Mix of short (5-10 words) and longer sentences (15-25 words)

## File Management
After completing the article, automatically save to:
- **File Location**: `drafts/[topic-slug]-[YYYY-MM-DD].md`
- **File Format**: Markdown with frontmatter and formatted content
- **Naming Convention**: Use lowercase, hyphenated topic slug and current date

Example: `drafts/content-marketing-strategies-2025-10-15.md`

## Automatic Content Scrubbing

**CRITICAL**: Immediately after saving the article file, automatically invoke the content scrubber to remove AI watermarks and telltale patterns.

### Why This Matters
AI-generated content often contains invisible Unicode watermarks and characteristic patterns (like em-dash overuse) that can identify it as AI-written. Scrubbing removes these indicators to make content appear naturally human-written.

### Scrubbing Process
1. **Invoke Scrubber**: Run `/scrub [file-path]` on the saved article file
2. **Automatic Execution**: This should happen automatically, not require user action
3. **Timing**: Must occur immediately after file save, before any other processing
4. **Scope**: Scrub the main article file only (not meta or analysis files)

### What Gets Cleaned
- Invisible Unicode watermarks (zero-width spaces, BOMs, format-control characters)
- Em-dashes replaced with contextually appropriate punctuation (commas, semicolons, periods)
- Whitespace normalization and formatting cleanup
- All changes preserve content meaning and markdown structure

### Verification
The scrubber will display statistics:
- Unicode watermarks removed
- Format-control characters removed
- Em-dashes replaced

### Example Workflow
```
1. Write article → Save to drafts/article-name-2025-10-31.md
2. IMMEDIATELY run: /scrub drafts/article-name-2025-10-31.md
3. Verify scrubbing statistics
4. THEN proceed with optimization agents below
```

This ensures all published content is free of AI signatures before any further processing.

## Automatic Agent Execution
After saving the main article, immediately execute optimization agents:

### 1. Content Analyzer Agent (NEW!)
- **Agent**: `content-analyzer`
- **Input**: Full article, meta elements, keywords, SERP data (if available)
- **Output**: Comprehensive analysis covering search intent, keyword density, content length comparison, readability score, and SEO quality rating
- **File**: `drafts/content-analysis-[topic-slug]-[YYYY-MM-DD].md`

This new agent uses 5 specialized analysis modules:
- Search intent analysis
- Keyword density & clustering
- Content length vs competitors
- Readability scoring (Flesch scores)
- SEO quality rating (0-100)

### 2. SEO Optimizer Agent
- **Agent**: `seo-optimizer`
- **Input**: Full article content
- **Output**: SEO optimization report and suggestions
- **File**: `drafts/seo-report-[topic-slug]-[YYYY-MM-DD].md`

### 3. Meta Creator Agent
- **Agent**: `meta-creator`
- **Input**: Article content and primary keyword
- **Output**: Multiple meta title/description options
- **File**: `drafts/meta-options-[topic-slug]-[YYYY-MM-DD].md`

### 4. Internal Linker Agent
- **Agent**: `internal-linker`
- **Input**: Article content
- **Output**: Specific internal linking recommendations
- **File**: `drafts/link-suggestions-[topic-slug]-[YYYY-MM-DD].md`

### 5. Keyword Mapper Agent
- **Agent**: `keyword-mapper`
- **Input**: Article and target keywords
- **Output**: Keyword placement analysis and improvements
- **File**: `drafts/keyword-analysis-[topic-slug]-[YYYY-MM-DD].md`

## Automatic Quality Loop

After saving the initial draft, automatically run the content quality scorer:

### Step 1: Score Content
Run the content scorer to evaluate the draft:
```bash
python data_sources/modules/content_scorer.py drafts/[article-file].md
```

### Step 2: Evaluate Score
The scorer evaluates 5 dimensions (composite score must be ≥70):

| Dimension | Weight | Target |
|-----------|--------|--------|
| Humanity/Voice | 30% | No AI phrases, use contractions |
| Specificity | 25% | Concrete examples, numbers, names |
| Structure Balance | 20% | 40-70% prose (not all lists) |
| SEO Compliance | 15% | Keywords, meta, structure |
| Readability | 10% | Flesch 60-70, grade 8-10 |

### Step 3: Auto-Revise if Needed
If composite score < 70:
1. Review the `priority_fixes` from the scorer
2. Apply the top 3-5 fixes automatically
3. Re-score the content
4. Repeat once more if still below threshold

### Step 4: Route Based on Final Score
- **Score ≥ 70**: Save to `drafts/` and proceed to optimization agents
- **Score < 70 after 2 iterations**: Save to `review-required/` with a `_REVIEW_NOTES.md` file containing the scoring details and remaining issues

### Review-Required Folder
Articles that fail quality threshold after 2 revision attempts go to `review-required/`:
```
review-required/
├── article-name-2025-12-10.md
└── article-name-2025-12-10_REVIEW_NOTES.md
```

The `_REVIEW_NOTES.md` file contains:
- Final composite score
- Dimension breakdown
- Remaining priority fixes
- Reason for human review

## Quality Standards
Every article must meet these requirements:

### Content Requirements
- 10,000文字以上（12,000〜15,000文字推奨）
- Proper H1/H2/H3 hierarchy
- Primary keyword naturally integrated
- 3-5 internal links to your site content
- 2-3 external authoritative links
- Compelling meta title and description
- Clear introduction and conclusion
- Actionable, valuable information
- Brand voice maintained
- Target audience focused

### Engagement Requirements
- **Compelling hook** in first 1-2 sentences (no generic openings)
- **2-3 mini-stories** with specific names, details, and outcomes
- **CTA 3点セット**（見出し+接続本文+バナー画像）で2-3箇所配置
- **最初のCTAは2,000文字以内**に配置
- **No paragraphs longer than 4 sentences**
- **Varied sentence rhythm** (mix short punchy + longer flowing)

### Quality Score
- **Composite quality score ≥70**
- Publish-ready quality

This ensures every article is comprehensive, optimized, engaging, and ready to rank while providing genuine value to your target audience.
