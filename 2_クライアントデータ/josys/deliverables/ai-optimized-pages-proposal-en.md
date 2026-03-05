# Josys AI-Optimized Pages Proposal

**Date**: March 3, 2026
**Author**: malna Inc.
**Audience**: Josys Marketing Team / Global Team

---

## Executive Summary

87% of B2B buyers now use AI tools for vendor research, and LLM-driven signups convert at 6x the rate of Google Organic (per Webflow). Meanwhile, none of Josys's seven major competitors have implemented AI-specific pages such as brand-facts or llms.txt — the entire SaaS Management category is an **LLMO white space**.

This represents a clear opportunity for Josys to establish **first-mover advantage** in AI search visibility.

This proposal outlines the pages to build, their structure, technical requirements, and an execution roadmap.

---

## 1. Current State Analysis

### 1.1 Josys Site Status

| Page | Status | Gap |
|------|--------|-----|
| `/brand-facts` | **Does not exist** | No primary source for AI to retrieve Josys facts |
| `/compare/josys-vs-[competitor]` | **Does not exist** (1 article only) | Missing citation opportunities for comparison queries |
| `/case-studies` | Exists (12+ EN/JP) | No schema markup. Not AI-extractable |
| `/integrations` | Exists (350+ apps) | No schema markup. Numeric strength not machine-readable |
| `/faq` | **No standalone page** | FAQ content yields 2.7x citation rate — untapped |
| `/pricing` | Exists (quote-based) | No FAQ section or schema |
| `llms.txt` | **Does not exist** | No AI site guide |
| Structured data | **Minimal** (homepage FAQ only) | Most pages lack schema |

### 1.2 Competitor LLMO Readiness

| Competitor | brand-facts | Comparison Pages | llms.txt | Schema |
|-----------|------------|-----------------|---------|--------|
| Zylo | None | 2 pages | None | Org + Breadcrumb |
| Productiv | None | 3 pages | None | Org + Breadcrumb |
| BetterCloud | None | **5+ pages** (most) | None | Org + Breadcrumb |
| Zluri | None | Many (blog format) | None | Dynamic JS |
| Torii | None | 2 pages | None | Unverified |
| LeanIX (SAP) | None | None | None | HubDB |
| Snow (Flexera) | None | None | None | Unverified |
| **Josys** | **None** | **1 only** | **None** | **Minimal** |

**No competitor has implemented llms.txt or brand-facts. First-mover opportunity for Josys.**

---

## 2. Pages to Build

### 2.1 Priority A: Core Pages (Foundation for AI Citations)

#### (1) `/llms.txt` — AI Site Guide

**Purpose**: Help AI crawlers efficiently understand Josys site structure and key pages.

**Recommended content**:

```markdown
# Josys

> Unified Identity Governance platform for IT teams and MSPs to manage
> SaaS applications, access controls, and devices across the organization.

Josys is developed by Josys International Pte. Ltd., a subsidiary of Raksul Inc.
Founded in 2022, headquartered in Tokyo, Japan.
600+ customers globally. 350+ app integrations.
SOC 2 Type II and ISO 27001 certified.

## Core Product

- [Platform Overview](https://www.josys.com/platform): AI Identity Governance
- [Pricing](https://www.josys.com/pricing): Plans and packaging
- [Integrations](https://www.josys.com/integrations): 350+ app catalog

## Key Features

- [SaaS Discovery](https://www.josys.com/features/saas-discovery)
- [Access Automation](https://www.josys.com/features/access-automation)
- [Access Reviews](https://www.josys.com/features/access-reviews)
- [SaaS Insights](https://www.josys.com/features/saas-insights)
- [Josys AI](https://www.josys.com/ai)

## Solutions

- [SaaS Visibility](https://www.josys.com/identity-and-application-visibility)
- [Lifecycle Management](https://www.josys.com/identity-lifecycle-management)
- [Security & Risk](https://www.josys.com/identity-security-and-risk)
- [Cost Optimization](https://www.josys.com/cost-optimization)
- [Device Management](https://www.josys.com/device-management)

## Resources

- [Case Studies](https://www.josys.com/case-studies)
- [Blog](https://www.josys.com/blog)
- [Brand Facts](https://www.josys.com/brand-facts)
- [FAQ](https://www.josys.com/faq)
- [Trust & Security](https://www.josys.com/trust-security)
```

**Effort**: 2 hours
**Japanese version**: Deploy `/llms-ja.txt` with localized content

---

#### (2) `/brand-facts` — AI Fact Sheet

**Purpose**: Serve as the authoritative primary source when AI answers "What is Josys?" or "Tell me about Josys." This page **validates** what external media says about Josys.

**Recommended structure**:

| Section | Content |
|---------|---------|
| About Josys | 2-3 sentence product definition |
| Key Facts (table) | Founded, HQ, parent company, customers, integrations, certifications, G2 rating |
| Product Categories | SMP, IGA, ITAM, Device Management |
| Core Capabilities (table) | Feature name + 1-line description for each |
| Target Customers | Enterprise segments, industries, company sizes |
| Awards & Recognition | Media mentions, analyst coverage |
| FAQ (5-8 questions) | "What is Josys?", "How is Josys different?", "What certifications?", etc. |

**Schema**: Organization + FAQPage + SoftwareApplication (JSON-LD)
**Japanese version**: `/jp/brand-facts`
**Effort**: 4-6 hours

---

#### (3) `/compare/josys-vs-[competitor]` — Comparison Pages (5 pages)

**Purpose**: Get cited for "Josys vs [competitor]" and "[competitor] alternative" AI queries.

**Pages to create** (priority order):

| Priority | Page | Rationale |
|----------|------|-----------|
| 1 | `/compare/josys-vs-zylo` | Largest SMP competitor. Highest comparison search volume |
| 2 | `/compare/josys-vs-productiv` | Direct competitor. Enterprise segment overlap |
| 3 | `/compare/josys-vs-bettercloud` | Has most comparison pages (defensive need) |
| 4 | `/compare/josys-vs-zluri` | Fast-growing competitor with aggressive content |
| 5 | `/compare/josys-vs-torii` | Mid-market competitor. Others already compare |

**Page structure** (each):

1. **Opening 50 words**: Answer-first conclusion
2. **Comparison table**: HTML table (not image) — features, pricing, support
3. **Josys strengths**: 3-5 specific differentiators
4. **[Competitor] strengths**: 2-3 points (objectivity)
5. **"Josys is best for..."**: Use-case-based recommendations
6. **FAQ**: 3-5 questions (with FAQPage schema)
7. **Last updated date**: Always visible (content updated within 30 days gets 3.2x citations)

**Effort**: 4-6 hours per page x 5 = 20-30 hours total

---

#### (4) `/faq` — Comprehensive FAQ Page

**Purpose**: Pages with FAQPage schema achieve **2.7x citation rate** vs. non-schema pages. Josys currently has no standalone FAQ.

**Recommended categories**:

- **Product**: What is Josys? Key features? Target customers?
- **Pricing**: Plans? Free trial? How to get a quote?
- **Security**: Certifications? Data protection? Compliance?
- **Implementation**: Timeline? Support? Migration?
- **Integrations**: How many apps? API? Custom integrations?
- **Comparison**: How does Josys differ from alternatives?

**Answer length**: 40-60 words per answer (optimal for AI extraction)
**Schema**: FAQPage schema required
**Japanese version**: `/jp/faq`
**Effort**: 6-8 hours

---

### 2.2 Priority B: Enhance Existing Pages

#### (5) `/case-studies` — Add Structured Data

- Implement Article / CaseStudy schema
- Surface ROI metrics (cost savings, time reduction) in structured data
- Add industry/size/challenge filters to schema

#### (6) `/integrations` — Add Structured Data

- Implement SoftwareApplication + ItemList schema
- Make "350+" machine-readable in JSON schema
- Add category-based software classification to schema

#### (7) `/pricing` — Add FAQ Section

- Add 5-8 pricing FAQs with FAQPage schema
- Target "How much does Josys cost?" queries

---

### 2.3 Priority C: Technical Foundation

#### (8) robots.txt — Allow AI Search Bots

```
User-agent: ChatGPT-User
Allow: /

User-agent: OAI-SearchBot
Allow: /

User-agent: PerplexityBot
Allow: /

User-agent: Claude-Web
Allow: /

User-agent: GoogleOther
Allow: /
```

**Note**: `GPTBot` (training) and `ChatGPT-User` (search/citation) are different bots. Allow the latter for citation visibility.

#### (9) Site-wide Organization Schema

Deploy unified JSON-LD across all pages with:
- Organization type, name, URL, logo
- foundingDate, description
- parentOrganization (Raksul Inc.)
- sameAs links (LinkedIn, G2, Crunchbase, Twitter)
- aggregateRating (4.5/5, 600+ reviews)

#### (10) External Entity Synchronization

AI cross-checks information across sources. Ensure consistency:

| Platform | Priority | Status |
|----------|----------|--------|
| G2 | Critical | Active (4.5 stars, 600+ reviews) |
| LinkedIn | Critical | Verify & sync |
| Crunchbase | High | Verify & sync |
| Wikidata | Medium | Likely not registered (verify) |
| Product Hunt | Medium | Verify |

---

## 3. Execution Roadmap

### Phase 1: Technical Foundation (Week 1-2)

| Task | Effort | Owner |
|------|--------|-------|
| Add AI search bots to robots.txt | 30 min | Engineering |
| Deploy Organization schema site-wide | 2 hours | Engineering |
| Create & deploy llms.txt (EN + JP) | 3 hours | Marketing + Engineering |
| Sync external profiles (G2, LinkedIn, Crunchbase) | 2 hours | Marketing |

### Phase 2: Core Page Creation (Week 3-6)

| Task | Effort | Owner |
|------|--------|-------|
| Build `/brand-facts` (EN + JP) | 8 hours | Marketing + Engineering |
| Build `/faq` (EN + JP) | 8 hours | Marketing + Engineering |
| Create 5 competitor comparison pages | 30 hours | Marketing (content) + Engineering |
| Implement FAQPage schema on all FAQ sections | 4 hours | Engineering |

### Phase 3: Existing Page Enhancement (Week 7-8)

| Task | Effort | Owner |
|------|--------|-------|
| Add Article schema to `/case-studies` | 4 hours | Engineering |
| Add ItemList schema to `/integrations` | 4 hours | Engineering |
| Add FAQ section to `/pricing` | 4 hours | Marketing + Engineering |
| Add "Last updated" dates to all pages | 2 hours | Engineering |

### Phase 4: Measurement (Week 9+ ongoing)

| Task | Effort | Owner |
|------|--------|-------|
| Set up AI referral traffic tracking in GA4 | 2 hours | Marketing |
| Begin weekly AI response monitoring for target queries | 1 hr/week | Marketing |
| Create Wikidata entry | 2 hours | Marketing |

**GA4 regex for detecting AI referral traffic**:
```
^https:\/\/(www\.meta\.ai|www\.perplexity\.ai|chat\.openai\.com|claude\.ai|chatgpt\.com|copilot\.microsoft\.com|gemini\.google\.com)
```

---

## 4. Expected Impact

| Metric | Evidence |
|--------|----------|
| FAQPage schema pages AI citation rate | **2.7x** vs. non-schema (Relixir study) |
| Pages with comparison tables | **+47%** higher AI citation |
| Content updated within 30 days | **3.2x** citation rate |
| Sites with structured data | **2-3x** AI citation rate |
| LLM-driven conversion rate | **6x** vs. Google Organic (Webflow) |

### Note

LLMO/AEO effectiveness measurement is still an emerging field industry-wide. We recommend starting weekly monitoring of AI responses for target queries from day one to build Josys's own data set.

---

## 5. External Media + Owned Media Synergy

```
External Media (note, ITmedia, etc.)     Owned Site (josys.com)
┌──────────────────────────────┐    ┌──────────────────────────────┐
│                              │    │                              │
│  Role: "Josys is great"     │───→│  Role: "That's correct"      │
│  (recommend)                 │    │  (validate)                  │
│                              │    │                              │
│  - Comparison articles       │    │  - /brand-facts              │
│  - Case study interviews     │    │  - /compare/josys-vs-*       │
│  - Industry trend pieces     │    │  - /case-studies             │
│                              │    │  - /integrations             │
│                              │    │  - /faq                      │
│                              │    │  - /pricing                  │
│                              │    │  - llms.txt                  │
└──────────────────────────────┘    └──────────────────────────────┘
               ↓                                  ↓
    AI cross-checks multiple sources → info matches → recommendation probability UP
```

---

*For questions or discussion, please reach out via Slack.*
