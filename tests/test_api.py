import pytest
from unittest.mock import MagicMock, patch
from app.api import api
from app.db import DatabaseManager
import json

@pytest.fixture
def client():
    api.config['TESTING'] = True
    with api.test_client() as client:
        yield client

@pytest.fixture
def mock_db():
    with patch('app.api.db_manager') as mock:
        yield mock

class MockNote:
    def __init__(self, id, title, content):
        self.id = id
        self.title = title
        self.content = content
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content
        }

def test_sign_in_success(client, mock_db):
    mock_db.verify_user.return_value = (1, 'valid-token')
    
    response = client.post('/sign_in', json={
        'username': 'username',
        'password': 'password'
    })
    
    assert response.status_code == 200
    assert 'token' in json.loads(response.data)

def test_sign_in_invalid_credentials(client, mock_db):
    mock_db.verify_user.return_value = DatabaseManager.INVALID_PASSWORD
    
    response = client.post('/sign_in', json={
        'username': 'username',
        'password': 'wrongpass_password'
    })
    
    assert response.status_code == 404
    assert 'error' in json.loads(response.data)

def test_sign_up_success(client, mock_db):
    mock_db.create_user.return_value = (1, 'new-token')
    
    response = client.post('/sign_up', json={
        'email': 'email',
        'username': 'new_username',
        'password': 'password'
    })
    
    assert response.status_code == 200
    assert 'token' in json.loads(response.data)

def test_sign_up_user_exists(client, mock_db):
    mock_db.create_user.return_value = DatabaseManager.USER_ALREADY_EXISTS
    
    response = client.post('/sign_up', json={
        'email': 'existed_email',
        'username': 'existed_username',
        'password': 'password'
    })
    
    assert response.status_code == 400
    assert 'error' in json.loads(response.data)

def test_get_notes_success(client, mock_db):
    mock_note = MockNote(1, 'Test Note', 'Test Content')
    mock_db.get_all_notes.return_value = [mock_note]
    mock_db.verify_user.return_value = (1, 'valid-token')
    
    response = client.get('/notes', 
                        headers={'Authorization': 'Bearer valid-token'})
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert isinstance(data, list)
    assert len(data) == 1

def test_create_note_success(client, mock_db):
    mock_db.create_note.return_value = 1
    mock_db.verify_user.return_value = (1, 'valid-token')
    
    response = client.post('/notes', 
                         json={
                             'title': 'New Note',
                             'content': 'Note content'
                         },
                         headers={'Authorization': 'Bearer valid-token'})
    
    assert response.status_code == 201
    assert 'note_id' in json.loads(response.data)

def test_get_note_by_id_success(client, mock_db):
    mock_note = MockNote(1, 'Test Note', 'Test Content')
    mock_db.get_note.return_value = mock_note
    mock_db.verify_user.return_value = (1, 'valid-token')
    
    response = client.get('/notes/1', 
                        headers={'Authorization': 'Bearer valid-token'})
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['id'] == 1

def test_update_note_success(client, mock_db):
    mock_db.update_note.return_value = DatabaseManager.OK
    mock_db.verify_user.return_value = (1, 'valid-token')
    
    response = client.patch('/notes/1', 
                          json={
                              'title': 'Updated Note',
                              'content': 'Updated content'
                          },
                          headers={'Authorization': 'Bearer valid-token'})
    
    assert response.status_code == 200
    assert 'message' in json.loads(response.data)

def test_delete_note_success(client, mock_db):
    mock_db.delete_note.return_value = DatabaseManager.OK
    mock_db.verify_user.return_value = (1, 'valid-token')
    
    response = client.delete('/notes/1', 
                           headers={'Authorization': 'Bearer valid-token'})
    
    assert response.status_code == 200
    assert 'message' in json.loads(response.data)

def test_translate_success(client, mock_db):
    mock_db.get_user_id_from_token.return_value = 1
    
    with patch('requests.post') as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'data': {
                'translations': {
                    'translatedText': 'Texte traduit'
                }
            }
        }
        mock_post.return_value = mock_response
        
        response = client.post('/translate', 
                             json={'query': 'Text to translate'},
                             headers={'Authorization': 'Bearer valid-token'})
        
        assert response.status_code == 200
        assert 'translation' in json.loads(response.data)