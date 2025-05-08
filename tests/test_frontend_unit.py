import pytest
import streamlit as st
import requests

import app.frontend as F


@pytest.fixture(autouse=True)
def clear_secrets_and_session(monkeypatch):
    """
    Clear Streamlit secrets and session state before and after each test.

    This fixture allows tests to be executed in isolation,
    erasing any remaining secrets or session state.
    """
    st.secrets.clear()
    st.session_state.clear()
    yield
    st.secrets.clear()
    st.session_state.clear()


def test_get_backend_url_default():
    """
    Test that get_backend_url returns the default URL when no secret is set.

    Verifies that the fallback value "http://127.0.0.1:8080" is returned
    when st.secrets does not contain "backend_url".
    """
    assert F.get_backend_url() == "http://127.0.0.1:8080"


def test_api_request_success_json(requests_mock):
    """
    Test api_request returns parsed JSON on a successful GET.

    Mocks a GET to /notes returning JSON {"foo":"bar"} and verifies
    that api_request returns the same dict.
    """
    url = "http://127.0.0.1:8080/notes"
    requests_mock.get(url, json={"foo": "bar"})
    r = F.api_request("/notes", method="GET", token=None)
    assert r == {"foo": "bar"}


def test_api_request_empty_body(requests_mock):
    """
    Test api_request handles a 204 No Content response.

    Mocks a DELETE to /notes/1 returning status 204 with empty body,
    and verifies that api_request returns an empty dict.
    """
    url = "http://127.0.0.1:8080/notes/1"
    requests_mock.delete(url, status_code=204, text="")
    r = F.api_request("/notes/1", method="DELETE", token="tok")
    assert r == {}


def test_api_request_http_error_shows_error(monkeypatch, requests_mock):
    """
    Test api_request logs an error message on HTTPError.

    Mocks a GET to /fail returning status 500 with {"error":"oops"}.
    Ensures api_request returns None and calls st.error with the
    appropriate message prefix.
    """
    url = "http://127.0.0.1:8080/fail"
    requests_mock.get(url, status_code=500, json={"error": "oops"})
    errors = []
    monkeypatch.setattr(st, "error", lambda msg: errors.append(msg))
    r = F.api_request("/fail", method="GET", token=None)
    assert r is None
    assert "API Error: oops" in errors[0]


def test_api_request_connection_error(monkeypatch):
    """
    Test api_request logs an error on network failure.

    Monkeypatches requests.request to raise RequestException, and
    verifies that api_request returns None and calls st.error with
    "Connection Error: ..." message.
    """

    def bad_request(*args, **kwargs):
        raise requests.RequestException("conn failed")

    monkeypatch.setattr(requests, "request", bad_request)
    errors = []
    monkeypatch.setattr(st, "error", lambda msg: errors.append(msg))

    r = F.api_request("/any", method="GET", token=None)
    assert r is None
    assert "Connection Error: conn failed" in errors[0]
