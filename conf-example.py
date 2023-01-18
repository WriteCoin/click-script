from selenium.webdriver.common.by import By

AUTH_TOKEN = ""
DRIVER_PATH = "C:\\chromedriver-windows-x64.exe"

LIMIT_PROFILES = 50

URL = "https://example.site.com"

# By.ID, By.XPATH, By.LINK_TEXT, By.PARTIAL_LINK_TEXT, By.NAME = "name", By.TAG_NAME = "tag name", By.CLASS_NAME = "class name", By.CSS_SELECTOR = "css selector"
SELECTORS = [
    # FRAME
    {
        'by': By.CSS_SELECTOR,
        'value': '#frame_css'
    },
    # ANCHOR
    {
        'by': By.CSS_SELECTOR,
        'value': 'anchor'
    }
]
