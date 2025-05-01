import pytest
import os

from app.db import DatabaseManager

TEST_DB_NAME = "test_notes.db"
TEST_DB_PATH = "tests"


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """
    Creates and populates a test database before all tests.
    Deletes the test database after all tests have finished.
    """

    os.makedirs(TEST_DB_PATH, exist_ok=True)
    db_file_path = os.path.join(TEST_DB_PATH, TEST_DB_NAME)
    with DatabaseManager(db_name=TEST_DB_NAME, db_path=TEST_DB_PATH) as db:
        db.create_user("testuser", "password123", "test@example.com")

    yield

    if os.path.exists(db_file_path):
        os.remove(db_file_path)


@pytest.fixture()
def db():
    """
    Fixture to provide a DatabaseManager instance for each test function.
    """
    with DatabaseManager(db_name=TEST_DB_NAME, db_path=TEST_DB_PATH) as db:
        yield db


@pytest.fixture
def test_user_id(db):
    """Fixture to get the ID of the test user."""
    db.cursor.execute("SELECT user_id FROM Users WHERE username = 'testuser'")
    user = db.cursor.fetchone()
    return user['user_id']
