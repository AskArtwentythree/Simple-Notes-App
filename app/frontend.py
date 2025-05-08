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

st.set_page_config(page_title="Simple Notes", layout="centered")


def get_backend_url() -> str:
    """
    Retrieve the base URL for the backend API.

    Reads the "backend_url" key from Streamlit secrets; if missing,
    defaults to "http://127.0.0.1:8080".

    Returns:
        str: The URL to use for all API requests.
    """
    return st.secrets.get("backend_url", "http://127.0.0.1:8080")


# Custom CSS to style each note card
st.markdown(
    """
    <style>
      .note-card {
        border: 1px solid #444;
        padding: 12px;
        border-radius: 8px;
        margin-bottom: 16px;
      }
    </style>
    """,
    unsafe_allow_html=True,
)


def api_request(path, method="GET", token=None, data=None):
    """
    Make a JSON HTTP request to the backend and handle errors.

    Builds the full URL by prepending the backend base URL,
    attaches a Bearer token (if provided), and attempts to
    parse the response body as JSON.

    Parameters:
    -----------
    path : str
        The API path (e.g. "/notes" or "/notes/1").
    method : str, optional
        The HTTP method to use (default: "GET").
    token : str or None, optional
        A Bearer token for the Authorization header (default: None).
    data : dict or None, optional
        A JSON‐serializable payload for POST/PATCH (default: None).

    Returns:
    --------
    dict or list or {}
        The parsed JSON response, or an empty dict if no response body.
    None
        If an HTTP or network error occurred (and was reported via st.error).

    Side Effects:
    -------------
    - Calls `st.error(...)` on any HTTP or connection error.
    """
    url = f"{get_backend_url()}{path}"
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        r = requests.request(
          method, url, json=data, headers=headers, timeout=5)
        r.raise_for_status()

        if not r.text:
            return {}

        try:
            return r.json()
        except ValueError:
            return {}

    except requests.HTTPError:
        msg = ""
        try:
            msg = r.json().get("error", "")
        except Exception:
            pass
        st.error(f"API Error: {msg or r.status_code}")

    except requests.RequestException as e:
        st.error(f"Connection Error: {e}")

    return None


def do_translate_callback(content_key: str):
    """
    Callback to translate the current note content from Russian to English.

    Reads the raw content from `st.session_state[content_key]`,
    calls the `/translate` endpoint, and on success replaces
    `session_state[content_key]` with the translated text.

    Parameters:
    -----------
    content_key : str
        The session_state key under which the note's content is stored.

    Side Effects:
    -------------
    - May call `st.error(...)` if the API call fails.
    """
    res = api_request(
        "/translate",
        "POST",
        token=st.session_state.token,
        data={"query": st.session_state[content_key]},
    )
    if res and res.get("translation"):
        st.session_state[content_key] = res["translation"]


# Ensure session_state keys exist
st.session_state.setdefault("token", None)
st.session_state.setdefault("just_saved", False)


if st.session_state.token is None:
    _ = """
    Render and process the authentication sidebar.

    If unauthenticated, shows a "Sign In"/"Sign Up" toggle.
    On Sign Up: validates email/username/password, then POSTs to /sign_up.
    On Sign In: validates username/password, then POSTs to /sign_in.
    On success: sets `session_state.token`, shows a success message,
    and calls `st.rerun()`.
    """
    st.sidebar.title("🔒 Authentication")
    choice = st.sidebar.radio("Navigate",
                              ["Sign In", "Sign Up"], key="auth_page")

    if choice == "Sign Up":
        st.title("Create New Account")
        email = st.text_input("Email", key="su_email")
        username = st.text_input(
          "Username", key="su_username")
        password = st.text_input(
          "Password", type="password", key="su_pass")
        confirm = st.text_input(
          "Confirm Password", type="password", key="su_confirm")

        if st.button("Sign Up", key="su_btn"):
            if not email or not username or not password:
                st.error("Fields cannot be empty.")
            elif password != confirm:
                st.error("Passwords must match.")
            else:
                resp = api_request(
                    "/sign_up",
                    "POST",
                    data={"email": email,
                          "username": username, "password": password},
                )
                if resp and resp.get("token"):
                    st.success("Account created: now sign in.")

    else:
        st.title("Welcome Back")
        u = st.text_input("Username", key="si_username")
        p = st.text_input("Password", type="password", key="si_pass")

        if st.button("Sign In", key="si_btn"):
            if not u or not p:
                st.error("Fill both fields.")
            else:
                resp = api_request(
                    "/sign_in", "POST", data={"username": u, "password": p}
                )
                if resp and resp.get("token"):
                    st.session_state.token = resp["token"]
                    st.success("Signed in!")
                    st.rerun()

    st.stop()


# Main app once authenticated
st.sidebar.success("Logged in 🎉")
if st.sidebar.button("Log out", key="logout"):
    st.session_state.token = None
    st.rerun()

params = st.query_params
note_param = params.get("note", [None])[0]

if note_param:
    _ = """
    Edit Note view:

    - Loads note via GET /notes/{id}
    - Provides Title +
    Content inputs bound to session_state
    - Buttons: Save (PATCH), Translate, Delete, Back
    """
    note_id = int(note_param)
    st.title("✏️ Edit Note")

    note = api_request(
      f"/notes/{note_id}", "GET", token=st.session_state.token)
    if not note:
        st.error("Failed to load note.")
        st.stop()

    # title field
    title_key = f"title_{note_id}"
    if title_key not in st.session_state:
        st.session_state[title_key] = note["title"]
    st.text_input("Title", key=title_key)

    # content field
    content_key = f"content_{note_id}"
    if content_key not in st.session_state:
        st.session_state[content_key] = note["content"]
    st.text_area("Content", key=content_key)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
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

    with c2:
        st.button(
            "Translate",
            key=f"trans_{note_id}",
            on_click=lambda ck=content_key: do_translate_callback(ck),
            disabled=(not st.session_state[content_key].strip()),
        )

    with c3:
        if st.button(
          "Delete Note", key=f"del_{note_id}"):
            api_request(
              f"/notes/{note_id}",
              "DELETE",
              token=st.session_state.token)
            st.query_params = {}
            st.rerun()

    with c4:
        if st.button("Back to list", key="back"):
            st.query_params = {}
            st.rerun()

else:
    _ = """
    Notes List view:

    - Shows "Saved." toast if `just_saved` was set.
    - Search box + "Add new note" POST /notes
    - Renders each note with Open & Delete buttons.
    """
    st.title("🗒️ Simple Notes")
    if st.session_state.just_saved:
        st.success("Saved.")
        st.session_state.just_saved = False

    search = st.text_input("Search notes…", key="search")
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
          f"/notes?query={search}",
          "GET",
          token=st.session_state.token) or []
    )
    for n in notes:
        nid = n.get("id")
        title = n.get("title") or "(No Title)"
        with st.container(border=True):
            col_title, col_buttons = st.columns([4, 1])
            with col_title:
                st.markdown(
                  f"<strong>{title.strip()}</strong>",
                  unsafe_allow_html=True)
            with col_buttons:
                if st.button("Open", key=f"open_{nid}"):
                    st.query_params = {"note": [str(nid)]}
                    st.rerun()
                if st.button("Delete", key=f"del_{nid}"):
                    api_request(
                      f"/notes/{nid}", "DELETE", token=st.session_state.token)
                    st.rerun()
