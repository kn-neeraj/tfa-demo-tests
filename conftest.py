"""
conftest.py — BrowserStack driver setup for TFA test bed.

Target app: https://browserstack.github.io/selfheal-demo-app

The browserstack-sdk Python package intercepts pytest and patches WebDriver
creation automatically when browserstack.yml is present in the working directory.
We define a standard ChromeDriver fixture here; the SDK swaps it for a
BrowserStack RemoteWebDriver at runtime.
"""

import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions

DEMO_APP = "https://kn-neeraj.github.io/tfa-demo-app"


@pytest.fixture(scope="function")
def driver():
    """
    Standard ChromeDriver fixture.
    When invoked via `browserstack-sdk pytest ...`, the SDK replaces this
    with a RemoteWebDriver using config from browserstack.yml.
    """
    options = ChromeOptions()
    options.add_argument("--start-maximized")
    d = webdriver.Chrome(options=options)
    d.implicitly_wait(0)  # No implicit wait — makes timing bugs surface naturally
    yield d
    try:
        d.quit()
    except Exception:
        pass
