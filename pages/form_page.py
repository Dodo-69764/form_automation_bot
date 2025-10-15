import logging
from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError

logging.basicConfig(level=logging.INFO)

class FormPage:
    """Web form page object for automation using Playwright."""

    def __init__(self, page: Page, url: str, timeout: int = 15000) -> None:
        """Initialize FormPage."""
        self.page: Page = page
        self.URL: str = url
        self.timeout: int = timeout
    async def get_present_fields(self) -> set:
        """
        Detect which fields are present on the form at runtime.
        Returns a set of field names as used in the automation logic.
        """
        present_fields = set()
        # Map form field labels/placeholders to canonical field names
        field_map = {
            "First Name": "First Name",
            "Last Name": "Last Name",
            "Email": "Email",
            "Desired Role": "Desired Role"
        }
        for label, canonical in field_map.items():
            locator = self.page.get_by_label(label)
            try:
                await locator.wait_for(state="visible", timeout=2000)
                present_fields.add(canonical)
                continue
            except Exception:
                pass
            locator = self.page.locator(f'input[placeholder="{label}"]')
            try:
                await locator.wait_for(state="visible", timeout=2000)
                present_fields.add(canonical)
            except Exception:
                pass
        return present_fields

    async def open(self) -> None:
        """Open the form page."""
        await self.page.goto(self.URL, timeout=self.timeout)

    async def _fill_field_by_label_or_placeholder(self, label: str, value: str) -> None:
        """
        Fill an input field by its label (preferred) or placeholder (fallback).
        """
        locator = self.page.get_by_label(label)
        try:
            await locator.wait_for(state="visible", timeout=self.timeout)
        except PlaywrightTimeoutError:
            locator = self.page.locator(f'input[placeholder="{label}"]')
            await locator.wait_for(state="visible", timeout=self.timeout)
        await locator.scroll_into_view_if_needed(timeout=self.timeout)
        await locator.fill(value)

    async def fill_first_name(self, first_name: str) -> None:
        """Fill first name field using label or placeholder."""
        await self._fill_field_by_label_or_placeholder("First Name", first_name)

    async def fill_last_name(self, last_name: str) -> None:
        """Fill last name field using label or placeholder."""
        await self._fill_field_by_label_or_placeholder("Last Name", last_name)

    async def fill_email(self, email: str) -> None:
        """Fill email field."""
        await self._fill_field_by_label_or_placeholder("Email", email)

    async def fill_desired_role(self, desired_role: str) -> None:
        """Fill desired role field."""
        await self._fill_field_by_label_or_placeholder("Desired Role", desired_role)

    async def submit_and_handle_alert(self) -> str:
        """
        Click the Submit button, then wait for and handle the browser's success alert/dialog.
        Returns the alert message.

        After clicking, also sends a space bar keypress.
        """
        button = self.page.get_by_role("button", name="Submit Data")
        logging.debug("[DEBUG] Resolved submit button locator: %s", button)
        await button.wait_for(state="visible", timeout=self.timeout)
        logging.debug("[DEBUG] Submit button is visible and ready.")
        await button.scroll_into_view_if_needed(timeout=self.timeout)
        logging.debug("[DEBUG] Submit button scrolled into view.")
        # Only click and wait for the alert to be handled by the global handler in main.py
        logging.debug("[DEBUG] Attaching dialog handler and clicking submit button...")
        await button.click(timeout=self.timeout)
        logging.debug("[DEBUG] Clicked submit button, sending space bar keypress...")
        await self.page.keyboard.press("Space")
        # No need to handle dialog here, global handler will accept it
        return "Alert handled by global dialog handler."
