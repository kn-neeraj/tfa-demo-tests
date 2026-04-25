"""
test_passing.py — 3 tests that reliably PASS on selfheal-demo-app.

These establish a baseline: if these fail, there's an infra or setup issue,
not a problem with our failure-engineering. They mirror the style of
BStackDemoTest.java from the self-healing reference repo.

App: https://browserstack.github.io/selfheal-demo-app
"""

import time
import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from conftest import DEMO_APP


class TestPassingScenarios:
    """Baseline passing tests — should always succeed."""

    def test_page_title_and_cta(self, driver):
        """
        Verify the demo app loads and the CTA button is clickable.

        Steps:
        1. Navigate to demo app
        2. Assert page title matches 'browserstack-selfheal-demo'
        3. Click 'Try Demo Scenarios' CTA button
        4. Assert the demo scenarios section becomes visible
        """
        driver.get(DEMO_APP)

        assert driver.title == "browserstack-selfheal-demo", \
            f"Unexpected title: {driver.title}"

        # Click the CTA button — same selector as BStackDemoTest.java
        driver.find_element(By.ID, "cta-button").click()
        time.sleep(2)

        # Verify demo scenario fields are now visible
        wait = WebDriverWait(driver, 10)
        static_field = wait.until(
            EC.visibility_of_element_located((By.ID, "static-id-field"))
        )
        assert static_field.is_displayed(), "Demo scenario fields should be visible after CTA click"

    def test_demo_scenarios_form_interaction(self, driver):
        """
        Walk through the demo scenarios form — type into fields, click buttons.
        Mirrors testDemoScenarios() from BStackDemoTest.java.

        Steps:
        1. Load page, click CTA
        2. Type into static-id-field (ID selector)
        3. Type into xpath-form input (XPath selector)
        4. Click Submit button (title attribute selector)
        5. Click Proceed button (text selector)
        6. Toggle feature toggle (class name selector)
        7. Assert progress bar starts In Progress, click to 100%, assert Complete
        """
        driver.get(DEMO_APP)
        driver.find_element(By.ID, "cta-button").click()
        time.sleep(2)

        # ID Attribute scenario
        driver.find_element(By.ID, "static-id-field").send_keys("TFA test run")

        # XPath scenario
        driver.find_element(By.XPATH, "//div[@id='xpath-form']/input").send_keys("xpath field test")

        # Content description change — button with title attribute
        driver.find_element(By.XPATH, "//button[@title='Submit']").click()
        time.sleep(1)

        # Text change scenario
        driver.find_element(By.XPATH, "//button[text()='Proceed']").click()
        time.sleep(1)

        # Class name change — feature toggle
        driver.find_element(By.CLASS_NAME, "feature-toggle").click()

        # Progress bar — ID change scenario
        assert driver.find_element(By.ID, "progress-status-id").text == "Status: In Progress"
        driver.find_element(By.ID, "progress-btn-100").click()
        time.sleep(1)
        assert driver.find_element(By.ID, "progress-status-id").text == "Status: Complete"

    def test_user_flow_login_and_cart(self, driver):
        """
        Full user flow: login, add products to cart, checkout.
        Mirrors testUserFlow() from BStackDemoTest.java.

        Steps:
        1. Load page, click Profile
        2. Select a user from the dropdown
        3. Sign in
        4. Add 4 products to cart via different selector strategies
        5. Navigate to cart, assert 4 items
        6. Checkout and place order
        7. View invoice
        """
        driver.get(DEMO_APP)

        wait = WebDriverWait(driver, 15)

        # Profile / login
        driver.find_element(By.ID, "profile-btn").click()
        driver.find_element(By.XPATH, "//*[@id='user-select']/option[2]").click()
        driver.find_element(By.ID, "login-submit").click()
        time.sleep(2)

        # Add 4 products using different selector strategies
        card1 = driver.find_element(By.ID, "product-card-1")
        card1.find_element(By.XPATH, ".//button[@title='Add to Cart']").click()
        time.sleep(1)

        card2 = driver.find_element(By.ID, "product-card-2")
        card2.find_element(By.CSS_SELECTOR, "#add-to-cart-2").click()
        time.sleep(1)

        driver.find_element(By.ID, "add-to-cart-3").click()
        time.sleep(1)

        driver.find_element(By.CSS_SELECTOR, "#add-to-cart-9").click()
        time.sleep(1)

        # Navigate to cart
        driver.find_element(By.ID, "shopping-cart-btn").click()

        # Assert 4 items in cart
        cart_items = driver.find_elements(By.ID, "cart-item")
        assert len(cart_items) == 4, f"Expected 4 items in cart, got {len(cart_items)}"

        # Checkout
        driver.find_element(By.ID, "checkout-btn").click()
        driver.find_element(By.ID, "place-order-btn").click()
        time.sleep(2)

        # View invoice for first order
        driver.execute_script("window.scrollTo(0, 0)")
        first_order = driver.find_element(By.CSS_SELECTOR, "li.order-list-item")
        order_id = first_order.get_attribute("data-order-id")
        driver.find_element(By.ID, f"view-invoice-btn-{order_id}").click()
        time.sleep(2)
