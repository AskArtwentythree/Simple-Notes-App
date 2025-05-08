import sqlite3
import bcrypt
import os
import uuid
from app.date_utils import current_timestamp_millis, next_day_timestamp_millis
from app.entity.note import Note


class DatabaseManager:
    """
    A class to manage SQLite database operations for the Simple Notes App.
    Handles user authentication and note management.
    """

    USER_NOT_FOUND = 'user_not_found'
    USER_ALREADY_EXISTS = 'user_alredy_exists'
    STATUS_INVALID_PASSWORD = 'invalid_password'
    TOKEN_EXPIRED = 'token_expired'
    INVALID_TOKEN = 'invalid_token'
    NOTE_NOT_FOUND = 'note_not_found'
    UNKNOWN_ERROR = 'unknown_error'
    OK = 'ok'

    def __init__(self, db_name="notes.db", db_path="."):
        """
        Initializes the DatabaseManager.

        Args:
            db_name (str): The name of the SQLite database file.
            db_path (str): The relative path to create database in.
                           Defaults to current directory.
        """
        self.db_name = db_name
        self.db_path = db_path

        self.db_file_path = os.path.join(self.db_path, self.db_name)

        self.conn = None
        self.cursor = None
        self.connect()
        self._create_tables()

    def connect(self):
        """Connect to the database."""
        try:
            self.conn = sqlite3.connect(
                self.db_file_path, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row
            self.cursor = self.conn.cursor()

        except sqlite3.Error as e:
            print(f"Database connection error: {e}")
            raise

    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None
            self.cursor = None

    def _create_tables(self):
        """
        Creates the Users, Tokens and Notes tables if they don't already exist.
        """
        try:
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS Users (
                    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username VARCHAR(255) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    email VARCHAR(255) UNIQUE NOT NULL
                )
            """)

            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS Tokens (
                    user_id INTEGER PRIMARY KEY,
                    value VARCHAR(36) UNIQUE NOT NULL,
                    expiration INTEGER NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES Users(user_id)
                )
            """)

            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS Notes (
                    note_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    title VARCHAR(255) NOT NULL,
                    content TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES Users(user_id)
                )
            """)

            self.cursor.execute("""
                CREATE TRIGGER IF NOT EXISTS update_notes_updated_at
                AFTER UPDATE ON Notes
                BEGIN
                    UPDATE Notes SET updated_at = CURRENT_TIMESTAMP
                    WHERE note_id = NEW.note_id;
                END;
            """)

            self.conn.commit()
            return DatabaseManager.OK
        except sqlite3.Error as e:
            print(f"Error creating tables: {e}")
            self.conn.rollback()
            return DatabaseManager.UNKNOWN_ERROR

    def create_user(self, username, password, email):
        """
        Creates a new user in the database.

        Args:
            username (str): The username of the new user.
            password (str): The plain-text password of the new user.
            email (str): The email address of the new user.

        Returns:
            int: The user_id of the newly created user.
        """
        try:
            hashed_password = bcrypt.hashpw(
                password.encode('utf-8'),
                bcrypt.gensalt()
            ).decode('utf-8')

            self.cursor.execute(
                """INSERT INTO Users (username, password_hash, email)
                VALUES (?, ?, ?)""",
                (username, hashed_password, email)
            )

            user_id = self.cursor.lastrowid

            token_value = str(uuid.uuid4())
            expiration = next_day_timestamp_millis()

            self.cursor.execute(
                """INSERT INTO Tokens (value, user_id, expiration)
                VALUES (?, ?, ?)""",
                (token_value, user_id, expiration)
            )

            self.conn.commit()
            return (user_id, token_value)
        except sqlite3.IntegrityError:
            print("Username or email already exists.")
            self.conn.rollback()
            return DatabaseManager.USER_ALREADY_EXISTS
        except sqlite3.Error as e:
            print(f"Error creating user: {e}")
            self.conn.rollback()
            return DatabaseManager.UNKNOWN_ERROR

    def verify_user(self, username, password):
        """
        Verifies a user's credentials.

        Args:
            username (str): The username of the user.
            password (str): The plain-text password of the user.

        Returns:
            int: The user_id if the credentials are valid, otherwise None.
        """
        try:
            self.cursor.execute("BEGIN TRANSACTION")

            self.cursor.execute(
                """SELECT user_id, password_hash
                FROM Users WHERE username = ?""", (username,))
            user = self.cursor.fetchone()

            if user:
                hashed_password = user['password_hash']

                if bcrypt.checkpw(password.encode('utf-8'),
                                  hashed_password.encode('utf-8')):
                    token_value = str(uuid.uuid4())
                    expiration = next_day_timestamp_millis()

                    user_id = user['user_id']

                    self.cursor.execute(
                        """INSERT OR REPLACE INTO
                        Tokens (user_id, value, expiration)
                        VALUES (?, ?, ?)""",
                        (user_id, token_value, expiration)
                    )
                    self.conn.commit()
                    return (user_id, token_value)
                else:
                    self.conn.rollback()
                    return DatabaseManager.STATUS_INVALID_PASSWORD
            else:
                self.conn.rollback()
                return DatabaseManager.USER_NOT_FOUND
        except sqlite3.Error as e:
            print(f"Error verifying user: {e}")
            self.conn.rollback()
            return DatabaseManager.UNKNOWN_ERROR

    def get_user_by_id(self, user_id):
        """
        Gets user information by user ID.

        Args:
            user_id (int): The ID of the user to retrieve.

        Returns:
            sqlite3.Row: A dictionary-like object representing the user.
        """
        try:
            self.cursor.execute(
                """SELECT user_id, username, email
                FROM Users WHERE user_id = ?""", (user_id,))
            user = self.cursor.fetchone()
            return user
        except sqlite3.Error as e:
            print(f"Error getting user: {e}")
            return DatabaseManager.USER_NOT_FOUND

    def get_user_id_from_token(self, user_token):
        """
        Retrieves the user ID from the user token.
        Checks if it's expired.
        """
        self.cursor.execute("""
            SELECT Users.user_id, Tokens.expiration
            FROM Users
            JOIN Tokens ON Users.user_id = Tokens.user_id
            WHERE Tokens.value = ?""",
                            (user_token,))
        result = self.cursor.fetchone()

        if result:
            user_id, expiration = result

            if expiration > current_timestamp_millis():
                return user_id
            else:
                print("Token is expired.")
                return DatabaseManager.TOKEN_EXPIRED

        print("Invalid user token.")
        return DatabaseManager.INVALID_TOKEN

    def _create_note(self, user_id, title, content):
        """
        Creates a new note for a user.

        Args:
            user_id (int): The ID of the user creating the note.
            title (str): The title of the note.
            content (str): The content of the note.

        Returns:
            int: The note_id of the newly created note.
        """
        try:
            self.cursor.execute(
                """INSERT INTO Notes (user_id, title, content)
                VALUES (?, ?, ?)""",
                (user_id, title, content))
            self.conn.commit()
            return self.cursor.lastrowid
        except sqlite3.Error as e:
            print(f"Error creating note: {e}")
            self.conn.rollback()
            return DatabaseManager.UNKNOWN_ERROR

    def create_note(self, user_token, title, content):
        """
        Creates a new note for a user using their token.

        Args:
            user_token (str): The JWT token of the user creating the note.
            title (str): The title of the note.
            content (str): The content of the note.

        Returns:
            int: The note_id of the newly created note.
        """
        try:
            user_id = self.get_user_id_from_token(user_token)

            if user_id == DatabaseManager.TOKEN_EXPIRED or \
               user_id == DatabaseManager.INVALID_TOKEN:
                return user_id

            return self._create_note(
                user_id=user_id, title=title, content=content)
        except sqlite3.Error:
            return DatabaseManager.UNKNOWN_ERROR

    def _get_note(self, note_id, user_id):
        """
        Retrieves a specific note by its ID and user ID.

        Args:
            note_id (int): The ID of the note.
            user_id (int):  The ID of the user who owns the note.

        Returns:
            sqlite3.Row: A dictionary-like object representing the note.
        """
        try:
            self.cursor.execute(
                """SELECT * FROM Notes
                WHERE note_id = ? AND user_id = ?""",
                (note_id, user_id))

            note = self.cursor.fetchone()

            if note is None:
                return DatabaseManager.NOTE_NOT_FOUND

            return Note.from_row(note)
        except sqlite3.Error as e:
            print(f"Error getting note: {e}")
            return DatabaseManager.UNKNOWN_ERROR

    def get_note(self, note_id, user_token):
        """
        Retrieves a specific note by its ID and user token.

        Args:
            note_id (int): The ID of the note.
            user_token (str): The JWT token of the user who owns the note.

        Returns:
            sqlite3.Row: A dictionary-like object representing the note.
        """
        try:
            user_id = self.get_user_id_from_token(user_token)

            if user_id == DatabaseManager.TOKEN_EXPIRED or \
               user_id == DatabaseManager.INVALID_TOKEN or \
               user_id == DatabaseManager.NOTE_NOT_FOUND:
                return user_id

            return self._get_note(note_id=note_id, user_id=user_id)
        except sqlite3.Error:
            return DatabaseManager.UNKNOWN_ERROR

    def _get_all_notes(self, user_id, search_query=''):
        """
        Retrieves all notes for a specific user.
        If search_query is provided and not empty/blank,
        filters notes by title.

        Args:
            user_id (int): The ID of the user.
            search_query (str):Optional search string to filter notes by title.

        Returns:
            list: A list of objects representing the user's notes.
        """
        query = search_query.strip()

        try:
            if query:
                self.cursor.execute("""
                    SELECT * FROM Notes
                    WHERE user_id = ? AND title LIKE ?
                    ORDER BY updated_at DESC""",
                                    (user_id, f'%{query}%'))
            else:
                self.cursor.execute("""
                    SELECT * FROM Notes
                    WHERE user_id = ?
                    ORDER BY updated_at DESC""",
                                    (user_id,))

            notes = self.cursor.fetchall()
            return list(map(Note.from_row, notes))
        except sqlite3.Error as e:
            print(f"Error getting all notes: {e}")
            return []

    def get_all_notes(self, user_token, search_query=''):
        """
        Retrieves all notes for a specific user.

        Args:
            user_token (str): The JWT token of the user.

        Returns:
            list: A list of objects representing the user's notes.
        """
        try:
            user_id = self.get_user_id_from_token(user_token,)

            if user_id == DatabaseManager.TOKEN_EXPIRED or \
               user_id == DatabaseManager.INVALID_TOKEN:
                return user_id

            return self._get_all_notes(
                user_id=user_id, search_query=search_query)
        except sqlite3.Error:
            return []

    def _update_note(self, note_id, user_id, title, content):
        """
        Updates an existing note.

        Args:
            note_id (int): The ID of the note to update.
            user_id (int): The ID of the user updating the note.
            title (str): The new title of the note.
            content (str): The new content of the note.

        Returns:
            bool: True if the update was successful, False otherwise.
        """
        try:
            self.cursor.execute(
                """UPDATE Notes SET title = ?, content = ?
                WHERE note_id = ? AND user_id = ?""",
                (title, content, note_id, user_id))

            if self.cursor.rowcount == 0:
                return DatabaseManager.NOTE_NOT_FOUND

            self.conn.commit()
            return DatabaseManager.OK
        except sqlite3.Error as e:
            print(f"Error updating note: {e}")
            self.conn.rollback()
            return DatabaseManager.UNKNOWN_ERROR

    def update_note(self, note_id, user_token, title, content):
        """
        Updates an existing note.

        Args:
            note_id (int): The ID of the note to update.
            user_token (str): The JWT token of the user updating the note.
            title (str): The new title of the note.
            content (str): The new content of the note.

        Returns:
            bool: True if the update was successful, False otherwise.
        """
        try:
            user_id = self.get_user_id_from_token(user_token)

            if user_id == DatabaseManager.TOKEN_EXPIRED or \
               user_id == DatabaseManager.INVALID_TOKEN:
                return user_id

            return self._update_note(
                note_id=note_id, user_id=user_id, title=title, content=content)
        except sqlite3.Error:
            return DatabaseManager.UNKNOWN_ERROR

    def _delete_note(self, note_id, user_id):
        """
        Deletes a note.

        Args:
            note_id (int): The ID of the note to delete.
            user_id (int): The ID of the user deleting the note (for security).

        Returns:
            bool: True if the deletion was successful, False otherwise.
        """
        try:
            self.cursor.execute(
                "DELETE FROM Notes WHERE note_id = ? AND user_id = ?",
                (note_id, user_id))

            if self.cursor.rowcount == 0:
                return DatabaseManager.NOTE_NOT_FOUND
            self.conn.commit()
            return DatabaseManager.OK
        except sqlite3.Error as e:
            print(f"Error deleting note: {e}")
            self.conn.rollback()
            return DatabaseManager.UNKNOWN_ERROR

    def delete_note(self, note_id, user_token):
        """
        Deletes a note.

        Args:
            note_id (int): The ID of the note to delete.
            user_token (str): The ID of the user deleting the note.

        Returns:
            bool: True if the deletion was successful, False otherwise.
        """
        try:
            user_id = self.get_user_id_from_token(user_token)

            if user_id == DatabaseManager.TOKEN_EXPIRED or \
               user_id == DatabaseManager.INVALID_TOKEN:
                return user_id

            return self._delete_note(note_id=note_id, user_id=user_id)
        except sqlite3.Error:
            return DatabaseManager.UNKNOWN_ERROR

    def __enter__(self):
        """
        Context manager entry point.  Allows use of 'with' statement.
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Context manager exit point.  Closes the connection.
        """
        self.close()
