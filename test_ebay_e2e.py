"""
E2E Test Suite - תרחיש קצה לקצה על eBay.

מבנה כל תרחיש:
  1. הזדהות (Login)
  2. searchItemsByNameUnderPrice  → אוסף עד N קישורים
  3. addItemsToCart               → מוסיף כל פריט לסל
  4. assertCartTotalNotExceeds    → מוודא שהסכום בתקציב

ריצה:
    pytest tests/test_ebay_e2e.py -v --alluredir=reports/allure-results
"""
import os
import pytest
import allure
import logging
from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page

# ── Local imports ──────────────────────────────
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pages.login_page import LoginPage
from pages.search_page import SearchPage
from pages.item_page import ItemPage
from pages.cart_page import CartPage
from utils.data_loader import DataLoader
from utils.logger import setup_logger

# ── Logger ─────────────────────────────────────
setup_logger()
logger = logging.getLogger("TestSuite")


# ══════════════════════════════════════════════
#  Fixtures
# ══════════════════════════════════════════════

@pytest.fixture(scope="session")
def test_data():
    """Load test data once per session."""
    return DataLoader(data_file=os.path.join(os.path.dirname(__file__), "../data/test_data.json"))


@pytest.fixture(scope="function")
def browser_context(test_data):
    """
    Spin up a Playwright browser context for every test function.
    Yields (context, page); tears down after the test.
    """
    settings = test_data.get_settings()
    headless = settings.get("headless", True)
    slow_mo = settings.get("slow_mo", 200)

    with sync_playwright() as pw:
        browser: Browser = pw.chromium.launch(
            headless=headless,
            slow_mo=slow_mo,
            args=["--no-sandbox", "--disable-dev-shm-usage"],
        )
        context: BrowserContext = browser.new_context(
            viewport={"width": 1366, "height": 768},
            locale="en-US",
            timezone_id="America/New_York",
        )
        page: Page = context.new_page()

        yield context, page

        # ── Teardown ──────────────────────────
        page.close()
        context.close()
        browser.close()


@pytest.fixture
def screenshots_dir(tmp_path):
    d = str(tmp_path / "screenshots")
    os.makedirs(d, exist_ok=True)
    return d


# ══════════════════════════════════════════════
#  Parametrised E2E Test
# ══════════════════════════════════════════════

def _scenario_ids(test_data_fixture):
    """Helper to produce pytest parameter IDs from scenario data."""
    loader = DataLoader(data_file="data/test_data.json")
    return [s["scenario_id"] for s in loader.get_scenarios()]


def pytest_generate_tests(metafunc):
    """Dynamically parametrise with all scenarios from the JSON data file."""
    if "scenario" in metafunc.fixturenames:
        loader = DataLoader(data_file=os.path.join(os.path.dirname(__file__), "../data/test_data.json"))
        scenarios = loader.get_scenarios()
        metafunc.parametrize(
            "scenario",
            scenarios,
            ids=[s["scenario_id"] for s in scenarios],
        )


@allure.epic("eBay E2E Automation")
@allure.feature("Shopping Flow")
class TestEbayE2E:
    """
    Data-Driven E2E test class.
    One test method; parametrised over all scenarios in test_data.json.
    """

    @allure.story("Full shopping flow: search → add-to-cart → assert total")
    def test_full_shopping_flow(
        self,
        browser_context,
        test_data: DataLoader,
        scenario: dict,
        screenshots_dir: str,
    ):
        """
        End-to-end scenario:
          1. Login
          2. Search for items under max_price
          3. Add all found items to cart
          4. Assert cart total ≤ budget
        """
        _, page = browser_context
        creds = test_data.get_credentials()
        settings = test_data.get_settings()
        base_url = settings.get("base_url", "https://www.ebay.com")

        query = scenario["search_query"]
        max_price = float(scenario["max_price"])
        limit = int(scenario["limit"])
        budget_per_item = float(scenario["budget_per_item"])

        allure.dynamic.title(scenario["description"])
        allure.dynamic.parameter("query", query)
        allure.dynamic.parameter("max_price", max_price)

        logger.info("=" * 60)
        logger.info(f"SCENARIO {scenario['scenario_id']}: {scenario['description']}")
        logger.info("=" * 60)

        # ── Step 1 – Login ────────────────────────────────────────
        with allure.step("1. Login to eBay"):
            login_page = LoginPage(page, screenshots_dir)
            login_page.navigate_to_login(base_url)

            logged_in = login_page.login(
                creds.get("username", ""),
                creds.get("password", ""),
            )
            if not logged_in:
                allure.attach(
                    page.screenshot(),
                    name="login_failure",
                    attachment_type=allure.attachment_type.PNG,
                )
                pytest.skip("Login failed – credentials may be invalid in CI environment")

        # ── Step 2 – Search with price filter ────────────────────
        with allure.step(f"2. Search '{query}' under ${max_price}"):
            search_page = SearchPage(page, screenshots_dir)
            item_urls = search_page.search_items_by_name_under_price(
                query=query,
                max_price=max_price,
                limit=limit,
            )
            logger.info(f"Found {len(item_urls)} items matching criteria")
            allure.attach(
                "\n".join(item_urls),
                name="collected_item_urls",
                attachment_type=allure.attachment_type.TEXT,
            )

            if not item_urls:
                pytest.skip(f"No items found for query='{query}' under ${max_price}")

        # ── Step 3 – Add items to cart ────────────────────────────
        with allure.step(f"3. Add {len(item_urls)} items to cart"):
            item_page = ItemPage(page, screenshots_dir)
            item_page.add_items_to_cart(item_urls)

        # ── Step 4 – Assert cart total ────────────────────────────
        with allure.step(f"4. Assert cart total ≤ ${budget_per_item} × {len(item_urls)}"):
            cart_page = CartPage(page, screenshots_dir)
            cart_page.assert_cart_total_not_exceeds(
                budget_per_item=budget_per_item,
                items_count=len(item_urls),
            )

        logger.info(f"✅ Scenario {scenario['scenario_id']} PASSED")


# ══════════════════════════════════════════════
#  Standalone smoke test (no parametrisation)
# ══════════════════════════════════════════════

class TestSmoke:
    """Quick smoke test – verifies the eBay homepage loads."""

    @allure.story("Smoke: homepage loads")
    def test_homepage_loads(self, browser_context):
        _, page = browser_context
        page.goto("https://www.ebay.com", wait_until="domcontentloaded")
        assert "eBay" in page.title(), "eBay homepage did not load"
        logger.info("✅ Smoke test passed – eBay homepage loaded")
