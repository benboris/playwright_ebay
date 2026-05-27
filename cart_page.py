"""
Cart Page Object - סל הקניות ב-eBay.

מממש את assertCartTotalNotExceeds (requirement §4.3):
  - פתיחת עמוד הסל
  - קריאת הסכום הכולל
  - אימות שהסכום ≤ budgetPerItem * itemsCount
  - שמירת Screenshot + Trace
"""
import re
import logging
from playwright.sync_api import Page
from pages.base_page import BasePage


class CartPage(BasePage):
    """
    Page Object for the eBay shopping cart.
    Handles price extraction and total assertion.
    """

    CART_URL = "https://cart.payments.ebay.com/sc/view"

    # ── Locators ──────────────────────────────────
    # The subtotal / order total shown in the summary panel
    SUBTOTAL_SELECTORS = [
        ".order-summary__price",
        ".sc-subtotal .gh-price",
        "[data-test-id='ORDER_SUMMARY'] .order-summary__value",
        ".sc-price-block .sc-price",
        "#estimate-total-price",
        ".summary-item-cost",
    ]
    CART_ITEMS = ".sc-list-item"
    EMPTY_CART_MSG = ".empty-cart, #cart-empty-message"

    def __init__(self, page: Page, screenshots_dir: str = "screenshots"):
        super().__init__(page, screenshots_dir)
        self.logger = logging.getLogger("CartPage")

    # ─────────────────────────────────────────────
    # Main public method (requirement §4.3)
    # ─────────────────────────────────────────────

    def assert_cart_total_not_exceeds(
        self,
        budget_per_item: float,
        items_count: int,
    ) -> None:
        """
        Open the cart, read the displayed total, and assert it does not
        exceed budget_per_item * items_count.

        Raises AssertionError if the total exceeds the threshold.
        Saves a screenshot regardless of the outcome.
        """
        self.logger.info(
            f"Asserting cart total ≤ {budget_per_item} × {items_count} = "
            f"{budget_per_item * items_count:.2f}"
        )

        self._open_cart()
        total = self._read_cart_total()
        threshold = budget_per_item * items_count

        self.logger.info(f"Cart total: ${total:.2f} | Threshold: ${threshold:.2f}")
        self.take_screenshot("cart_total_assertion")

        assert total <= threshold, (
            f"Cart total ${total:.2f} exceeds allowed budget "
            f"${threshold:.2f} ({budget_per_item} × {items_count})"
        )
        self.logger.info("✅ Assertion passed – cart total is within budget")

    # ─────────────────────────────────────────────
    # Private helpers
    # ─────────────────────────────────────────────

    def _open_cart(self) -> None:
        """Navigate to the eBay cart page and wait for it to load."""
        self.navigate_to(self.CART_URL)
        self.page.wait_for_load_state("networkidle", timeout=80000)

        if self.is_visible(self.EMPTY_CART_MSG):
            self.logger.warning("Cart appears to be empty!")

    def _read_cart_total(self) -> float:
        """
        Try each locator in SUBTOTAL_SELECTORS until a parseable price is found.
        Falls back to scanning the whole page for the largest dollar amount.
        """
        for selector in self.SUBTOTAL_SELECTORS:
            el = self.page.query_selector(selector)
            if el:
                raw = el.inner_text()
                price = self._parse_price(raw)
                if price is not None:
                    self.logger.debug(f"  Total read via '{selector}': ${price:.2f}")
                    return price

        # Fallback – scan entire page text
        self.logger.warning("Primary selectors failed; scanning full page for price…")
        return self._scan_page_for_total()

    def _scan_page_for_total(self) -> float:
        """Last-resort: extract the largest dollar figure from the cart page text."""
        body = self.page.inner_text("body")
        amounts = re.findall(r"\$\s*([\d,]+\.?\d*)", body)
        if not amounts:
            raise RuntimeError("Could not read any price from the cart page")
        prices = [float(a.replace(",", "")) for a in amounts]
        return max(prices)

    @staticmethod
    def _parse_price(text: str) -> float | None:
        """Extract the first dollar amount from a text string."""
        match = re.search(r"[\$]?\s*([\d,]+\.?\d*)", text)
        if match:
            try:
                return float(match.group(1).replace(",", ""))
            except ValueError:
                return None
        return None

    def get_cart_item_count(self) -> int:
        """Return the number of distinct line-items in the cart."""
        items = self.page.query_selector_all(self.CART_ITEMS)
        return len(items)
