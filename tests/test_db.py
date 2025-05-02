def test_create_user(db):
    """Test creating a new user."""
    user_id = db.create_user("newuser", "secure_password", "new@example.com")
    assert user_id is not None
    user = db.get_user_by_id(user_id)
    assert user['username'] == "newuser"
    assert user['email'] == "new@example.com"


def test_verify_user(db, test_user_id):
    """Test verifying an existing user."""
    verified_user_id = db.verify_user("testuser", "password123")
    assert verified_user_id == test_user_id


def test_verify_user_invalid_credentials(db):
    """Test verifying a user with invalid credentials."""
    verified_user_id = db.verify_user("testuser", "wrong_password")
    assert verified_user_id is None


def test_verify_user_user_not_found(db):
    """Test verifying a user that does not exist"""
    verified_user_id = db.verify_user("nonexistentuser", "password")
    assert verified_user_id is None


def test_create_note(db, test_user_id):
    """Test creating a new note."""
    note_id = db.create_note(test_user_id, "Test Note", "This is a test note.")
    assert note_id is not None
    note = db.get_note(note_id, test_user_id)
    assert note['title'] == "Test Note"
    assert note['content'] == "This is a test note."


def test_get_all_notes(db, test_user_id):
    """Test getting all notes for a user."""
    db.create_note(test_user_id, "Note 1", "Content 1")
    db.create_note(test_user_id, "Note 2", "Content 2")

    notes = db.get_all_notes(test_user_id)
    assert len(notes) >= 2
    assert notes[0]['user_id'] == test_user_id
    assert notes[1]['user_id'] == test_user_id


def test_update_note(db, test_user_id):
    """Test updating an existing note."""
    note_id = db.create_note(
        test_user_id, "Original Title", "Original Content")
    updated = db.update_note(note_id, test_user_id,
                             "Updated Title", "Updated Content")
    assert updated is True
    note = db.get_note(note_id, test_user_id)
    assert note['title'] == "Updated Title"
    assert note['content'] == "Updated Content"


def test_update_note_not_found(db, test_user_id):
    """Test updating a note that doesn't exist for the user."""
    updated = db.update_note(999, test_user_id, "Updated Title",
                             "Updated Content")
    assert updated is False


def test_delete_note(db, test_user_id):
    """Test deleting a note."""
    note_id = db.create_note(test_user_id, "To Delete", "Delete Me")
    deleted = db.delete_note(note_id, test_user_id)
    assert deleted is True
    note = db.get_note(note_id, test_user_id)
    assert note is None


def test_delete_nonexistent_note(db, test_user_id):
    """Test deleting a note that doesn't exist."""
    deleted = db.delete_note(999, test_user_id)
    assert deleted is False


def test_get_user_by_id(db):
    """Test getting a user by ID."""
    user_id = db.create_user("testuser2", "password123", "test2@example.com")
    user = db.get_user_by_id(user_id)
    assert user is not None
    assert user['username'] == "testuser2"
    assert user['email'] == "test2@example.com"


def test_create_user_duplicate_username(db):
    """Test creating a user with a duplicate username."""
    db.create_user("duplicateuser", "password123", "unique@example.com")
    user_id = db.create_user(
        "duplicateuser", "anotherpassword", "another@example.com")
    assert user_id is None
