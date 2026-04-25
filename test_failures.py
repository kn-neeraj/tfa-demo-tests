"""
test_failures.py — 8 failures for TFA skill evaluation on selfheal-demo-app.

Split into two groups:

SIMPLE BASELINES (3) — guaranteed to fire, obvious root cause.
  These give us a floor: if TFA can't diagnose these, it can't diagnose anything.
  S1 - NoSuchElementException: element ID that does not exist
  S2 - AssertionError: wrong expected page title
  S3 - TimeoutException: wait with correct selector but zero setup

HARD FAILURES (5) — non-trivial, require reading the command log sequence.
  The exception type alone is insufficient for root cause.
  F1 - ElementNotInteractableException: Submit clicked before animation settles
  F2 - StaleElementReferenceException: stale ref after navigate away + back
  F3 - AssertionError: cart count wrong because login was silently skipped
  F4 - Cascading failure: NoSuchElementException at step 6, bug is at step 2
  F5 - TimeoutException: element exists in app but prerequisite steps skipped

Ground truth from Java passing tests (BStackDemoTest.java):
  - cta-button click triggers ~2s CSS animation (Java uses Thread.sleep(2000))
  - progress-status-id text updates in-place (no DOM re-render on same node)
  - add-to-cart-9 / product-card-9 requires authenticated state
  - user-select option[2] = real user; option[1] = blank placeholder
  - All element IDs confirmed real from passing Java test runs
"""

import time
import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    ElementNotInteractableException,
    StaleElementReferenceException,
    TimeoutException,
    NoSuchElementException,
)
from conftest import DEMO_APP


# ===========================================================================
# SIMPLE BASELINES — obvious failures, easy RCA, set the floor
# ===========================================================================

class TestSimpleBaselines:

    def test_s1_element_does_not_exist(self, driver):
        """
        S1 — NoSuchElementException on a made-up element ID.

        Root cause (obvious): The ID 'submit-payment-btn' does not exist
        anywhere on selfheal-demo-app. Any TFA tool should immediately
        identify this as a bad/wrong selector in the test code.

        Expected exception: TimeoutException (via WebDriverWait)
        Diagnostic difficulty: Very low — error message contains the selector,
        and no command history is needed.
        """
        driver.get(DEMO_APP)

        wait = WebDriverWait(driver, 5)
        # This element has never existed on this app
        wait.until(
            EC.presence_of_element_located((By.ID, "submit-payment-btn"))
        )

    def test_s2_wrong_page_title_assertion(self, driver):
        """
        S2 — AssertionError: hardcoded wrong expected title.

        Root cause (obvious): Test asserts title is "BrowserStack Demo Store"
        but the actual title is "browserstack-selfheal-demo". This is a
        copy-paste error in the test — the wrong app's title was used.

        Expected exception: AssertionError with both values visible in message.
        Diagnostic difficulty: Very low — the actual vs expected values are
        printed directly in the assertion failure message.
        """
        driver.get(DEMO_APP)

        # Wait for page to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        # Wrong title — copied from a different test suite targeting bstackdemo.com
        assert driver.title == "BrowserStack Demo Store", \
            f"Expected 'BrowserStack Demo Store' but got '{driver.title}'"

    def test_s3_wait_timeout_missing_cta_click(self, driver):
        """
        S3 — TimeoutException: waiting for element that requires a prior click.

        Root cause (obvious): static-id-field only appears AFTER clicking
        cta-button. The test goes directly to waiting for it without the
        prerequisite click. Any TFA tool should note the absence of the
        cta-button click in the command history.

        Expected exception: TimeoutException after 5 seconds.
        Diagnostic difficulty: Low-medium — the exception is clear, but you
        do need to look at the command log to see what step was missing.
        """
        driver.get(DEMO_APP)

        # BUG: Skipping cta-button click entirely.
        # static-id-field is inside a section that is hidden until CTA is clicked.
        wait = WebDriverWait(driver, 5)
        wait.until(
            EC.element_to_be_clickable((By.ID, "static-id-field"))
        )
        driver.find_element(By.ID, "static-id-field").send_keys("this will never run")


# ===========================================================================
# HARD FAILURES — require reading the full command log for correct RCA
# ===========================================================================

class TestHardFailures:

    def test_f1_click_intercepted_mid_animation(self, driver):
        """
        F1 — ElementNotInteractableException: Submit clicked before animation settles.

        Why it's hard:
          The element IS found in the DOM. EC.element_to_be_clickable passes
          because Selenium checks visibility + enabled state, not CSS animation
          completion. The Submit button is technically visible but the containing
          section is still sliding in via CSS transition when we click it.
          On BrowserStack infra (slightly slower rendering than local), this
          reliably produces an interactability error or a misfire on a covered
          element.

          The error message says "element not interactable" or "other element
          would receive the click" — but doesn't say WHY. TFA must:
            1. See the cta-button click in the command log
            2. Notice the ABSENCE of any sleep/wait after that click
            3. See the immediate find + click on static-id-field
            4. Recognize the animation race pattern

          Ground truth: BStackDemoTest.java does Thread.sleep(2000) here.
          We intentionally omit it.

        Root cause (known): No wait after CTA animation trigger.
        """
        driver.get(DEMO_APP)
        assert driver.title == "browserstack-selfheal-demo"

        # Trigger the CTA — starts CSS slide-in animation for the demo section
        driver.find_element(By.ID, "cta-button").click()

        # BUG: No sleep or wait. Animation takes ~2s (confirmed by Java test).
        # The Submit button is in the animating container and not yet stable.

        # These field interactions may or may not succeed depending on timing
        try:
            driver.find_element(By.ID, "static-id-field").send_keys("animation test")
            driver.find_element(By.XPATH, "//div[@id='xpath-form']/input").send_keys("test")
        except Exception:
            pass

        # This click fires mid-animation — should fail on BrowserStack infra
        # where rendering is slower than developer's local machine
        driver.find_element(By.XPATH, "//button[@title='Submit']").click()

        # If click somehow lands, the next step will fail because Proceed
        # won't be present yet either
        time.sleep(0.1)  # Minimal delay — nowhere near the 2s needed
        driver.find_element(By.XPATH, "//button[text()='Proceed']").click()

    def test_f2_stale_element_after_page_navigation(self, driver):
        """
        F2 — StaleElementReferenceException after full page reload.

        Why it's hard:
          The element reference was 100% valid when obtained. Staleness is
          caused by navigating away from the page and back — which destroys
          and recreates all DOM nodes. The exception says "element is not
          attached to the page document" which looks like a bad selector.
          TFA must read the command log to see:
            1. Element was found successfully on first page load
            2. driver.get() was called (navigation away + back)
            3. The OLD reference was used after navigation — that's the bug

          This is a realistic production pattern: tests that cache element
          references across page navigations.

        Root cause (known): Element reference cached before navigation,
          used after navigation causes full DOM teardown.
        """
        driver.get(DEMO_APP)

        wait = WebDriverWait(driver, 10)

        # Step 1: Get a valid reference to the CTA button
        cta_button = wait.until(
            EC.presence_of_element_located((By.ID, "cta-button"))
        )
        # Verify it works right now
        assert cta_button.is_displayed()

        # Step 2: Navigate away (simulates a test helper that changes page)
        driver.get("https://browserstack.github.io/selfheal-demo-app/")
        time.sleep(1)

        # Step 3: BUG — using the old reference after navigation.
        # All DOM nodes from the previous page load are now detached.
        # This will throw StaleElementReferenceException.
        cta_button.click()

        # If somehow that worked, the next assertion will fail differently
        time.sleep(2)
        assert driver.find_element(By.ID, "static-id-field").is_displayed()

    def test_f3_cart_count_wrong_due_to_skipped_login(self, driver):
        """
        F3 — AssertionError: cart count 3 != 4 because login was skipped.

        Why it's hard:
          Fails with "Expected 4 items in cart, got 3". Looks like one of
          the add-to-cart clicks failed, or there's a cart bug. But reading
          the command log reveals no login step was ever performed.

          product-card-9 / add-to-cart-9 only renders for authenticated users
          (confirmed: BStackDemoTest.java does login BEFORE add-to-cart-9,
          and it's the only product using CSS selector #add-to-cart-9 rather
          than a positional selector).

          The silent failure: the find_element for add-to-cart-9 either throws
          a caught exception or clicks the wrong element — no assertion guards
          it, so the test continues with 3 items.

          TFA must correlate: missing login command → card-9 not rendered →
          4th add-to-cart silently fails → assertion fails at cart check.

        Root cause (known): Login prerequisite skipped; product-card-9
          requires auth state that was never established.
        """
        driver.get(DEMO_APP)

        wait = WebDriverWait(driver, 10)

        # BUG: No login step. In the working test, profile-btn → user-select
        # → login-submit comes first. Skipped entirely here.

        # First 3 add-to-cart actions work for anonymous users
        wait.until(EC.element_to_be_clickable((By.ID, "add-to-cart-1"))).click()
        time.sleep(1)

        card2 = driver.find_element(By.ID, "product-card-2")
        card2.find_element(By.CSS_SELECTOR, "#add-to-cart-2").click()
        time.sleep(1)

        driver.find_element(By.ID, "add-to-cart-3").click()
        time.sleep(1)

        # 4th add-to-cart: product-card-9 requires auth — won't render
        # Exception is swallowed so test continues, giving no signal
        try:
            driver.find_element(By.CSS_SELECTOR, "#add-to-cart-9").click()
        except (NoSuchElementException, TimeoutException):
            pass  # Intentionally silent — this is what makes it hard to diagnose
        time.sleep(1)

        # Navigate to cart
        driver.find_element(By.ID, "shopping-cart-btn").click()
        time.sleep(1)

        # This fails: 3 items in cart, expected 4
        cart_items = driver.find_elements(By.ID, "cart-item")
        assert len(cart_items) == 4, \
            f"Expected 4 items in cart, got {len(cart_items)}"

    def test_f4_cascading_failure_login_silent_at_step2(self, driver):
        """
        F4 — NoSuchElementException at step 6; real bug is at step 2.

        Why it's hard:
          The test fails at the very end when looking for the order/invoice.
          The exception message and stack trace point to step 6. A shallow TFA
          tool will say "invoice element not found — checkout failed". But
          the real cause is at step 2: option[1] in user-select is the blank
          placeholder. Selecting it and clicking login-submit proceeds without
          error but leaves the user unauthenticated.

          All intermediate steps (add-to-cart, checkout button) may appear
          to work — the app may allow anonymous cart usage — but place-order
          requires auth and silently does nothing or redirects. No order is
          created, so no order-list-item exists.

          TFA must trace backwards:
            step 6: NoSuchElementException on li.order-list-item
            → step 5: place-order-btn was clicked (but did it work?)
            → step 4: checkout-btn was clicked
            → step 3: login-submit was clicked after selecting option[1]
            → step 2: option[1] = blank — user was never authenticated
            → ROOT CAUSE: wrong option index in user select

        Root cause (known): option[1] is the blank placeholder;
          correct selector is option[2]. Silent auth failure cascades.
        """
        driver.get(DEMO_APP)

        wait = WebDriverWait(driver, 10)

        # Step 1: Open profile modal
        driver.find_element(By.ID, "profile-btn").click()
        time.sleep(1)

        # Step 2: BUG — option[1] is the blank placeholder (index is 1-based in XPath)
        # The working test uses option[2]. No exception is raised here.
        driver.find_element(By.XPATH, "//*[@id='user-select']/option[1]").click()

        # Step 3: Click Sign In — proceeds silently with no user selected
        driver.find_element(By.ID, "login-submit").click()
        time.sleep(2)

        # Steps 4a-4d: Add products — works partially for anonymous users
        wait.until(EC.element_to_be_clickable((By.ID, "add-to-cart-1"))).click()
        time.sleep(1)
        driver.find_element(By.ID, "add-to-cart-2").click()
        time.sleep(1)

        # Step 5: Attempt checkout flow
        driver.find_element(By.ID, "shopping-cart-btn").click()
        time.sleep(1)
        driver.find_element(By.ID, "checkout-btn").click()
        time.sleep(1)
        driver.find_element(By.ID, "place-order-btn").click()
        time.sleep(2)

        # Step 6: Look for order — FAILS here. No order was created because
        # the user was never authenticated. The exception lands here but the
        # bug is 4 steps back.
        driver.execute_script("window.scrollTo(0, 0)")
        first_order = driver.find_element(By.CSS_SELECTOR, "li.order-list-item")
        order_id = first_order.get_attribute("data-order-id")
        driver.find_element(By.ID, f"view-invoice-btn-{order_id}").click()

    def test_f5_timeout_element_exists_but_setup_skipped(self, driver):
        """
        F5 — TimeoutException on progress-btn-100 which genuinely exists in the app.

        Why it's hard:
          TimeoutException normally means "element is absent from the page".
          But progress-btn-100 IS a real element in this app — the Java
          passing test clicks it successfully. The timeout occurs because
          progress-btn-100 is inside a section that only renders after:
            1. Clicking cta-button
            2. Filling static-id-field
            3. Filling xpath-form
            4. Clicking Submit (title='Submit')
            5. Clicking Proceed button
            6. Clicking feature-toggle

          All 6 steps are skipped here. We go straight to waiting for
          progress-btn-100. It will never appear.

          A shallow TFA will say "element not found — selector may be wrong".
          The correct RCA: element exists conditionally after a prerequisite
          interaction chain that was entirely omitted from this test.

          TFA must notice: after driver.get(), the ONLY command is
          WebDriverWait for progress-btn-100. No CTA click, no form filling,
          no Submit, no Proceed, no toggle. The entire setup chain is absent.

        Root cause (known): 6 prerequisite interaction steps completely
          skipped before waiting for a conditionally-rendered element.
        """
        driver.get(DEMO_APP)

        # BUG: Skipping ALL prerequisites:
        #   driver.find_element(By.ID, "cta-button").click()       ← missing
        #   time.sleep(2)                                           ← missing
        #   ... fill static-id-field ...                            ← missing
        #   ... fill xpath-form ...                                 ← missing
        #   driver.find_element(By.XPATH, "//button[@title='Submit']").click()  ← missing
        #   driver.find_element(By.XPATH, "//button[text()='Proceed']").click() ← missing
        #   driver.find_element(By.CLASS_NAME, "feature-toggle").click()        ← missing

        # Jump straight to the progress button — it will never appear
        wait = WebDriverWait(driver, 15)
        wait.until(
            EC.element_to_be_clickable((By.ID, "progress-btn-100"))
        )

        # These lines will never execute
        driver.find_element(By.ID, "progress-btn-100").click()
        assert driver.find_element(By.ID, "progress-status-id").text == "Status: Complete"
