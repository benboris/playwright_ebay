"""
Item Page Object - דף מוצר ב-eBay.

מממש את addItemsToCart (requirement §4.2):
  - פתיחת כל URL
  - בחירת וריאנטים אקראיים (מידה / צבע / כמות)
  - לחיצה על "Add to cart"
  - שמירת צילום מסך לכל פריט
"""
import random
import logging
from typing import List
from playwright.sync_api import Page
from pages.base_page import BasePage


class ItemPage(BasePage):
    """
    Page Object for an individual eBay item/product page.
    Handles variant selection and add-to-cart logic.
    """

    # ── Locators ──────────────────────────────────
    ADD_TO_CART_BTN = "#atcBtn_btn, .ux-call-to-action[data-testid='x-atc-action'], button[data-track='atcBtn']"
    BUY_NOW_BTN = "#binBtn_btn"
    ITEM_TITLE = "h1.x-item-title__mainTitle span, h1[itemprop='name']"

    # Variant selectors
    VARIANT_SECTION = ".ux-layout-section--variation"
    SELECT_OPTION = "select.msku-sel"
    LISTBOX_OPTION = ".listbox-button__control"

    # Cart confirmation modal
    CART_CONFIRM_MODAL = ".vi-overlay, #cartSidebarLayer, .go-to-cart-btn"
    VIEW_CART_LINK = "a.go-to-cart-btn, a[href*='cart']"
    CONTINUE_SHOPPING = "button.overlay-add2cartLayer--continue, button[data-btn-key='continue']"

    def __init__(self, page: Page, screenshots_dir: str = "screenshots"):
        super().__init__(page, screenshots_dir)
        self.logger = logging.getLogger("ItemPage")

    # ─────────────────────────────────────────────
    # Main public method (requirement §4.2)
    # ─────────────────────────────────────────────

    def add_items_to_cart(self, urls: List[str]) -> None:
        """
        Iterate over item URLs, open each, pick variants randomly, add to cart,
        dismiss the confirmation overlay, and save a screenshot per item.
        """
        self.logger.info(f"Adding {len(urls)} items to cart")

        for idx, url in enumerate(urls, start=1):
            self.logger.info(f"[{idx}/{len(urls)}] Opening item: {url[:80]}…")
            try:
                self._add_single_item(idx, url)
            except Exception as exc:
                self.logger.error(f"Failed to add item {idx}: {exc}")
                self.take_screenshot(f"add_to_cart_FAIL_item{idx}")

    # ─────────────────────────────────────────────
    # Private helpers
    # ─────────────────────────────────────────────

    def _add_single_item(self, idx: int, url: str) -> None:
        """Open an item page, choose variants, click Add-to-Cart, and screenshot."""
        self.navigate_to(url)
        self.page.wait_for_load_state("domcontentloaded")

        title = self._get_item_title()
        self.logger.info(f"  Item title: {title}")

        self._select_variants_randomly()
        self._click_add_to_cart()
        self._dismiss_cart_overlay()

        self.take_screenshot(f"added_to_cart_item{idx}")
        self.logger.info(f"  ✓ Item {idx} added successfully")

    def _get_item_title(self) -> str:
        try:
            el = self.page.query_selector(self.ITEM_TITLE)
            return el.inner_text().strip() if el else "Unknown"
        except Exception:
            return "Unknown"

    def _select_variants_randomly(self) -> None:
        """
        Detect variant selection controls (dropdowns or listbox buttons)
        and pick a random *available* option from each.
        """
        # ── Dropdown (<select>) variants ──────────
        selects = self.page.query_selector_all(self.SELECT_OPTION)
        for sel in selects:
            options = sel.query_selector_all("option:not([disabled])")
            if len(options) > 1:
                # skip the first "Select" placeholder option if present
                candidates = [o for o in options if o.get_attribute("value")]
                if candidates:
                    chosen = random.choice(candidates)
                    value = chosen.get_attribute("value")
                    sel.select_option(value=value)
                    self.logger.debug(f"  Dropdown variant selected: {value}")

        # ── Listbox / button variants ──────────────
        listboxes = self.page.query_selector_all(self.LISTBOX_OPTION)
        for lb in listboxes:
            try:
                # collect enabled sibling buttons in the same group
                parent = lb.evaluate_handle(
                    "el => el.closest('.ux-layout-section--variation, .listbox')"
                )
                btn_options = parent.query_selector_all(
                    "button.listbox-button__control:not([disabled]):not([aria-disabled='true'])"
                )
                if btn_options:
                    random.choice(btn_options).click()
                    self.page.wait_for_timeout(400)
            except Exception as exc:
                self.logger.debug(f"  Listbox variant selection skipped: {exc}")

    def _click_add_to_cart(self) -> None:
        """Click the Add-to-Cart button and wait for overlay / navigation."""
        try:
            atc = self.page.wait_for_selector(self.ADD_TO_CART_BTN, timeout=8_000)
            if atc and atc.is_visible():
                atc.click()
                self.page.wait_for_timeout(1_500)
            else:
                self.logger.warning("  Add-to-Cart button not visible – skipping")
        except Exception as exc:
            self.logger.warning(f"  Add-to-Cart not found: {exc}")

    def _dismiss_cart_overlay(self) -> None:
        """
        Dismiss the cart confirmation modal by clicking
        'Continue shopping' or navigating back.
        """
        try:
            modal = self.page.query_selector(self.CART_CONFIRM_MODAL)
            if modal and modal.is_visible():
                continue_btn = self.page.query_selector(self.CONTINUE_SHOPPING)
                if continue_btn and continue_btn.is_visible():
                    continue_btn.click()
                    self.page.wait_for_timeout(800)
                    return
        except Exception:
            pass

        # Fallback: go back to the search results tab/history
        self.page.go_back()
        self.page.wait_for_load_state("domcontentloaded")
