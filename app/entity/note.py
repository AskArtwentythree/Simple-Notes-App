class Note:
    def __init__(self, note_id=None, user_id=None, title="", content="", created_at=None, updated_at=None):
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
        return Note(
            note_id=row['note_id'],
            user_id=row['user_id'],
            title=row['title'],
            content=row['content'],
            created_at=row['created_at'],
            updated_at=row['updated_at'],
        )

    def to_dict(self):
					return {
							'id': self.note_id,  
							'user_id': self.user_id,
							'title': self.title,
							'content': self.content,
							'created_at': self.created_at,
							'updated_at': self.updated_at
					}