import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pytest
import requests

from api_interface import ApiInterface


@pytest.fixture
def api():
    return ApiInterface(
        control_ip="127.0.0.1",
        control_port=8080,
        control_token="test-token",
    )


# -------------------------
# make_request
# -------------------------

def test_make_request_get(api, mocker):
    mock_get = mocker.patch.object(api, "_get_endpoint", return_value=(True, {"ok": True}))

    result = api.make_request("status")

    mock_get.assert_called_once_with("status")
    assert result == (True, {"ok": True})


def test_make_request_post(api, mocker):
    payload = {"a": 1}
    mock_post = mocker.patch.object(api, "_post_endpoint", return_value=(True, {"ok": True}))

    result = api.make_request("update", payload)

    mock_post.assert_called_once_with("update", payload)
    assert result == (True, {"ok": True})


# -------------------------
# _post_endpoint
# -------------------------

def test_post_endpoint_success(api, mocker):
    mock_response = mocker.Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"result": "ok"}

    mock_post = mocker.patch("requests.post", return_value=mock_response)

    success, data = api._post_endpoint("update", {"x": 1})

    assert success is True
    assert data == {"result": "ok"}
    mock_post.assert_called_once()
    assert "Authorization" in api.headers
    assert api.headers["Content-Type"] == "application/json"


def test_post_endpoint_non_200(api, mocker):
    mock_response = mocker.Mock()
    mock_response.status_code = 400
    mock_response.text = "bad request"

    mocker.patch("requests.post", return_value=mock_response)

    success, data = api._post_endpoint("update", {"x": 1})

    assert success is False
    assert "error" in data
    assert data["error"] == "bad request"


def test_post_endpoint_exception(api, mocker):
    mocker.patch(
        "requests.post",
        side_effect=requests.exceptions.RequestException("connection error"),
    )

    success, data = api._post_endpoint("update", {"x": 1})

    assert success is False
    assert "connection error" in data["error"]


# -------------------------
# _get_endpoint
# -------------------------

def test_get_endpoint_success(api, mocker):
    mock_response = mocker.Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"status": "ok"}

    mock_get = mocker.patch("requests.get", return_value=mock_response)

    success, data = api._get_endpoint("status")

    assert success is True
    assert data == {"status": "ok"}
    mock_get.assert_called_once()
    assert "Authorization" in api.headers
    assert "Content-Type" not in api.headers


def test_get_endpoint_non_200(api, mocker):
    mock_response = mocker.Mock()
    mock_response.status_code = 500
    mock_response.text = "server error"

    mocker.patch("requests.get", return_value=mock_response)

    success, data = api._get_endpoint("status")

    assert success is False
    assert data["error"] == "server error"


def test_get_endpoint_exception(api, mocker):
    mocker.patch(
        "requests.get",
        side_effect=requests.exceptions.RequestException("timeout"),
    )

    success, data = api._get_endpoint("status")

    assert success is False
    assert "timeout" in data["error"]


# -------------------------
# Main entry
# -------------------------

if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__]))

