"""
test_demo_culprits.py — three isolated tests, one per culprit PR in tfa-demo-app.

Each test exercises ONE thing so the failures are independently attributable
during PR-causation analysis (no sequential masking).

Target app: https://kn-neeraj.github.io/tfa-demo-app/
"""

import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from conftest import DEMO_APP


class TestDemoCulprits:

    def test_cart_button_visible(self, driver):
        """
        Cart launcher (top-nav) must be present on landing.

        Catches PR3 — the navbar's cart launcher was renamed from
        id='shopping-cart-btn' to id='cart-launcher' on the app side
        without a corresponding update here.
        """
        driver.get(DEMO_APP)

        wait = WebDriverWait(driver, 8)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

        cart = driver.find_element(By.ID, "shopping-cart-btn")
        assert cart.is_displayed(), "Cart launcher should be visible on landing"

    def test_login_unlocks_premium_product(self, driver):
        """
        After logging in via option[2], the premium product card 9
        must be findable. add-to-cart-9 only renders for authenticated users.

        Catches PR4 — the login refactor writes the user profile straight
        to localStorage and never updates React state, so all auth-gated
        UI keeps rendering as anonymous.
        """
        driver.get(DEMO_APP)

        wait = WebDriverWait(driver, 10)

        driver.find_element(By.ID, "profile-btn").click()
        wait.until(EC.element_to_be_clickable((By.ID, "user-select")))
        driver.find_element(By.XPATH, "//*[@id='user-select']/option[2]").click()
        driver.find_element(By.ID, "login-submit").click()
        time.sleep(2)

        wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#add-to-cart-9"))
        )

    def test_cart_total_matches_items(self, driver):
        """
        Cart total displayed at checkout must equal the sum of line totals.

        Catches PR5 — the checkout reducer floors each line's price * quantity
        to the cent, which under-reports the total by 1 cent per line for
        prices like 499.99 (float artefact: 499.99 * 100 = 49998.999...).
        """
        driver.get(DEMO_APP)

        wait = WebDriverWait(driver, 10)

        # Sign in so cart actions persist a known user
        driver.find_element(By.ID, "profile-btn").click()
        wait.until(EC.element_to_be_clickable((By.ID, "user-select")))
        driver.find_element(By.XPATH, "//*[@id='user-select']/option[2]").click()
        driver.find_element(By.ID, "login-submit").click()
        time.sleep(2)

        # Add two products
        wait.until(EC.element_to_be_clickable((By.ID, "add-to-cart-1"))).click()
        time.sleep(1)
        driver.find_element(By.ID, "add-to-cart-2").click()
        time.sleep(1)

        # Go to cart, then checkout
        driver.find_element(By.ID, "shopping-cart-btn").click()
        time.sleep(1)
        driver.find_element(By.ID, "checkout-btn").click()
        time.sleep(1)

        # Read each displayed line total + the displayed grand total
        lines = driver.find_elements(By.CSS_SELECTOR, "li > span:nth-child(2)")
        line_totals = [float(t.text.replace("$", "")) for t in lines]
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
