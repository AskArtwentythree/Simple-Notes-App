import sqlite3
import bcrypt
import os


class DatabaseManager:
    """
    A class to manage SQLite database operations for the Simple Notes App.
    Handles user authentication and note management.
    """

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
            self.conn = sqlite3.connect(self.db_file_path)
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
        Creates the Users and Notes tables if they don't already exist.
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
        except sqlite3.Error as e:
            print(f"Error creating tables: {e}")
            self.conn.rollback()
            raise

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
            hashed_password = bcrypt.hashpw(password.encode(
                'utf-8'), bcrypt.gensalt()).decode('utf-8')
            self.cursor.execute(
                """INSERT INTO Users (username, password_hash, email)
                VALUES (?, ?, ?)""",
                (username, hashed_password, email))
            self.conn.commit()
            return self.cursor.lastrowid
        except sqlite3.IntegrityError:
            print("Username or email already exists.")
            self.conn.rollback()
            return None
        except sqlite3.Error as e:
            print(f"Error creating user: {e}")
            self.conn.rollback()
            return None

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
            self.cursor.execute(
                """SELECT user_id, password_hash
                FROM Users WHERE username = ?""", (username,))
            user = self.cursor.fetchone()

            if user:
                hashed_password = user['password_hash']

                if bcrypt.checkpw(password.encode('utf-8'),
                                  hashed_password.encode('utf-8')):
                    return user['user_id']
                else:
                    return None
            else:
                return None
        except sqlite3.Error as e:
            print(f"Error verifying user: {e}")
            return None

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
            return None

    def create_note(self, user_id, title, content):
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
            return None

    def get_note(self, note_id, user_id):
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
            return note
        except sqlite3.Error as e:
            print(f"Error getting note: {e}")
            return None

    def get_all_notes(self, user_id):
        """
        Retrieves all notes for a specific user.

        Args:
            user_id (int): The ID of the user.

        Returns:
            list: A list of objects representing the user's notes.
        """
        try:
            self.cursor.execute(
                """SELECT * FROM Notes
                WHERE user_id = ? ORDER BY updated_at DESC""",
                (user_id,))
            notes = self.cursor.fetchall()
            return notes
        except sqlite3.Error as e:
            print(f"Error getting all notes: {e}")
            return []

    def update_note(self, note_id, user_id, title, content):
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
                return False

            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Error updating note: {e}")
            self.conn.rollback()
            return False

    def delete_note(self, note_id, user_id):
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
                return False
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Error deleting note: {e}")
            self.conn.rollback()
            return False

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
