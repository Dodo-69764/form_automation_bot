import sys
import os
import pytest
from unittest.mock import AsyncMock, patch, call
from pages.form_page import FormPage
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

@pytest.mark.asyncio
async def test_open_calls_goto():
    mock_page = AsyncMock()
    form = FormPage(mock_page, url="http://test-url.com", timeout=1234)
    await form.open()
    mock_page.goto.assert_awaited_once_with("http://test-url.com", timeout=1234)

@pytest.mark.asyncio
async def test_fill_first_name_uses_label_and_fallback(monkeypatch):
    mock_page = AsyncMock()
    form = FormPage(mock_page)
    mock_label_locator = AsyncMock()
    mock_label_locator.wait_for.side_effect = PlaywrightTimeoutError("Timeout")
    mock_placeholder_locator = AsyncMock()
    mock_page.get_by_label.return_value = mock_label_locator
    mock_page.locator.return_value = mock_placeholder_locator

    await form.fill_first_name("Alice")

    mock_page.get_by_label.assert_called_once_with("First Name")
    mock_label_locator.wait_for.assert_awaited_once_with(state="visible", timeout=form.timeout)
    mock_page.locator.assert_called_once_with('input[placeholder="First Name"]')
    mock_placeholder_locator.wait_for.assert_awaited_once_with(state="visible", timeout=form.timeout)
    mock_placeholder_locator.scroll_into_view_if_needed.assert_awaited_once_with(timeout=form.timeout)
    mock_placeholder_locator.fill.assert_awaited_once_with("Alice")

@pytest.mark.asyncio
async def test_fill_first_name_uses_label_success(monkeypatch):
    mock_page = AsyncMock()
    form = FormPage(mock_page)
    mock_label_locator = AsyncMock()
    mock_page.get_by_label.return_value = mock_label_locator

    await form.fill_first_name("Bob")

    mock_page.get_by_label.assert_called_once_with("First Name")
    mock_label_locator.wait_for.assert_awaited_once_with(state="visible", timeout=form.timeout)
    mock_label_locator.scroll_into_view_if_needed.assert_awaited_once_with(timeout=form.timeout)
    mock_label_locator.fill.assert_awaited_once_with("Bob")
    mock_page.locator.assert_not_called()

@pytest.mark.asyncio
async def test_click_submit_prefers_role_selector(monkeypatch):
    mock_page = AsyncMock()
    form = FormPage(mock_page)
    mock_button = AsyncMock()
    mock_page.get_by_role.return_value = mock_button

    await form.click_submit()

    mock_page.get_by_role.assert_called_with("button", name="Submit Data")
    mock_button.wait_for.assert_any_await(state="visible", timeout=form.timeout)
    mock_button.wait_for.assert_any_await(state="enabled", timeout=form.timeout)
    mock_button.scroll_into_view_if_needed.assert_awaited_once_with(timeout=form.timeout)
    mock_button.click.assert_awaited_once_with(timeout=form.timeout)
    mock_page.get_by_text.assert_not_called()

@pytest.mark.asyncio
async def test_click_submit_fallbacks_to_text_selector(monkeypatch):
    mock_page = AsyncMock()
    form = FormPage(mock_page)
    mock_button_role = AsyncMock()
    mock_button_role.wait_for.side_effect = PlaywrightTimeoutError("Timeout")
    mock_page.get_by_role.return_value = mock_button_role
    mock_button_text = AsyncMock()
    mock_page.get_by_text.return_value = mock_button_text

    await form.click_submit()

    mock_page.get_by_role.assert_called_with("button", name="Submit Data")
    mock_button_role.wait_for.assert_awaited_with(state="visible", timeout=form.timeout)
    mock_page.get_by_text.assert_called_with("Submit Data", exact=True)
    mock_button_text.wait_for.assert_any_await(state="visible", timeout=form.timeout)
    mock_button_text.wait_for.assert_any_await(state="enabled", timeout=form.timeout)
    mock_button_text.scroll_into_view_if_needed.assert_awaited_once_with(timeout=form.timeout)
    mock_button_text.click.assert_awaited_once_with(timeout=form.timeout)

@pytest.mark.asyncio
async def test_click_submit_retries_and_raises():
    mock_page = AsyncMock()
    form = FormPage(mock_page)
    mock_button_role = AsyncMock()
    mock_button_role.wait_for.side_effect = PlaywrightTimeoutError("Timeout")
    mock_page.get_by_role.return_value = mock_button_role
    mock_button_text = AsyncMock()
    mock_button_text.wait_for.side_effect = PlaywrightTimeoutError("Timeout")
    mock_page.get_by_text.return_value = mock_button_text

    with pytest.raises(PlaywrightTimeoutError):
        await form.click_submit()

    assert mock_button_role.wait_for.await_count == 3
    assert mock_button_text.wait_for.await_count == 3

@pytest.mark.asyncio
async def test_form_fill_and_submit_robust(monkeypatch):
    """
    Integration-style test: fill all fields and submit, ensuring selectors are robust.
    Simulates a dynamic submit button (ID changes, but role/text remains).
    """
    mock_page = AsyncMock()
    form = FormPage(mock_page)
    mock_label_locator = AsyncMock()
    mock_page.get_by_label.return_value = mock_label_locator
    mock_button = AsyncMock()
    mock_page.get_by_role.return_value = mock_button

    await form.fill_first_name("Alice")
    await form.fill_last_name("Smith")
    await form.fill_email("alice@example.com")
    await form.fill_desired_role("QA Engineer")
    await form.click_submit()

    assert mock_page.get_by_label.call_args_list == [call("First Name"), call("Last Name")]
    mock_page.get_by_role.assert_called_with("button", name="Submit Data")
    mock_button.click.assert_awaited_once_with(timeout=form.timeout)
