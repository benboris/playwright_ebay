"""
conftest.py - Pytest hooks for automatic screenshots on failure
and Allure report integration.
"""
import os
import pytest
import allure
from playwright.sync_api import Page


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Attach a screenshot to the Allure report on test failure."""
    outcome = yield
    rep = outcome.get_result()

    if rep.when == "call" and rep.failed:
        # Try to get the page from the browser_context fixture
        browser_context_fixture = item.funcargs.get("browser_context")
        if browser_context_fixture:
            _, page = browser_context_fixture
            try:
                screenshot = page.screenshot(full_page=True)
                allure.attach(
                    screenshot,
                    name=f"failure_{item.name}",
                    attachment_type=allure.attachment_type.PNG,
                )
            except Exception as e:
                print(f"Could not capture failure screenshot: {e}")
