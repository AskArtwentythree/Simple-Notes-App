"""
entity/note.py

Defines the Note “entity” model, which represents a single
note record stored in the database
"""
class Note:
    def __init__(
        self,
        note_id=None,
        user_id=None,
        title="",
        content="",
        created_at=None,
        updated_at=None
    ):
        """
        Represents a single entry in the 'Notes' table.

        Attributes:
            note_id (int): Unique identifier for the note.
            user_id (int): Foreign key referencing the user's ID.
            title (str): Title of the note.
            content (str): Content of the note.
            created_at (str): Timestamp indicating creation time.
            updated_at (str): Timestamp indicating last update time.
        """
        self.note_id = note_id
        self.user_id = user_id
        self.title = title
        self.content = content
        self.created_at = created_at
        self.updated_at = updated_at

    @staticmethod
    def from_row(row):
        """
        Construct a Note object from a database row.

        Parameters:
        -----------
        row : dict
            A dict-like row returned by a database cursor, with keys
            matching the columns: 'note_id', 'user_id', 'title',
            'content', 'created_at', and 'updated_at'.

        Returns:
        --------
        Note
            A new Note instance populated with values from `row`.
        """
        return Note(
            note_id=row['note_id'],
            user_id=row['user_id'],
            title=row['title'],
            content=row['content'],
            created_at=row['created_at'],
            updated_at=row['updated_at'],
        )

    def to_dict(self):
        """
        Serialize this Note to a JSON-serializable dict.

        Returns:
        --------
        dict
            A dictionary with the following keys:
            - 'id': the note_id
            - 'user_id': the user_id
            - 'title': the note title
            - 'content': the note content
            - 'created_at': creation timestamp
            - 'updated_at': last update timestamp
        """
        return {
            'id': self.note_id,
            'user_id': self.user_id,
            'title': self.title,
            'content': self.content,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
