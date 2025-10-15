import sys
import os
import utils.utils as utils
import pytest
from unittest.mock import patch, MagicMock


sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

@pytest.mark.asyncio
async def test_get_page_initializes_playwright(monkeypatch):

    mock_playwright = MagicMock()
    mock_browser = MagicMock()
    mock_context = MagicMock()
    mock_page = MagicMock()
    monkeypatch.setattr("utils.utils.async_playwright", lambda: mock_playwright)
    mock_playwright.start.return_value = mock_playwright
    mock_playwright.chromium.launch.return_value = mock_browser
    mock_browser.new_context.return_value = mock_context
    mock_context.new_page.return_value = mock_page

    async def fake_start(): return mock_playwright
    async def fake_launch(*args, **kwargs): return mock_browser
    async def fake_new_context(*args, **kwargs): return mock_context
    async def fake_new_page(*args, **kwargs): return mock_page

    mock_playwright.start = fake_start
    mock_playwright.chromium.launch = fake_launch
    mock_browser.new_context = fake_new_context
    mock_context.new_page = fake_new_page

    page = await utils.get_page()
    assert page == mock_page

    
def test_setup_logging_configures_logging(monkeypatch):
    with patch("utils.utils.logging") as mock_logging, patch("utils.utils.sys") as mock_sys:
        utils.setup_logging()
        assert mock_logging.basicConfig.called
        kwargs = mock_logging.basicConfig.call_args.kwargs
        assert kwargs["level"] == mock_logging.INFO
        assert "format" in kwargs
        assert kwargs["stream"] == mock_sys.stdout
        assert kwargs["force"] is True
