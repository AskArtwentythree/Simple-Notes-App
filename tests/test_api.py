import pytest
from unittest.mock import MagicMock, patch
from app.api import api
from app.db import DatabaseManager
import json
import requests


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


def test_sign_in_user_not_found(client, mock_db):
    mock_db.verify_user.return_value = DatabaseManager.USER_NOT_FOUND

    response = client.post('/sign_in', json={
        'username': 'nonexistent_user',
        'password': 'password'
    })

    assert response.status_code == 404
    assert 'error' in json.loads(response.data)


def test_sign_in_unknown_error(client, mock_db):
    mock_db.verify_user.return_value = DatabaseManager.UNKNOWN_ERROR

    response = client.post('/sign_in', json={
        'username': 'username',
        'password': 'password'
    })

    assert response.status_code == 500
    assert 'error' in json.loads(response.data)


def test_sign_in_exception(client, mock_db):
    mock_db.verify_user.side_effect = Exception("Simulated error")
    response = client.post('/sign_in', json={'username': 'user', 'password': 'pass'})
    assert response.status_code == 500
    assert 'error' in json.loads(response.data)
    assert "Simulated error" in json.loads(response.data)['error']


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


def test_sign_up_unknown_error(client, mock_db):
    mock_db.create_user.return_value = DatabaseManager.UNKNOWN_ERROR

    response = client.post('/sign_up', json={
        'email': 'email',
        'username': 'new_username',
        'password': 'password'
    })

    assert response.status_code == 500
    assert 'error' in json.loads(response.data)


def test_sign_up_exception(client, mock_db):
    mock_db.create_user.side_effect = Exception("Simulated error")
    response = client.post('/sign_up', json={'email': 'email', 'username': 'user', 'password': 'pass'})
    assert response.status_code == 500
    assert 'error' in json.loads(response.data)
    assert "Simulated error" in json.loads(response.data)['error']


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


def test_get_notes_unauthorized_invalid_token(client, mock_db):
    mock_db.get_all_notes.return_value = DatabaseManager.INVALID_TOKEN
    mock_db.get_user_id_from_token.return_value = DatabaseManager.INVALID_TOKEN

    response = client.get('/notes', headers={'Authorization': 'Bearer invalid-token'})

    assert response.status_code == 401
    assert 'error' in json.loads(response.data)


def test_get_notes_unauthorized_expired_token(client, mock_db):
    mock_db.get_all_notes.return_value = DatabaseManager.TOKEN_EXPIRED
    mock_db.get_user_id_from_token.return_value = DatabaseManager.TOKEN_EXPIRED

    response = client.get('/notes', headers={'Authorization': 'Bearer expired-token'})

    assert response.status_code == 401
    assert 'error' in json.loads(response.data)


def test_get_notes_unknown_error(client, mock_db):
    mock_db.get_all_notes.return_value = DatabaseManager.UNKNOWN_ERROR
    mock_db.get_user_id_from_token.return_value = 1

    response = client.get('/notes', headers={'Authorization': 'Bearer valid-token'})

    assert response.status_code == 500
    assert 'error' in json.loads(response.data)


def test_get_notes_exception(client, mock_db):
    mock_db.get_all_notes.side_effect = Exception("Simulated error")
    response = client.get('/notes', headers={'Authorization': 'Bearer token'})
    assert response.status_code == 500
    assert 'error' in json.loads(response.data)
    assert "Simulated error" in json.loads(response.data)['error']


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


def test_create_note_unauthorized_invalid_token(client, mock_db):
    mock_db.create_note.return_value = DatabaseManager.INVALID_TOKEN
    mock_db.get_user_id_from_token.return_value = DatabaseManager.INVALID_TOKEN

    response = client.post('/notes',
                         json={
                             'title': 'New Note',
                             'content': 'Note content'
                         },
                         headers={'Authorization': 'Bearer invalid-token'})

    assert response.status_code == 401
    assert 'error' in json.loads(response.data)


def test_create_note_unauthorized_expired_token(client, mock_db):
    mock_db.create_note.return_value = DatabaseManager.TOKEN_EXPIRED
    mock_db.get_user_id_from_token.return_value = DatabaseManager.TOKEN_EXPIRED

    response = client.post('/notes',
                         json={
                             'title': 'New Note',
                             'content': 'Note content'
                         },
                         headers={'Authorization': 'Bearer expired-token'})

    assert response.status_code == 401
    assert 'error' in json.loads(response.data)


def test_create_note_unknown_error(client, mock_db):
    mock_db.create_note.return_value = DatabaseManager.UNKNOWN_ERROR
    mock_db.get_user_id_from_token.return_value = 1

    response = client.post('/notes',
                         json={
                             'title': 'New Note',
                             'content': 'Note content'
                         },
                         headers={'Authorization': 'Bearer valid-token'})

    assert response.status_code == 500
    assert 'error' in json.loads(response.data)


def test_create_note_exception(client, mock_db):
    mock_db.create_note.side_effect = Exception("Simulated error")
    response = client.post('/notes', json={'title': 'title', 'content': 'content'}, headers={'Authorization': 'Bearer token'})
    assert response.status_code == 500
    assert 'error' in json.loads(response.data)
    assert "Simulated error" in json.loads(response.data)['error']


def test_get_note_by_id_success(client, mock_db):
    mock_note = MockNote(1, 'Test Note', 'Test Content')
    mock_db.get_note.return_value = mock_note
    mock_db.verify_user.return_value = (1, 'valid-token')
    
    response = client.get('/notes/1', 
                        headers={'Authorization': 'Bearer valid-token'})
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['id'] == 1


def test_get_note_by_id_unauthorized_invalid_token(client, mock_db):
    mock_db.get_note.return_value = DatabaseManager.INVALID_TOKEN
    mock_db.get_user_id_from_token.return_value = DatabaseManager.INVALID_TOKEN

    response = client.get('/notes/1',
                        headers={'Authorization': 'Bearer invalid-token'})

    assert response.status_code == 401
    assert 'error' in json.loads(response.data)


def test_get_note_by_id_unauthorized_expired_token(client, mock_db):
    mock_db.get_note.return_value = DatabaseManager.TOKEN_EXPIRED
    mock_db.get_user_id_from_token.return_value = DatabaseManager.TOKEN_EXPIRED

    response = client.get('/notes/1',
                        headers={'Authorization': 'Bearer expired-token'})

    assert response.status_code == 401
    assert 'error' in json.loads(response.data)


def test_get_note_by_id_not_found(client, mock_db):
    mock_db.get_note.return_value = DatabaseManager.NOTE_NOT_FOUND
    mock_db.get_user_id_from_token.return_value = 1

    response = client.get('/notes/1',
                        headers={'Authorization': 'Bearer valid-token'})

    assert response.status_code == 404
    assert 'error' in json.loads(response.data)


def test_get_note_by_id_unknown_error(client, mock_db):
    mock_db.get_note.return_value = DatabaseManager.UNKNOWN_ERROR
    mock_db.get_user_id_from_token.return_value = 1

    response = client.get('/notes/1',
                        headers={'Authorization': 'Bearer valid-token'})

    assert response.status_code == 500
    assert 'error' in json.loads(response.data)


def test_get_note_by_id_exception(client, mock_db):
    mock_db.get_note.side_effect = Exception("Simulated error")
    response = client.get('/notes/1', headers={'Authorization': 'Bearer token'})
    assert response.status_code == 500
    assert 'error' in json.loads(response.data)
    assert "Simulated error" in json.loads(response.data)['error']


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


def test_update_note_unauthorized_invalid_token(client, mock_db):
    mock_db.update_note.return_value = DatabaseManager.INVALID_TOKEN
    mock_db.get_user_id_from_token.return_value = DatabaseManager.INVALID_TOKEN

    response = client.patch('/notes/1',
                          json={
                              'title': 'Updated Note',
                              'content': 'Updated content'
                          },
                          headers={'Authorization': 'Bearer invalid-token'})

    assert response.status_code == 401
    assert 'error' in json.loads(response.data)


def test_update_note_unauthorized_expired_token(client, mock_db):
    mock_db.update_note.return_value = DatabaseManager.TOKEN_EXPIRED
    mock_db.get_user_id_from_token.return_value = DatabaseManager.TOKEN_EXPIRED

    response = client.patch('/notes/1',
                          json={
                              'title': 'Updated Note',
                              'content': 'Updated content'
                          },
                          headers={'Authorization': 'Bearer expired-token'})

    assert response.status_code == 401
    assert 'error' in json.loads(response.data)


def test_update_note_not_found(client, mock_db):
    mock_db.update_note.return_value = DatabaseManager.NOTE_NOT_FOUND
    mock_db.get_user_id_from_token.return_value = 1

    response = client.patch('/notes/1',
                          json={
                              'title': 'Updated Note',
                              'content': 'Updated content'
                          },
                          headers={'Authorization': 'Bearer valid-token'})

    assert response.status_code == 404
    assert 'error' in json.loads(response.data)


def test_update_note_unknown_error(client, mock_db):
    mock_db.update_note.return_value = DatabaseManager.UNKNOWN_ERROR
    mock_db.get_user_id_from_token.return_value = 1

    response = client.patch('/notes/1',
                          json={
                              'title': 'Updated Note',
                              'content': 'Updated content'
                          },
                          headers={'Authorization': 'Bearer valid-token'})

    assert response.status_code == 500
    assert 'error' in json.loads(response.data)


def test_update_note_exception(client, mock_db):
    mock_db.update_note.side_effect = Exception("Simulated error")
    response = client.patch('/notes/1', json={'title': 'title', 'content': 'content'}, headers={'Authorization': 'Bearer token'})
    assert response.status_code == 500
    assert 'error' in json.loads(response.data)
    assert "Simulated error" in json.loads(response.data)['error']


def test_delete_note_success(client, mock_db):
    mock_db.delete_note.return_value = DatabaseManager.OK
    mock_db.verify_user.return_value = (1, 'valid-token')
    
    response = client.delete('/notes/1', 
                           headers={'Authorization': 'Bearer valid-token'})
    
    assert response.status_code == 200
    assert 'message' in json.loads(response.data)


def test_delete_note_unauthorized_invalid_token(client, mock_db):
    mock_db.delete_note.return_value = DatabaseManager.INVALID_TOKEN
    mock_db.get_user_id_from_token.return_value = DatabaseManager.INVALID_TOKEN

    response = client.delete('/notes/1',
                           headers={'Authorization': 'Bearer invalid-token'})

    assert response.status_code == 401
    assert 'error' in json.loads(response.data)


def test_delete_note_unauthorized_expired_token(client, mock_db):
    mock_db.delete_note.return_value = DatabaseManager.TOKEN_EXPIRED
    mock_db.get_user_id_from_token.return_value = DatabaseManager.TOKEN_EXPIRED

    response = client.delete('/notes/1',
                           headers={'Authorization': 'Bearer expired-token'})

    assert response.status_code == 401
    assert 'error' in json.loads(response.data)


def test_delete_note_not_found(client, mock_db):
    mock_db.delete_note.return_value = DatabaseManager.NOTE_NOT_FOUND
    mock_db.get_user_id_from_token.return_value = 1

    response = client.delete('/notes/1',
                           headers={'Authorization': 'Bearer valid-token'})

    assert response.status_code == 404
    assert 'error' in json.loads(response.data)


def test_delete_note_unknown_error(client, mock_db):
    mock_db.delete_note.return_value = DatabaseManager.UNKNOWN_ERROR
    mock_db.get_user_id_from_token.return_value = 1

    response = client.delete('/notes/1',
                           headers={'Authorization': 'Bearer valid-token'})

    assert response.status_code == 500
    assert 'error' in json.loads(response.data)


def test_delete_note_exception(client, mock_db):
    mock_db.delete_note.side_effect = Exception("Simulated error")
    response = client.delete('/notes/1', headers={'Authorization': 'Bearer token'})
    assert response.status_code == 500
    assert 'error' in json.loads(response.data)
    assert "Simulated error" in json.loads(response.data)['error']


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


def test_translate_unauthorized_invalid_token(client, mock_db):
    mock_db.get_user_id_from_token.return_value = DatabaseManager.INVALID_TOKEN

    response = client.post('/translate',
                         json={'query': 'Text to translate'},
                         headers={'Authorization': 'Bearer invalid-token'})

    assert response.status_code == 401
    assert 'error' in json.loads(response.data)

def test_translate_unauthorized_expired_token(client, mock_db):
    mock_db.get_user_id_from_token.return_value = DatabaseManager.TOKEN_EXPIRED

    response = client.post('/translate',
                         json={'query': 'Text to translate'},
                         headers={'Authorization': 'Bearer expired-token'})

    assert response.status_code == 401
    assert 'error' in json.loads(response.data)

def test_translate_no_query(client, mock_db):
    mock_db.get_user_id_from_token.return_value = 1

    response = client.post('/translate',
                         json={},
                         headers={'Authorization': 'Bearer valid-token'})

    assert response.status_code == 400
    assert 'error' in json.loads(response.data)
    assert json.loads(response.data)['error'] == 'No text to translate'

def test_translate_empty_query(client, mock_db):
    mock_db.get_user_id_from_token.return_value = 1

    response = client.post('/translate',
                         json={'query': ''},
                         headers={'Authorization': 'Bearer valid-token'})

    assert response.status_code == 400
    assert 'error' in json.loads(response.data)
    assert json.loads(response.data)['error'] == 'No text to translate'

def test_translate_api_error(client, mock_db):
    mock_db.get_user_id_from_token.return_value = 1

    with patch('requests.post') as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_post.return_value = mock_response

        response = client.post('/translate',
                             json={'query': 'Text to translate'},
                             headers={'Authorization': 'Bearer valid-token'})

        assert response.status_code == 500
        assert 'error' in json.loads(response.data)
        assert 'Translation API Error' in json.loads(response.data)['error']

def test_translate_api_invalid_json(client, mock_db):
    mock_db.get_user_id_from_token.return_value = 1

    with patch('requests.post') as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.side_effect = json.JSONDecodeError("Expecting value", "", 0)
        mock_post.return_value = mock_response

        response = client.post('/translate',
                             json={'query': 'Text to translate'},
                             headers={'Authorization': 'Bearer valid-token'})

        assert response.status_code == 500
        assert 'error' in json.loads(response.data)
        assert 'Expecting value' in json.loads(response.data)['error']

def test_translate_api_missing_translation_field(client, mock_db):
    mock_db.get_user_id_from_token.return_value = 1

    with patch('requests.post') as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'data': {'translations': {}}}
        mock_post.return_value = mock_response

        response = client.post('/translate',
                             json={'query': 'Text to translate'},
                             headers={'Authorization': 'Bearer valid-token'})

        assert response.status_code == 500
        assert 'error' in json.loads(response.data)

def test_translate_request_exception(client, mock_db):
    mock_db.get_user_id_from_token.return_value = 1

    with patch('requests.post', side_effect=requests.exceptions.RequestException("Connection error")):
        response = client.post('/translate',
                             json={'query': 'Text to translate'},
                             headers={'Authorization': 'Bearer valid-token'})

        assert response.status_code == 500
        assert 'error' in json.loads(response.data)
        assert 'Connection error' in json.loads(response.data)['error']

def test_translate_json_decode_exception(client, mock_db):
    mock_db.get_user_id_from_token.return_value = 1

    with patch('requests.post') as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
        mock_post.return_value = mock_response

        response = client.post('/translate',
                             json={'query': 'Text to translate'},
                             headers={'Authorization': 'Bearer valid-token'})

        assert response.status_code == 500
        assert 'error' in json.loads(response.data)
        assert 'Invalid JSON' in json.loads(response.data)['error']
