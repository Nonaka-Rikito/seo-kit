"""
WordPress Meta Updater Module

Write client for the WordPress REST API, used to apply SEO fixes.
Supports Yoast SEO and Rank Math meta field updates.

SAFETY: dry_run=True by default. Pass --execute to apply changes.
"""

import json
import os
import sys
import argparse
from datetime import datetime
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


# ---------------------------------------------------------------------------
# Field name mappings per SEO plugin
# ---------------------------------------------------------------------------

# Maps the canonical update key to the Yoast meta field name
_YOAST_META_FIELDS = {
    "meta_title":       "_yoast_wpseo_title",
    "meta_description": "_yoast_wpseo_metadesc",
    "canonical":        "_yoast_wpseo_canonical",
    "focus_keyphrase":  "_yoast_wpseo_focuskw",
}

# Maps the canonical update key to the Rank Math meta field name
_RANKMATH_META_FIELDS = {
    "meta_title":       "rank_math_title",
    "meta_description": "rank_math_description",
    "canonical":        "rank_math_canonical_url",
    "focus_keyphrase":  "rank_math_focus_keyword",
}

# Keys handled directly at the post level (not inside `meta`)
_POST_LEVEL_FIELDS = {"title", "slug"}


class WordPressMetaUpdater:
    """
    Write client for WordPress REST API.

    Supports updating post titles, slugs, and SEO plugin meta fields
    (Yoast SEO or Rank Math). All changes are logged with before/after values.
    Dry-run mode is active by default.
    """

    def __init__(self, client_id: str, dry_run: bool = True):
        """
        Initialize the updater for a specific client.

        Args:
            client_id: Key in clients.json (e.g. 'naimono').
            dry_run: When True (default) no API writes are performed.

        Raises:
            ValueError: If client_id is not found or password env var is missing.
            FileNotFoundError: If clients.json does not exist.
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
        self.dry_run = dry_run

        url: str = client.get("wordpress_url", "").rstrip("/")
        username: str = client.get("wordpress_username", "")
        password_env: str = client.get("wordpress_app_password_env", "")
        self.seo_plugin: str = client.get("seo_plugin", "yoast").lower()

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

        self.session = requests.Session()
        self.session.auth = (username, app_password)
        self.session.headers.update(
            {
                "Content-Type": "application/json",
                "User-Agent": "WPTechSEOAudit/1.0 (Meta Updater)",
            }
        )

        # In-session change log
        self._change_log: list[dict] = []

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get(self, url: str, params: Optional[dict] = None) -> requests.Response:
        """Perform a GET request and raise on HTTP errors."""
        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response
        except requests.exceptions.Timeout:
            raise RuntimeError(f"Request timed out after 30s: {url}")
        except requests.exceptions.HTTPError as e:
            status = e.response.status_code if e.response is not None else "unknown"
            body = e.response.text[:500] if e.response is not None else ""
            raise RuntimeError(f"HTTP {status} error for GET {url}: {body}") from e

    def _post(self, url: str, payload: dict) -> requests.Response:
        """Perform a POST request and raise on HTTP errors."""
        try:
            response = self.session.post(url, json=payload, timeout=30)
            response.raise_for_status()
            return response
        except requests.exceptions.Timeout:
            raise RuntimeError(f"Request timed out after 30s: {url}")
        except requests.exceptions.HTTPError as e:
            status = e.response.status_code if e.response is not None else "unknown"
            body = e.response.text[:500] if e.response is not None else ""
            raise RuntimeError(f"HTTP {status} error for POST {url}: {body}") from e

    def _patch(self, url: str, payload: dict) -> requests.Response:
        """Perform a PATCH request and raise on HTTP errors."""
        try:
            response = self.session.patch(url, json=payload, timeout=30)
            response.raise_for_status()
            return response
        except requests.exceptions.Timeout:
            raise RuntimeError(f"Request timed out after 30s: {url}")
        except requests.exceptions.HTTPError as e:
            status = e.response.status_code if e.response is not None else "unknown"
            body = e.response.text[:500] if e.response is not None else ""
            raise RuntimeError(f"HTTP {status} error for PATCH {url}: {body}") from e

    def _log_change(
        self,
        post_id: int,
        field: str,
        before: str,
        after: str,
    ) -> dict:
        """Record a change and print a diff-style line."""
        entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "post_id": post_id,
            "field": field,
            "before": before,
            "after": after,
            "dry_run": self.dry_run,
        }
        self._change_log.append(entry)

        prefix = "[DRY RUN]" if self.dry_run else "[APPLIED]"
        print(f'{prefix} post #{post_id} | {field}: "{before}" → "{after}"')
        return entry

    def _seo_meta_map(self) -> dict:
        """Return the field-name mapping for the configured SEO plugin."""
        if self.seo_plugin == "rankmath":
            return _RANKMATH_META_FIELDS
        # Default to Yoast
        return _YOAST_META_FIELDS

    def _validate_post_exists(self, post_id: int, post_type: str) -> dict:
        """
        Fetch the raw post object. Raises RuntimeError if the post is not found.

        Returns:
            The raw JSON dict from the WP REST API.
        """
        endpoint = f"{self.api_base}/{post_type}/{post_id}"
        try:
            response = self._get(endpoint, params={"context": "edit"})
            return response.json()
        except RuntimeError as e:
            raise RuntimeError(
                f"Post #{post_id} (type '{post_type}') not found or inaccessible: {e}"
            ) from e

    # ------------------------------------------------------------------
    # Public methods
    # ------------------------------------------------------------------

    def get_current_meta(self, post_id: int, post_type: str = "posts") -> dict:
        """
        Fetch current SEO-relevant meta values for a post.

        Args:
            post_id: WordPress post ID.
            post_type: REST API endpoint name (default 'posts').

        Returns:
            Dict with keys: title, slug, meta_title, meta_description,
            canonical, robots, focus_keyphrase.
        """
        raw = self._validate_post_exists(post_id, post_type)
        meta = raw.get("meta", {}) or {}

        # Yoast values may also live under yoast_head_json
        yoast = raw.get("yoast_head_json", {}) or {}

        if self.seo_plugin == "rankmath":
            meta_title = meta.get("rank_math_title", "")
            meta_description = meta.get("rank_math_description", "")
            canonical = meta.get("rank_math_canonical_url", "")
            robots = meta.get("rank_math_robots", "")
            focus_keyphrase = meta.get("rank_math_focus_keyword", "")
        else:
            # Yoast: prefer raw meta fields, fall back to yoast_head_json
            meta_title = (
                meta.get("_yoast_wpseo_title")
                or yoast.get("title", "")
            )
            meta_description = (
                meta.get("_yoast_wpseo_metadesc")
                or yoast.get("description", "")
            )
            canonical = (
                meta.get("_yoast_wpseo_canonical")
                or yoast.get("canonical", "")
            )
            robots = meta.get("_yoast_wpseo_meta-robots-noindex", "")
            focus_keyphrase = meta.get("_yoast_wpseo_focuskw", "")

        return {
            "title": raw.get("title", {}).get("rendered", ""),
            "slug": raw.get("slug", ""),
            "meta_title": meta_title or "",
            "meta_description": meta_description or "",
            "canonical": canonical or "",
            "robots": robots or "",
            "focus_keyphrase": focus_keyphrase or "",
        }

    def update_post_meta(
        self,
        post_id: int,
        updates: dict,
        post_type: str = "posts",
    ) -> dict:
        """
        Apply SEO meta updates to a post.

        Args:
            post_id: WordPress post ID.
            updates: Dict of fields to update. Supported keys:
                title, slug, meta_title, meta_description,
                meta_title (alias for seo title), canonical,
                robots, focus_keyphrase.
            post_type: REST API endpoint name (default 'posts').

        Returns:
            Dict with post_id, changes (list of before/after dicts), dry_run.
        """
        # Validate post exists and get current values
        current = self.get_current_meta(post_id, post_type)

        seo_map = self._seo_meta_map()
        changes: list[dict] = []

        # Separate post-level fields from SEO meta fields
        post_payload: dict = {}
        meta_payload: dict = {}

        for key, new_value in updates.items():
            new_value = str(new_value) if new_value is not None else ""

            if key == "title":
                before = current.get("title", "")
                if before == new_value:
                    continue
                change = self._log_change(post_id, "title", before, new_value)
                changes.append(change)
                post_payload["title"] = new_value

            elif key == "slug":
                before = current.get("slug", "")
                if before == new_value:
                    continue
                print(
                    f"  WARNING: Changing slug for post #{post_id} "
                    f'from "{before}" to "{new_value}" can break existing links.'
                )
                change = self._log_change(post_id, "slug", before, new_value)
                changes.append(change)
                post_payload["slug"] = new_value

            elif key in seo_map:
                wp_field = seo_map[key]
                before = current.get(key, "")
                if before == new_value:
                    continue
                change = self._log_change(post_id, key, before, new_value)
                changes.append(change)
                meta_payload[wp_field] = new_value

            elif key == "robots":
                # robots is handled directly in meta; field name differs per plugin
                if self.seo_plugin == "rankmath":
                    wp_field = "rank_math_robots"
                else:
                    wp_field = "_yoast_wpseo_meta-robots-noindex"
                before = current.get("robots", "")
                if before == new_value:
                    continue
                change = self._log_change(post_id, "robots", before, new_value)
                changes.append(change)
                meta_payload[wp_field] = new_value

            else:
                print(f"  WARNING: Unknown update key '{key}' — skipped.")

        if not changes:
            print(f"  No changes needed for post #{post_id}.")
            return {"post_id": post_id, "changes": [], "dry_run": self.dry_run}

        if not self.dry_run:
            endpoint = f"{self.api_base}/{post_type}/{post_id}"
            payload: dict = {}
            if post_payload:
                payload.update(post_payload)
            if meta_payload:
                payload["meta"] = meta_payload

            # For Yoast, also attempt the yoast_seo top-level field if available
            if self.seo_plugin == "yoast" and meta_payload:
                yoast_updates = {}
                yoast_reverse = {v: k for k, v in _YOAST_META_FIELDS.items()}
                for wp_field, val in meta_payload.items():
                    canonical_key = yoast_reverse.get(wp_field)
                    if canonical_key == "meta_title":
                        yoast_updates["title"] = val
                    elif canonical_key == "meta_description":
                        yoast_updates["metadesc"] = val
                    elif canonical_key == "canonical":
                        yoast_updates["canonical"] = val
                    elif canonical_key == "focus_keyphrase":
                        yoast_updates["focuskw"] = val
                if yoast_updates:
                    payload["yoast_seo"] = yoast_updates

            self._patch(endpoint, payload)

        return {"post_id": post_id, "changes": changes, "dry_run": self.dry_run}

    def update_post_title(
        self,
        post_id: int,
        new_title: str,
        post_type: str = "posts",
    ) -> dict:
        """
        Update the WordPress post title.

        Args:
            post_id: WordPress post ID.
            new_title: New title string.
            post_type: REST API endpoint name (default 'posts').

        Returns:
            Dict with post_id, changes, dry_run.
        """
        return self.update_post_meta(
            post_id=post_id,
            updates={"title": new_title},
            post_type=post_type,
        )

    def update_post_slug(
        self,
        post_id: int,
        new_slug: str,
        post_type: str = "posts",
    ) -> dict:
        """
        Update the WordPress post slug.

        WARNING: Changing slugs can break existing links and inbound backlinks.
        Always create a redirect after changing a slug.

        Args:
            post_id: WordPress post ID.
            new_slug: New slug string (URL-safe, no leading/trailing slashes).
            post_type: REST API endpoint name (default 'posts').

        Returns:
            Dict with post_id, changes, dry_run.
        """
        return self.update_post_meta(
            post_id=post_id,
            updates={"slug": new_slug},
            post_type=post_type,
        )

    def create_redirect(
        self,
        source: str,
        target: str,
        redirect_type: int = 301,
    ) -> dict:
        """
        Create a redirect via the Redirection plugin REST API.

        Args:
            source: Source URL path (e.g. '/old-path/').
            target: Target URL path or full URL (e.g. '/new-path/').
            redirect_type: HTTP status code (default 301).

        Returns:
            Dict with source, target, type, status, dry_run.
        """
        result = {
            "source": source,
            "target": target,
            "type": redirect_type,
            "dry_run": self.dry_run,
        }

        prefix = "[DRY RUN]" if self.dry_run else "[APPLIED]"
        print(f"{prefix} redirect: {source} → {target} ({redirect_type})")

        if self.dry_run:
            result["status"] = "dry_run"
            return result

        endpoint = f"{self.url}/wp-json/redirection/v1/redirect"
        payload = {
            "url": source,
            "action_type": "url",
            "action_data": {"url": target},
            "action_code": redirect_type,
            "match_type": "url",
            "enabled": True,
        }

        try:
            response = self._post(endpoint, payload)
            data = response.json()
            result["status"] = "created"
            result["redirect_id"] = data.get("id")
        except RuntimeError as e:
            print(
                f"  WARNING: Redirection plugin API unavailable ({e}).\n"
                f"  Manual action required: Create {redirect_type} redirect\n"
                f"    Source: {source}\n"
                f"    Target: {target}"
            )
            result["status"] = "manual_required"
            result["error"] = str(e)

        return result

    def apply_fix_plan(self, plan_path: str) -> dict:
        """
        Apply all fixes defined in a JSON fix plan file.

        Expected plan format::

            {
              "fixes": [
                {
                  "post_id": 123,
                  "post_type": "posts",
                  "updates": {"meta_title": "New Title", "meta_description": "..."}
                },
                {
                  "action": "redirect",
                  "source": "/old-path/",
                  "target": "/new-path/",
                  "type": 301
                }
              ]
            }

        Args:
            plan_path: Path to the JSON fix plan file.

        Returns:
            Dict with total, succeeded, failed, results (list).
        """
        plan_file = Path(plan_path)
        if not plan_file.exists():
            raise FileNotFoundError(f"Fix plan not found: {plan_path}")

        with open(plan_file, "r", encoding="utf-8") as f:
            plan = json.load(f)

        fixes: list[dict] = plan.get("fixes", [])
        if not fixes:
            print("Fix plan contains no fixes.")
            return {"total": 0, "succeeded": 0, "failed": 0, "results": []}

        print(
            f"\n{'='*60}\n"
            f"Applying fix plan: {plan_file.name}\n"
            f"Total fixes: {len(fixes)} | Mode: {'DRY RUN' if self.dry_run else 'EXECUTE'}\n"
            f"{'='*60}\n"
        )

        results: list[dict] = []
        succeeded = 0
        failed = 0

        for i, fix in enumerate(fixes, start=1):
            print(f"[{i}/{len(fixes)}] Processing fix...")
            try:
                action = fix.get("action", "update_meta")

                if action == "redirect":
                    result = self.create_redirect(
                        source=fix["source"],
                        target=fix["target"],
                        redirect_type=fix.get("type", 301),
                    )
                    result["fix_index"] = i
                    result["action"] = "redirect"
                    results.append(result)
                    succeeded += 1

                else:
                    # Default: update post meta
                    post_id = fix.get("post_id")
                    if post_id is None:
                        raise ValueError("Fix entry is missing 'post_id'.")
                    post_type = fix.get("post_type", "posts")
                    updates = fix.get("updates", {})
                    if not updates:
                        print(f"  Skipping fix #{i}: no updates specified.")
                        continue

                    result = self.update_post_meta(
                        post_id=int(post_id),
                        updates=updates,
                        post_type=post_type,
                    )
                    result["fix_index"] = i
                    result["action"] = "update_meta"
                    results.append(result)
                    succeeded += 1

            except Exception as e:
                print(f"  ERROR in fix #{i}: {e}")
                results.append(
                    {
                        "fix_index": i,
                        "error": str(e),
                        "fix": fix,
                        "dry_run": self.dry_run,
                    }
                )
                failed += 1

        print(
            f"\n{'='*60}\n"
            f"Fix plan complete: {succeeded} succeeded, {failed} failed\n"
            f"{'='*60}\n"
        )

        return {
            "total": len(fixes),
            "succeeded": succeeded,
            "failed": failed,
            "results": results,
        }

    def generate_rollback(self, changes: list, output_path: str) -> str:
        """
        Generate a JSON rollback fix plan from a list of applied changes.

        The rollback plan uses the same format as a regular fix plan but
        with each field's `before` value as the new `after` value, allowing
        you to undo applied changes by running the rollback as a fix plan.

        Args:
            changes: List of change dicts as returned by update_post_meta.
            output_path: Directory where the rollback file will be written.

        Returns:
            Absolute path to the generated rollback JSON file.
        """
        timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        output_dir = Path(output_path)
        output_dir.mkdir(parents=True, exist_ok=True)
        rollback_file = output_dir / f"rollback_{timestamp}.json"

        # Group changes by post_id
        by_post: dict[int, dict] = {}
        for change in changes:
            post_id = change.get("post_id")
            if post_id is None:
                continue
            if post_id not in by_post:
                by_post[post_id] = {
                    "post_id": post_id,
                    "post_type": "posts",
                    "updates": {},
                }
            field = change.get("field", "")
            before = change.get("before", "")
            # Only include if this was actually applied (not dry run)
            if not change.get("dry_run", True):
                by_post[post_id]["updates"][field] = before

        fixes = [entry for entry in by_post.values() if entry["updates"]]

        rollback_plan = {
            "generated_at": timestamp,
            "source_client": self.client_id,
            "note": "Auto-generated rollback plan. Apply with wp_meta_updater.py --plan.",
            "fixes": fixes,
        }

        with open(rollback_file, "w", encoding="utf-8") as f:
            json.dump(rollback_plan, f, ensure_ascii=False, indent=2)

        print(f"Rollback plan written to: {rollback_file}")
        return str(rollback_file.resolve())

    def get_change_log(self) -> list:
        """
        Return all changes logged in this session.

        Returns:
            List of dicts, each with: timestamp, post_id, field,
            before, after, dry_run.
        """
        return list(self._change_log)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="WordPress REST API write client for SEO fixes (wp-techseo-audit)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Show current meta for post 123 (read-only)
  python wp_meta_updater.py --client naimono --post-id 123 --show-meta

  # Dry-run a single meta update (default, no --execute)
  python wp_meta_updater.py --client naimono --post-id 123 --meta-title "New Title"

  # Apply a single meta update for real
  python wp_meta_updater.py --client naimono --post-id 123 --meta-title "New Title" --execute

  # Dry-run a fix plan
  python wp_meta_updater.py --client naimono --plan fix-plan.json

  # Apply a fix plan and auto-generate rollback
  python wp_meta_updater.py --client naimono --plan fix-plan.json --execute
""",
    )

    parser.add_argument(
        "--client",
        required=True,
        help="Client ID as defined in config/clients.json (e.g. naimono)",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        default=False,
        help="Actually apply changes. Without this flag, dry-run mode is used.",
    )

    # Fix plan mode
    parser.add_argument(
        "--plan",
        metavar="PATH",
        help="Path to a JSON fix plan file to apply.",
    )

    # Single-post mode
    parser.add_argument(
        "--post-id",
        type=int,
        metavar="ID",
        help="WordPress post ID (required for single-post operations).",
    )
    parser.add_argument(
        "--post-type",
        default="posts",
        metavar="TYPE",
        help="WordPress REST API post type endpoint (default: posts).",
    )
    parser.add_argument(
        "--show-meta",
        action="store_true",
        help="Print current SEO meta for the given --post-id and exit.",
    )

    # Meta update fields
    parser.add_argument("--title", help="New WordPress post title.")
    parser.add_argument("--slug", help="New WordPress post slug (breaks links!).")
    parser.add_argument("--meta-title", help="New SEO/meta title.")
    parser.add_argument("--meta-description", help="New SEO meta description.")
    parser.add_argument("--canonical", help="New canonical URL.")
    parser.add_argument("--focus-keyphrase", help="New SEO focus keyphrase.")

    args = parser.parse_args()

    # Initialise updater
    dry_run = not args.execute
    try:
        updater = WordPressMetaUpdater(client_id=args.client, dry_run=dry_run)
    except (ValueError, FileNotFoundError) as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        sys.exit(1)

    mode_label = "DRY RUN" if dry_run else "EXECUTE"
    print(f"\nClient: {args.client} | Mode: {mode_label}\n")

    # --show-meta: read-only display
    if args.show_meta:
        if args.post_id is None:
            print("Error: --post-id is required with --show-meta.", file=sys.stderr)
            sys.exit(1)
        try:
            meta = updater.get_current_meta(
                post_id=args.post_id,
                post_type=args.post_type,
            )
            print(json.dumps(meta, ensure_ascii=False, indent=2))
        except RuntimeError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
        sys.exit(0)

    # --plan: apply fix plan
    if args.plan:
        try:
            aggregate = updater.apply_fix_plan(plan_path=args.plan)
            print(json.dumps(aggregate, ensure_ascii=False, indent=2, default=str))

            # Auto-generate rollback if we actually executed
            if not dry_run:
                all_changes = updater.get_change_log()
                if all_changes:
                    rollback_dir = Path(args.plan).parent
                    updater.generate_rollback(
                        changes=all_changes,
                        output_path=str(rollback_dir),
                    )
        except (FileNotFoundError, RuntimeError, ValueError) as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
        sys.exit(0)

    # Single-post meta update
    if args.post_id is None:
        print(
            "Error: --post-id is required for single-post updates "
            "(or use --plan for batch updates).",
            file=sys.stderr,
        )
        sys.exit(1)

    # Collect updates from CLI flags
    updates: dict = {}
    if args.title:
        updates["title"] = args.title
    if args.slug:
        updates["slug"] = args.slug
    if args.meta_title:
        updates["meta_title"] = args.meta_title
    if args.meta_description:
        updates["meta_description"] = args.meta_description
    if args.canonical:
        updates["canonical"] = args.canonical
    if args.focus_keyphrase:
        updates["focus_keyphrase"] = args.focus_keyphrase

    if not updates:
        print(
            "Error: No update fields provided. Specify at least one of: "
            "--title, --slug, --meta-title, --meta-description, "
            "--canonical, --focus-keyphrase.",
            file=sys.stderr,
        )
        sys.exit(1)

    try:
        result = updater.update_post_meta(
            post_id=args.post_id,
            updates=updates,
            post_type=args.post_type,
        )
        print(json.dumps(result, ensure_ascii=False, indent=2, default=str))

        # Auto-generate rollback if we actually executed
        if not dry_run:
            all_changes = updater.get_change_log()
            if all_changes:
                rollback_dir = Path(__file__).parent
                updater.generate_rollback(
                    changes=all_changes,
                    output_path=str(rollback_dir),
                )
    except (RuntimeError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
