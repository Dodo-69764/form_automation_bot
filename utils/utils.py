import logging
import sys
async def get_page():
    """
    Initialize and configure a Playwright browser and return a new page.
    """
    from playwright.async_api import async_playwright

    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=False, args=[
        "--start-maximized",
        "--disable-notifications",
        "--disable-infobars"
    ])
    context = await browser.new_context(
        viewport={"width": 1920, "height": 1080},
        ignore_https_errors=True
    )
    page = await context.new_page()
    return page

def setup_logging():
    """
    Centralized logging configuration for the project.
    Ensures consistent logging format and output.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        stream=sys.stdout,
        force=True
    )
