"""
site_crawler.py — Lightweight BFS Site Crawler for WordPress Technical SEO Audit
Usage: python site_crawler.py https://example.com --max-pages 100 --output ./reports/ --delay 0.5
"""

import json
import re
import time
import argparse
import sys
from collections import deque, defaultdict
from datetime import datetime
from urllib.parse import urljoin, urlparse, urlunparse, urlencode, parse_qs
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup


USER_AGENT = "WPTechSEOAudit/1.0 (Technical SEO Crawler)"

# WordPress-specific paths to exclude from crawling
WP_EXCLUDED_PATHS = {
    "/wp-admin/",
    "/wp-login.php",
    "/wp-content/",
    "/wp-json/",
    "/feed/",
    "/comments/feed/",
    "/?feed=",
    "/xmlrpc.php",
    "/wp-cron.php",
}

# Non-HTML extensions to skip
NON_HTML_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg", ".ico",
    ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
    ".zip", ".tar", ".gz", ".mp4", ".mp3", ".wav", ".avi",
    ".css", ".js", ".json", ".xml", ".txt", ".rss", ".atom",
    ".woff", ".woff2", ".ttf", ".eot",
}


def normalize_url(url: str, strip_query: bool = True) -> str:
    """Normalize URL: remove fragments, optionally strip query params, normalize trailing slash."""
    parsed = urlparse(url)
    # Remove fragment
    parsed = parsed._replace(fragment="")
    # Strip query parameters for deduplication
    if strip_query:
        parsed = parsed._replace(query="")
    # Normalize path: avoid double trailing slashes but keep root slash
    path = parsed.path.rstrip("/") or "/"
    parsed = parsed._replace(path=path)
    return urlunparse(parsed)


def is_html_content_type(content_type: str) -> bool:
    """Check if the content-type indicates HTML."""
    if not content_type:
        return False
    return "text/html" in content_type.lower()


def has_excluded_extension(url: str) -> bool:
    """Check if URL path ends with a non-HTML extension."""
    path = urlparse(url).path.lower()
    for ext in NON_HTML_EXTENSIONS:
        if path.endswith(ext):
            return True
    return False


def is_wp_excluded(url: str) -> bool:
    """Check if URL matches WordPress admin/system paths to exclude."""
    parsed = urlparse(url)
    path = parsed.path
    for excluded in WP_EXCLUDED_PATHS:
        if path.startswith(excluded) or path == excluded.rstrip("/"):
            return True
    # Also check query string for feed
    if "feed=" in parsed.query:
        return True
    return False


def extract_visible_text(soup: BeautifulSoup) -> str:
    """Extract visible text from BeautifulSoup, removing scripts/styles."""
    for tag in soup(["script", "style", "noscript", "head"]):
        tag.decompose()
    return soup.get_text(separator=" ", strip=True)


def count_content_length(text: str) -> int:
    """
    Count content length. For Japanese text, count characters.
    For English text, count words. Uses character count as a unified metric
    suitable for Japanese content.
    """
    # Use len() for character-based counting (handles Japanese properly)
    # Also compute a rough word estimate for ASCII-dominant text
    stripped = text.strip()
    return len(stripped)


class SiteCrawler:
    def __init__(
        self,
        base_url: str,
        max_pages: int = 100,
        crawl_delay: float = 0.5,
        respect_robots: bool = True,
        strip_query: bool = True,
    ):
        self.base_url = base_url.rstrip("/")
        self.max_pages = max_pages
        self.crawl_delay = crawl_delay
        self.respect_robots = respect_robots
        self.strip_query = strip_query

        parsed = urlparse(self.base_url)
        self.base_domain = parsed.netloc
        self.base_scheme = parsed.scheme

        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT})

        self.robot_parser: RobotFileParser = RobotFileParser()
        self._robots_loaded = False

        # State
        self.visited: set = set()
        self.pages: list = []
        # Map of url -> list of urls that link to it (for link graph)
        self.incoming_links: dict = defaultdict(set)

    # ------------------------------------------------------------------
    # robots.txt
    # ------------------------------------------------------------------

    def _load_robots(self):
        robots_url = f"{self.base_scheme}://{self.base_domain}/robots.txt"
        try:
            self.robot_parser.set_url(robots_url)
            self.robot_parser.read()
        except Exception:
            # If robots.txt can't be fetched, assume allowed
            pass
        self._robots_loaded = True

    def _is_allowed_by_robots(self, url: str) -> bool:
        if not self.respect_robots:
            return True
        if not self._robots_loaded:
            self._load_robots()
        return self.robot_parser.can_fetch(USER_AGENT, url)

    # ------------------------------------------------------------------
    # URL helpers
    # ------------------------------------------------------------------

    def _is_same_domain(self, url: str) -> bool:
        parsed = urlparse(url)
        return parsed.netloc == self.base_domain

    def _should_crawl(self, url: str) -> bool:
        """Determine whether a URL should be crawled."""
        if not url:
            return False
        if not self._is_same_domain(url):
            return False
        if has_excluded_extension(url):
            return False
        if is_wp_excluded(url):
            return False
        if not self._is_allowed_by_robots(url):
            return False
        return True

    def _extract_links(self, soup: BeautifulSoup, current_url: str) -> tuple:
        """Return (internal_links, external_links) as lists of absolute URLs."""
        internal = []
        external = []
        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            if not href or href.startswith("#") or href.startswith("mailto:") or href.startswith("tel:"):
                continue
            abs_url = urljoin(current_url, href)
            # Strip fragment for classification
            abs_url_no_frag = abs_url.split("#")[0]
            if self._is_same_domain(abs_url_no_frag):
                internal.append(abs_url_no_frag)
            else:
                external.append(abs_url_no_frag)
        return internal, external

    # ------------------------------------------------------------------
    # Main crawl
    # ------------------------------------------------------------------

    def crawl(self) -> dict:
        """BFS crawl starting from base_url. Returns result dict."""
        start_norm = normalize_url(self.base_url, self.strip_query)
        queue = deque([start_norm])
        self.visited = set()
        self.pages = []
        self.incoming_links = defaultdict(set)
        # Track depth for each URL
        depth_map = {start_norm: 0}

        while queue and len(self.pages) < self.max_pages:
            url = queue.popleft()

            if url in self.visited:
                continue
            if not self._should_crawl(url):
                self.visited.add(url)
                continue

            self.visited.add(url)

            # Crawl delay
            if self.pages:  # skip delay for first page
                time.sleep(self.crawl_delay)

            page_data = self._fetch_and_analyze(url)
            if page_data is None:
                continue

            page_data["depth"] = depth_map.get(url, 0)
            self.pages.append(page_data)

            # Enqueue internal links
            for link in page_data.get("internal_links", []):
                norm_link = normalize_url(link, self.strip_query)
                # Record incoming link
                self.incoming_links[norm_link].add(url)
                if norm_link not in self.visited and norm_link not in [normalize_url(q, self.strip_query) for q in queue]:
                    if self._should_crawl(norm_link):
                        queue.append(norm_link)
                        if norm_link not in depth_map:
                            depth_map[norm_link] = depth_map.get(url, 0) + 1

        issues = self.detect_issues(self.pages)
        link_graph = self.build_link_graph()
        summary = self._build_summary(issues)

        return {
            "crawled_at": datetime.now().isoformat(),
            "base_url": self.base_url,
            "pages": self.pages,
            "link_graph": link_graph,
            "issues": issues,
            "summary": summary,
        }

    def _fetch_and_analyze(self, url: str) -> dict | None:
        """Fetch a URL and return analyzed page data, or None on fatal error."""
        start = time.time()
        try:
            response = self.session.get(url, timeout=30, allow_redirects=True)
            elapsed_ms = int((time.time() - start) * 1000)
        except requests.exceptions.Timeout:
            return {
                "url": url,
                "status_code": None,
                "error": "timeout",
                "response_time_ms": 30000,
            }
        except requests.exceptions.RequestException as e:
            return {
                "url": url,
                "status_code": None,
                "error": str(e),
                "response_time_ms": int((time.time() - start) * 1000),
            }

        # Handle redirects: record final URL
        final_url = response.url
        redirect_chain = [r.url for r in response.history] if response.history else []

        # Check content type
        content_type = response.headers.get("Content-Type", "")
        if not is_html_content_type(content_type) and response.status_code == 200:
            return None  # Skip non-HTML

        if response.status_code != 200 or not is_html_content_type(content_type):
            return {
                "url": url,
                "final_url": final_url,
                "status_code": response.status_code,
                "redirect_chain": redirect_chain,
                "response_time_ms": elapsed_ms,
                "content_type": content_type,
                "internal_links": [],
                "external_links": [],
                "images": [],
                "json_ld": [],
                "og_tags": {},
                "hreflang": [],
                "response_headers": self._extract_headers(response),
            }

        # Detect encoding
        try:
            html = response.content.decode(response.apparent_encoding or "utf-8", errors="replace")
        except Exception:
            html = response.text

        page_data = self.analyze_page(url, html, response)
        page_data["final_url"] = final_url
        page_data["redirect_chain"] = redirect_chain
        page_data["response_time_ms"] = elapsed_ms
        page_data["status_code"] = response.status_code

        return page_data

    # ------------------------------------------------------------------
    # Page analysis
    # ------------------------------------------------------------------

    def analyze_page(self, url: str, html: str, response) -> dict:
        """Extract SEO signals from a single page."""
        soup = BeautifulSoup(html, "lxml")

        # Title
        title_tag = soup.find("title")
        title = title_tag.get_text(strip=True) if title_tag else ""

        # Meta description
        meta_desc_tag = soup.find("meta", attrs={"name": re.compile(r"^description$", re.I)})
        meta_description = meta_desc_tag.get("content", "").strip() if meta_desc_tag else ""

        # Canonical
        canonical_tag = soup.find("link", rel=lambda r: r and "canonical" in r)
        canonical = canonical_tag.get("href", "").strip() if canonical_tag else ""

        # Headings
        h1_tags = soup.find_all("h1")
        h1 = [h.get_text(strip=True) for h in h1_tags]
        h2_tags = soup.find_all("h2")
        h2 = [h.get_text(strip=True) for h in h2_tags]
        h3_count = len(soup.find_all("h3"))
        h4_count = len(soup.find_all("h4"))
        h5_count = len(soup.find_all("h5"))
        h6_count = len(soup.find_all("h6"))

        # Links
        internal_links, external_links = self._extract_links(soup, url)

        # Images
        images = []
        for img in soup.find_all("img"):
            src = img.get("src", "").strip()
            alt = img.get("alt", "")
            images.append({
                "src": urljoin(url, src) if src else "",
                "alt": alt,
                "has_alt": bool(alt.strip()),
            })

        # JSON-LD
        json_ld = []
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(script.string or "")
                json_ld.append(data)
            except (json.JSONDecodeError, TypeError):
                pass

        # OG tags
        og_tags = {}
        for meta in soup.find_all("meta", property=True):
            prop = meta.get("property", "")
            if prop.startswith("og:"):
                og_tags[prop] = meta.get("content", "").strip()

        # Robots meta
        robots_meta_tag = soup.find("meta", attrs={"name": re.compile(r"^robots$", re.I)})
        robots_meta = robots_meta_tag.get("content", "").strip() if robots_meta_tag else ""

        # Word / character count (visible text)
        visible_text = extract_visible_text(BeautifulSoup(html, "lxml"))
        word_count = count_content_length(visible_text)

        # Hreflang
        hreflang = []
        for link in soup.find_all("link", rel=lambda r: r and "alternate" in r):
            hl = link.get("hreflang", "")
            href = link.get("href", "")
            if hl:
                hreflang.append({"hreflang": hl, "href": href})

        # Response headers (selected)
        headers = self._extract_headers(response)

        return {
            "url": url,
            "title": title,
            "meta_description": meta_description,
            "canonical": canonical,
            "h1": h1,
            "h2": h2,
            "h3_count": h3_count,
            "h4_count": h4_count,
            "h5_count": h5_count,
            "h6_count": h6_count,
            "internal_links": internal_links,
            "external_links": external_links,
            "images": images,
            "json_ld": json_ld,
            "og_tags": og_tags,
            "robots_meta": robots_meta,
            "word_count": word_count,
            "hreflang": hreflang,
            "response_headers": headers,
        }

    def _extract_headers(self, response) -> dict:
        """Extract selected response headers."""
        header_keys = ["content-type", "x-robots-tag", "cache-control", "last-modified", "etag"]
        return {k: response.headers.get(k, "") for k in header_keys}

    # ------------------------------------------------------------------
    # Issue detection
    # ------------------------------------------------------------------

    def detect_issues(self, pages: list) -> list:
        """Analyze collected pages and return list of issue dicts."""
        issues = []

        # Build lookup structures
        title_map: dict = defaultdict(list)   # title -> [url]
        url_set = {p["url"] for p in pages}
        all_linked_urls: set = set()

        for page in pages:
            t = page.get("title", "")
            if t:
                title_map[t].append(page["url"])
            for link in page.get("internal_links", []):
                all_linked_urls.add(normalize_url(link, self.strip_query))

        for page in pages:
            url = page.get("url", "")
            title = page.get("title", "")
            meta_desc = page.get("meta_description", "")
            canonical = page.get("canonical", "")
            h1 = page.get("h1", [])
            robots_meta = page.get("robots_meta", "")
            word_count = page.get("word_count", 0)
            images = page.get("images", [])
            status = page.get("status_code")
            redirect_chain = page.get("redirect_chain", [])
            final_url = page.get("final_url", url)

            # --- META issues ---

            # Missing title
            if not title:
                issues.append(self._issue("META", "HIGH", url, "タイトルが未設定", "", "ページにtitleタグを追加してください"))
            else:
                # Title too long (>60 chars)
                if len(title) > 60:
                    issues.append(self._issue("META", "MEDIUM", url, "タイトルが長すぎる (60文字超)", title, "タイトルを60文字以内に収めてください"))
                # Title too short (<10 chars)
                if len(title) < 10:
                    issues.append(self._issue("META", "LOW", url, "タイトルが短すぎる (10文字未満)", title, "タイトルに適切なキーワードを含め、10文字以上にしてください"))

            # Missing meta description
            if not meta_desc:
                issues.append(self._issue("META", "MEDIUM", url, "メタディスクリプションが未設定", "", "120〜160文字のメタディスクリプションを設定してください"))
            else:
                if len(meta_desc) > 160:
                    issues.append(self._issue("META", "LOW", url, "メタディスクリプションが長すぎる (160文字超)", meta_desc[:50] + "...", "メタディスクリプションを160文字以内に収めてください"))
                if len(meta_desc) < 50:
                    issues.append(self._issue("META", "LOW", url, "メタディスクリプションが短すぎる (50文字未満)", meta_desc, "120〜160文字のメタディスクリプションを設定してください"))

            # Missing canonical
            if not canonical:
                issues.append(self._issue("META", "MEDIUM", url, "canonicalタグが未設定", "", "各ページにself-referencing canonicalタグを設定してください"))
            else:
                # Canonical points to different URL (non-self-referencing)
                norm_url = normalize_url(url, self.strip_query)
                norm_canonical = normalize_url(canonical, self.strip_query)
                if norm_url != norm_canonical and normalize_url(canonical, False) != normalize_url(url, False):
                    issues.append(self._issue(
                        "META", "HIGH", url,
                        "canonicalが別URLを指している",
                        canonical,
                        "canonicalが意図的でない場合、自己参照canonicalに修正してください"
                    ))

            # --- STRC issues ---

            # Missing H1
            if not h1:
                issues.append(self._issue("STRC", "HIGH", url, "H1が未設定", "", "ページに1つのH1タグを追加してください"))
            # Multiple H1s
            elif len(h1) > 1:
                issues.append(self._issue("STRC", "MEDIUM", url, f"H1が複数存在する ({len(h1)}個)", "; ".join(h1[:3]), "H1はページ内に1つだけ設定してください"))

            # Heading level skip (H1 exists but H3 before H2)
            h2_count = len(page.get("h2", []))
            h3_count = page.get("h3_count", 0)
            if h1 and h3_count > 0 and h2_count == 0:
                issues.append(self._issue("STRC", "LOW", url, "見出し階層のスキップ (H1→H3, H2なし)", f"H2: {h2_count}, H3: {h3_count}", "見出し階層はH1→H2→H3の順番に従ってください"))

            # --- CONT issues ---

            # Thin content
            if word_count < 200:
                issues.append(self._issue("CONT", "MEDIUM", url, f"コンテンツが薄い (文字数: {word_count})", str(word_count), "ページの文字数を増やし、有益な情報を追加してください"))

            # Images missing alt text
            if images:
                missing_alt = [img for img in images if not img.get("has_alt")]
                ratio = len(missing_alt) / len(images)
                if ratio > 0.1:
                    issues.append(self._issue(
                        "CONT", "MEDIUM", url,
                        f"alt属性なし画像が多い ({len(missing_alt)}/{len(images)}枚, {int(ratio*100)}%)",
                        f"{len(missing_alt)}枚",
                        "全ての画像にalt属性を設定してください"
                    ))

            # --- RDIR issues ---

            # 404
            if status == 404:
                issues.append(self._issue("RDIR", "HIGH", url, "404エラー", str(status), "ページを復元するか、適切なURLへ301リダイレクトを設定してください"))

            # Other 4xx/5xx
            elif status and status >= 400:
                severity = "CRITICAL" if status >= 500 else "HIGH"
                issues.append(self._issue("RDIR", severity, url, f"HTTPエラー {status}", str(status), "サーバーエラーを調査し、修正してください"))

            # Redirect chain (more than 1 redirect = chain)
            if len(redirect_chain) > 1:
                issues.append(self._issue(
                    "RDIR", "MEDIUM", url,
                    f"リダイレクトチェーンが存在する ({len(redirect_chain)}段階)",
                    " → ".join(redirect_chain[:3]) + (" → ..." if len(redirect_chain) > 3 else ""),
                    "リダイレクトは1段階に短縮し、最終URLへ直接リダイレクトしてください"
                ))

            # Redirect loop detection (final_url == url after redirect chain implies loop was broken by requests)
            if redirect_chain and final_url in redirect_chain[:-1]:
                issues.append(self._issue("RDIR", "CRITICAL", url, "リダイレクトループを検出", " → ".join(redirect_chain[:5]), "リダイレクトループを解消してください"))

            # --- INDX issues ---

            # noindex in robots meta
            if robots_meta and "noindex" in robots_meta.lower():
                issues.append(self._issue("INDX", "HIGH", url, "noindexが設定されている", robots_meta, "インデックスさせるページの場合、noindexを削除してください"))

            # x-robots-tag noindex
            x_robots = page.get("response_headers", {}).get("x-robots-tag", "")
            if x_robots and "noindex" in x_robots.lower():
                issues.append(self._issue("INDX", "HIGH", url, "X-Robots-Tag: noindexが設定されている", x_robots, "意図しない場合、HTTPヘッダーのnoindex指定を削除してください"))

        # --- Duplicate titles (cross-page) ---
        for title, urls in title_map.items():
            if len(urls) > 1:
                for dup_url in urls:
                    issues.append(self._issue(
                        "CONT", "HIGH", dup_url,
                        f"タイトルが重複している ({len(urls)}ページで同一)",
                        title,
                        "各ページに固有のタイトルを設定してください"
                    ))

        # --- Orphan pages ---
        all_page_urls = {normalize_url(p["url"], self.strip_query) for p in pages}
        start_norm = normalize_url(self.base_url, self.strip_query)
        for page in pages:
            norm = normalize_url(page["url"], self.strip_query)
            if norm == start_norm:
                continue  # homepage is never orphan
            incoming = self.incoming_links.get(norm, set())
            if not incoming:
                issues.append(self._issue(
                    "STRC", "MEDIUM", page["url"],
                    "孤立ページ (内部リンクが存在しない)",
                    "0 internal links",
                    "サイト内の関連ページから内部リンクを追加してください"
                ))

        return issues

    @staticmethod
    def _issue(code: str, severity: str, url: str, issue: str, current: str, recommendation: str) -> dict:
        return {
            "code": code,
            "severity": severity,
            "url": url,
            "issue": issue,
            "current": current,
            "recommendation": recommendation,
        }

    # ------------------------------------------------------------------
    # Link graph
    # ------------------------------------------------------------------

    def build_link_graph(self) -> dict:
        """Build link graph metrics after crawl."""
        if not self.pages:
            return {}

        start_norm = normalize_url(self.base_url, self.strip_query)

        # Count incoming links per page
        incoming_count: dict = defaultdict(int)
        for page in self.pages:
            for link in page.get("internal_links", []):
                norm = normalize_url(link, self.strip_query)
                incoming_count[norm] += 1

        # Orphan pages: 0 incoming links (excluding homepage)
        orphan_pages = []
        for page in self.pages:
            norm = normalize_url(page["url"], self.strip_query)
            if norm == start_norm:
                continue
            if incoming_count.get(norm, 0) == 0:
                orphan_pages.append(page["url"])

        # Most linked pages (top 10)
        sorted_by_links = sorted(
            [(url, cnt) for url, cnt in incoming_count.items()],
            key=lambda x: x[1],
            reverse=True
        )
        most_linked = [{"url": url, "incoming_links": cnt} for url, cnt in sorted_by_links[:10]]

        # Depth distribution
        depth_distribution: dict = defaultdict(int)
        max_depth = 0
        for page in self.pages:
            d = page.get("depth", 0)
            depth_distribution[d] += 1
            if d > max_depth:
                max_depth = d

        # Average internal links per page
        total_internal = sum(len(p.get("internal_links", [])) for p in self.pages)
        avg_internal = round(total_internal / len(self.pages), 2) if self.pages else 0.0

        return {
            "orphan_pages": orphan_pages,
            "most_linked": most_linked,
            "max_depth": max_depth,
            "depth_distribution": {str(k): v for k, v in sorted(depth_distribution.items())},
            "avg_internal_links_per_page": avg_internal,
        }

    # ------------------------------------------------------------------
    # Sampling strategy
    # ------------------------------------------------------------------

    def get_sampling_strategy(self, total_urls: list, config: dict) -> list:
        """
        Stratified sampling for large sites.
        config keys: sampling_threshold, sample_size_percent, sample_min_pages, sample_max_pages
        """
        import random

        threshold = config.get("sampling_threshold", 500)
        size_pct = config.get("sample_size_percent", 20)
        min_pages = config.get("sample_min_pages", 50)
        max_pages = config.get("sample_max_pages", 300)

        if len(total_urls) < threshold:
            return total_urls

        target = max(min_pages, min(max_pages, int(len(total_urls) * size_pct / 100)))

        base = urlparse(self.base_url)

        # Strata
        homepage = [u for u in total_urls if urlparse(u).path in ("", "/", f"/{base.netloc}")]
        category_pages = [u for u in total_urls if re.search(r"/(category|tag|archive|カテゴリ|タグ)/", u)]
        random_sample = random.sample(total_urls, min(target // 2, len(total_urls)))

        # Combine strata without duplicates
        selected = list(dict.fromkeys(homepage + category_pages + random_sample))
        return selected[:target]

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------

    def _build_summary(self, issues: list) -> dict:
        total_pages = len(self.pages)
        total_internal = sum(len(p.get("internal_links", [])) for p in self.pages)
        total_external = sum(len(p.get("external_links", [])) for p in self.pages)

        response_times = [p.get("response_time_ms", 0) for p in self.pages if p.get("response_time_ms") is not None]
        avg_rt = round(sum(response_times) / len(response_times), 1) if response_times else 0.0

        # Pages with issues
        urls_with_issues = {iss["url"] for iss in issues}
        pages_with_issues = len(urls_with_issues)

        # Issue count by category
        by_category: dict = defaultdict(int)
        by_severity: dict = defaultdict(int)
        for iss in issues:
            by_category[iss["code"]] += 1
            by_severity[iss["severity"]] += 1

        return {
            "total_pages_crawled": total_pages,
            "total_internal_links": total_internal,
            "total_external_links": total_external,
            "avg_response_time_ms": avg_rt,
            "pages_with_issues_count": pages_with_issues,
            "issue_count_by_category": dict(by_category),
            "issue_count_by_severity": dict(by_severity),
        }


# ------------------------------------------------------------------
# CLI entry point
# ------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="WordPress Technical SEO Site Crawler",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Example: python site_crawler.py https://example.com --max-pages 100 --output ./reports/ --delay 0.5"
    )
    parser.add_argument("url", help="Base URL to crawl (e.g. https://example.com)")
    parser.add_argument("--max-pages", type=int, default=100, help="Maximum number of pages to crawl (default: 100)")
    parser.add_argument("--output", default="./reports/", help="Output directory for JSON report (default: ./reports/)")
    parser.add_argument("--delay", type=float, default=0.5, help="Crawl delay in seconds between requests (default: 0.5)")
    parser.add_argument("--no-robots", action="store_true", help="Ignore robots.txt restrictions")
    parser.add_argument("--keep-query", action="store_true", help="Keep query parameters (don't strip for deduplication)")
    args = parser.parse_args()

    base_url = args.url
    if not base_url.startswith(("http://", "https://")):
        base_url = "https://" + base_url

    print(f"[SiteCrawler] Starting crawl: {base_url}")
    print(f"  max_pages={args.max_pages}, delay={args.delay}s, respect_robots={not args.no_robots}")

    crawler = SiteCrawler(
        base_url=base_url,
        max_pages=args.max_pages,
        crawl_delay=args.delay,
        respect_robots=not args.no_robots,
        strip_query=not args.keep_query,
    )

    result = crawler.crawl()

    # Prepare output path
    import os
    domain = urlparse(base_url).netloc.replace(".", "_").replace(":", "_")
    date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{domain}_crawl_{date_str}.json"

    output_dir = args.output
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, filename)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    summary = result.get("summary", {})
    print(f"\n[SiteCrawler] Crawl complete.")
    print(f"  Pages crawled   : {summary.get('total_pages_crawled', 0)}")
    print(f"  Issues found    : {len(result.get('issues', []))}")
    print(f"  Pages w/ issues : {summary.get('pages_with_issues_count', 0)}")
    print(f"  Avg resp time   : {summary.get('avg_response_time_ms', 0)} ms")
    print(f"  Output          : {output_path}")

    by_sev = summary.get("issue_count_by_severity", {})
    if by_sev:
        print(f"\n  Issues by severity:")
        for sev in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
            count = by_sev.get(sev, 0)
            if count:
                print(f"    {sev:<10}: {count}")

    by_cat = summary.get("issue_count_by_category", {})
    if by_cat:
        print(f"\n  Issues by category:")
        for cat, count in sorted(by_cat.items()):
            print(f"    {cat:<10}: {count}")


if __name__ == "__main__":
    main()
