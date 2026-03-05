"""
WordPress Reader Module

Read-only WordPress REST API client for wp-techseo-audit.
Supports multi-client configuration via config/clients.json.
"""

import json
import os
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional

import requests
from dotenv import load_dotenv

# Load .env from ../config/.env relative to this script
_CONFIG_DIR = Path(__file__).parent.parent / "config"
_ENV_PATH = _CONFIG_DIR / ".env"
if _ENV_PATH.exists():
    load_dotenv(_ENV_PATH)


def _load_clients_config() -> dict:
    """Load clients.json from config directory."""
    config_path = _CONFIG_DIR / "clients.json"
    if not config_path.exists():
        raise FileNotFoundError(f"clients.json not found at {config_path}")
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


class WordPressReader:
    """Read-only WordPress REST API client with multi-client support."""

    def __init__(self, client_id: str):
        """
        Initialize the reader for a specific client.

        Args:
            client_id: Key in clients.json (e.g. 'naimono')

        Raises:
            ValueError: If client_id is not found or password env var is not set.
        """
        config = _load_clients_config()

        clients = config.get("clients", {})
        if client_id not in clients:
            available = ", ".join(clients.keys()) if clients else "(none)"
            raise ValueError(
                f"Client '{client_id}' not found in clients.json. "
                f"Available clients: {available}"
            )

        client = clients[client_id]
        self.client_id = client_id
        self.client_config = client

        url: str = client.get("wordpress_url", "").rstrip("/")
        username: str = client.get("wordpress_username", "")
        password_env: str = client.get("wordpress_app_password_env", "")

        if not url:
            raise ValueError(f"Client '{client_id}' is missing 'wordpress_url'.")
        if not username:
            raise ValueError(f"Client '{client_id}' is missing 'wordpress_username'.")
        if not password_env:
            raise ValueError(
                f"Client '{client_id}' is missing 'wordpress_app_password_env'."
            )

        app_password = os.environ.get(password_env)
        if not app_password:
            raise ValueError(
                f"Environment variable '{password_env}' is not set. "
                f"Add it to {_ENV_PATH} or set it in the shell environment."
            )

        self.url = url
        self.api_base = f"{url}/wp-json/wp/v2"
        self.sitemap_url: Optional[str] = client.get("sitemap_url")

        self.session = requests.Session()
        self.session.auth = (username, app_password)
        self.session.headers.update(
            {
                "Content-Type": "application/json",
                "User-Agent": "WPTechSEOAudit/1.0",
            }
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get(self, url: str, params: Optional[dict] = None, timeout: int = 30) -> requests.Response:
        """Perform a GET request and raise on HTTP errors."""
        try:
            response = self.session.get(url, params=params, timeout=timeout)
            response.raise_for_status()
            return response
        except requests.exceptions.Timeout:
            raise RuntimeError(f"Request timed out after {timeout}s: {url}")
        except requests.exceptions.HTTPError as e:
            status = e.response.status_code if e.response is not None else "unknown"
            body = e.response.text[:500] if e.response is not None else ""
            raise RuntimeError(
                f"HTTP {status} error for {url}: {body}"
            ) from e

    def _get_paginated(
        self,
        endpoint: str,
        params: Optional[dict] = None,
        per_page: int = 100,
    ) -> list:
        """
        Fetch all pages from a paginated WP REST API endpoint.
        Checks X-WP-TotalPages header to iterate all pages.
        """
        base_params = {"per_page": per_page, "page": 1}
        if params:
            base_params.update(params)

        results = []
        page = 1

        while True:
            base_params["page"] = page
            response = self._get(endpoint, params=base_params)
            data = response.json()

            if not data:
                break

            results.extend(data)

            total_pages = int(response.headers.get("X-WP-TotalPages", 1))
            if page >= total_pages:
                break
            page += 1

        return results

    # ------------------------------------------------------------------
    # Public methods
    # ------------------------------------------------------------------

    def get_site_info(self) -> dict:
        """
        Fetch basic site information from the WP REST API root endpoint.

        Returns:
            dict with keys: name, description, url, timezone, gmt_offset, wp_version
        """
        response = self._get(f"{self.url}/wp-json")
        data = response.json()

        return {
            "name": data.get("name", ""),
            "description": data.get("description", ""),
            "url": data.get("url", ""),
            "home": data.get("home", ""),
            "timezone": data.get("timezone_string", ""),
            "gmt_offset": data.get("gmt_offset", 0),
            "wp_version": data.get("generator", ""),
            "namespaces": data.get("namespaces", []),
        }

    def get_all_posts(
        self,
        per_page: int = 100,
        post_type: str = "posts",
        status: str = "publish",
    ) -> list:
        """
        Fetch all published posts (or custom post type entries) via pagination.

        Args:
            per_page: Number of items per API request (max 100).
            post_type: WordPress REST API endpoint name (e.g. 'posts', 'campus').
            status: Post status to filter by (default 'publish').

        Returns:
            List of dicts with: id, title, slug, link, date, modified,
            excerpt, categories, tags.
        """
        endpoint = f"{self.api_base}/{post_type}"
        raw_items = self._get_paginated(
            endpoint,
            params={"status": status},
            per_page=per_page,
        )

        posts = []
        for item in raw_items:
            posts.append(
                {
                    "id": item.get("id"),
                    "title": item.get("title", {}).get("rendered", ""),
                    "slug": item.get("slug", ""),
                    "link": item.get("link", ""),
                    "date": item.get("date", ""),
                    "modified": item.get("modified", ""),
                    "excerpt": item.get("excerpt", {}).get("rendered", ""),
                    "categories": item.get("categories", []),
                    "tags": item.get("tags", []),
                }
            )
        return posts

    def get_pages(self, per_page: int = 100, status: str = "publish") -> list:
        """
        Fetch all published pages via pagination.

        Args:
            per_page: Number of items per API request (max 100).
            status: Post status to filter by (default 'publish').

        Returns:
            List of dicts with: id, title, slug, link, date, modified, excerpt.
        """
        endpoint = f"{self.api_base}/pages"
        raw_items = self._get_paginated(
            endpoint,
            params={"status": status},
            per_page=per_page,
        )

        pages = []
        for item in raw_items:
            pages.append(
                {
                    "id": item.get("id"),
                    "title": item.get("title", {}).get("rendered", ""),
                    "slug": item.get("slug", ""),
                    "link": item.get("link", ""),
                    "date": item.get("date", ""),
                    "modified": item.get("modified", ""),
                    "excerpt": item.get("excerpt", {}).get("rendered", ""),
                    "parent": item.get("parent", 0),
                    "menu_order": item.get("menu_order", 0),
                }
            )
        return pages

    def get_post_meta(self, post_id: int, post_type: str = "posts") -> dict:
        """
        Fetch full data for a single post including Yoast SEO head JSON.

        Args:
            post_id: WordPress post ID.
            post_type: REST API endpoint name (default 'posts').

        Returns:
            Dict with full post data. Includes yoast_head_json if available.
        """
        endpoint = f"{self.api_base}/{post_type}/{post_id}"
        response = self._get(endpoint, params={"context": "edit"})
        data = response.json()

        result = {
            "id": data.get("id"),
            "title": data.get("title", {}).get("rendered", ""),
            "slug": data.get("slug", ""),
            "link": data.get("link", ""),
            "date": data.get("date", ""),
            "modified": data.get("modified", ""),
            "status": data.get("status", ""),
            "excerpt": data.get("excerpt", {}).get("rendered", ""),
            "content": data.get("content", {}).get("rendered", ""),
            "categories": data.get("categories", []),
            "tags": data.get("tags", []),
            "featured_media": data.get("featured_media", 0),
            "meta": data.get("meta", {}),
        }

        # Include Yoast head JSON if present
        if "yoast_head_json" in data:
            result["yoast_head_json"] = data["yoast_head_json"]

        return result

    def get_sitemap_urls(self) -> list[str]:
        """
        Fetch and parse the sitemap XML, returning all <loc> URLs.
        Supports sitemap index files (recursively fetches child sitemaps).

        Returns:
            Sorted list of unique page URLs found in the sitemap(s).

        Raises:
            ValueError: If no sitemap_url is configured for this client.
            RuntimeError: If the sitemap cannot be fetched or parsed.
        """
        if not self.sitemap_url:
            raise ValueError(
                f"No sitemap_url configured for client '{self.client_id}'."
            )

        def _fetch_and_parse(url: str) -> list[str]:
            try:
                response = requests.get(
                    url,
                    timeout=30,
                    headers={"User-Agent": "WPTechSEOAudit/1.0"},
                )
                response.raise_for_status()
            except requests.exceptions.RequestException as e:
                raise RuntimeError(f"Failed to fetch sitemap at {url}: {e}") from e

            try:
                root = ET.fromstring(response.content)
            except ET.ParseError as e:
                raise RuntimeError(
                    f"Failed to parse sitemap XML at {url}: {e}"
                ) from e

            # Detect namespace
            tag = root.tag
            ns = ""
            if tag.startswith("{"):
                ns = tag[: tag.index("}") + 1]

            # Sitemap index: contains <sitemap> elements
            sitemap_tags = root.findall(f"{ns}sitemap")
            if sitemap_tags:
                all_urls: list[str] = []
                for sitemap_el in sitemap_tags:
                    loc_el = sitemap_el.find(f"{ns}loc")
                    if loc_el is not None and loc_el.text:
                        child_urls = _fetch_and_parse(loc_el.text.strip())
                        all_urls.extend(child_urls)
                return all_urls

            # Regular sitemap: contains <url> elements
            url_tags = root.findall(f"{ns}url")
            urls: list[str] = []
            for url_el in url_tags:
                loc_el = url_el.find(f"{ns}loc")
                if loc_el is not None and loc_el.text:
                    urls.append(loc_el.text.strip())
            return urls

        all_urls = _fetch_and_parse(self.sitemap_url)
        # Deduplicate while preserving order
        seen: set[str] = set()
        unique_urls: list[str] = []
        for u in all_urls:
            if u not in seen:
                seen.add(u)
                unique_urls.append(u)
        return unique_urls

    def get_redirects(self) -> list[dict]:
        """
        Attempt to retrieve redirects from common WordPress redirect plugins.

        Tries:
        1. Redirection plugin REST API (/wp-json/redirection/v1/redirect)
        2. Yoast SEO redirects (/wp-json/yoast/v1/redirects)

        Returns:
            List of dicts with keys: source, target, type (HTTP status code).
            Returns an empty list if no redirect plugin is detected.
        """
        redirects: list[dict] = []

        # --- Attempt 1: Redirection plugin ---
        try:
            endpoint = f"{self.url}/wp-json/redirection/v1/redirect"
            response = self._get(endpoint, params={"per_page": 1000, "page": 1})
            data = response.json()

            items = data if isinstance(data, list) else data.get("items", [])
            for item in items:
                redirects.append(
                    {
                        "source": item.get("url", ""),
                        "target": item.get("action_data", {}).get("url", "")
                        if isinstance(item.get("action_data"), dict)
                        else item.get("action_data", ""),
                        "type": item.get("action_code", 301),
                        "enabled": item.get("status", "enabled") == "enabled",
                        "plugin": "redirection",
                    }
                )
            if redirects:
                return redirects
        except RuntimeError:
            pass  # Plugin not installed or endpoint unavailable

        # --- Attempt 2: Yoast SEO redirects ---
        try:
            endpoint = f"{self.url}/wp-json/yoast/v1/redirects"
            response = self._get(endpoint)
            data = response.json()

            yoast_redirects = data.get("redirects", []) if isinstance(data, dict) else []
            for item in yoast_redirects:
                redirects.append(
                    {
                        "source": item.get("origin", ""),
                        "target": item.get("url", ""),
                        "type": int(item.get("type", 301)),
                        "enabled": True,
                        "plugin": "yoast",
                    }
                )
            if redirects:
                return redirects
        except RuntimeError:
            pass  # Plugin not installed or endpoint unavailable

        return redirects

    def get_site_health(self) -> dict:
        """
        Aggregate site health information.

        Returns:
            Dict with: total_posts, total_pages, last_modified (ISO string),
            plugins (list if accessible), client_id, wordpress_url.
        """
        # Total posts count
        total_posts = 0
        try:
            response = self._get(
                f"{self.api_base}/posts",
                params={"per_page": 1, "status": "publish"},
            )
            total_posts = int(response.headers.get("X-WP-Total", 0))
        except RuntimeError:
            pass

        # Total pages count
        total_pages = 0
        try:
            response = self._get(
                f"{self.api_base}/pages",
                params={"per_page": 1, "status": "publish"},
            )
            total_pages = int(response.headers.get("X-WP-Total", 0))
        except RuntimeError:
            pass

        # Most recently modified post or page
        last_modified = ""
        try:
            response = self._get(
                f"{self.api_base}/posts",
                params={
                    "per_page": 1,
                    "status": "publish",
                    "orderby": "modified",
                    "order": "desc",
                },
            )
            items = response.json()
            if items:
                last_modified = items[0].get("modified", "")
        except RuntimeError:
            pass

        # Plugins list (requires administrator role; returns empty list otherwise)
        plugins: list[dict] = []
        try:
            endpoint = f"{self.url}/wp-json/wp/v2/plugins"
            response = self._get(endpoint)
            raw_plugins = response.json()
            if isinstance(raw_plugins, list):
                for p in raw_plugins:
                    plugins.append(
                        {
                            "name": p.get("name", ""),
                            "plugin": p.get("plugin", ""),
                            "version": p.get("version", ""),
                            "status": p.get("status", ""),
                            "author": p.get("author", ""),
                        }
                    )
        except RuntimeError:
            pass  # Not accessible with current permissions

        return {
            "client_id": self.client_id,
            "wordpress_url": self.url,
            "total_posts": total_posts,
            "total_pages": total_pages,
            "last_modified": last_modified,
            "plugins": plugins,
            "plugins_accessible": len(plugins) > 0,
        }


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main():
    import argparse
    import sys

    parser = argparse.ArgumentParser(
        description="WordPress REST API read-only client for wp-techseo-audit",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python wp_reader.py --client naimono --action site-info
  python wp_reader.py --client naimono --action posts
  python wp_reader.py --client naimono --action pages
  python wp_reader.py --client naimono --action meta --post-id 123
  python wp_reader.py --client naimono --action sitemap
  python wp_reader.py --client naimono --action redirects
  python wp_reader.py --client naimono --action health
""",
    )
    parser.add_argument(
        "--client",
        required=True,
        help="Client ID as defined in config/clients.json (e.g. naimono)",
    )
    parser.add_argument(
        "--action",
        required=True,
        choices=["site-info", "posts", "pages", "meta", "sitemap", "redirects", "health"],
        help="Action to perform",
    )
    parser.add_argument(
        "--post-id",
        type=int,
        default=None,
        help="Post ID (required for --action meta)",
    )
    parser.add_argument(
        "--post-type",
        default="posts",
        help="WordPress post type REST endpoint (default: posts). "
             "Used with --action posts and --action meta.",
    )
    parser.add_argument(
        "--status",
        default="publish",
        help="Post status filter for --action posts/pages (default: publish)",
    )
    args = parser.parse_args()

    try:
        reader = WordPressReader(client_id=args.client)
    except (ValueError, FileNotFoundError) as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        if args.action == "site-info":
            result = reader.get_site_info()

        elif args.action == "posts":
            result = reader.get_all_posts(
                post_type=args.post_type,
                status=args.status,
            )

        elif args.action == "pages":
            result = reader.get_pages(status=args.status)

        elif args.action == "meta":
            if args.post_id is None:
                print(
                    "Error: --post-id is required for --action meta",
                    file=sys.stderr,
                )
                sys.exit(1)
            result = reader.get_post_meta(
                post_id=args.post_id,
                post_type=args.post_type,
            )

        elif args.action == "sitemap":
            urls = reader.get_sitemap_urls()
            result = {"total": len(urls), "urls": urls}

        elif args.action == "redirects":
            result = reader.get_redirects()

        elif args.action == "health":
            result = reader.get_site_health()

        else:
            print(f"Unknown action: {args.action}", file=sys.stderr)
            sys.exit(1)

    except (RuntimeError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
