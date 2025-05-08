import pytest
import requests
from streamlit.testing.v1 import AppTest

BACKEND_URL = "http://localhost:8080"
FRONTEND_FILE = "app/frontend.py"


@pytest.fixture
def test_user():
    """
    Create a unique test user payload.

    Uses a UUID suffix to avoid collisions on repeated runs.

    Returns:
        dict: A mapping with keys "username", "email", and "password".
    """
    import uuid

    unique = uuid.uuid4().hex[:6]
    return {
        "username": f"testuser_{unique}",
        "email": f"{unique}@test.com",
        "password": "Test123!",
    }


@pytest.fixture
def auth_token(test_user):
    """
    Register and authenticate the test user to obtain an auth token.

    Posts to /sign_up and then /sign_in on the backend, asserting success,
    and extracts whichever token field is returned.

    Args:
        test_user (dict): The user credentials dict from the test_user fixture.

    Returns:
        str: The bearer token for subsequent authenticated requests.
    """
    requests.post(f"{BACKEND_URL}/sign_up", json=test_user)
    resp = requests.post(
        f"{BACKEND_URL}/sign_in",
        json={"username": test_user["username"],
              "password": test_user["password"]},
    )
    resp.raise_for_status()
    data = resp.json()
    token = data.get(
      "access_token") or data.get(
        "token") or data.get(
          "auth_token")
    return token


def test_signup_form_validation_and_success(test_user):
    """
    End-to-end test of the Sign Up form validation.

    1) Loads the Streamlit app and switches to "Sign Up".
    2) Submits incomplete data to trigger validation errors.
    3) Submits mismatched passwords
    to trigger another validation.
    4) Submits correct data,
    expects a success message and token in session_state.

    Args:
        test_user (dict): The user credentials dict from the test_user fixture.
    """
    at = AppTest.from_file(FRONTEND_FILE).run()
    at.radio[0].set_value("Sign Up").run()
    at.text_input[0].set_value(test_user["email"]).run()
    at.text_input[1].set_value(test_user["username"]).run()
    at.text_input[2].set_value(test_user["password"]).run()
    at.button[0].click().run()
    assert (
        len(at.error) >= 1 or len(at.warning) >= 1
    ), "Expected validation error for missing confirm password"
    at.text_input[3].set_value("WrongPass").run()
    at.button[0].click().run()
    errors_warnings = list(at.error) + list(at.warning)
    assert any(
        "password" in e.value.lower() for e in errors_warnings
    ), "Expected validation error for password mismatch"
    at.text_input[3].set_value(test_user["password"]).run()
    at.button[0].click().run()
    assert len(at.success) >= 1, "Expected success message after signup"
    assert (
        "token" in at.session_state or "access_token" in at.session_state
    ), "Auth token should be stored in session state after signup"


def test_signin_form_validation_and_success(test_user):
    """
    End-to-end test of the Sign In form validation.

    1) Registers the test user via the backend.
    2) Loads the Streamlit app and switches to "Sign In".
    3) Submits wrong password to trigger validation.
    4) Submits correct credentials,
    expects the main app to appear and token stored.

    Args:
        test_user (dict): The user credentials dict from the test_user fixture.
    """
    requests.post(f"{BACKEND_URL}/sign_up", json=test_user)
    at = AppTest.from_file(FRONTEND_FILE).run()
    at.radio[0].set_value("Sign In").run()
    at.text_input[0].set_value(test_user["username"]).run()
    at.text_input[1].set_value("WrongPassword").run()
    at.button[0].click().run()
    assert (
        len(
          at.error) >= 1 or len(at.warning) >= 1
    ), "Expected error on wrong password"
    at.text_input[1].set_value(test_user["password"]).run()
    at.button[0].click().run()
    titles_headers = [
      el.value for el in at.title] + [el.value for el in at.header]
    assert any(
        "simple notes" in t.lower() for t in titles_headers
    ), "Expected to see Simple Notes title after login"
    assert (
        "token" in at.session_state or "access_token" in at.session_state
    ), "Auth token should be stored in session state after login"


def test_note_crud_operations(auth_token, test_user):
    """
    Full CRUD cycle for a note in the authenticated app.

    1) Launches the app with an injected auth token.
    2) Creates a new note and verifies it appears in the list.
    3) Edits the note and checks for a saved confirmation.
    4) Deletes the note, re-runs the app, and confirms it no longer appears.

    Args:
        auth_token (str): The bearer token for authentication.
        test_user (dict): The user credentials dict from the test_user fixture.
    """
    at = AppTest.from_file(FRONTEND_FILE)
    at.session_state["token"] = auth_token
    at.session_state["username"] = test_user["username"]
    at.run()

    add_btn = next(b for b in at.button if "add new note" in b.label.lower())
    add_btn.click().run()

    at.text_input[0].set_value("Test Note").run()
    at.text_area[0].set_value("This is a test note.").run()

    save_btn = next(b for b in at.button if b.label.lower() == "save")
    save_btn.click().run()

    all_text = [el.value.lower() for el in at.text] + [
        el.value.lower() for el in at.markdown
    ]
    assert any("test note" in txt for txt in all_text)

    open_btn = next(b for b in at.button if b.label.lower() == "open")
    open_btn.click().run()

    at.text_area[0].set_value("Updated content.").run()
    save_btn = next(b for b in at.button if b.label.lower() == "save")
    save_btn.click().run()
    assert any("saved" in s.value.lower() for s in at.success)

    delete_btn = next(b for b in at.button if b.label.lower() == "delete")
    delete_btn.click().run()

    at2 = AppTest.from_file(FRONTEND_FILE)
    at2.session_state["token"] = auth_token
    at2.session_state["username"] = test_user["username"]
    at2.run()

    remaining = [el.value.lower() for el in at2.text] + [
        el.value.lower() for el in at2.markdown
    ]
    assert not any(
        "test note" in txt for txt in remaining
    ), "Note should be deleted from list"


def test_note_translation(auth_token, test_user):
    """
    Test the in-app translation feature from Russian to English.

    1) Launches the app with an injected auth token.
    2) Creates a note containing Russian text.
    3) Opens that note and clicks the "Translate" button.
    4) Verifies the resulting content includes English words.

    Args:
        auth_token (str):
        The bearer token for authentication.
        test_user (dict):
        The user credentials dict from the test_user fixture.
    """
    at = AppTest.from_file(FRONTEND_FILE)
    at.session_state["token"] = auth_token
    at.session_state["username"] = test_user["username"]
    at = at.run()
    add_buttons = [
      btn for btn in at.button if "add new note" in btn.label.lower()]
    assert add_buttons, "Add new note button should be present"
    add_buttons[0].click().run()
    at.text_input[0].set_value(
      "Russian Note").run()
    at.text_area[0].set_value(
      "Привет мир").run()
    save_buttons = [btn for btn in at.button if btn.label.lower() == "save"]
    assert save_buttons, "Save button should be present"
    save_buttons[0].click().run()
    open_buttons = [btn for btn in at.button if btn.label.lower() == "open"]
    assert open_buttons, "Open button for the note should exist"
    open_buttons[0].click().run()
    translate_buttons = [
      btn for btn in at.button if "translate" in btn.label.lower()]
    assert translate_buttons, "Translate button should be present"
    translate_buttons[0].click().run()
    translated_text = at.text_area[0].value
    assert (
        "Hello" in translated_text
    ), f"Expected English translation, got: {translated_text}"
