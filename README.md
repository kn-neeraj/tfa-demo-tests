# BrowserStack Automate Test Bed

A complete pytest test suite for evaluating a Test Failure Analysis skill against BrowserStack Automate and https://bstackdemo.com.

## Test Suite Overview

This test bed contains **8 total tests**: 3 that **PASS** reliably and 5 that **FAIL** with known, specific failure types.

### Passing Tests (test_passing.py)

- **test_valid_login**: Tests the login flow using dropdown selections
- **test_add_to_cart**: Tests adding a product to the shopping cart
- **test_search_product**: Tests filtering products by vendor (Apple)

### Failing Tests (test_failures.py)

Each test is designed to fail with a distinct, identifiable root cause:

1. **test_broken_selector**: `TimeoutException` / `NoSuchElementException`
   - Root cause: Locator matches no element on the page

2. **test_race_condition_checkout**: `AssertionError`
   - Root cause: Cart total hasn't been updated yet (AJAX/animation not complete)

3. **test_assertion_wrong_title**: `AssertionError`
   - Root cause: Test code has wrong expected value (page title mismatch)

4. **test_timeout_slow_page**: `TimeoutException`
   - Root cause: Wait time too short for page/element to load

5. **test_stale_element_after_sort**: `StaleElementReferenceException`
   - Root cause: Element reference becomes stale after DOM re-render

## Setup

### Prerequisites

- Python 3.8+
- BrowserStack account with valid credentials
- Internet access to BrowserStack hub and bstackdemo.com

### Installation

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set up environment variables (create a `.env` file in the `test_bed` directory):
   ```
   BROWSERSTACK_USERNAME=your_username
   BROWSERSTACK_ACCESS_KEY=your_access_key
   BROWSERSTACK_BUILD_NAME=optional-build-name
   ```

   Alternatively, export them in your shell:
   ```bash
   export BROWSERSTACK_USERNAME="your_username"
   export BROWSERSTACK_ACCESS_KEY="your_access_key"
   ```

## Running Tests

### Run All Tests
```bash
pytest -v
```

### Run Only Passing Tests
```bash
pytest -v test_passing.py
```

### Run Only Failing Tests
```bash
pytest -v test_failures.py
```

### Run a Specific Test
```bash
pytest -v test_passing.py::TestPassingScenarios::test_valid_login
```

### Run with More Verbose Output
```bash
pytest -v -s
```

## Test Configuration

The test suite uses the following configuration (set in `conftest.py`):

- **Browser**: Chrome (latest version)
- **Operating System**: Windows 11
- **Project Name**: `TFA-Skill-TestBed`
- **Build Name**: Auto-generated with timestamp if not provided via env var
- **Debug Options Enabled**:
  - Browser console logs (verbose)
  - Network logs
  - Selenium logs

Each test automatically:
- Creates a unique session on BrowserStack
- Marks the test result (passed/failed) on BrowserStack
- Cleans up the driver after test completion

## BrowserStack Session Management

All tests run on BrowserStack Automate using the W3C capabilities format. Test results are automatically marked in the BrowserStack dashboard:

- Passed tests show as "✓ Passed"
- Failed tests show as "✗ Failed" with failure details

## Debugging

To view test results in BrowserStack:

1. Log in to BrowserStack Automate
2. Look for sessions under the "TFA-Skill-TestBed" project
3. Each test session shows:
   - Screenshots from the test
   - Network activity
   - Browser console logs
   - Selenium logs

## Test Reliability Notes

### Passing Tests

- Use explicit waits (`WebDriverWait`) with 10-second timeouts
- Target stable elements that exist on page load
- Wait for elements to be clickable/visible before interacting

### Failing Tests

- **test_race_condition_checkout**: Simulates missing AJAX updates by clearing cart count
- **test_timeout_slow_page**: Uses 1-second implicit waits (too short for page load)
- **test_stale_element_after_sort**: Relies on DOM re-render between element capture and interaction
- **test_broken_selector**: Uses intentionally non-existent element IDs
- **test_assertion_wrong_title**: Uses known-incorrect expected values

## Notes for TFA Skill Development

This test bed is designed to:

1. Provide realistic test failures with clear root causes
2. Generate BrowserStack logs and debugging data
3. Allow the Test Failure Analysis skill to practice failure categorization
4. Demonstrate diverse failure patterns (timeout, assertion, stale element, race condition, selector)
5. Run on real browsers via BrowserStack cloud

Use these test results to train and evaluate failure analysis capabilities.
