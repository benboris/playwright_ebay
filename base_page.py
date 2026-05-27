"""
Base Page Object - כל ה-Page Objects יורשים ממחלקה זו.
מספק פונקציונליות משותפת: ניווט, המתנה, צילומי מסך ולוגים.
"""
import os
import logging
from datetime import datetime

from playwright.sync_api import sync_playwright, Page


class BasePage:
    """
    Base class for all Page Objects.
    Implements common browser interactions and utility methods.
    """

    def __init__(self, page: Page, screenshots_dir: str = "screenshots"):
        self.page = page
        self.screenshots_dir = screenshots_dir
        self.logger = logging.getLogger(self.__class__.__name__)
        os.makedirs(screenshots_dir, exist_ok=True)

    # ─────────────────────────────────────────────
    # Navigation
    # ─────────────────────────────────────────────

    def navigate_to(self, url: str) -> None:
        """Navigate to a given URL and wait for load."""
        self.logger.info(f"Navigating to: {url}")
        self.page.goto(url, wait_until="domcontentloaded", timeout=380000)

    def get_current_url(self) -> str:
        return self.page.url

    # ─────────────────────────────────────────────
    # Wait helpers
    # ─────────────────────────────────────────────

    def wait_for_selector(self, selector: str, timeout: int = 330000):
        return self.page.wait_for_selector(selector, timeout=timeout)

    def wait_for_navigation(self, timeout: int = 330000):
        self.page.wait_for_load_state("domcontentloaded", timeout=timeout)

    # ─────────────────────────────────────────────
    # Screenshots
    # ─────────────────────────────────────────────

    def take_screenshot(self, name: str) -> str:
        """Save a timestamped screenshot and return its path."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{name}_{timestamp}.png"
        path = os.path.join(self.screenshots_dir, filename)
        self.page.screenshot(path=path, full_page=True)
        self.logger.info(f"Screenshot saved: {path}")
        return path

    # ─────────────────────────────────────────────
    # Generic interactions
    # ─────────────────────────────────────────────

    def click(self, selector: str, timeout: int = 330000) -> None:
        self.logger.debug(f"Clicking: {selector}")
        self.page.click(selector, timeout=timeout)

    def fill(self, selector: str, text: str, timeout: int = 330000) -> None:
        self.logger.debug(f"Filling '{selector}' with '{text}'")
        self.page.fill(selector, text, timeout=timeout)

    def get_text(self, selector: str) -> str:
        element = self.page.query_selector(selector)
        return element.inner_text().strip() if element else ""

    def is_visible(self, selector: str) -> bool:
        return self.page.is_visible(selector)
