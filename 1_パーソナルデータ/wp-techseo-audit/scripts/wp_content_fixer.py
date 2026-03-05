"""
WordPress Content Fixer

FIX-002: 内部リンクの trailing slash 正規化
FIX-003: 画像の width/height 属性追加

WP REST API 経由でポストコンテンツを取得し、HTML を修正して書き戻す。
SAFETY: dry_run=True がデフォルト。--execute を渡さない限り書き込みゼロ。
"""

import json
import os
import re
import sys
import argparse
from datetime import datetime
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup, Tag
from dotenv import load_dotenv

# Load .env from ../config/.env relative to this script
_CONFIG_DIR = Path(__file__).parent.parent / "config"
_ENV_PATH = _CONFIG_DIR / ".env"
if _ENV_PATH.exists():
    load_dotenv(_ENV_PATH)


def _load_clients_config() -> dict:
    config_path = _CONFIG_DIR / "clients.json"
    if not config_path.exists():
        raise FileNotFoundError(f"clients.json not found at {config_path}")
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


class WordPressContentFixer:
    """
    WP REST API 経由でポストコンテンツを修正するクライアント。

    対応修正:
      fix-links  - 内部リンクの trailing slash 正規化 (FIX-002)
      fix-images - img タグに width/height 属性を追加 (FIX-003)
    """

    def __init__(self, client_id: str, dry_run: bool = True):
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
        self.dry_run = dry_run

        url: str = client.get("wordpress_url", "").rstrip("/")
        username: str = client.get("wordpress_username", "")
        password_env: str = client.get("wordpress_app_password_env", "")

        if not url:
            raise ValueError(f"Client '{client_id}' is missing 'wordpress_url'.")
        if not username:
            raise ValueError(f"Client '{client_id}' is missing 'wordpress_username'.")
        if not password_env:
            raise ValueError(f"Client '{client_id}' is missing 'wordpress_app_password_env'.")

        app_password = os.environ.get(password_env)
        if not app_password:
            raise ValueError(
                f"Environment variable '{password_env}' is not set. "
                f"Add it to {_ENV_PATH} or set it in the shell environment."
            )

        self.url = url
        self.site_host = urlparse(url).netloc
        self.api_base = f"{url}/wp-json/wp/v2"

        self.session = requests.Session()
        self.session.auth = (username, app_password)
        self.session.headers.update({
            "Content-Type": "application/json",
            "User-Agent": "WPTechSEOAudit/1.0 (Content Fixer)",
        })

        self._change_log: list[dict] = []

    # ------------------------------------------------------------------
    # HTTP helpers
    # ------------------------------------------------------------------

    def _get(self, url: str, params: Optional[dict] = None) -> requests.Response:
        try:
            r = self.session.get(url, params=params, timeout=30)
            r.raise_for_status()
            return r
        except requests.exceptions.Timeout:
            raise RuntimeError(f"Request timed out: {url}")
        except requests.exceptions.HTTPError as e:
            status = e.response.status_code if e.response is not None else "unknown"
            body = e.response.text[:300] if e.response is not None else ""
            raise RuntimeError(f"HTTP {status} for GET {url}: {body}") from e

    def _patch(self, url: str, payload: dict) -> requests.Response:
        try:
            r = self.session.patch(url, json=payload, timeout=30)
            r.raise_for_status()
            return r
        except requests.exceptions.Timeout:
            raise RuntimeError(f"Request timed out: {url}")
        except requests.exceptions.HTTPError as e:
            status = e.response.status_code if e.response is not None else "unknown"
            body = e.response.text[:300] if e.response is not None else ""
            raise RuntimeError(f"HTTP {status} for PATCH {url}: {body}") from e

    def _get_paginated(self, endpoint: str, params: Optional[dict] = None) -> list:
        base_params = {"per_page": 100, "page": 1, "context": "edit"}
        if params:
            base_params.update(params)
        results = []
        page = 1
        while True:
            base_params["page"] = page
            r = self._get(endpoint, params=base_params)
            data = r.json()
            if not data:
                break
            results.extend(data)
            total_pages = int(r.headers.get("X-WP-TotalPages", 1))
            if page >= total_pages:
                break
            page += 1
        return results

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _is_internal_link(self, href: str) -> bool:
        """True if href points to the same site (or is a relative path)."""
        if not href:
            return False
        # skip anchors, mailto, tel, javascript
        if href.startswith(("#", "mailto:", "tel:", "javascript:")):
            return False
        parsed = urlparse(href)
        if parsed.netloc and parsed.netloc != self.site_host:
            return False  # external domain
        return True

    def _normalize_trailing_slash(self, href: str) -> str:
        """
        Add trailing slash to internal path if missing.
        Paths with file extensions (e.g. /file.pdf) are left unchanged.
        Query strings and fragments are preserved.
        """
        parsed = urlparse(href)
        path = parsed.path

        # Skip if path has a file extension
        last_segment = path.split("/")[-1]
        if "." in last_segment:
            return href

        # Skip if already ends with /
        if path.endswith("/"):
            return href

        new_path = path + "/"
        new_url = parsed._replace(path=new_path).geturl()
        return new_url

    def _fetch_post_content(self, post_id: int, post_type: str) -> dict:
        """Fetch raw post data including rendered and raw content."""
        endpoint = f"{self.api_base}/{post_type}/{post_id}"
        r = self._get(endpoint, params={"context": "edit"})
        return r.json()

    def _log(self, post_id: int, action: str, detail: str) -> None:
        entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "post_id": post_id,
            "action": action,
            "detail": detail,
            "dry_run": self.dry_run,
        }
        self._change_log.append(entry)
        prefix = "[DRY RUN]" if self.dry_run else "[APPLIED]"
        print(f"  {prefix} #{post_id} | {action}: {detail}")

    # ------------------------------------------------------------------
    # FIX-002: fix-links
    # ------------------------------------------------------------------

    def fix_internal_links(self, post_id: int, post_type: str = "posts") -> dict:
        """
        Normalize trailing slashes on all internal <a href> in post content.

        Returns:
            dict with post_id, changes_count, dry_run, content_changed.
        """
        raw = self._fetch_post_content(post_id, post_type)
        content_raw: str = raw.get("content", {}).get("raw", "")
        if not content_raw:
            # Fallback to rendered (less reliable for editing)
            content_raw = raw.get("content", {}).get("rendered", "")

        if not content_raw:
            print(f"  post #{post_id}: content is empty, skipping.")
            return {"post_id": post_id, "changes_count": 0, "dry_run": self.dry_run, "content_changed": False}

        soup = BeautifulSoup(content_raw, "html.parser")
        changes = 0

        for a in soup.find_all("a", href=True):
            original_href = a["href"]
            if not self._is_internal_link(original_href):
                continue
            normalized = self._normalize_trailing_slash(original_href)
            if normalized != original_href:
                a["href"] = normalized
                self._log(post_id, "fix-link", f"{original_href} → {normalized}")
                changes += 1

        if changes == 0:
            print(f"  post #{post_id}: no link changes needed.")
            return {"post_id": post_id, "changes_count": 0, "dry_run": self.dry_run, "content_changed": False}

        new_content = str(soup)

        if not self.dry_run:
            endpoint = f"{self.api_base}/{post_type}/{post_id}"
            self._patch(endpoint, {"content": new_content})

        return {
            "post_id": post_id,
            "changes_count": changes,
            "dry_run": self.dry_run,
            "content_changed": True,
        }

    # ------------------------------------------------------------------
    # FIX-003: fix-images
    # ------------------------------------------------------------------

    def _get_image_dimensions_from_media_api(self, src: str) -> Optional[tuple[int, int]]:
        """
        Attempt to retrieve width/height from WP Media Library for a given src URL.
        Returns (width, height) or None if not found.
        """
        # Extract filename to search media library
        filename = src.split("/")[-1].split("?")[0]
        try:
            r = self._get(
                f"{self.api_base}/media",
                params={"search": filename, "per_page": 5},
            )
            items = r.json()
            for item in items:
                media_src = item.get("source_url", "")
                if filename in media_src:
                    details = item.get("media_details", {})
                    w = details.get("width")
                    h = details.get("height")
                    if w and h:
                        return (int(w), int(h))
        except RuntimeError:
            pass
        return None

    def fix_image_dimensions(self, post_id: int, post_type: str = "posts") -> dict:
        """
        Add missing width/height attributes to <img> tags in post content.
        Dimensions are fetched from WP Media Library API.

        Returns:
            dict with post_id, changes_count, dry_run, content_changed.
        """
        raw = self._fetch_post_content(post_id, post_type)
        content_raw: str = raw.get("content", {}).get("raw", "")
        if not content_raw:
            content_raw = raw.get("content", {}).get("rendered", "")

        if not content_raw:
            print(f"  post #{post_id}: content is empty, skipping.")
            return {"post_id": post_id, "changes_count": 0, "dry_run": self.dry_run, "content_changed": False}

        soup = BeautifulSoup(content_raw, "html.parser")
        changes = 0

        for img in soup.find_all("img", src=True):
            # Skip if already has both width and height
            if img.get("width") and img.get("height"):
                continue

            src = img["src"]
            dims = self._get_image_dimensions_from_media_api(src)
            if not dims:
                print(f"  post #{post_id}: could not get dimensions for {src}, skipping.")
                continue

            w, h = dims
            img["width"] = str(w)
            img["height"] = str(h)
            self._log(post_id, "fix-image-dims", f"{src} → width={w} height={h}")
            changes += 1

        if changes == 0:
            print(f"  post #{post_id}: no image dimension changes needed.")
            return {"post_id": post_id, "changes_count": 0, "dry_run": self.dry_run, "content_changed": False}

        new_content = str(soup)

        if not self.dry_run:
            endpoint = f"{self.api_base}/{post_type}/{post_id}"
            self._patch(endpoint, {"content": new_content})

        return {
            "post_id": post_id,
            "changes_count": changes,
            "dry_run": self.dry_run,
            "content_changed": True,
        }

    # ------------------------------------------------------------------
    # Batch: scan all posts of a type
    # ------------------------------------------------------------------

    def scan_and_fix_all(self, action: str, post_type: str = "posts") -> dict:
        """
        Scan and fix all posts of the given post_type.

        Args:
            action: 'fix-links' or 'fix-images'
            post_type: WP REST API endpoint name.

        Returns:
            Aggregate result dict.
        """
        print(f"\n{'='*60}")
        print(f"Action: {action} | post_type: {post_type} | mode: {'DRY RUN' if self.dry_run else 'EXECUTE'}")
        print(f"{'='*60}\n")

        endpoint = f"{self.api_base}/{post_type}"
        try:
            posts = self._get_paginated(endpoint)
        except RuntimeError as e:
            raise RuntimeError(f"Failed to fetch posts for type '{post_type}': {e}") from e

        if not posts:
            print(f"No posts found for type '{post_type}'.")
            return {"total": 0, "changed": 0, "failed": 0, "results": []}

        total = len(posts)
        changed = 0
        failed = 0
        results = []

        for i, post in enumerate(posts, start=1):
            post_id = post.get("id")
            print(f"[{i}/{total}] post #{post_id}...")
            try:
                if action == "fix-links":
                    result = self.fix_internal_links(post_id, post_type)
                elif action == "fix-images":
                    result = self.fix_image_dimensions(post_id, post_type)
                else:
                    raise ValueError(f"Unknown action: {action}")

                results.append(result)
                if result.get("content_changed"):
                    changed += 1
            except Exception as e:
                print(f"  ERROR: {e}")
                results.append({"post_id": post_id, "error": str(e)})
                failed += 1

        print(f"\n{'='*60}")
        print(f"Done: {changed} changed, {failed} failed out of {total} posts")
        print(f"{'='*60}\n")

        return {"total": total, "changed": changed, "failed": failed, "results": results}

    # ------------------------------------------------------------------
    # Plan file support
    # ------------------------------------------------------------------

    def apply_plan(self, plan_path: str) -> dict:
        """
        Apply fixes from a JSON plan file.

        Plan format:
            {
              "action": "fix-links",   // or "fix-images"
              "fixes": [
                {"post_id": 123, "post_type": "posts"},
                ...
              ]
            }
        """
        plan_file = Path(plan_path)
        if not plan_file.exists():
            raise FileNotFoundError(f"Plan file not found: {plan_path}")

        with open(plan_file, "r", encoding="utf-8") as f:
            plan = json.load(f)

        action = plan.get("action", "fix-links")
        fixes = plan.get("fixes", [])

        print(f"\n{'='*60}")
        print(f"Plan: {plan_file.name} | action: {action} | fixes: {len(fixes)} | mode: {'DRY RUN' if self.dry_run else 'EXECUTE'}")
        print(f"{'='*60}\n")

        total = len(fixes)
        changed = 0
        failed = 0
        results = []

        for i, fix in enumerate(fixes, start=1):
            post_id = fix.get("post_id")
            post_type = fix.get("post_type", "posts")
            print(f"[{i}/{total}] post #{post_id} ({post_type})...")
            try:
                if action == "fix-links":
                    result = self.fix_internal_links(post_id, post_type)
                elif action == "fix-images":
                    result = self.fix_image_dimensions(post_id, post_type)
                else:
                    raise ValueError(f"Unknown action: {action}")
                results.append(result)
                if result.get("content_changed"):
                    changed += 1
            except Exception as e:
                print(f"  ERROR: {e}")
                results.append({"post_id": post_id, "error": str(e)})
                failed += 1

        print(f"\n{'='*60}")
        print(f"Done: {changed} changed, {failed} failed")
        print(f"{'='*60}\n")

        return {"total": total, "changed": changed, "failed": failed, "results": results}

    def get_change_log(self) -> list:
        return list(self._change_log)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="WordPress Content Fixer — trailing slash & image dimensions (wp-techseo-audit)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # campusページ全件のリンクをドライラン確認
  python wp_content_fixer.py --client naimono --action fix-links --post-type campus

  # 実際に適用
  python wp_content_fixer.py --client naimono --action fix-links --post-type campus --execute

  # 特定の post_id のみ
  python wp_content_fixer.py --client naimono --action fix-links --post-id 37260 --post-type campus

  # 画像 dimensions 追加
  python wp_content_fixer.py --client naimono --action fix-images --post-type posts

  # JSONプランファイルで指定
  python wp_content_fixer.py --client naimono --plan reports/naimono_fix_content.json
""",
    )

    parser.add_argument("--client", required=True, help="Client ID (e.g. naimono)")
    parser.add_argument("--execute", action="store_true", default=False,
                        help="Actually apply changes. Default is dry-run.")
    parser.add_argument("--action", choices=["fix-links", "fix-images"],
                        help="Action to perform (required unless --plan is used).")
    parser.add_argument("--post-type", default="posts",
                        help="WP REST API post type endpoint (default: posts).")
    parser.add_argument("--post-id", type=int, default=None,
                        help="Single post ID to fix (optional; omit to scan all).")
    parser.add_argument("--plan", metavar="PATH",
                        help="Path to a JSON fix plan file.")

    args = parser.parse_args()

    if not args.plan and not args.action:
        parser.error("Either --action or --plan is required.")

    dry_run = not args.execute
    try:
        fixer = WordPressContentFixer(client_id=args.client, dry_run=dry_run)
    except (ValueError, FileNotFoundError) as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        sys.exit(1)

    mode_label = "DRY RUN" if dry_run else "EXECUTE"
    print(f"\nClient: {args.client} | Mode: {mode_label}\n")

    try:
        if args.plan:
            result = fixer.apply_plan(plan_path=args.plan)
        elif args.post_id is not None:
            if args.action == "fix-links":
                result = fixer.fix_internal_links(args.post_id, args.post_type)
            else:
                result = fixer.fix_image_dimensions(args.post_id, args.post_type)
        else:
            result = fixer.scan_and_fix_all(action=args.action, post_type=args.post_type)

        print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
    except (RuntimeError, ValueError, FileNotFoundError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
