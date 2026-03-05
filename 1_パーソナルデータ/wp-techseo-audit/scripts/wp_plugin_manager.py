"""
WordPress Plugin Manager

WP REST API /wp/v2/plugins エンドポイントでプラグインの確認・有効化を行う。
パフォーマンス改善に必要なプラグイン（Redis Object Cache等）の管理。

SAFETY: --execute なしはドライラン。有効化/インストールは --execute が必要。
"""

import json
import os
import sys
import argparse
from pathlib import Path
from typing import Optional

import requests
from dotenv import load_dotenv

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


# パフォーマンス改善に推奨するプラグイン
_PERF_PLUGINS = {
    "redis-cache": {
        "name": "Redis Object Cache",
        "purpose": "FIX-001: オブジェクトキャッシュでTTFB改善",
        "priority": "HIGH",
    },
    "w3-total-cache": {
        "name": "W3 Total Cache",
        "purpose": "FIX-001: ページキャッシュ・ブラウザキャッシュ・minify",
        "priority": "HIGH",
    },
    "wp-super-cache": {
        "name": "WP Super Cache",
        "purpose": "FIX-001: 静的HTMLキャッシュ（W3TCの代替）",
        "priority": "HIGH",
    },
    "autoptimize": {
        "name": "Autoptimize",
        "purpose": "FIX-013: CSS/JS minify・遅延読み込み",
        "priority": "MEDIUM",
    },
    "perfmatters": {
        "name": "Perfmatters",
        "purpose": "FIX-013: 投稿タイプ別CSS/JS読み込み制御（有料）",
        "priority": "MEDIUM",
    },
    "asset-cleanup": {
        "name": "Asset CleanUp",
        "purpose": "FIX-013: CSS/JS 読み込み制御（無料）",
        "priority": "MEDIUM",
    },
    "query-monitor": {
        "name": "Query Monitor",
        "purpose": "FIX-001: DBクエリのプロファイリング（診断用・本番では無効化推奨）",
        "priority": "DIAGNOSTIC",
    },
}


class WordPressPluginManager:
    """
    WP REST API /wp/v2/plugins を使ったプラグイン管理クライアント。

    WP 5.5+ が必要。管理者権限のアプリパスワードが必要。
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
        self.plugins_endpoint = f"{url}/wp-json/wp/v2/plugins"

        self.session = requests.Session()
        self.session.auth = (username, app_password)
        self.session.headers.update({
            "Content-Type": "application/json",
            "User-Agent": "WPTechSEOAudit/1.0 (Plugin Manager)",
        })

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

    def _post(self, url: str, payload: dict) -> requests.Response:
        try:
            r = self.session.post(url, json=payload, timeout=60)
            r.raise_for_status()
            return r
        except requests.exceptions.Timeout:
            raise RuntimeError(f"Request timed out (plugin install can be slow): {url}")
        except requests.exceptions.HTTPError as e:
            status = e.response.status_code if e.response is not None else "unknown"
            body = e.response.text[:500] if e.response is not None else ""
            raise RuntimeError(f"HTTP {status} for POST {url}: {body}") from e

    def _put(self, url: str, payload: dict) -> requests.Response:
        try:
            r = self.session.put(url, json=payload, timeout=30)
            r.raise_for_status()
            return r
        except requests.exceptions.Timeout:
            raise RuntimeError(f"Request timed out: {url}")
        except requests.exceptions.HTTPError as e:
            status = e.response.status_code if e.response is not None else "unknown"
            body = e.response.text[:300] if e.response is not None else ""
            raise RuntimeError(f"HTTP {status} for PUT {url}: {body}") from e

    # ------------------------------------------------------------------
    # Public methods
    # ------------------------------------------------------------------

    def list_plugins(self) -> list[dict]:
        """
        インストール済みプラグインの一覧を取得する。

        Returns:
            List of dicts: name, plugin (slug/file), version, status, author
        """
        try:
            r = self._get(self.plugins_endpoint)
            raw = r.json()
        except RuntimeError as e:
            raise RuntimeError(
                f"Plugin API unavailable. Requires WP 5.5+ and administrator role: {e}"
            ) from e

        plugins = []
        for p in raw:
            plugins.append({
                "name": p.get("name", ""),
                "plugin": p.get("plugin", ""),
                "version": p.get("version", ""),
                "status": p.get("status", ""),
                "author": p.get("author", ""),
                "description": p.get("description", {}).get("raw", "")[:100],
            })
        return plugins

    def check_perf_plugins(self) -> dict:
        """
        パフォーマンス改善に推奨するプラグインの導入状況を確認する。

        Returns:
            Dict with installed, missing, diagnostic plugins.
        """
        installed_plugins = self.list_plugins()
        installed_slugs = {
            p["plugin"].split("/")[0].lower() for p in installed_plugins
        }
        installed_names = {p["name"].lower() for p in installed_plugins}

        result = {
            "installed": [],
            "missing": [],
            "diagnostic": [],
        }

        for slug, info in _PERF_PLUGINS.items():
            is_installed = (
                slug in installed_slugs
                or info["name"].lower() in installed_names
            )
            entry = {
                "slug": slug,
                "name": info["name"],
                "purpose": info["purpose"],
                "priority": info["priority"],
                "installed": is_installed,
            }

            if info["priority"] == "DIAGNOSTIC":
                result["diagnostic"].append(entry)
            elif is_installed:
                # Get status from installed plugins
                for p in installed_plugins:
                    if p["plugin"].split("/")[0].lower() == slug or p["name"].lower() == info["name"].lower():
                        entry["status"] = p["status"]
                        break
                result["installed"].append(entry)
            else:
                result["missing"].append(entry)

        return result

    def activate_plugin(self, plugin_file: str) -> dict:
        """
        インストール済みプラグインを有効化する。

        Args:
            plugin_file: プラグインファイルパス（例: redis-cache/redis-cache.php）

        Returns:
            dict with plugin, status, dry_run
        """
        prefix = "[DRY RUN]" if self.dry_run else "[APPLIED]"
        print(f"{prefix} activate plugin: {plugin_file}")

        result = {"plugin": plugin_file, "dry_run": self.dry_run}

        if self.dry_run:
            result["status"] = "dry_run"
            return result

        # URL-encode the plugin file path
        import urllib.parse
        encoded = urllib.parse.quote(plugin_file, safe="")
        endpoint = f"{self.plugins_endpoint}/{encoded}"

        try:
            r = self._put(endpoint, {"status": "active"})
            data = r.json()
            result["status"] = data.get("status", "unknown")
            print(f"  → status: {result['status']}")
        except RuntimeError as e:
            result["status"] = "error"
            result["error"] = str(e)
            print(f"  ERROR: {e}")

        return result

    def install_and_activate_plugin(self, slug: str) -> dict:
        """
        WordPress.org からプラグインをインストールして有効化する。

        Args:
            slug: WordPress.org プラグインスラッグ（例: redis-cache）

        Returns:
            dict with slug, status, dry_run
        """
        prefix = "[DRY RUN]" if self.dry_run else "[APPLIED]"
        print(f"{prefix} install & activate: {slug}")

        result = {"slug": slug, "dry_run": self.dry_run}

        if self.dry_run:
            result["status"] = "dry_run"
            return result

        try:
            r = self._post(self.plugins_endpoint, {
                "slug": slug,
                "status": "active",
            })
            data = r.json()
            result["status"] = data.get("status", "unknown")
            result["plugin"] = data.get("plugin", "")
            result["version"] = data.get("version", "")
            print(f"  → installed: {result.get('plugin')} v{result.get('version')} | status: {result['status']}")
        except RuntimeError as e:
            result["status"] = "error"
            result["error"] = str(e)
            print(f"  ERROR: {e}")
            if "403" in str(e):
                print("  → Tip: プラグインインストールには管理者権限が必要です。")
            elif "file_system" in str(e).lower():
                print("  → Tip: サーバーのファイルシステム書き込み権限を確認してください。")

        return result


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="WordPress Plugin Manager (wp-techseo-audit)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # インストール済みプラグイン一覧
  python wp_plugin_manager.py --client naimono --action list

  # パフォーマンス関連プラグインのステータス確認
  python wp_plugin_manager.py --client naimono --action check-perf

  # プラグインを有効化（ドライラン）
  python wp_plugin_manager.py --client naimono --action activate --plugin redis-cache/redis-cache.php

  # プラグインを有効化（実行）
  python wp_plugin_manager.py --client naimono --action activate --plugin redis-cache/redis-cache.php --execute

  # WordPress.orgからインストールして有効化
  python wp_plugin_manager.py --client naimono --action install --slug redis-cache --execute
""",
    )

    parser.add_argument("--client", required=True, help="Client ID (e.g. naimono)")
    parser.add_argument("--execute", action="store_true", default=False,
                        help="Actually apply changes. Default is dry-run.")
    parser.add_argument("--action",
                        choices=["list", "check-perf", "activate", "install"],
                        required=True,
                        help="Action to perform.")
    parser.add_argument("--plugin", default=None,
                        help="Plugin file path for --action activate (e.g. redis-cache/redis-cache.php)")
    parser.add_argument("--slug", default=None,
                        help="WordPress.org plugin slug for --action install (e.g. redis-cache)")

    args = parser.parse_args()

    dry_run = not args.execute
    try:
        manager = WordPressPluginManager(client_id=args.client, dry_run=dry_run)
    except (ValueError, FileNotFoundError) as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        sys.exit(1)

    mode_label = "DRY RUN" if dry_run else "EXECUTE"
    print(f"\nClient: {args.client} | Mode: {mode_label}\n")

    try:
        if args.action == "list":
            result = manager.list_plugins()
            print(f"Installed plugins ({len(result)}):\n")
            for p in result:
                status_icon = "✓" if p["status"] == "active" else "○"
                print(f"  {status_icon} [{p['status']:8}] {p['name']} v{p['version']}  ({p['plugin']})")
            print()
            sys.exit(0)

        elif args.action == "check-perf":
            result = manager.check_perf_plugins()
            print("=== パフォーマンス関連プラグイン チェック結果 ===\n")

            if result["installed"]:
                print("【導入済み】")
                for p in result["installed"]:
                    print(f"  ✓ {p['name']} [{p.get('status', '?')}]")
                    print(f"    └ {p['purpose']}")
                print()

            if result["missing"]:
                print("【未導入（推奨）】")
                for p in result["missing"]:
                    print(f"  ✗ {p['name']} [{p['priority']}]")
                    print(f"    └ {p['purpose']}")
                    print(f"    └ インストール: python wp_plugin_manager.py --client {args.client} --action install --slug {p['slug']} --execute")
                print()

            if result["diagnostic"]:
                print("【診断ツール】")
                for p in result["diagnostic"]:
                    status_str = "導入済み" if p["installed"] else "未導入"
                    print(f"  {'✓' if p['installed'] else '○'} {p['name']} ({status_str})")
                    print(f"    └ {p['purpose']}")
                print()

            sys.exit(0)

        elif args.action == "activate":
            if not args.plugin:
                parser.error("--action activate requires --plugin (e.g. redis-cache/redis-cache.php)")
            result = manager.activate_plugin(args.plugin)

        elif args.action == "install":
            if not args.slug:
                parser.error("--action install requires --slug (e.g. redis-cache)")
            result = manager.install_and_activate_plugin(args.slug)

        else:
            parser.error(f"Unknown action: {args.action}")
            return

        print(json.dumps(result, ensure_ascii=False, indent=2))

    except RuntimeError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
