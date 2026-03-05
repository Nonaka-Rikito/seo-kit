"""
structured_data_validator.py
WordPress Technical SEO Audit — Structured Data Validator

Fetches pages, extracts JSON-LD and Microdata, validates against schema.org
types, and generates corrected markup for any issues found.

Usage:
    python structured_data_validator.py https://example.com/page
    python structured_data_validator.py --batch urls.txt --output ./reports/
"""

import argparse
import json
import re
import sys
from typing import Any, Optional
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

USER_AGENT = "WPTechSEOAudit/1.0"
REQUEST_TIMEOUT = 30

KNOWN_SCHEMA_TYPES = {
    "Article",
    "BlogPosting",
    "NewsArticle",
    "FAQPage",
    "HowTo",
    "BreadcrumbList",
    "Organization",
    "LocalBusiness",
    "Product",
    "WebPage",
    "WebSite",
    "Person",
    "Event",
    "Recipe",
    "Review",
    "ItemList",
}

SEVERITY_HIGH = "HIGH"
SEVERITY_MEDIUM = "MEDIUM"
SEVERITY_LOW = "LOW"

ISSUE_CODE = "SCHM"


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def _get_type(data: dict) -> Optional[str]:
    """Return the first @type string from a schema dict, or None."""
    raw = data.get("@type")
    if raw is None:
        return None
    if isinstance(raw, list):
        return raw[0] if raw else None
    return str(raw)


def _type_matches(data: dict, *types: str) -> bool:
    """Return True if the schema's @type matches any of the given type names."""
    schema_type = _get_type(data)
    if schema_type is None:
        return False
    return schema_type in types


def _nested_get(data: dict, *keys) -> Any:
    """
    Safely traverse nested dicts/lists.
    _nested_get(data, "author", "name") → data["author"]["name"]
    """
    current = data
    for key in keys:
        if isinstance(current, dict):
            current = current.get(key)
        elif isinstance(current, list) and isinstance(key, int):
            try:
                current = current[key]
            except IndexError:
                return None
        else:
            return None
    return current


def _score_from_errors(errors: list, warnings: list) -> int:
    """
    Compute a 0-100 quality score.
    Each error deducts 20 points; each warning deducts 5 points.
    """
    score = 100 - (len(errors) * 20) - (len(warnings) * 5)
    return max(0, score)


# ---------------------------------------------------------------------------
# Main class
# ---------------------------------------------------------------------------

class StructuredDataValidator:
    """
    Validates structured data (JSON-LD and Microdata) found on web pages.
    Supports Article, FAQPage, HowTo, BreadcrumbList, Organization,
    Product, and WebPage schema types.
    """

    def __init__(self) -> None:
        self._session = requests.Session()
        self._session.headers.update({"User-Agent": USER_AGENT})

    # ------------------------------------------------------------------
    # 1. Fetch & Extract
    # ------------------------------------------------------------------

    def fetch_and_extract(self, url: str) -> dict:
        """
        Fetch the URL and extract all structured data found on the page.

        Returns
        -------
        {
            "url": str,
            "json_ld": [dict, ...],   # parsed JSON-LD objects (flattened from @graph)
            "microdata": [dict, ...], # extracted Microdata items
            "raw_html_snippet": str,  # first 500 chars of <body> for debugging
        }
        """
        response = self._session.get(url, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "lxml")

        json_ld_items = self._extract_json_ld(soup)
        microdata_items = self._extract_microdata(soup)

        body = soup.find("body")
        raw_snippet = (body.get_text()[:500] if body else "")[:500]

        return {
            "url": url,
            "json_ld": json_ld_items,
            "microdata": microdata_items,
            "raw_html_snippet": raw_snippet,
        }

    def _extract_json_ld(self, soup: BeautifulSoup) -> list:
        """Parse all <script type="application/ld+json"> blocks on the page."""
        items = []
        for tag in soup.find_all("script", type="application/ld+json"):
            raw = (tag.string or "").strip()
            if not raw:
                continue
            try:
                parsed = json.loads(raw)
            except json.JSONDecodeError as exc:
                print(
                    f"[WARNING] Malformed JSON-LD skipped: {exc}",
                    file=sys.stderr,
                )
                continue

            # Flatten @graph arrays (common in WordPress themes like Yoast)
            if isinstance(parsed, dict) and "@graph" in parsed:
                for node in parsed["@graph"]:
                    if isinstance(node, dict):
                        items.append(node)
            elif isinstance(parsed, list):
                for node in parsed:
                    if isinstance(node, dict):
                        items.append(node)
            elif isinstance(parsed, dict):
                items.append(parsed)

        return items

    def _extract_microdata(self, soup: BeautifulSoup) -> list:
        """
        Walk the DOM and extract Microdata items (elements with itemscope).
        Returns a list of dicts, each representing one itemscope block.
        """
        items = []
        for root in soup.find_all(attrs={"itemscope": True}, recursive=True):
            # Only process top-level itemscope elements (not nested ones) to
            # avoid duplicates; nested items will be embedded recursively.
            if root.find_parent(attrs={"itemscope": True}):
                continue
            items.append(self._microdata_node_to_dict(root))
        return items

    def _microdata_node_to_dict(self, element) -> dict:
        """Recursively convert a single Microdata element to a dict."""
        result = {}
        item_type = element.get("itemtype", "")
        if item_type:
            result["@type"] = item_type.split("/")[-1]  # e.g. "Article"

        # Collect direct itemprop children (not deeper nested itemscopes)
        for child in element.find_all(attrs={"itemprop": True}, recursive=True):
            # Skip properties that belong to a nested itemscope
            if child.find_parent(attrs={"itemscope": True}) != element:
                continue

            prop_name = child.get("itemprop")
            if not prop_name:
                continue

            # Value extraction
            if child.get("itemscope") is not None:
                value = self._microdata_node_to_dict(child)
            elif child.name == "a":
                value = child.get("href") or child.get_text(strip=True)
            elif child.name == "img":
                value = child.get("src", "")
            elif child.name in ("meta", "link"):
                value = child.get("content") or child.get("href", "")
            elif child.name == "time":
                value = child.get("datetime") or child.get_text(strip=True)
            else:
                value = child.get_text(strip=True)

            # Support multiple values for the same property
            if prop_name in result:
                existing = result[prop_name]
                if isinstance(existing, list):
                    existing.append(value)
                else:
                    result[prop_name] = [existing, value]
            else:
                result[prop_name] = value

        return result

    # ------------------------------------------------------------------
    # 2. validate_schema (dispatcher)
    # ------------------------------------------------------------------

    def validate_schema(self, schema_data: dict, schema_type: str = None) -> dict:
        """
        Validate a single schema object against known schema.org types.

        Parameters
        ----------
        schema_data : dict
            The parsed schema object (from JSON-LD or Microdata).
        schema_type : str, optional
            Override the @type detection.

        Returns
        -------
        {
            "type": str,
            "valid": bool,
            "errors": [str, ...],
            "warnings": [str, ...],
            "score": int (0-100),
        }
        """
        detected_type = schema_type or _get_type(schema_data) or "Unknown"

        dispatch = {
            "Article": self.validate_article,
            "BlogPosting": self.validate_article,
            "NewsArticle": self.validate_article,
            "FAQPage": self.validate_faq,
            "HowTo": self.validate_howto,
            "BreadcrumbList": self.validate_breadcrumb,
            "Organization": self.validate_organization,
            "LocalBusiness": self.validate_organization,
            "Product": self.validate_product,
            "WebPage": self.validate_webpage,
        }

        validator_fn = dispatch.get(detected_type)
        if validator_fn is None:
            return {
                "type": detected_type,
                "valid": True,
                "errors": [],
                "warnings": [
                    f"No specific validator for type '{detected_type}'. "
                    "Basic presence confirmed."
                ],
                "score": 80,
            }

        result = validator_fn(schema_data)
        result["type"] = detected_type
        return result

    # ------------------------------------------------------------------
    # 3. validate_article
    # ------------------------------------------------------------------

    def validate_article(self, data: dict) -> dict:
        """
        Validate Article / BlogPosting / NewsArticle schema.

        Required  : headline, author.name, datePublished,
                    publisher.name, publisher.logo, image, mainEntityOfPage
        Recommended: dateModified, description, articleBody
        """
        errors: list[str] = []
        warnings: list[str] = []

        # --- Required fields ---
        headline = data.get("headline")
        if not headline:
            errors.append("Missing required field: 'headline'")
        elif len(str(headline)) >= 110:
            warnings.append(
                f"'headline' exceeds 110 characters ({len(str(headline))} chars). "
                "Google may truncate it in rich results."
            )

        author = data.get("author")
        if not author:
            errors.append("Missing required field: 'author'")
        else:
            author_name = (
                author.get("name")
                if isinstance(author, dict)
                else (author[0].get("name") if isinstance(author, list) and author else None)
            )
            if not author_name:
                errors.append("'author' is present but missing 'name' property")
            elif str(author_name).lower() == "admin":
                warnings.append(
                    "'author.name' is set to 'admin'. Use a real author name for better E-E-A-T."
                )

        if not data.get("datePublished"):
            errors.append("Missing required field: 'datePublished'")

        publisher = data.get("publisher")
        if not publisher:
            errors.append("Missing required field: 'publisher'")
        else:
            if isinstance(publisher, dict):
                if not publisher.get("name"):
                    errors.append("'publisher' is missing required 'name'")
                logo = publisher.get("logo")
                if not logo:
                    errors.append("'publisher' is missing required 'logo'")
                elif isinstance(logo, dict) and not logo.get("url"):
                    errors.append("'publisher.logo' is missing 'url'")

        if not data.get("image"):
            errors.append("Missing required field: 'image'")

        if not data.get("mainEntityOfPage"):
            errors.append("Missing required field: 'mainEntityOfPage'")

        # --- Recommended fields ---
        if not data.get("dateModified"):
            warnings.append("Recommended field 'dateModified' is missing")
        if not data.get("description"):
            warnings.append("Recommended field 'description' is missing")
        if not data.get("articleBody"):
            warnings.append("Recommended field 'articleBody' is missing")

        valid = len(errors) == 0
        return {
            "valid": valid,
            "errors": errors,
            "warnings": warnings,
            "score": _score_from_errors(errors, warnings),
        }

    # ------------------------------------------------------------------
    # 4. validate_faq
    # ------------------------------------------------------------------

    def validate_faq(self, data: dict) -> dict:
        """
        Validate FAQPage schema.

        Required  : mainEntity (array of Question with name + acceptedAnswer.text)
        Check     : at least 2 questions, no empty answers
        """
        errors: list[str] = []
        warnings: list[str] = []

        main_entity = data.get("mainEntity")
        if not main_entity:
            errors.append("Missing required field: 'mainEntity'")
        elif not isinstance(main_entity, list):
            errors.append("'mainEntity' must be an array of Question objects")
        else:
            if len(main_entity) < 2:
                warnings.append(
                    f"FAQPage has only {len(main_entity)} question(s). "
                    "Google recommends at least 2 for rich results."
                )
            for idx, q in enumerate(main_entity, start=1):
                if not isinstance(q, dict):
                    errors.append(f"mainEntity[{idx}] is not a valid Question object")
                    continue
                if not q.get("name"):
                    errors.append(f"mainEntity[{idx}] (Question) is missing required 'name'")

                accepted_answer = q.get("acceptedAnswer")
                if not accepted_answer:
                    errors.append(
                        f"mainEntity[{idx}] (Question) is missing required 'acceptedAnswer'"
                    )
                else:
                    answer_text = (
                        accepted_answer.get("text")
                        if isinstance(accepted_answer, dict)
                        else None
                    )
                    if not answer_text:
                        errors.append(
                            f"mainEntity[{idx}].acceptedAnswer is missing required 'text'"
                        )
                    elif str(answer_text).strip() == "":
                        errors.append(
                            f"mainEntity[{idx}].acceptedAnswer.text is empty"
                        )

        valid = len(errors) == 0
        return {
            "valid": valid,
            "errors": errors,
            "warnings": warnings,
            "score": _score_from_errors(errors, warnings),
        }

    # ------------------------------------------------------------------
    # 5. validate_howto
    # ------------------------------------------------------------------

    def validate_howto(self, data: dict) -> dict:
        """
        Validate HowTo schema.

        Required  : name, step (array with name + text or itemListElement)
        Recommended: image, totalTime, estimatedCost
        """
        errors: list[str] = []
        warnings: list[str] = []

        if not data.get("name"):
            errors.append("Missing required field: 'name'")

        steps = data.get("step")
        if not steps:
            errors.append("Missing required field: 'step'")
        elif not isinstance(steps, list):
            errors.append("'step' must be an array of HowToStep objects")
        else:
            for idx, step in enumerate(steps, start=1):
                if not isinstance(step, dict):
                    errors.append(f"step[{idx}] is not a valid HowToStep object")
                    continue
                has_name = bool(step.get("name"))
                has_text = bool(step.get("text"))
                has_item_list = bool(step.get("itemListElement"))
                if not has_name:
                    errors.append(f"step[{idx}] is missing required 'name'")
                if not has_text and not has_item_list:
                    errors.append(
                        f"step[{idx}] must have either 'text' or 'itemListElement'"
                    )

        if not data.get("image"):
            warnings.append("Recommended field 'image' is missing")
        if not data.get("totalTime"):
            warnings.append("Recommended field 'totalTime' is missing (ISO 8601 duration)")
        if not data.get("estimatedCost"):
            warnings.append("Recommended field 'estimatedCost' is missing")

        valid = len(errors) == 0
        return {
            "valid": valid,
            "errors": errors,
            "warnings": warnings,
            "score": _score_from_errors(errors, warnings),
        }

    # ------------------------------------------------------------------
    # 6. validate_breadcrumb
    # ------------------------------------------------------------------

    def validate_breadcrumb(self, data: dict) -> dict:
        """
        Validate BreadcrumbList schema.

        Required  : itemListElement (array of ListItem with position, name, item)
        Check     : positions sequential from 1, last item matches page context
        """
        errors: list[str] = []
        warnings: list[str] = []

        items = data.get("itemListElement")
        if not items:
            errors.append("Missing required field: 'itemListElement'")
        elif not isinstance(items, list):
            errors.append("'itemListElement' must be an array of ListItem objects")
        else:
            expected_position = 1
            for idx, list_item in enumerate(items, start=1):
                if not isinstance(list_item, dict):
                    errors.append(f"itemListElement[{idx}] is not a valid ListItem object")
                    continue

                position = list_item.get("position")
                if position is None:
                    errors.append(
                        f"itemListElement[{idx}] is missing required 'position'"
                    )
                else:
                    try:
                        pos_int = int(position)
                        if pos_int != expected_position:
                            errors.append(
                                f"itemListElement[{idx}] has position {pos_int}, "
                                f"expected {expected_position}. Positions must be sequential from 1."
                            )
                        expected_position = pos_int + 1
                    except (ValueError, TypeError):
                        errors.append(
                            f"itemListElement[{idx}].position is not a valid integer: {position!r}"
                        )

                if not list_item.get("name"):
                    errors.append(f"itemListElement[{idx}] is missing required 'name'")

                # 'item' (URL) is required for all but possibly the last breadcrumb
                if not list_item.get("item") and idx < len(items):
                    errors.append(
                        f"itemListElement[{idx}] is missing required 'item' (URL). "
                        "Only the last breadcrumb may omit 'item'."
                    )

            # Advisory: last breadcrumb should match the current page
            last = items[-1]
            if isinstance(last, dict) and last.get("item"):
                warnings.append(
                    "The last breadcrumb has an 'item' URL. "
                    "Some implementations omit this for the current page — verify it matches the canonical URL."
                )

        valid = len(errors) == 0
        return {
            "valid": valid,
            "errors": errors,
            "warnings": warnings,
            "score": _score_from_errors(errors, warnings),
        }

    # ------------------------------------------------------------------
    # 7. validate_organization
    # ------------------------------------------------------------------

    def validate_organization(self, data: dict) -> dict:
        """
        Validate Organization / LocalBusiness schema.

        Required  : name, url
        Recommended: logo, contactPoint, sameAs, address
        """
        errors: list[str] = []
        warnings: list[str] = []

        if not data.get("name"):
            errors.append("Missing required field: 'name'")
        if not data.get("url"):
            errors.append("Missing required field: 'url'")

        if not data.get("logo"):
            warnings.append("Recommended field 'logo' is missing")
        if not data.get("contactPoint"):
            warnings.append("Recommended field 'contactPoint' is missing")
        if not data.get("sameAs"):
            warnings.append("Recommended field 'sameAs' (social profiles list) is missing")
        if not data.get("address"):
            warnings.append("Recommended field 'address' is missing")

        valid = len(errors) == 0
        return {
            "valid": valid,
            "errors": errors,
            "warnings": warnings,
            "score": _score_from_errors(errors, warnings),
        }

    # ------------------------------------------------------------------
    # 8. validate_product
    # ------------------------------------------------------------------

    def validate_product(self, data: dict) -> dict:
        """
        Validate Product schema.

        Required  : name
        Recommended: image, description, offers (price, priceCurrency, availability)
        """
        errors: list[str] = []
        warnings: list[str] = []

        if not data.get("name"):
            errors.append("Missing required field: 'name'")

        if not data.get("image"):
            warnings.append("Recommended field 'image' is missing")
        if not data.get("description"):
            warnings.append("Recommended field 'description' is missing")

        offers = data.get("offers")
        if not offers:
            warnings.append("Recommended field 'offers' is missing")
        else:
            offer_obj = offers if isinstance(offers, dict) else (offers[0] if isinstance(offers, list) and offers else None)
            if offer_obj:
                if not offer_obj.get("price") and not offer_obj.get("priceSpecification"):
                    warnings.append("'offers' is missing recommended 'price'")
                if not offer_obj.get("priceCurrency"):
                    warnings.append("'offers' is missing recommended 'priceCurrency'")
                if not offer_obj.get("availability"):
                    warnings.append("'offers' is missing recommended 'availability'")

        valid = len(errors) == 0
        return {
            "valid": valid,
            "errors": errors,
            "warnings": warnings,
            "score": _score_from_errors(errors, warnings),
        }

    # ------------------------------------------------------------------
    # 9. validate_webpage
    # ------------------------------------------------------------------

    def validate_webpage(self, data: dict) -> dict:
        """
        Validate WebPage schema.

        Required  : name
        Recommended: description, url, isPartOf
        """
        errors: list[str] = []
        warnings: list[str] = []

        if not data.get("name"):
            errors.append("Missing required field: 'name'")

        if not data.get("description"):
            warnings.append("Recommended field 'description' is missing")
        if not data.get("url"):
            warnings.append("Recommended field 'url' is missing")
        if not data.get("isPartOf"):
            warnings.append("Recommended field 'isPartOf' (link to WebSite) is missing")

        valid = len(errors) == 0
        return {
            "valid": valid,
            "errors": errors,
            "warnings": warnings,
            "score": _score_from_errors(errors, warnings),
        }

    # ------------------------------------------------------------------
    # 10. generate_fix
    # ------------------------------------------------------------------

    def generate_fix(self, url: str, page_data: dict, issues: list) -> str:
        """
        Generate a corrected JSON-LD <script> block based on the issues found.
        Missing required fields are filled with TODO placeholders.

        Returns a complete <script type="application/ld+json"> string.
        """
        parsed_url = urlparse(url)
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"

        # Determine the primary schema type from existing JSON-LD or issues
        existing = page_data.get("json_ld", [])
        primary_type = _get_type(existing[0]) if existing else "Article"

        # Build a base template per type
        templates = {
            "Article": self._template_article(url, base_url),
            "BlogPosting": self._template_article(url, base_url),
            "NewsArticle": self._template_article(url, base_url),
            "FAQPage": self._template_faq(),
            "HowTo": self._template_howto(),
            "BreadcrumbList": self._template_breadcrumb(url),
            "Organization": self._template_organization(base_url),
            "LocalBusiness": self._template_organization(base_url),
            "Product": self._template_product(),
            "WebPage": self._template_webpage(url, base_url),
        }

        template = templates.get(primary_type, templates["Article"])

        # Merge in any correct values from the existing first schema block
        if existing:
            template = self._merge_existing_values(template, existing[0])

        json_str = json.dumps(template, ensure_ascii=False, indent=2)
        return f'<script type="application/ld+json">\n{json_str}\n</script>'

    def _template_article(self, url: str, base_url: str) -> dict:
        return {
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": "TODO: Article headline (max 110 chars)",
            "author": {
                "@type": "Person",
                "name": "TODO: Author full name",
            },
            "datePublished": "TODO: ISO 8601 date e.g. 2024-01-01",
            "dateModified": "TODO: ISO 8601 date e.g. 2024-01-01",
            "publisher": {
                "@type": "Organization",
                "name": "TODO: Publisher name",
                "logo": {
                    "@type": "ImageObject",
                    "url": "TODO: Absolute URL to logo image",
                },
            },
            "image": {
                "@type": "ImageObject",
                "url": "TODO: Absolute URL to featured image",
                "width": 1200,
                "height": 630,
            },
            "mainEntityOfPage": {
                "@type": "WebPage",
                "@id": url,
            },
            "description": "TODO: Page meta description",
        }

    def _template_faq(self) -> dict:
        return {
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "mainEntity": [
                {
                    "@type": "Question",
                    "name": "TODO: Question 1 text?",
                    "acceptedAnswer": {
                        "@type": "Answer",
                        "text": "TODO: Answer 1 text",
                    },
                },
                {
                    "@type": "Question",
                    "name": "TODO: Question 2 text?",
                    "acceptedAnswer": {
                        "@type": "Answer",
                        "text": "TODO: Answer 2 text",
                    },
                },
            ],
        }

    def _template_howto(self) -> dict:
        return {
            "@context": "https://schema.org",
            "@type": "HowTo",
            "name": "TODO: HowTo title",
            "image": {
                "@type": "ImageObject",
                "url": "TODO: Absolute URL to main image",
            },
            "totalTime": "TODO: ISO 8601 duration e.g. PT30M",
            "estimatedCost": {
                "@type": "MonetaryAmount",
                "currency": "JPY",
                "value": "TODO: Cost amount or '0'",
            },
            "step": [
                {
                    "@type": "HowToStep",
                    "name": "TODO: Step 1 title",
                    "text": "TODO: Step 1 description",
                    "image": "TODO: Absolute URL to step 1 image (optional)",
                },
                {
                    "@type": "HowToStep",
                    "name": "TODO: Step 2 title",
                    "text": "TODO: Step 2 description",
                },
            ],
        }

    def _template_breadcrumb(self, url: str) -> dict:
        return {
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            "itemListElement": [
                {
                    "@type": "ListItem",
                    "position": 1,
                    "name": "ホーム",
                    "item": "TODO: https://example.com/",
                },
                {
                    "@type": "ListItem",
                    "position": 2,
                    "name": "TODO: Category name",
                    "item": "TODO: https://example.com/category/",
                },
                {
                    "@type": "ListItem",
                    "position": 3,
                    "name": "TODO: Current page title",
                    "item": url,
                },
            ],
        }

    def _template_organization(self, base_url: str) -> dict:
        return {
            "@context": "https://schema.org",
            "@type": "Organization",
            "name": "TODO: Organization name",
            "url": base_url,
            "logo": {
                "@type": "ImageObject",
                "url": "TODO: Absolute URL to logo",
            },
            "contactPoint": {
                "@type": "ContactPoint",
                "telephone": "TODO: +81-XX-XXXX-XXXX",
                "contactType": "customer service",
                "availableLanguage": "Japanese",
            },
            "sameAs": [
                "TODO: https://twitter.com/yourhandle",
                "TODO: https://www.linkedin.com/company/yourcompany",
            ],
            "address": {
                "@type": "PostalAddress",
                "streetAddress": "TODO: Street address",
                "addressLocality": "TODO: City",
                "addressRegion": "TODO: Prefecture",
                "postalCode": "TODO: 000-0000",
                "addressCountry": "JP",
            },
        }

    def _template_product(self) -> dict:
        return {
            "@context": "https://schema.org",
            "@type": "Product",
            "name": "TODO: Product name",
            "image": "TODO: Absolute URL to product image",
            "description": "TODO: Product description",
            "offers": {
                "@type": "Offer",
                "price": "TODO: 0",
                "priceCurrency": "JPY",
                "availability": "https://schema.org/InStock",
            },
        }

    def _template_webpage(self, url: str, base_url: str) -> dict:
        return {
            "@context": "https://schema.org",
            "@type": "WebPage",
            "name": "TODO: Page title",
            "description": "TODO: Page meta description",
            "url": url,
            "isPartOf": {
                "@type": "WebSite",
                "@id": base_url + "/#website",
                "url": base_url,
                "name": "TODO: Site name",
            },
        }

    def _merge_existing_values(self, template: dict, existing: dict) -> dict:
        """
        Overwrite TODO placeholders in the template with real values from
        the existing schema where available.
        """
        def _is_todo(value) -> bool:
            return isinstance(value, str) and value.startswith("TODO:")

        def _merge(tmpl, src):
            if not isinstance(tmpl, dict) or not isinstance(src, dict):
                return tmpl
            result = dict(tmpl)
            for key, tmpl_val in tmpl.items():
                if key in src:
                    src_val = src[key]
                    if isinstance(tmpl_val, dict) and isinstance(src_val, dict):
                        result[key] = _merge(tmpl_val, src_val)
                    elif _is_todo(tmpl_val) and src_val:
                        result[key] = src_val
            return result

        return _merge(template, existing)

    # ------------------------------------------------------------------
    # 11. detect_issues
    # ------------------------------------------------------------------

    def detect_issues(self, url: str, validation_results: list) -> list:
        """
        Convert validation errors/warnings into the standard issue format.

        Parameters
        ----------
        url : str
        validation_results : list of dicts returned by validate_schema()

        Returns
        -------
        list of {
            "code": "SCHM",
            "severity": "HIGH"|"MEDIUM"|"LOW",
            "url": str,
            "issue": str,
            "current": str,
            "recommendation": str,
        }
        """
        issues = []
        for result in validation_results:
            schema_type = result.get("type", "Unknown")

            for error in result.get("errors", []):
                issues.append({
                    "code": ISSUE_CODE,
                    "severity": SEVERITY_HIGH,
                    "url": url,
                    "issue": f"[{schema_type}] Required field error: {error}",
                    "current": "Missing or invalid required field",
                    "recommendation": (
                        f"Add the required field to your {schema_type} schema. "
                        "Use Google's Rich Results Test to verify: "
                        "https://search.google.com/test/rich-results"
                    ),
                })

            for warning in result.get("warnings", []):
                # Distinguish recommended-field warnings from best-practice notes
                is_recommended = "Recommended field" in warning
                severity = SEVERITY_MEDIUM if is_recommended else SEVERITY_LOW
                issues.append({
                    "code": ISSUE_CODE,
                    "severity": severity,
                    "url": url,
                    "issue": f"[{schema_type}] {warning}",
                    "current": "Field absent or suboptimal",
                    "recommendation": (
                        "Adding this field improves eligibility for rich results "
                        f"and signals completeness to Google for {schema_type} schema."
                    ),
                })

        return issues

    # ------------------------------------------------------------------
    # 12. validate_batch
    # ------------------------------------------------------------------

    def validate_batch(self, urls: list) -> dict:
        """
        Validate structured data for a list of URLs.

        Returns
        -------
        {
            "results": [
                {
                    "url": str,
                    "json_ld": [...],
                    "microdata": [...],
                    "validation": [...],
                    "issues": [...],
                    "error": str or None,
                },
                ...
            ],
            "summary": {
                "total_urls": int,
                "urls_with_schema": int,
                "urls_without_schema": int,
                "total_errors": int,
                "total_warnings": int,
                "types_found": {"Article": int, "FAQPage": int, ...},
            },
        }
        """
        results = []
        summary = {
            "total_urls": len(urls),
            "urls_with_schema": 0,
            "urls_without_schema": 0,
            "total_errors": 0,
            "total_warnings": 0,
            "types_found": {},
        }

        for url in urls:
            url = url.strip()
            if not url:
                continue

            entry = {
                "url": url,
                "json_ld": [],
                "microdata": [],
                "validation": [],
                "issues": [],
                "error": None,
            }

            try:
                page_data = self.fetch_and_extract(url)
                entry["json_ld"] = page_data["json_ld"]
                entry["microdata"] = page_data["microdata"]

                all_schemas = page_data["json_ld"] + page_data["microdata"]

                if all_schemas:
                    summary["urls_with_schema"] += 1
                    for schema in all_schemas:
                        validation = self.validate_schema(schema)
                        entry["validation"].append(validation)

                        schema_type = validation.get("type", "Unknown")
                        summary["types_found"][schema_type] = (
                            summary["types_found"].get(schema_type, 0) + 1
                        )
                        summary["total_errors"] += len(validation.get("errors", []))
                        summary["total_warnings"] += len(validation.get("warnings", []))
                else:
                    summary["urls_without_schema"] += 1

                entry["issues"] = self.detect_issues(url, entry["validation"])

            except requests.RequestException as exc:
                entry["error"] = f"HTTP error: {exc}"
                print(f"[WARNING] Failed to fetch {url}: {exc}", file=sys.stderr)
            except Exception as exc:  # noqa: BLE001
                entry["error"] = f"Unexpected error: {exc}"
                print(f"[WARNING] Error processing {url}: {exc}", file=sys.stderr)

            results.append(entry)

        summary_result = dict(summary)
        return {"results": results, "summary": summary_result}


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="WordPress Technical SEO — Structured Data Validator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python structured_data_validator.py https://example.com/page\n"
            "  python structured_data_validator.py --batch urls.txt --output ./reports/\n"
        ),
    )
    parser.add_argument(
        "url",
        nargs="?",
        help="Single URL to validate",
    )
    parser.add_argument(
        "--batch",
        metavar="FILE",
        help="Path to a text file containing one URL per line",
    )
    parser.add_argument(
        "--output",
        metavar="DIR",
        help="Directory to write JSON report files (used with --batch)",
    )
    parser.add_argument(
        "--generate-fix",
        action="store_true",
        default=False,
        help="Also output a corrected JSON-LD block for each URL",
    )
    return parser


def _run_single(validator: StructuredDataValidator, url: str, generate_fix: bool) -> None:
    """Validate a single URL and print results to stdout."""
    print(f"Fetching: {url}", file=sys.stderr)
    try:
        page_data = validator.fetch_and_extract(url)
    except Exception as exc:  # noqa: BLE001
        print(json.dumps({"url": url, "error": str(exc)}, ensure_ascii=False, indent=2))
        sys.exit(1)

    all_schemas = page_data["json_ld"] + page_data["microdata"]
    validation_results = [validator.validate_schema(s) for s in all_schemas]
    issues = validator.detect_issues(url, validation_results)

    output = {
        "url": url,
        "schemas_found": len(all_schemas),
        "json_ld_count": len(page_data["json_ld"]),
        "microdata_count": len(page_data["microdata"]),
        "validation": validation_results,
        "issues": issues,
    }

    if generate_fix and all_schemas:
        output["generated_fix"] = validator.generate_fix(url, page_data, issues)

    print(json.dumps(output, ensure_ascii=False, indent=2))


def _run_batch(
    validator: StructuredDataValidator,
    batch_file: str,
    output_dir: Optional[str],
    generate_fix: bool,
) -> None:
    """Validate all URLs in the batch file and write/print results."""
    import os

    with open(batch_file, encoding="utf-8") as f:
        urls = [line.strip() for line in f if line.strip() and not line.startswith("#")]

    print(f"Processing {len(urls)} URLs...", file=sys.stderr)
    batch_result = validator.validate_batch(urls)

    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        report_path = os.path.join(output_dir, "structured_data_report.json")

        if generate_fix:
            for entry in batch_result["results"]:
                if entry.get("json_ld") or entry.get("microdata"):
                    page_data = {
                        "json_ld": entry["json_ld"],
                        "microdata": entry["microdata"],
                    }
                    entry["generated_fix"] = validator.generate_fix(
                        entry["url"], page_data, entry["issues"]
                    )

        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(batch_result, f, ensure_ascii=False, indent=2)
        print(f"Report written to: {report_path}", file=sys.stderr)
    else:
        print(json.dumps(batch_result, ensure_ascii=False, indent=2))


def main() -> None:
    parser = _build_arg_parser()
    args = parser.parse_args()

    if not args.url and not args.batch:
        parser.print_help()
        sys.exit(1)

    validator = StructuredDataValidator()

    if args.batch:
        _run_batch(validator, args.batch, args.output, args.generate_fix)
    elif args.url:
        _run_single(validator, args.url, args.generate_fix)


if __name__ == "__main__":
    main()
