import json
import os
from unittest.mock import MagicMock

import pytest
from starlette.requests import Request

os.environ.setdefault("SECRET_KEY", "test-secret-key-minimum-32-bytes!!!!")

from app.api.utils.utils import rest_api_response  # noqa: E402
from app.logging.logger import AppLogger  # noqa: E402


def _parse(response) -> dict:
    return json.loads(response.body)


def _make_request(mock_adapter=None) -> Request:
    """Build a minimal Starlette Request with an optional logger_adapter on app.state."""
    mock_app = MagicMock()
    if mock_adapter is not None:
        mock_app.state.logger_adapter = mock_adapter
    else:
        # getattr(..., None) must return None  -  simulate missing attribute
        del mock_app.state.logger_adapter
        mock_app.state = MagicMock(spec=[])  # no logger_adapter attribute
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/",
        "query_string": b"",
        "headers": [],
        "app": mock_app,
    }
    return Request(scope)


class TestRestApiResponse:
    def test_default_returns_200_success(self):
        response = rest_api_response()
        assert response.status_code == 200
        body = _parse(response)
        assert body["success"] is True
        assert body["message"] == ""
        assert body["data"] == {}

    def test_failure_with_custom_status(self):
        response = rest_api_response(success=False, message="Not found", status_code=404)
        assert response.status_code == 404
        body = _parse(response)
        assert body["success"] is False
        assert body["message"] == "Not found"

    def test_data_is_included_in_body(self):
        response = rest_api_response(data={"user_id": "abc"})
        assert _parse(response)["data"] == {"user_id": "abc"}

    def test_data_defaults_to_empty_dict_when_none(self):
        response = rest_api_response(data=None)
        assert _parse(response)["data"] == {}

    def test_500_status_code(self):
        response = rest_api_response(success=False, status_code=500)
        assert response.status_code == 500

    def test_response_always_has_three_keys(self):
        body = _parse(rest_api_response())
        assert set(body.keys()) == {"success", "message", "data"}

    def test_logger_adapter_called_when_present(self):
        mock_adapter = MagicMock()
        rest_api_response(success=True, message="ok", request=_make_request(mock_adapter))
        mock_adapter.log.assert_called_once()
        _, kwargs = mock_adapter.log.call_args
        assert kwargs["level"] == AppLogger.Level.INFO

    def test_logger_adapter_uses_error_level_for_5xx(self):
        mock_adapter = MagicMock()
        rest_api_response(
            success=False, status_code=500, request=_make_request(mock_adapter)
        )
        _, kwargs = mock_adapter.log.call_args
        assert kwargs["level"] == AppLogger.Level.ERROR

    def test_logger_adapter_uses_warn_level_for_4xx(self):
        mock_adapter = MagicMock()
        rest_api_response(
            success=False, status_code=400, request=_make_request(mock_adapter)
        )
        _, kwargs = mock_adapter.log.call_args
        assert kwargs["level"] == AppLogger.Level.WARN
