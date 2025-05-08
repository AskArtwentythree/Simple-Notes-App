"""
Simple Notes frontend.

This module implements the Streamlit UI for:
  - user authentication (sign in / sign up)
  - creating, editing, deleting notes via a JSON API
  - translating note content from Russian to English

All API communication is handled by a small helper that
prepends the backend base URL, sends a Bearer token, parses
JSON, and surfaces any errors via `st.error()`.
"""

import streamlit as st
import requests


def get_backend_url() -> str:
    """
    Retrieve the base URL for the backend API.

    Reads the "backend_url" key from Streamlit secrets; if missing,
    defaults to "http://127.0.0.1:8080".

    Returns:
        str: The URL to use for all API requests.
    """
    return st.secrets.get("backend_url", "http://127.0.0.1:8080")


def _safe_json_parse(response: requests.Response):
    """
    Attempt to parse a requests.Response as JSON.

    Returns {} on empty body or invalid JSON.
    """
    try:
        return response.json()
    except ValueError:
        return {}


def api_request(
  path: str,
  method: str = "GET",
  token: str = None,
  data: dict = None):
    """
    Make a JSON HTTP request to the backend and handle errors.

    Builds the full URL by prepending the backend base URL, attaches
    a Bearer token if provided, and then parses the response body.

    Parameters:
    -----------
    path : str
        The API path (e.g. "/notes" or "/notes/1").
    method : str, optional
        The HTTP method to use (default: "GET").
    token : str or None, optional
        A Bearer token for Authorization header (default: None).
    data : dict or None, optional
        A JSON-serializable payload for POST/PATCH (default: None).

    Returns:
    --------
    dict or list or {}
        The parsed JSON response, or an empty dict if no response body.
    None
        If an HTTP or network error occurred and an error was displayed.

    Side Effects:
    -------------
    - Calls `st.error(...)` on any HTTP or connection error.
    """
    url = f"{get_backend_url()}{path}"
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        resp = requests.request(
          method, url, json=data, headers=headers, timeout=5)
        resp.raise_for_status()
        # parse or return empty dict
        return _safe_json_parse(resp)

    except requests.HTTPError:
        # try to pull error message from JSON, else show status code
        err = _safe_json_parse(resp).get("error", "")
        st.error(f"API Error: {err or resp.status_code}")
        return None

    except requests.RequestException as exc:
        st.error(f"Connection Error: {exc}")
        return None


def do_translate_callback(content_key: str):
    """
    Translate the current note content from Russian to English.

    Reads the raw content from `st.session_state[content_key]`,
    calls the `/translate` endpoint, and on success replaces
    `session_state[content_key]` with the translated text.

    Parameters:
    -----------
    content_key : str
        The session_state key under which the note's content is stored.
    """
    result = api_request(
        "/translate",
        "POST",
        token=st.session_state.token,
        data={"query": st.session_state[content_key]},
    )
    if result and result.get("translation"):
        st.session_state[content_key] = result["translation"]


def _render_sign_up() -> None:
    """
    Render the Sign Up form and handle its submission.
    """
    st.title("Create New Account")
    email = st.text_input("Email", key="su_email")
    user = st.text_input("Username", key="su_username")
    pwd = st.text_input("Password", type="password", key="su_pass")
    confirm = st.text_input(
      "Confirm Password", type="password", key="su_confirm")

    if not st.button("Sign Up", key="su_btn"):
        return

    if not (email and user and pwd):
        st.error("Fields cannot be empty.")
    elif pwd != confirm:
        st.error("Passwords must match.")
    else:
        resp = api_request(
            "/sign_up",
            "POST",
            data={"email": email, "username": user, "password": pwd},
        )
        if resp and resp.get("token"):
            st.success("Account created: now sign in.")


def _render_sign_in() -> None:
    """
    Render the Sign In form and handle its submission.
    """
    st.title("Welcome Back")
    user = st.text_input("Username", key="si_username")
    pwd = st.text_input("Password", type="password", key="si_pass")

    if not st.button("Sign In", key="si_btn"):
        return

    if not (user and pwd):
        st.error("Fill both fields.")
    else:
        resp = api_request(
          "/sign_in", "POST", data={"username": user, "password": pwd})
        if resp and resp.get("token"):
            st.session_state.token = resp["token"]
            st.success("Signed in!")
            st.rerun()


def render_auth() -> None:
    """
    Render and process the authentication sidebar.

    If unauthenticated, shows a "Sign In"/"Sign Up" toggle,
    and calls the appropriate helper.
    """
    st.sidebar.title("🔒 Authentication")
    choice = st.sidebar.radio(
      "Navigate", ["Sign In", "Sign Up"], key="auth_page")
    if choice == "Sign Up":
        _render_sign_up()
    else:
        _render_sign_in()
    st.stop()


def _save_note(note_id: int, title_key: str, content_key: str) -> None:
    """
    Handle the Save button in the Edit Note view.
    """
    if st.button("Save", key=f"save_{note_id}"):
        api_request(
            f"/notes/{note_id}",
            "PATCH",
            token=st.session_state.token,
            data={
                "title": st.session_state[title_key],
                "content": st.session_state[content_key],
            },
        )
        st.session_state.just_saved = True
        st.query_params = {}
        st.rerun()


def _translate_button(content_key: str) -> None:
    """
    Render the Translate button in the Edit Note view.
    """
    st.button(
        "Translate",
        key=f"trans_{content_key}",
        on_click=do_translate_callback,
        args=(content_key,),
        disabled=not st.session_state[content_key].strip(),
    )


def _delete_note_button(note_id: int) -> None:
    """
    Handle the Delete Note button in the Edit Note view.
    """
    if st.button("Delete Note", key=f"del_{note_id}"):
        api_request(
          f"/notes/{note_id}", "DELETE", token=st.session_state.token)
        st.query_params = {}
        st.rerun()


def _back_button() -> None:
    """
    Handle the Back to list button in the Edit Note view.
    """
    if st.button("Back to list", key="back"):
        st.query_params = {}
        st.rerun()


def render_editor() -> None:
    """
    Render the Edit Note view with Save,
    Translate, Delete, and Back.
    """
    note_id = int(st.query_params["note"][0])
    st.title("✏️ Edit Note")

    note = api_request(
      f"/notes/{note_id}", "GET", token=st.session_state.token)
    if not note:
        st.error("Failed to load note.")
        st.stop()

    tkey = f"title_{note_id}"
    ckey = f"content_{note_id}"
    st.session_state.setdefault(tkey, note["title"])
    st.session_state.setdefault(ckey, note["content"])

    st.text_input("Title", key=tkey)
    st.text_area("Content", key=ckey)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        _save_note(note_id, tkey, ckey)
    with c2:
        _translate_button(ckey)
    with c3:
        _delete_note_button(note_id)
    with c4:
        _back_button()


def _render_note_card(n: dict) -> None:
    """
    Render a single note in the list with Open & Delete buttons.
    """
    nid = n.get("id")
    title = n.get("title") or "(No Title)"
    with st.container(border=True):
        col, buttons = st.columns([4, 1])
        with col:
            st.markdown(
              f"**{title.strip()}**", unsafe_allow_html=True)
        with buttons:
            if st.button(
              "Open", key=f"open_{nid}"):
                st.query_params = {"note": [str(nid)]}
                st.rerun()
            if st.button("Delete", key=f"del_{nid}"):
                api_request(
                  f"/notes/{nid}", "DELETE", token=st.session_state.token)
                st.rerun()


def render_list() -> None:
    """
    Render the Notes List view with Add, Search, Open, and Delete.
    """
    st.title("🗒️ Simple Notes")
    if st.session_state.just_saved:
        st.success("Saved.")
        st.session_state.just_saved = False

    search = st.text_input(
      "Search notes…", key="search")
    if st.button("➕ Add new note", key="add"):
        new = api_request(
            "/notes",
            "POST",
            token=st.session_state.token,
            data={"title": "", "content": ""},
        )
        if new and new.get("note_id"):
            st.query_params = {"note": [str(new["note_id"])]}
            st.rerun()

    notes = (
        api_request(
          f"/notes?query={search}", "GET", token=st.session_state.token) or []
    )
    for note in notes:
        _render_note_card(note)


def main() -> None:
    """
    Entry point for the Streamlit app.

    - Sets page config and CSS
    - Initializes session_state
    - Routes to authentication, editor, or list views
    """
    st.set_page_config(page_title="Simple Notes", layout="centered")
    st.markdown(
        """
        <style>
          .note-card { border: 1px solid #444;
          padding: 12px; border-radius: 8px; margin-bottom: 16px; }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.session_state.setdefault("token", None)
    st.session_state.setdefault("just_saved", False)

    if st.session_state.token is None:
        render_auth()
        return

    st.sidebar.success("Logged in 🎉")
    if st.sidebar.button("Log out", key="logout"):
        st.session_state.token = None
        st.rerun()

    if "note" in st.query_params:
        render_editor()
    else:
        render_list()


if __name__ == "__main__":
    main()
