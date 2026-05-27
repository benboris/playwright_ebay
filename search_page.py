"""
Search Page Object - חיפוש מוצרים וסינון לפי מחיר ב-eBay.

מממש את searchItemsByNameUnderPrice:
  - חיפוש לפי מילת מפתח
  - שימוש בפילטר מחיר מקסימלי
  - איסוף קישורים לפריטים תחת תקרת מחיר
  - מעבר עמודים (Paging) במידת הצורך
"""
import re
import logging
from typing import List
from playwright.sync_api import Page
from pages.base_page import BasePage


class SearchPage(BasePage):
    """
    Page Object for eBay search results page.
    Handles search, price filtering, and item URL collection.
    """

    # ── Locators ──────────────────────────────────
    SEARCH_INPUT         = "#gh-ac"
    SEARCH_BUTTON        = "#gh-btn"
    PRICE_MAX_INPUT      = "input[aria-label='Maximum Value in $'], input[placeholder='Max']"
    PRICE_FILTER_SUBMIT  = "button.x-refine__select__svg--14, button[aria-label='Submit price range']"

    # XPath לפריטים בדף התוצאות
    ITEM_CARDS_XPATH     = "//li[contains(@class,'s-item') and not(contains(@class,'s-item--watch-at-corner'))]"
    ITEM_LINK_XPATH      = ".//a[contains(@class,'s-item__link')]"
    ITEM_PRICE_XPATH     = ".//*[contains(@class,'s-item__price')]"

    NEXT_PAGE_BTN        = "a.pagination__next, a[aria-label='Go to next search page']"

    def __init__(self, page: Page, screenshots_dir: str = "screenshots"):
        super().__init__(page, screenshots_dir)
        self.logger = logging.getLogger("SearchPage")

    # ─────────────────────────────────────────────
    # Main public method (requirement §4.1)
    # ─────────────────────────────────────────────

    def search_items_by_name_under_price(
        self,
        query: str,
        max_price: float,
        limit: int = 5,
    ) -> List[str]:
        """
        Search for `query` on eBay and return up to `limit` item URLs
        whose price is ≤ max_price.

        Behaviour:
          1. Perform a keyword search.
          2. Apply the max-price filter if available on the page.
          3. Collect items (via XPath) whose displayed price ≤ max_price.
          4. If fewer than `limit` found, follow "Next" pagination until
             enough are collected or pages run out.
          5. Return the collected URL list (may be < limit, including 0).
        """
        self.logger.info(f"Searching: query='{query}', max_price={max_price}, limit={limit}")

        self._perform_search(query)
        self._apply_price_filter(max_price)

        collected: List[str] = []
        page_num = 1

        while len(collected) < limit:
            self.logger.info(f"Scraping page {page_num} (collected {len(collected)}/{limit})")
            new_urls = self._collect_items_on_page(max_price, limit - len(collected))
            collected.extend(new_urls)

            if len(collected) >= limit:
                break

            if self._go_to_next_page():
                page_num += 1
            else:
                self.logger.info("No more pages available.")
                break

        self.logger.info(f"Total items collected: {len(collected)}")
        self.take_screenshot(f"search_results_{query.replace(' ', '_')}")
        return collected[:limit]

    # ─────────────────────────────────────────────
    # Private helpers
    # ─────────────────────────────────────────────

    def _perform_search(self, query: str) -> None:
        """Type query into the search bar and submit."""
        self.logger.info(f"Performing search for: '{query}'")
        self.wait_for_selector(self.SEARCH_INPUT)
        self.fill(self.SEARCH_INPUT, query)
        self.click(self.SEARCH_BUTTON)
        self.wait_for_navigation()

    def _apply_price_filter(self, max_price: float) -> None:
        """Fill in the max-price filter and submit it if the input exists."""
        try:
            price_input = self.page.query_selector(self.PRICE_MAX_INPUT)
            if price_input:
                self.logger.info(f"Applying max-price filter: {max_price}")
                price_input.fill(str(int(max_price)))
                submit_btn = self.page.query_selector(self.PRICE_FILTER_SUBMIT)
                if submit_btn:
                    submit_btn.click()
                else:
                    price_input.press("Enter")
                self.wait_for_navigation()
            else:
                self.logger.warning("Price filter input not found – skipping filter step.")
        except Exception as exc:
            self.logger.warning(f"Could not apply price filter: {exc}")

    def _collect_items_on_page(self, max_price: float, needed: int) -> List[str]:
        """
        Scrape the current SERP and return up to `needed` URLs
        whose price ≤ max_price.
        """
        urls: List[str] = []
        cards = self.page.query_selector_all(f"xpath={self.ITEM_CARDS_XPATH}")
        self.logger.debug(f"Found {len(cards)} item cards on page")

        for card in cards:
            if len(urls) >= needed:
                break

            price = self._extract_price(card)
            if price is None or price > max_price:
                continue

            link_el = card.query_selector(f"xpath={self.ITEM_LINK_XPATH}")
            if link_el:
                href = link_el.get_attribute("href")
                if href and href.startswith("http") and href not in urls:
                    self.logger.debug(f"  + Added item (price={price}): {href[:80]}…")
                    urls.append(href)

        return urls

    def _extract_price(self, card) -> float | None:
        """
        Parse the first numeric price found inside a card element.
        Handles ranges (e.g. "$10.00 to $20.00") by taking the lower bound.
        Returns None if no parseable price is found.
        """
        price_el = card.query_selector(f"xpath={self.ITEM_PRICE_XPATH}")
        if not price_el:
            return None

        raw = price_el.inner_text()
        numbers = re.findall(r"[\d,]+\.?\d*", raw.replace(",", ""))
        if not numbers:
            return None

        try:
            return float(numbers[0])
        except ValueError:
            return None

    def _go_to_next_page(self) -> bool:
        """Click the 'Next' pagination button if it exists. Returns True on success."""
        try:
            next_btn = self.page.query_selector(self.NEXT_PAGE_BTN)
            if next_btn and next_btn.is_visible():
                next_btn.click()
                self.wait_for_navigation()
                return True
        except Exception as exc:
            self.logger.debug(f"Next-page navigation failed: {exc}")
        return False
