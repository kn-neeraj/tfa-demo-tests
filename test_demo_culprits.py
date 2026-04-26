"""
test_demo_culprits.py — three small isolated checks against the deployed app.

Target app: https://kn-neeraj.github.io/tfa-demo-app/
"""

import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from conftest import DEMO_APP


class TestDemoCulprits:

    def test_cart_button_visible(self, driver):
        """The cart launcher in the top nav must be present on landing."""
        driver.get(DEMO_APP)

        wait = WebDriverWait(driver, 8)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

        cart = driver.find_element(By.ID, "shopping-cart-btn")
        assert cart.is_displayed(), "Cart launcher should be visible on landing"

    def test_navbar_shows_user_after_login(self, driver):
        """After logging in via the user dropdown, the navbar profile button
        must show the user's full display name."""
        driver.get(DEMO_APP)

        wait = WebDriverWait(driver, 10)

        driver.find_element(By.ID, "profile-btn").click()
        wait.until(EC.element_to_be_clickable((By.ID, "user-select")))
        driver.find_element(By.XPATH, "//*[@id='user-select']/option[2]").click()
        driver.find_element(By.ID, "login-submit").click()
        time.sleep(2)

        profile = wait.until(EC.presence_of_element_located((By.ID, "profile-btn")))
        text = profile.text.strip()
        assert "Demo One" in text, (
            f"Expected 'Demo One' in profile-btn after login, got: {text!r}"
        )

    def test_cart_total_matches_items(self, driver):
        """The order total displayed at checkout must equal the sum of the
        per-line item amounts shown on the same page."""
        driver.get(DEMO_APP)

        wait = WebDriverWait(driver, 10)

        driver.find_element(By.ID, "profile-btn").click()
        wait.until(EC.element_to_be_clickable((By.ID, "user-select")))
        driver.find_element(By.XPATH, "//*[@id='user-select']/option[2]").click()
        driver.find_element(By.ID, "login-submit").click()
        time.sleep(2)

        wait.until(EC.element_to_be_clickable((By.ID, "add-to-cart-1"))).click()
        time.sleep(1)
        driver.find_element(By.ID, "add-to-cart-2").click()
        time.sleep(1)

        driver.find_element(By.CSS_SELECTOR, "a[href='/tfa-demo-app/cart']").click()
        time.sleep(2)

        cart_items = driver.find_elements(By.ID, "cart-item")
        assert len(cart_items) >= 2, (
            f"Cart unexpectedly empty before checkout: found {len(cart_items)} items"
        )

        driver.find_element(By.ID, "checkout-btn").click()
        time.sleep(2)

        lines = driver.find_elements(By.CSS_SELECTOR, "li > span:nth-child(2)")
        line_totals = [float(t.text.replace("$", "")) for t in lines]
        assert len(line_totals) >= 2, (
            f"Checkout page missing line items: only {len(line_totals)} spans found"
        )
        expected_total = round(sum(line_totals), 2)

        total_el = wait.until(
            EC.presence_of_element_located(
                (By.XPATH, "//*[contains(text(),'Total: $')]")
            )
        )
        displayed_total = float(total_el.text.split("$")[-1])

        assert displayed_total == expected_total, (
            f"Cart total mismatch: displayed={displayed_total}, "
            f"sum of lines={expected_total}"
        )
