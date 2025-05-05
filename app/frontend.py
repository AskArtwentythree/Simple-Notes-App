import streamlit as st
import requests

# ------------------------
# Configuration
# ------------------------
def get_backend_url() -> str:
    return st.secrets.get("backend_url", "http://127.0.0.1:8080")

# ------------------------
# API helper
# ------------------------
def api_request(path, method='GET', token=None, data=None):
    url = f"{get_backend_url()}{path}"
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        r = requests.request(method, url, json=data, headers=headers, timeout=5)
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

# ------------------------
# Session State init
# ------------------------
st.session_state.setdefault("token", None)

# ------------------------
# Page Configuration
# ------------------------
st.set_page_config(page_title="Simple Notes", layout="centered")

# ------------------------
# Authentication Sidebar
# ------------------------
if st.session_state.token is None:
    st.sidebar.title("🔒 Authentication")
    auth_page = st.sidebar.radio("Navigate", ["Sign In", "Sign Up"], key="auth_page")

    if auth_page == "Sign Up":
        st.title("Create New Account")
        email    = st.text_input("Email", key="su_email")
        username = st.text_input("Username", key="su_username")
        password = st.text_input("Password", type="password", key="su_pass")
        confirm  = st.text_input("Confirm Password", type="password", key="su_confirm")
        if st.button("Sign Up", key="su_btn"):
            if not email or not username or not password:
                st.error("Email, username, and password cannot be empty.")
            elif password != confirm:
                st.error("Passwords do not match.")
            else:
                resp = api_request(
                    "/sign_up", "POST",
                    data={"email": email, "username": username, "password": password}
                )
                if resp and resp.get("token"):
                    st.success("Account created! You can now sign in.")
    else:
        st.title("Welcome Back")
        username = st.text_input("Username", key="si_username")
        password = st.text_input("Password", type="password", key="si_pass")
        if st.button("Sign In", key="si_btn"):
            if not username or not password:
                st.error("Please fill in both fields.")
            else:
                resp = api_request(
                    "/sign_in", "POST",
                    data={"username": username, "password": password}
                )
                if resp and resp.get("token"):
                    st.session_state.token = resp["token"]
                    st.success("Signed in successfully!")
                    st.rerun()

    st.stop()

# ------------------------
# Main Application
# ------------------------
# If we get here, token is present
st.sidebar.success("Logged in 🎉")

def logout():
    st.session_state.token = None
    st.rerun()

if st.sidebar.button("Log out", key="logout_btn"):
    logout()

st.title("🗒️ Simple Notes")

# Fetch notes
notes = api_request(f"/notes?query=", "GET", token=st.session_state.token) or []

# Add & Search (search not wired yet)
col_search, col_add = st.columns([3,1])
with col_search:
    st.text_input("Search", placeholder="Search notes...", key="search")
with col_add:
    st.button("➕ Add new note", key="add_btn")

for i, note in enumerate(notes):
    note_id = note.get('id')
    title = note.get('title', '(No Title)')
    st.markdown(f"### {title}")

    if not note_id:
        st.error("Note is missing an ID. Cannot perform actions.")
        continue

    c1, c2 = st.columns(2)

    with c1:
        if st.button("Open", key=f"open_{i}"):
            st.warning("Note editor not implemented in this view.")

    with c2:
        if st.button("Delete", key=f"delete_{i}"):
            api_request(f"/notes/{note_id}", "DELETE", token=st.session_state.token)
            st.success("Deleted.")
            st.rerun()
