"""Accessibility scanning service using Playwright and axe-core."""

import asyncio
from typing import Any, Optional
from datetime import datetime
from uuid import UUID
from playwright.async_api import async_playwright, Browser
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.scan import Scan, Issue, Severity, ScanStatus
from app.models.website import Website
from app.models.usage import UsageEvent, EventType
from app.config import get_settings

settings = get_settings()


# WCAG 2.1 rule mappings
AXE_RULES = {
    # Critical issues
    "image-alt": {"severity": Severity.CRITICAL, "category": "images"},
    "image-redundant-alt": {"severity": Severity.MODERATE, "category": "images"},
    "label": {"severity": Severity.CRITICAL, "category": "forms"},
    "legend": {"severity": Severity.SERIOUS, "category": "forms"},
    "button-name": {"severity": Severity.CRITICAL, "category": "content"},
    "link-name": {"severity": Severity.SERIOUS, "category": "content"},
    "document-title": {"severity": Severity.SERIOUS, "category": "content"},
    "html-has-lang": {"severity": Severity.SERIOUS, "category": "content"},
    # Serious issues
    "color-contrast": {"severity": Severity.SERIOUS, "category": "visual"},
    "link-in-text-block": {"severity": Severity.SERIOUS, "category": "visual"},
    "aria-label": {"severity": Severity.SERIOUS, "category": "aria"},
    "aria-required-attr": {"severity": Severity.CRITICAL, "category": "aria"},
    "aria-required-children": {"severity": Severity.SERIOUS, "category": "aria"},
    "aria-roles": {"severity": Severity.SERIOUS, "category": "aria"},
    # Moderate issues
    "heading-order": {"severity": Severity.MODERATE, "category": "content"},
    "empty-heading": {"severity": Severity.MODERATE, "category": "content"},
    "duplicate-id": {"severity": Severity.MODERATE, "category": "content"},
    "table-headers": {"severity": Severity.SERIOUS, "category": "tables"},
    "th-headers": {"severity": Severity.SERIOUS, "category": "tables"},
    "table-duplicate-name": {"severity": Severity.MODERATE, "category": "tables"},
    # Minor issues
    "bypass": {"severity": Severity.MINOR, "category": "navigation"},
    "meta-viewport": {"severity": Severity.MINOR, "category": "content"},
}


class AccessibilityScanner:
    """Scanner for accessibility issues using Playwright and axe-core."""

    def __init__(self, db: AsyncSession):
        """Initialize the scanner.

        Args:
            db: Database session for saving results
        """
        self.db = db
        self.browser: Optional[Browser] = None

    async def __aenter__(self):
        """Enter context manager and launch browser."""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=True)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager and cleanup."""
        if self.browser:
            await self.browser.close()
        await self.playwright.stop()

    async def scan_website(self, website: Website, full_scan: bool = False) -> Scan:
        """Scan a website for accessibility issues.

        Args:
            website: The website to scan
            full_scan: Whether to scan multiple pages or just homepage

        Returns:
            The created Scan object with results
        """
        # Create scan record
        scan = Scan(
            website_id=website.id,
            status=ScanStatus.RUNNING,
            started_at=datetime.utcnow(),
        )
        self.db.add(scan)
        await self.db.commit()
        await self.db.refresh(scan)

        try:
            # Get URLs to scan
            urls = [website.url]
            if full_scan:
                urls.extend(await self._discover_pages(website.url, max_pages=settings.max_pages_per_scan))

            # Scan each URL
            all_issues = []
            for url in urls:
                page_issues = await self._scan_page(url, scan.id)
                all_issues.extend(page_issues)

            # Update scan with results
            scan.status = ScanStatus.COMPLETED
            scan.completed_at = datetime.utcnow()
            scan.total_issues = len(all_issues)
            scan.critical_issues = sum(1 for i in all_issues if i.severity == Severity.CRITICAL)
            scan.serious_issues = sum(1 for i in all_issues if i.severity == Severity.SERIOUS)
            scan.moderate_issues = sum(1 for i in all_issues if i.severity == Severity.MODERATE)
            scan.minor_issues = sum(1 for i in all_issues if i.severity == Severity.MINOR)
            scan.score = scan.calculate_score()

            # Update website
            website.last_scan_at = datetime.utcnow()
            website.latest_score = scan.score

            # Track usage
            usage = UsageEvent(
                user_id=website.user_id,
                event_type=EventType.SCAN,
                resource_id=str(scan.id),
            )
            self.db.add(usage)

            await self.db.commit()
            await self.db.refresh(scan)

            return scan

        except Exception as e:
            scan.status = ScanStatus.FAILED
            scan.completed_at = datetime.utcnow()
            scan.error_message = str(e)
            await self.db.commit()
            await self.db.refresh(scan)
            raise

    async def _scan_page(self, url: str, scan_id: UUID) -> list[Issue]:
        """Scan a single page for accessibility issues.

        Args:
            url: The URL to scan
            scan_id: The scan ID to associate issues with

        Returns:
            List of Issue objects found
        """
        if not self.browser:
            raise RuntimeError("Browser not initialized")

        page = await self.browser.new_page()
        issues = []

        try:
            # Navigate to the page
            await page.goto(url, wait_until="networkidle", timeout=settings.scan_timeout_seconds * 1000)

            # Inject and run axe-core
            axe_results = await page.evaluate("""() => {
                return axe.run(document, {
                    runOnly: {
                        type: 'tag',
                        values: ['wcag2a', 'wcag2aa', 'wcag21aa', 'wcag21a']
                    }
                });
            }""")

            # Process results
            if axe_results.get("violations"):
                for violation in axe_results["violations"]:
                    # Get severity from rule mapping
                    rule_info = AXE_RULES.get(violation["id"], {
                        "severity": Severity.MODERATE,
                        "category": "general"
                    })

                    # Create issue for each node
                    for node in violation.get("nodes", [])[:10]:  # Limit to first 10 per rule
                        issue = Issue(
                            scan_id=scan_id,
                            type=violation["id"],
                            severity=rule_info["severity"],
                            selector=self._get_selector(node),
                            description=violation["description"],
                            impact=violation.get("impact", ""),
                            fix_suggestion=self._generate_fix_suggestion(violation),
                            page_url=url,
                            element_html=self._get_element_html(page, node),
                        )
                        issues.append(issue)
                        self.db.add(issue)

        except Exception as e:
            print(f"Error scanning {url}: {e}")
        finally:
            await page.close()

        return issues

    async def _discover_pages(self, base_url: str, max_pages: int = 10) -> list[str]:
        """Discover pages to scan by following internal links.

        Args:
            base_url: The base URL to start from
            max_pages: Maximum number of pages to discover

        Returns:
            List of URLs to scan
        """
        if not self.browser:
            return []

        discovered = {base_url}
        to_visit = [base_url]

        while to_visit and len(discovered) < max_pages:
            url = to_visit.pop(0)

            try:
                page = await self.browser.new_page()
                await page.goto(url, wait_until="networkidle", timeout=30000)

                # Get all internal links
                links = await page.evaluate("""() => {
                    const links = [];
                    document.querySelectorAll('a[href]').forEach(a => {
                        links.push(a.href);
                    });
                    return [...new Set(links)];
                }""")

                await page.close()

                from urllib.parse import urlparse

                base_domain = urlparse(base_url).netloc

                for link in links:
                    parsed = urlparse(link)
                    if parsed.netloc == base_domain and link not in discovered:
                        # Clean the URL (remove fragments, some query params)
                        clean_link = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
                        if clean_link not in discovered:
                            discovered.add(clean_link)
                            to_visit.append(clean_link)

            except Exception as e:
                print(f"Error discovering pages from {url}: {e}")

        return list(discovered)[:max_pages]

    def _get_selector(self, node: dict) -> str:
        """Extract CSS selector from axe node."""
        target = node.get("target", [])
        if target:
            return target[0] if isinstance(target[0], str) else str(target[0])
        return ""

    def _generate_fix_suggestion(self, violation: dict) -> str:
        """Generate a fix suggestion from axe violation."""
        help_text = violation.get("help", "")
        return help_text

    def _get_element_html(self, page, node: dict) -> str:
        """Get the HTML of the element with the issue."""
        try:
            target = node.get("target", [])
            if target and target[0]:
                selector = target[0]
                html = page.locator(selector).inner_html(timeout=5000)
                return html[:500]  # Limit length
        except Exception:
            pass
        return ""


async def run_scan(db: AsyncSession, website_id: UUID, full_scan: bool = False) -> Scan:
    """Run a scan in a background context.

    This is the entry point for triggering scans from the API.
    """
    from sqlalchemy import select

    result = await db.execute(select(Website).where(Website.id == website_id))
    website = result.scalar_one_or_none()

    if not website:
        raise ValueError(f"Website {website_id} not found")

    async with AccessibilityScanner(db) as scanner:
        return await scanner.scan_website(website, full_scan=full_scan)
