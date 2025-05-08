from app.db import DatabaseManager
from app.date_utils import current_timestamp_millis, next_day_timestamp_millis
import sqlite3
from unittest.mock import patch
from app.entity.note import Note
import uuid


def test_create_user(db):
    """Test creating a new user."""
    (user_id, _) = db.create_user("newuser", "secure_password", "new@example.com")
    user = db.get_user_by_id(user_id)
    assert user["username"] == "newuser"
    assert user["email"] == "new@example.com"


def test_create_user_duplicate_username(db):
    """Test creating a user with a duplicate username."""
    db.create_user("duplicateuser", "password123", "unique@example.com")
    user_data = db.create_user(
        "duplicateuser", "anotherpassword", "another@example.com")
    assert user_data is DatabaseManager.USER_ALREADY_EXISTS


def test_create_user_duplicate_email(db):
    """Test creating a user with a duplicate email."""
    db.create_user("uniqueuser", "password123", "duplicate@example.com")
    user_data = db.create_user(
        "anotheruser", "anotherpassword", "duplicate@example.com")
    assert user_data is DatabaseManager.USER_ALREADY_EXISTS


def test_verify_user(db, test_user_id):
    """Test verifying an existing user."""
    (user_id, _) = db.verify_user("testuser", "password123")
    assert user_id == test_user_id


def test_verify_user_invalid_credentials(db):
    """Test verifying a user with invalid credentials."""
    user_data = db.verify_user("testuser", "wrong_password")
    assert user_data is DatabaseManager.INVALID_PASSWORD


def test_verify_user_user_not_found(db):
    """Test verifying a user that does not exist"""
    user_data = db.verify_user("nonexistentuser", "password")
    assert user_data is DatabaseManager.USER_NOT_FOUND


def test_create_note(db, test_user_id):
    """Test creating a new note."""
    note_id = db._create_note(test_user_id, "Test Note", "This is a test note.")
    assert note_id is not None
    note = db._get_note(note_id, test_user_id)
    assert note.title == "Test Note"
    assert note.content == "This is a test note."


def test_close_connection(db):
    """Test closing the database connection."""
    db.close()
    assert db.conn is None
    assert db.cursor is None


def test_update_note(db, test_user_id):
    """Test updating an existing note."""
    note_id = db._create_note(test_user_id, "Original Title", "Original Content")
    updated = db._update_note(note_id, test_user_id, "Updated Title", "Updated Content")
    assert updated == "ok"
    note = db._get_note(note_id, test_user_id)
    assert note.title == "Updated Title"
    assert note.content == "Updated Content"

    db.cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='Tokens'")
    assert db.cursor.fetchone() is not None

def test_update_note_not_found(db, test_user_id):
    """Test updating a note that doesn't exist for the user."""
    updated = db._update_note(999, test_user_id, "Updated Title", "Updated Content")
    assert updated == DatabaseManager.NOTE_NOT_FOUND


def test_delete_note(db, test_user_id):
    """Test deleting a note."""
    note_id = db._create_note(test_user_id, "To Delete", "Delete Me")
    deleted = db._delete_note(note_id, test_user_id)
    assert deleted == DatabaseManager.OK
    note = db._get_note(note_id, test_user_id)
    assert note == DatabaseManager.NOTE_NOT_FOUND


def test_delete_nonexistent_note(db, test_user_id):
    """Test deleting a note that doesn't exist."""
    deleted = db._delete_note(999, test_user_id)
    assert deleted == DatabaseManager.NOTE_NOT_FOUND


def test_get_user_by_id(db):
    """Test getting a user by ID."""
    (user_id, _) = db.create_user("testuser2", "password123", "test2@example.com")
    user = db.get_user_by_id(user_id)
    assert user is not None
    assert user["username"] == "testuser2"
    assert user["email"] == "test2@example.com"


def test_create_user_duplicate_username(db):
    """Test creating a user with a duplicate username."""
    db.create_user("duplicateuser", "password123", "unique@example.com")
    user_data = db.create_user(
        "duplicateuser", "anotherpassword", "another@example.com"
    )
    assert user_data is DatabaseManager.USER_ALREADY_EXISTS
