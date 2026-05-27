"""
Login Page Object - מטפל בהזדהות ב-eBay.
"""
import logging
from playwright.sync_api import Page
from pages.base_page import BasePage


class LoginPage(BasePage):
    """
    Page Object for eBay sign-in flow.
    Encapsulates all locators and actions related to authentication.
    """

    # ── Locators ──────────────────────────────────
    SIGN_IN_LINK        = "a#gh-ug, a[href*='signin']"
    EMAIL_INPUT         = "#userid"
    EMAIL_CONTINUE_BTN  = "#signin-continue-btn, button[type='submit']"
    PASSWORD_INPUT      = "#pass"
    SIGN_IN_BTN         = "#sgnBt, button[type='submit']"
    USER_GREETING       = "#gh-ug span, .gh-ug-guest"
    ERROR_MSG           = "#errmsg, .errrtxt"

    def __init__(self, page: Page, screenshots_dir: str = "screenshots"):
        super().__init__(page, screenshots_dir)
        self.logger = logging.getLogger("LoginPage")

    # ─────────────────────────────────────────────
    # Public API
    # ─────────────────────────────────────────────

    def navigate_to_login(self, base_url: str = "https://www.ebay.com") -> None:
        """Open eBay homepage and click the Sign-in link."""
        self.navigate_to(base_url)
        self.logger.info("Clicking Sign-in link")
        self.page.click(self.SIGN_IN_LINK)
        self.wait_for_navigation()

    def login(self, username: str, password: str) -> bool:
        """
        Perform the two-step eBay login flow.
        Returns True if login succeeded, False otherwise.
        """
        self.logger.info(f"Logging in as: {username}")

        # Step 1 – enter email
        self.wait_for_selector(self.EMAIL_INPUT)
        self.fill(self.EMAIL_INPUT, username)
        self.click(self.EMAIL_CONTINUE_BTN)
        self.wait_for_navigation()

        # Step 2 – enter password
        self.wait_for_selector(self.PASSWORD_INPUT)
        self.fill(self.PASSWORD_INPUT, password)
        self.click(self.SIGN_IN_BTN)
        self.wait_for_navigation()

        success = self._is_logged_in()
        if success:
            self.logger.info("Login successful")
            self.take_screenshot("login_success")
        else:
            error = self.get_text(self.ERROR_MSG)
            self.logger.error(f"Login failed. Error: {error}")
            self.take_screenshot("login_failure")

        return success

    # ─────────────────────────────────────────────
    # Private helpers
    # ─────────────────────────────────────────────

    def _is_logged_in(self) -> bool:
        """Check for a user-greeting element that appears after a successful login."""
        try:
            self.page.wait_for_selector(self.USER_GREETING, timeout=8_000)
            return True
        except Exception:
            return False
