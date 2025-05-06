import streamlit as st
import requests

API_URL = st.secrets.get("backend_url", "http://localhost:8080")

if 'token' not in st.session_state or not st.session_state.token:
    st.error("Not authorized. Please log in first.")
    st.stop()

def logout():
    st.session_state.token = None
    st.rerun()

# Loading note
def load_notes():
    headers = {"Authorization": f"Bearer {st.session_state.token}"}
    resp = requests.get(f"{API_URL}/notes", headers=headers)
    if resp.status_code == 200:
        return resp.json()
    else:
        st.error(f"Error loading notes: {resp.json().get('error')}")
        return []

# Deleting note
def delete_note(note_id):
    headers = {"Authorization": f"Bearer {st.session_state.token}"}
    resp = requests.delete(f"{API_URL}/notes/{note_id}", headers=headers)
    if resp.status_code == 200:
        st.success("Note deleted.")
        st.rerun()
    else:
        st.error(f"Failed to delete: {resp.json().get('error')}")

# UI
st.set_page_config(page_title="Simple Notes", layout="centered")
st.markdown("<h1 style='color: black;'>📝 Simple Notes</h1>", unsafe_allow_html=True)

# Log out button
st.button("Log out", on_click=logout)

# Search bar
search_query = st.text_input("Search", placeholder="Search notes...")

# Add button
if st.button("➕ Add new note"):
    st.warning("....")

# Notes list
notes = load_notes()

for idx, note in enumerate(notes):
    with st.container():
        st.markdown(f"### {note['title']}")
        col1, col2 = st.columns(2)

        with col1:
            if st.button("Open", key=f"open_{idx}"):
                st.warning("...")

        with col2:
            if st.button("Delete", key=f"delete_{idx}"):
                delete_note(note["id"])
