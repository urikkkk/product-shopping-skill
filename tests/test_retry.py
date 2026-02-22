"""Tests for the retry/backoff logic in BaseAdapter._get()."""

from unittest.mock import MagicMock, patch

import httpx
import pytest

from src.adapters.base import BaseAdapter, MAX_RETRIES


class ConcreteAdapter(BaseAdapter):
    """Concrete subclass for testing base functionality."""
    name = "test"
    _min_delay = 0.0  # No throttle in tests


def _make_adapter_with_mock_client():
    """Create an adapter with a mocked HTTP client."""
    adapter = ConcreteAdapter(mode="seed")
    mock_client = MagicMock(spec=httpx.Client)
    adapter._client = mock_client
    return adapter, mock_client


class TestRetry:
    def test_succeeds_first_try(self):
        adapter, mock_client = _make_adapter_with_mock_client()
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.raise_for_status = MagicMock()
        mock_client.get.return_value = mock_response

        resp = adapter._get("https://example.com/api")
        assert resp is mock_response
        assert mock_client.get.call_count == 1

    @patch("src.adapters.base.time.sleep")
    def test_retries_on_transport_error(self, mock_sleep):
        adapter, mock_client = _make_adapter_with_mock_client()
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.raise_for_status = MagicMock()
        mock_client.get.side_effect = [
            httpx.ConnectError("Connection refused"),
            mock_response,
        ]

        resp = adapter._get("https://example.com/api")
        assert resp is mock_response
        assert mock_client.get.call_count == 2

    @patch("src.adapters.base.time.sleep")
    def test_retries_on_http_status_error(self, mock_sleep):
        adapter, mock_client = _make_adapter_with_mock_client()

        mock_response_ok = MagicMock(spec=httpx.Response)
        mock_response_ok.raise_for_status = MagicMock()

        error_request = MagicMock(spec=httpx.Request)
        error_response = MagicMock(spec=httpx.Response)
        error_response.status_code = 503
        error_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Service Unavailable", request=error_request, response=error_response,
        )

        mock_client.get.side_effect = [error_response, mock_response_ok]
        resp = adapter._get("https://example.com/api")
        assert resp is mock_response_ok

    @patch("src.adapters.base.time.sleep")
    def test_max_retries_then_raises(self, mock_sleep):
        adapter, mock_client = _make_adapter_with_mock_client()
        mock_client.get.side_effect = httpx.ConnectError("Connection refused")

        with pytest.raises(httpx.ConnectError):
            adapter._get("https://example.com/api")
        assert mock_client.get.call_count == MAX_RETRIES

    @patch("src.adapters.base.time.sleep")
    def test_backoff_delay_increases(self, mock_sleep):
        adapter, mock_client = _make_adapter_with_mock_client()
        mock_client.get.side_effect = httpx.ConnectError("Connection refused")

        with pytest.raises(httpx.ConnectError):
            adapter._get("https://example.com/api")

        # Should have slept MAX_RETRIES - 1 times (no sleep after last failure)
        assert mock_sleep.call_count == MAX_RETRIES - 1
        # Each delay should be larger than the previous (exponential)
        delays = [call.args[0] for call in mock_sleep.call_args_list]
        for i in range(1, len(delays)):
            assert delays[i] > delays[i - 1]
