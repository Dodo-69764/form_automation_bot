import sys
import os
import pytest
import asyncio
from unittest.mock import patch, AsyncMock, MagicMock
import logging
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

pytest_plugins = "pytest_asyncio"
logging.basicConfig(level=logging.INFO)

from main import run_form_submission, _print_summary

def log_start(msg):
    logging.info(f"LOG: {msg}")

@pytest.mark.asyncio
async def test_run_form_submission_success(monkeypatch, tmp_path):
    log_start("test_run_form_submission_success started")
    csv_path = tmp_path / "users.csv"
    csv_path.write_text("First_Name,Last_Name,Email,Desired_Role\nJohn,Doe,john@example.com,Engineer\nJane,Smith,jane@example.com,Designer\n")

    with patch("main.FormPage") as MockFormPage, \
         patch("main.async_playwright") as mock_playwright, \
         patch("main.setup_logging"), \
         patch("logging.info") as mock_info, \
         patch("logging.error") as mock_error, \
         patch("logging.critical") as mock_critical:

        mock_browser = AsyncMock()
        mock_context = AsyncMock()
        mock_page = AsyncMock()
        mock_playwright.return_value.__aenter__.return_value.chromium.launch.return_value = mock_browser
        mock_browser.new_context.return_value = mock_context
        mock_context.new_page.return_value = mock_page

        mock_form_page = AsyncMock()
        MockFormPage.return_value = mock_form_page

        await run_form_submission(str(csv_path), "http://test-url.com")

        assert MockFormPage.call_count == 1
        assert mock_form_page.open.await_count == 2
        assert mock_form_page.fill_first_name.await_count == 2
        assert mock_form_page.fill_last_name.await_count == 2
        assert mock_form_page.fill_email.await_count == 2
        assert mock_form_page.fill_desired_role.await_count == 2
        assert mock_form_page.click_submit.await_count == 2

@pytest.mark.asyncio
async def test_run_form_submission_handles_exception(monkeypatch, tmp_path):
    log_start("test_run_form_submission_handles_exception started")
    csv_path = tmp_path / "users.csv"
    csv_path.write_text("First_Name,Last_Name,Email,Desired_Role\nJohn,Doe,john@example.com,Engineer\n")

    with patch("main.FormPage") as MockFormPage, \
         patch("main.async_playwright") as mock_playwright, \
         patch("main.setup_logging"), \
         patch("logging.info") as mock_info, \
         patch("logging.error") as mock_error, \
         patch("logging.critical") as mock_critical:

        mock_browser = AsyncMock()
        mock_context = AsyncMock()
        mock_page = AsyncMock()
        mock_playwright.return_value.__aenter__.return_value.chromium.launch.return_value = mock_browser
        mock_browser.new_context.return_value = mock_context
        mock_context.new_page.return_value = mock_page

        mock_form_page = AsyncMock()
        MockFormPage.return_value = mock_form_page
        mock_form_page.click_submit.side_effect = Exception("Submission failed")

        await run_form_submission(str(csv_path), "http://test-url.com")
        assert mock_error.called

def test_print_summary_prints_and_warns_when_empty(capsys):
    log_start("test_print_summary_prints_and_warns_when_empty started")
    with patch("logging.warning") as mock_warning:
        _print_summary([])
        assert mock_warning.called
    results = [
        {"First Name": "A", "Last Name": "B", "Email": "a@b.com", "Desired Role": "X"}
    ]
    with patch("logging.warning"):
        _print_summary(results)
        out = capsys.readouterr().out
        assert "FINAL SUBMISSION SUMMARY" in out
        assert "A" in out and "B" in out and "a@b.com" in out and "X" in out
