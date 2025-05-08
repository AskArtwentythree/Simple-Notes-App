from app.db import DatabaseManager
from app.date_utils import current_timestamp_millis, next_day_timestamp_millis
import sqlite3
from unittest.mock import patch
from app.entity.note import Note
import uuid


def test_create_user(db):
    """Test creating a new user."""
    (user_id, _) = db.create_user(
        "newuser", "secure_password", "new@example.com")
    user = db.get_user_by_id(user_id)
    assert user['username'] == "newuser"
    assert user['email'] == "new@example.com"


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


def test_database_connection(db):
    """Test the database connection."""
    assert db.conn is not None
    assert db.cursor is not None


def test_close_connection(db):
    """Test closing the database connection."""
    db.close()
    assert db.conn is None
    assert db.cursor is None


def test_database_creation(db):
    """Test if the database tables are created."""
    db.cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='Users'")
    assert db.cursor.fetchone() is not None

    db.cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='Tokens'")
    assert db.cursor.fetchone() is not None

    db.cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='Notes'")
    assert db.cursor.fetchone() is not None


def test_get_user_by_id(db):
    """Test getting a user by ID."""
    (user_id, _) = db.create_user(
        "testuser2", "password123", "test2@example.com")
    user = db.get_user_by_id(user_id)
    assert user is not None
    assert user['username'] == "testuser2"
    assert user['email'] == "test2@example.com"


def test_get_user_by_id_not_found(db):
    """Test getting a user by ID when the user does not exist."""
    user = db.get_user_by_id(999)
    assert user is None


def test_get_user_id_from_token(db, test_user_id):
    """Test getting a user ID from a valid token."""
    db.cursor.execute("SELECT value FROM Tokens WHERE user_id = ?",
                      (test_user_id,))
    token_data = db.cursor.fetchone()
    token = token_data['value']
    user_id = db.get_user_id_from_token(token)
    assert user_id == test_user_id


def test_get_user_id_from_token_invalid_token(db):
    """Test getting a user ID from an invalid token."""
    user_id = db.get_user_id_from_token("invalid_token")
    assert user_id is DatabaseManager.INVALID_TOKEN


def test_get_user_id_from_token_expired_token(db, test_user_id):
    """Test getting a user ID from an expired token."""
    token_value = "expired_token"
    expiration = current_timestamp_millis() - 1000

    db.cursor.execute(
        """INSERT OR REPLACE INTO Tokens (user_id, value, expiration)
        VALUES (?, ?, ?)""",
        (test_user_id, token_value, expiration)
    )
    db.conn.commit()

    user_id = db.get_user_id_from_token(token_value)
    assert user_id is DatabaseManager.TOKEN_EXPIRED


def test_get_user_by_id_error(db):
    """Test the get_user_by_id method handles errors correctly"""
    with patch.object(db, 'cursor', create=True) as mock_cursor:
        mock_cursor.execute.side_effect = sqlite3.Error("Simulated error")
        result = db.get_user_by_id(1)
    assert result == DatabaseManager.USER_NOT_FOUND


def _refresh_token(db, test_user_id):
    """Helper function to refresh the user token."""
    token_value = str(uuid.uuid4())
    expiration = next_day_timestamp_millis()

    db.cursor.execute(
        """INSERT OR REPLACE INTO Tokens (user_id, value, expiration)
        VALUES (?, ?, ?)""",
        (test_user_id, token_value, expiration)
    )
    db.conn.commit()
    return token_value


def test_create_note_success(db, test_user_id):
    """Test creating a note using a valid token."""
    token = _refresh_token(db, test_user_id)

    note_id = db.create_note(token, "My Note", "Note content")
    assert isinstance(note_id, int)


def test_create_note_invalid_token(db):
    """Test creating a note using an invalid token."""
    note_id = db.create_note("invalid_token", "My Note", "Note content")
    assert note_id is DatabaseManager.INVALID_TOKEN


def test_create_note_expired_token(db, test_user_id):
    """Test creating a note using an expired token."""
    token_value = "expired_token"
    expiration = current_timestamp_millis() - 1000

    db.cursor.execute(
        """INSERT OR REPLACE INTO Tokens (user_id, value, expiration)
        VALUES (?, ?, ?)""",
        (test_user_id, token_value, expiration)
    )
    db.conn.commit()
    note_id = db.create_note(token_value, "My Note", "Note content")
    assert note_id is DatabaseManager.TOKEN_EXPIRED


def test_get_note_success(db, test_user_id):
    """Test getting a note using a valid token."""
    token = _refresh_token(db, test_user_id)

    note_id = db._create_note(
        test_user_id, "Test Note", "This is a test note.")
    note = db.get_note(note_id, token)
    assert isinstance(note, Note)
    assert note.note_id == note_id


def test_get_note_invalid_token(db, test_user_id):
    """Test getting a note using an invalid token."""
    note_id = 1
    note = db.get_note(note_id, "invalid_token")
    assert note is DatabaseManager.INVALID_TOKEN


def test_get_note_expired_token(db, test_user_id):
    """Test getting a note using an expired token."""
    token_value = "expired_token"
    expiration = current_timestamp_millis() - 1000

    db.cursor.execute(
        """INSERT OR REPLACE INTO Tokens (user_id, value, expiration)
        VALUES (?, ?, ?)""",
        (test_user_id, token_value, expiration)
    )
    db.conn.commit()
    note_id = 1
    note = db.get_note(note_id, token_value)
    assert note is DatabaseManager.TOKEN_EXPIRED


def test_get_note_note_not_found(db, test_user_id):
    """Test getting a note that doesn't exist."""
    token = _refresh_token(db, test_user_id)
    note = db.get_note(999, token)
    assert note is DatabaseManager.NOTE_NOT_FOUND


def test_update_note_success(db, test_user_id):
    """Test updating a note using a valid token."""
    token = _refresh_token(db, test_user_id)
    note_id = db._create_note(test_user_id, "Original Title",
                              "Original Content")
    status = db.update_note(note_id, token,
                            "Updated Title", "Updated Content")
    assert status == DatabaseManager.OK
    note = db._get_note(note_id, test_user_id)
    assert note.title == "Updated Title"
    assert note.content == "Updated Content"


def test_update_note_invalid_token(db):
    """Test updating a note using an invalid token."""
    note_id = 1
    status = db.update_note(note_id, "invalid_token",
                            "Updated Title", "Updated Content")
    assert status is DatabaseManager.INVALID_TOKEN


def test_update_note_expired_token(db, test_user_id):
    """Test updating a note using an expired token."""
    token_value = "expired_token"
    expiration = current_timestamp_millis() - 1000

    db.cursor.execute(
        """INSERT OR REPLACE INTO Tokens (user_id, value, expiration)
        VALUES (?, ?, ?)""",
        (test_user_id, token_value, expiration)
    )
    db.conn.commit()
    note_id = 1
    status = db.update_note(note_id, token_value,
                            "Updated Title", "Updated Content")
    assert status is DatabaseManager.TOKEN_EXPIRED


def test_update_note_not_found(db, test_user_id):
    """Test updating a note that doesn't exist for the user."""
    updated = db._update_note(999, test_user_id, "Updated Title",
                              "Updated Content")
    assert updated == DatabaseManager.NOTE_NOT_FOUND


def test_delete_note_success(db, test_user_id):
    """Test deleting a note using a valid token."""
    token = _refresh_token(db, test_user_id)

    note_id = db._create_note(test_user_id, "To Delete", "Delete Me")
    status = db.delete_note(note_id, token)
    assert status == DatabaseManager.OK
    note = db._get_note(note_id, test_user_id)
    assert note == DatabaseManager.NOTE_NOT_FOUND


def test_delete_nonexistent_note(db, test_user_id):
    """Test deleting a note that doesn't exist."""
    deleted = db._delete_note(999, test_user_id)
    assert deleted == DatabaseManager.NOTE_NOT_FOUND


def test_delete_note_invalid_token(db):
    """Test deleting a note using an invalid token."""
    note_id = 1
    status = db.delete_note(note_id, "invalid_token")
    assert status is DatabaseManager.INVALID_TOKEN


def test_delete_note_expired_token(db, test_user_id):
    """Test deleting a note using an expired token."""
    token_value = "expired_token"
    expiration = current_timestamp_millis() - 1000

    db.cursor.execute(
        """INSERT OR REPLACE INTO Tokens (user_id, value, expiration)
        VALUES (?, ?, ?)""",
        (test_user_id, token_value, expiration)
    )
    db.conn.commit()
    note_id = 1
    status = db.delete_note(note_id, token_value)
    assert status is DatabaseManager.TOKEN_EXPIRED


def test_get_note_error(db, test_user_id):
    """Test the _get_note method handles errors correctly"""
    with patch.object(db, 'cursor', create=True) as mock_cursor:
        mock_cursor.execute.side_effect = sqlite3.Error("Simulated error")
        result = db._get_note(1, test_user_id)
    assert result == DatabaseManager.UNKNOWN_ERROR


def test_get_all_notes_success(db, test_user_id):
    """Test getting all notes using a valid token."""
    token = _refresh_token(db, test_user_id)
    db._create_note(test_user_id, "Note 1", "Content 1")
    db._create_note(test_user_id, "Note 2", "Content 2")

    notes = db.get_all_notes(token)
    assert isinstance(notes, list)
    assert len(notes) >= 2
    assert all(isinstance(note, Note) for note in notes)


def test_get_all_notes_invalid_token(db):
    """Test getting all notes using an invalid token."""
    notes = db.get_all_notes("invalid_token")
    assert notes is DatabaseManager.INVALID_TOKEN


def test_get_all_notes_expired_token(db, test_user_id):
    """Test getting all notes using an expired token."""
    token_value = "expired_token"
    expiration = current_timestamp_millis() - 1000

    db.cursor.execute(
        """INSERT OR REPLACE INTO Tokens (user_id, value, expiration)
        VALUES (?, ?, ?)""",
        (test_user_id, token_value, expiration)
    )
    db.conn.commit()
    notes = db.get_all_notes(token_value)
    assert notes is DatabaseManager.TOKEN_EXPIRED


def test_get_all_notes_error(db, test_user_id):
    """Test the _get_all_notes method handles errors correctly"""
    with patch.object(db, 'cursor', create=True) as mock_cursor:
        mock_cursor.execute.side_effect = sqlite3.Error("Simulated error")
        result = db._get_all_notes(test_user_id)
    assert result == []


def test_get_all_notes_search_query(db, test_user_id):
    """Test getting all notes for a user with a search query."""
    db._create_note(test_user_id, "Qwerty 1", "Content 1")
    db._create_note(test_user_id, "Qwerty 2", "Content 2")
    db._create_note(test_user_id, "Zxcvb 1", "Content 3")

    notes = db._get_all_notes(test_user_id, search_query="Qwerty")
    assert len(notes) == 2
    assert all(isinstance(note, Note) for note in notes)

    notes = db._get_all_notes(test_user_id, search_query="Zxcvb")
    assert len(notes) == 1
    assert notes[0].title == "Zxcvb 1"


def test_get_all_notes_search_query_empty_result(db, test_user_id):
    """Test getting all notes with a search query that returns no results."""
    db._create_note(test_user_id, "Note 1", "Content 1")
    db._create_note(test_user_id, "Note 2", "Content 2")

    notes = db._get_all_notes(test_user_id, search_query="NonExistent")
    assert len(notes) == 0


def test_get_all_notes_search_query_blank(db, test_user_id):
    """Test getting all notes when the search query is blank/empty."""
    db._create_note(test_user_id, "Note 1", "Content 1")
    db._create_note(test_user_id, "Note 2", "Content 2")

    notes = db._get_all_notes(test_user_id, search_query="   ")
    assert len(notes) >= 2


def test_get_all_notes_search_query_valid_token(db, test_user_id):
    """Test getting all notes with a search query and a valid token."""
    token = _refresh_token(db, test_user_id)
    db._create_note(test_user_id, "Wasd 1", "Content 1")
    db._create_note(test_user_id, "Wasd 2", "Content 2")
    db._create_note(test_user_id, "Iop 1", "Content 3")

    notes = db.get_all_notes(token, search_query="Wasd")
    assert len(notes) == 2
    assert all(isinstance(note, Note) for note in notes)

    notes = db.get_all_notes(token, search_query="Iop")
    assert len(notes) == 1
    assert notes[0].title == "Iop 1"
