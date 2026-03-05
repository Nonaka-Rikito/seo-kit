"""
lighthouse_runner.py
Lighthouse CLI wrapper for running performance audits on WordPress sites.

Usage:
    python lighthouse_runner.py https://example.com --output ./reports/ --device mobile
    python lighthouse_runner.py --batch urls.txt --output ./reports/
"""

import subprocess
import json
import os
import sys
import argparse
from pathlib import Path
from datetime import datetime


class LighthouseRunner:
    """Lighthouse CLI wrapper for WordPress performance audits."""

    # CWV thresholds (in base units: seconds for time, raw for CLS)
    DEFAULT_THRESHOLDS = {
        "lcp": {"good": 2.5, "needs_improvement": 4.0, "unit": "s"},
        "fid": {"good": 0.1, "needs_improvement": 0.3, "unit": "s"},    # stored in seconds
        "cls": {"good": 0.1, "needs_improvement": 0.25, "unit": ""},
        "fcp": {"good": 1.8, "needs_improvement": 3.0, "unit": "s"},
        "ttfb": {"good": 0.8, "needs_improvement": 1.8, "unit": "s"},
        "tbt": {"good": 0.2, "needs_improvement": 0.6, "unit": "s"},    # stored in seconds
        "si": {"good": 3.4, "needs_improvement": 5.8, "unit": "s"},
    }

    # Lighthouse audit result key names for each metric
    METRIC_KEYS = {
        "lcp": "largest-contentful-paint",
        "fid": "max-potential-fid",
        "cls": "cumulative-layout-shift",
        "fcp": "first-contentful-paint",
        "ttfb": "server-response-time",
        "tbt": "total-blocking-time",
        "si": "speed-index",
    }

    # Display units for human-readable output
    DISPLAY_UNITS = {
        "lcp": "s",
        "fid": "ms",
        "cls": "",
        "fcp": "s",
        "ttfb": "s",
        "tbt": "ms",
        "si": "s",
    }

    def __init__(self, chrome_path: str = None):
        """
        Initialize LighthouseRunner.

        Args:
            chrome_path: Path to Chrome executable. Auto-detected on Windows if not provided.
        """
        self.chrome_path = chrome_path or self.find_chrome()

    def find_chrome(self) -> str:
        """
        Auto-detect Chrome executable on Windows.

        Returns:
            str: Path to chrome.exe

        Raises:
            FileNotFoundError: If Chrome is not found in common locations.
        """
        candidate_paths = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        ]

        local_app_data = os.environ.get("LOCALAPPDATA", "")
        if local_app_data:
            candidate_paths.append(
                os.path.join(local_app_data, r"Google\Chrome\Application\chrome.exe")
            )

        for path in candidate_paths:
            if Path(path).exists():
                return path

        raise FileNotFoundError(
            "Chrome executable not found. Please install Google Chrome or provide "
            "the chrome_path argument.\nChecked paths:\n" +
            "\n".join(f"  - {p}" for p in candidate_paths)
        )

    def find_lighthouse(self) -> str:
        """
        Find Lighthouse CLI executable.

        Returns:
            str: 'npx' if available via npx, 'lighthouse' if globally installed.

        Raises:
            FileNotFoundError: If Lighthouse is not installed.
        """
        shell = sys.platform == "win32"

        # Try npx lighthouse first
        try:
            result = subprocess.run(
                ["npx", "lighthouse", "--version"],
                capture_output=True,
                text=True,
                timeout=30,
                shell=shell,
            )
            if result.returncode == 0:
                return "npx"
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            pass

        # Try global lighthouse
        try:
            result = subprocess.run(
                ["lighthouse", "--version"],
                capture_output=True,
                text=True,
                timeout=30,
                shell=shell,
            )
            if result.returncode == 0:
                return "lighthouse"
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            pass

        raise FileNotFoundError(
            "Lighthouse CLI is not installed or not found.\n"
            "Install it with: npm install -g lighthouse"
        )

    def run_audit(
        self,
        url: str,
        output_dir: str = None,
        categories: list = None,
        device: str = "mobile",
    ) -> dict:
        """
        Run a Lighthouse audit for a single URL.

        Args:
            url: URL to audit.
            output_dir: Directory to save JSON output. Defaults to temp directory.
            categories: List of categories to audit. Defaults to all four.
            device: 'mobile' (default) or 'desktop'.

        Returns:
            dict: Full Lighthouse result dictionary.

        Raises:
            subprocess.TimeoutExpired: If audit takes longer than 120 seconds.
            RuntimeError: If Lighthouse exits with a non-zero status.
        """
        if categories is None:
            categories = ["performance", "accessibility", "best-practices", "seo"]

        # Prepare output path
        if output_dir is None:
            output_dir = Path.cwd() / "lighthouse_reports"
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_url = url.replace("https://", "").replace("http://", "").replace("/", "_").strip("_")
        output_filename = f"{safe_url}_{device}_{timestamp}.json"
        output_path = output_dir / output_filename

        categories_str = ",".join(categories)
        chrome_flags = "--headless --no-sandbox --disable-gpu"

        shell = sys.platform == "win32"

        # Build command
        cmd = [
            "npx",
            "lighthouse",
            url,
            "--output=json",
            f"--output-path={str(output_path)}",
            f"--chrome-flags={chrome_flags}",
            f"--chrome-path={self.chrome_path}",
            f"--only-categories={categories_str}",
            "--quiet",
        ]

        if device == "desktop":
            cmd.append("--preset=desktop")

        print(f"  Running Lighthouse for {url} [{device}]...", file=sys.stderr)

        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,
                shell=shell,
            )
        except subprocess.TimeoutExpired:
            print(f"  [TIMEOUT] Audit timed out after 120s for {url}", file=sys.stderr)
            raise

        if proc.returncode != 0:
            stderr_msg = proc.stderr.strip() if proc.stderr else "(no stderr)"
            raise RuntimeError(
                f"Lighthouse exited with code {proc.returncode} for {url}.\n"
                f"stderr: {stderr_msg}"
            )

        # Lighthouse may append .report.json to the output path
        result_path = output_path
        if not result_path.exists():
            alt_path = output_path.with_suffix(".report.json")
            if alt_path.exists():
                result_path = alt_path
            else:
                # Search for the most recent JSON in the output directory
                candidates = sorted(
                    output_dir.glob("*.json"),
                    key=lambda p: p.stat().st_mtime,
                    reverse=True,
                )
                if candidates:
                    result_path = candidates[0]
                else:
                    raise FileNotFoundError(
                        f"Lighthouse output file not found. Expected: {output_path}"
                    )

        try:
            with open(result_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        finally:
            # Clean up the output file after parsing
            try:
                result_path.unlink()
            except OSError:
                pass

        return data

    def run_batch(
        self,
        urls: list,
        output_dir: str,
        device: str = "mobile",
        max_concurrent: int = 1,
    ) -> list:
        """
        Run Lighthouse audits for a list of URLs sequentially.

        Args:
            urls: List of URLs to audit.
            output_dir: Directory to save reports.
            device: 'mobile' or 'desktop'.
            max_concurrent: Kept for API compatibility. Lighthouse runs sequentially.

        Returns:
            list[dict]: List of CWV result dicts from extract_cwv().
        """
        results = []
        total = len(urls)

        for i, url in enumerate(urls, start=1):
            url = url.strip()
            if not url:
                continue

            print(f"[{i}/{total}] Auditing {url}", file=sys.stderr)

            try:
                raw = self.run_audit(url, output_dir=output_dir, device=device)
                cwv = self.extract_cwv(raw)
                cwv["device"] = device
                results.append(cwv)
            except subprocess.TimeoutExpired:
                print(f"  [SKIP] {url} — timed out", file=sys.stderr)
                results.append({"url": url, "device": device, "error": "timeout"})
            except Exception as exc:
                print(f"  [ERROR] {url} — {exc}", file=sys.stderr)
                results.append({"url": url, "device": device, "error": str(exc)})

        return results

    def _get_rating(self, metric_key: str, value_seconds: float) -> str:
        """Return rating string for a metric value (value in seconds)."""
        thresholds = self.DEFAULT_THRESHOLDS.get(metric_key, {})
        good = thresholds.get("good", float("inf"))
        needs_improvement = thresholds.get("needs_improvement", float("inf"))

        if value_seconds <= good:
            return "good"
        elif value_seconds <= needs_improvement:
            return "needs_improvement"
        else:
            return "poor"

    def _format_display_value(self, metric_key: str, value_seconds: float) -> tuple:
        """
        Convert internal seconds value to display value and unit.

        Returns:
            (display_value: float, unit: str)
        """
        display_unit = self.DISPLAY_UNITS.get(metric_key, "s")
        if display_unit == "ms":
            return round(value_seconds * 1000, 1), "ms"
        elif display_unit == "s":
            return round(value_seconds, 3), "s"
        else:
            return round(value_seconds, 4), ""

    def extract_cwv(self, result: dict) -> dict:
        """
        Extract Core Web Vitals and scores from a Lighthouse result dict.

        Args:
            result: Full Lighthouse JSON result.

        Returns:
            dict: Structured CWV data with scores, metrics, opportunities, diagnostics.
        """
        url = result.get("finalUrl") or result.get("requestedUrl", "")
        device = result.get("configSettings", {}).get("formFactor", "mobile")

        # Extract category scores (0-1 scale → 0-100)
        categories = result.get("categories", {})
        scores = {
            "performance": int((categories.get("performance", {}).get("score") or 0) * 100),
            "accessibility": int((categories.get("accessibility", {}).get("score") or 0) * 100),
            "best_practices": int(
                (categories.get("best-practices", {}).get("score") or 0) * 100
            ),
            "seo": int((categories.get("seo", {}).get("score") or 0) * 100),
        }

        audits = result.get("audits", {})

        # Extract CWV metrics
        cwv = {}
        for short_key, audit_key in self.METRIC_KEYS.items():
            audit = audits.get(audit_key, {})
            # Lighthouse stores times in milliseconds internally; numericValue is in ms
            raw_numeric = audit.get("numericValue")

            if raw_numeric is None:
                cwv[short_key] = {"value": None, "unit": self.DISPLAY_UNITS[short_key], "rating": "n/a"}
                continue

            # Convert to seconds for internal rating logic
            # CLS is unitless; others are in ms from Lighthouse
            if short_key == "cls":
                value_seconds = raw_numeric  # CLS is already a ratio
            else:
                value_seconds = raw_numeric / 1000.0  # ms → s

            display_value, display_unit = self._format_display_value(short_key, value_seconds)
            rating = self._get_rating(short_key, value_seconds)

            cwv[short_key] = {
                "value": display_value,
                "unit": display_unit,
                "rating": rating,
            }

        # Extract opportunities (items with potential savings)
        opportunities = []
        for audit_id, audit in audits.items():
            if audit.get("details", {}).get("type") == "opportunity":
                savings_ms = audit.get("details", {}).get("overallSavingsMs")
                if savings_ms and savings_ms > 0:
                    opportunities.append(
                        {
                            "id": audit_id,
                            "title": audit.get("title", ""),
                            "estimated_savings_ms": int(savings_ms),
                        }
                    )

        opportunities.sort(key=lambda x: x["estimated_savings_ms"], reverse=True)

        # Extract diagnostics (table-type audits with score < 1)
        diagnostics = []
        for audit_id, audit in audits.items():
            detail_type = audit.get("details", {}).get("type")
            score = audit.get("score")
            if detail_type in ("table", "list") and score is not None and score < 1:
                description = audit.get("description", "")
                display_value_str = audit.get("displayValue", "")
                diagnostics.append(
                    {
                        "id": audit_id,
                        "title": audit.get("title", ""),
                        "details": display_value_str or description[:120],
                    }
                )

        return {
            "url": url,
            "device": device,
            "scores": scores,
            "cwv": cwv,
            "opportunities": opportunities,
            "diagnostics": diagnostics,
        }

    def detect_issues(self, cwv_data: dict, thresholds: dict = None) -> list:
        """
        Detect performance issues by comparing CWV values against thresholds.

        Args:
            cwv_data: Output from extract_cwv().
            thresholds: Optional custom thresholds dict. Falls back to DEFAULT_THRESHOLDS.

        Returns:
            list[dict]: List of issue dicts with code, severity, url, issue, current, target, recommendation.
        """
        if thresholds is None:
            # Try loading from audit-rules.json next to this script
            rules_path = Path(__file__).parent / "audit-rules.json"
            if rules_path.exists():
                try:
                    with open(rules_path, "r", encoding="utf-8") as f:
                        rules = json.load(f)
                        thresholds = rules.get("thresholds", self.DEFAULT_THRESHOLDS)
                except (json.JSONDecodeError, OSError):
                    thresholds = self.DEFAULT_THRESHOLDS
            else:
                thresholds = self.DEFAULT_THRESHOLDS

        issues = []
        url = cwv_data.get("url", "")
        cwv = cwv_data.get("cwv", {})
        scores = cwv_data.get("scores", {})

        # Check overall performance score
        perf_score = scores.get("performance", 100)
        if perf_score < 50:
            issues.append(
                {
                    "code": "PERF",
                    "severity": "CRITICAL",
                    "url": url,
                    "issue": "Performance score is critically low",
                    "current": f"{perf_score}/100",
                    "target": ">=90/100",
                    "recommendation": "Conduct a full performance audit and address top opportunities.",
                }
            )
        elif perf_score < 70:
            issues.append(
                {
                    "code": "PERF",
                    "severity": "HIGH",
                    "url": url,
                    "issue": "Performance score is below acceptable threshold",
                    "current": f"{perf_score}/100",
                    "target": ">=90/100",
                    "recommendation": "Prioritize LCP, TBT, and CLS improvements.",
                }
            )
        elif perf_score < 90:
            issues.append(
                {
                    "code": "PERF",
                    "severity": "MEDIUM",
                    "url": url,
                    "issue": "Performance score has room for improvement",
                    "current": f"{perf_score}/100",
                    "target": ">=90/100",
                    "recommendation": "Address remaining opportunities for score improvement.",
                }
            )

        # Metric-specific issue definitions
        metric_meta = {
            "lcp": {
                "code": "PERF",
                "name": "Largest Contentful Paint (LCP)",
                "recommendation": "Optimize server response times, remove render-blocking resources, and optimize images.",
            },
            "fid": {
                "code": "PERF",
                "name": "First Input Delay (FID) / Max Potential FID",
                "recommendation": "Reduce JavaScript execution time and break up long tasks.",
            },
            "cls": {
                "code": "MOBL",
                "name": "Cumulative Layout Shift (CLS)",
                "recommendation": "Set explicit dimensions on images/videos and avoid inserting content above existing content.",
            },
            "fcp": {
                "code": "PERF",
                "name": "First Contentful Paint (FCP)",
                "recommendation": "Eliminate render-blocking resources and reduce server response times.",
            },
            "ttfb": {
                "code": "PERF",
                "name": "Time to First Byte (TTFB)",
                "recommendation": "Optimize server performance, use a CDN, and implement server-side caching.",
            },
            "tbt": {
                "code": "PERF",
                "name": "Total Blocking Time (TBT)",
                "recommendation": "Minimize main-thread work by splitting long tasks and deferring non-critical JavaScript.",
            },
            "si": {
                "code": "MOBL",
                "name": "Speed Index (SI)",
                "recommendation": "Optimize critical rendering path and reduce visual content load times.",
            },
        }

        for metric_key, metric_data in cwv.items():
            rating = metric_data.get("rating", "good")
            value = metric_data.get("value")
            unit = metric_data.get("unit", "")
            meta = metric_meta.get(metric_key, {})

            if rating == "n/a" or value is None:
                continue

            # Determine good threshold for target display
            th = thresholds.get(metric_key, self.DEFAULT_THRESHOLDS.get(metric_key, {}))
            good_val = th.get("good", "")
            th_unit = self.DISPLAY_UNITS.get(metric_key, "s")
            if th_unit == "ms" and isinstance(good_val, (int, float)):
                good_display = f"{good_val * 1000:.0f}ms"
            elif th_unit == "s" and isinstance(good_val, (int, float)):
                good_display = f"{good_val}s"
            else:
                good_display = str(good_val)

            if rating == "poor":
                severity = "CRITICAL"
            elif rating == "needs_improvement":
                severity = "HIGH"
            else:
                continue  # No issue for "good"

            issues.append(
                {
                    "code": meta.get("code", "PERF"),
                    "severity": severity,
                    "url": url,
                    "issue": f"{meta.get('name', metric_key)} is {rating.replace('_', ' ')}",
                    "current": f"{value}{unit}",
                    "target": f"<{good_display}",
                    "recommendation": meta.get("recommendation", ""),
                }
            )

        return issues

    def format_summary(self, results: list) -> str:
        """
        Format batch audit results as a Markdown table.

        Args:
            results: List of dicts from extract_cwv() or run_batch().

        Returns:
            str: Markdown table string.
        """
        header = "| URL | Performance | LCP | FID | CLS | Issues |"
        separator = "|-----|------------|-----|-----|-----|--------|"
        rows = [header, separator]

        for r in results:
            if "error" in r:
                rows.append(
                    f"| {r.get('url', '')} | ERROR | — | — | — | {r['error']} |"
                )
                continue

            url = r.get("url", "")
            scores = r.get("scores", {})
            cwv = r.get("cwv", {})

            perf = scores.get("performance", "—")

            lcp = cwv.get("lcp", {})
            lcp_str = f"{lcp.get('value', '—')}{lcp.get('unit', '')} ({lcp.get('rating', '—')})" if lcp else "—"

            fid = cwv.get("fid", {})
            fid_str = f"{fid.get('value', '—')}{fid.get('unit', '')} ({fid.get('rating', '—')})" if fid else "—"

            cls = cwv.get("cls", {})
            cls_str = f"{cls.get('value', '—')} ({cls.get('rating', '—')})" if cls else "—"

            issues = self.detect_issues(r)
            issue_count = len(issues)
            critical = sum(1 for i in issues if i["severity"] == "CRITICAL")
            issue_summary = f"{issue_count} ({critical} critical)" if issue_count > 0 else "0"

            rows.append(f"| {url} | {perf} | {lcp_str} | {fid_str} | {cls_str} | {issue_summary} |")

        return "\n".join(rows)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Lighthouse CLI wrapper for WordPress performance audits.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python lighthouse_runner.py https://example.com --output ./reports/ --device mobile
  python lighthouse_runner.py --batch urls.txt --output ./reports/ --device desktop
        """,
    )

    parser.add_argument(
        "url",
        nargs="?",
        help="URL to audit (omit when using --batch).",
    )
    parser.add_argument(
        "--batch",
        metavar="URLS_FILE",
        help="Path to a text file containing one URL per line.",
    )
    parser.add_argument(
        "--output",
        default="./lighthouse_reports",
        help="Directory to save reports (default: ./lighthouse_reports).",
    )
    parser.add_argument(
        "--device",
        choices=["mobile", "desktop"],
        default="mobile",
        help="Emulation device (default: mobile).",
    )
    parser.add_argument(
        "--chrome-path",
        dest="chrome_path",
        default=None,
        help="Path to Chrome executable (auto-detected if not provided).",
    )
    parser.add_argument(
        "--categories",
        default="performance,accessibility,best-practices,seo",
        help="Comma-separated list of categories to audit.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Output results as JSON to stdout.",
    )

    args = parser.parse_args()

    if not args.url and not args.batch:
        parser.error("Provide a URL positional argument or use --batch.")

    try:
        runner = LighthouseRunner(chrome_path=args.chrome_path)
    except FileNotFoundError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        sys.exit(1)

    categories = [c.strip() for c in args.categories.split(",") if c.strip()]

    # --- Batch mode ---
    if args.batch:
        batch_file = Path(args.batch)
        if not batch_file.exists():
            print(f"[ERROR] Batch file not found: {batch_file}", file=sys.stderr)
            sys.exit(1)

        urls = [line.strip() for line in batch_file.read_text(encoding="utf-8").splitlines() if line.strip()]

        if not urls:
            print("[ERROR] Batch file is empty.", file=sys.stderr)
            sys.exit(1)

        print(f"Starting batch audit of {len(urls)} URL(s) [{args.device}]...", file=sys.stderr)
        results = runner.run_batch(urls, output_dir=args.output, device=args.device)

        if args.json_output:
            print(json.dumps(results, ensure_ascii=False, indent=2))
        else:
            print("\n" + runner.format_summary(results))

        # Print issue summary to stderr
        all_issues = []
        for r in results:
            if "error" not in r:
                all_issues.extend(runner.detect_issues(r))
        if all_issues:
            print(f"\n[ISSUES FOUND: {len(all_issues)}]", file=sys.stderr)
            for issue in all_issues:
                print(
                    f"  [{issue['severity']}] {issue['code']} — {issue['issue']} "
                    f"(current: {issue['current']}, target: {issue['target']})",
                    file=sys.stderr,
                )

        sys.exit(0)

    # --- Single URL mode ---
    print(f"Auditing {args.url} [{args.device}]...", file=sys.stderr)

    try:
        raw_result = runner.run_audit(
            url=args.url,
            output_dir=args.output,
            categories=categories,
            device=args.device,
        )
    except subprocess.TimeoutExpired:
        print("[ERROR] Audit timed out.", file=sys.stderr)
        sys.exit(1)
    except (RuntimeError, FileNotFoundError) as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        sys.exit(1)

    cwv = runner.extract_cwv(raw_result)
    issues = runner.detect_issues(cwv)

    if args.json_output:
        output = {"cwv": cwv, "issues": issues}
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        # Human-readable summary
        print(f"\n=== Lighthouse Audit: {cwv['url']} [{cwv['device']}] ===", file=sys.stderr)
        scores = cwv.get("scores", {})
        print(f"  Performance:    {scores.get('performance', '—')}/100", file=sys.stderr)
        print(f"  Accessibility:  {scores.get('accessibility', '—')}/100", file=sys.stderr)
        print(f"  Best Practices: {scores.get('best_practices', '—')}/100", file=sys.stderr)
        print(f"  SEO:            {scores.get('seo', '—')}/100", file=sys.stderr)

        print("\n  Core Web Vitals:", file=sys.stderr)
        for key, data in cwv.get("cwv", {}).items():
            val = data.get("value", "—")
            unit = data.get("unit", "")
            rating = data.get("rating", "—")
            print(f"    {key.upper():6s}: {val}{unit} ({rating})", file=sys.stderr)

        if cwv.get("opportunities"):
            print("\n  Top Opportunities:", file=sys.stderr)
            for opp in cwv["opportunities"][:5]:
                print(
                    f"    - {opp['title']} (~{opp['estimated_savings_ms']}ms savings)",
                    file=sys.stderr,
                )

        if issues:
            print(f"\n  Issues ({len(issues)}):", file=sys.stderr)
            for issue in issues:
                print(
                    f"    [{issue['severity']}] {issue['issue']} "
                    f"(current: {issue['current']}, target: {issue['target']})",
                    file=sys.stderr,
                )
        else:
            print("\n  No performance issues detected.", file=sys.stderr)

        # Output JSON to stdout for piping
        print(json.dumps({"cwv": cwv, "issues": issues}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
