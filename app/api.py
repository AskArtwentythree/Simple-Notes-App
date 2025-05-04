import json
from flask import Flask, request, jsonify
from app.db import DatabaseManager


api = Flask(__name__)
db_manager = DatabaseManager()


@api.route('/sign_in', methods=['POST'])
def sign_in():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    result = db_manager.verify_user(username=username, password=password)

    if result is None or result == DatabaseManager.UNKNOWN_ERROR:
        return jsonify({'error': DatabaseManager.UNKNOWN_ERROR}), 500

    if result == DatabaseManager.INVALID_PASSWORD or result == DatabaseManager.USER_NOT_FOUND:
        return jsonify({'error': result}), 404

    (_, token) = result
    return jsonify({'token': token}), 200


@api.route('/sign_up', methods=['POST'])
def sign_up():
    data = request.json
    email = data.get('email')
    username = data.get('username')
    password = data.get('password')

    result = db_manager.create_user(username=username, password=password, email=email)

    if result is None or result == DatabaseManager.UNKNOWN_ERROR:
        return jsonify({'error': DatabaseManager.UNKNOWN_ERROR}), 500

    if result == DatabaseManager.USER_ALREADY_EXISTS:
        return jsonify({'error': result}), 400

    (_, token) = result
    return jsonify({'token': token}), 200


@api.route('/notes', methods=['GET'])
def get_notes():
    token = request.headers.get('Authorization').replace('Bearer', '').strip()
    search_query = request.args.get('query', '')

    result = db_manager.get_all_notes(user_token=token, search_query=search_query)

    if result is None or result == DatabaseManager.UNKNOWN_ERROR:
        return jsonify({'error': DatabaseManager.UNKNOWN_ERROR}), 500

    if result == DatabaseManager.TOKEN_EXPIRED or result == DatabaseManager.INVALID_TOKEN:
        return jsonify({'error': result}), 401

    return jsonify([x.to_dict() for x in result]), 200


@api.route('/notes/<int:id>', methods=['GET'])
def get_note_by_id(id):
    token = request.headers.get('Authorization').replace('Bearer', '').strip()

    result = db_manager.get_note(note_id=id, user_token=token)

    if result is None or result == DatabaseManager.UNKNOWN_ERROR:
        return jsonify({'error': DatabaseManager.UNKNOWN_ERROR}), 500

    if result == DatabaseManager.TOKEN_EXPIRED or result == DatabaseManager.INVALID_TOKEN:
        return jsonify({'error': result}), 401

    if result == DatabaseManager.NOTE_NOT_FOUND:
        return jsonify({'error': result}), 404

    return json.dumps(result.to_dict()), 200


@api.route('/notes', methods=['POST'])
def create_note():
    token = request.headers.get('Authorization').replace('Bearer', '').strip()

    data = request.json
    title = data.get('title')
    content = data.get('content')

    result = db_manager.create_note(user_token=token, title=title, content=content)

    if result is None or result == DatabaseManager.UNKNOWN_ERROR:
        return jsonify({'error': DatabaseManager.UNKNOWN_ERROR}), 500

    if result == DatabaseManager.TOKEN_EXPIRED or result == DatabaseManager.INVALID_TOKEN:
        return jsonify({'error': result}), 401

    return jsonify({'note_id': result}), 201


@api.route('/notes/<int:id>', methods=['PATCH'])
def update_note(id):
    token = request.headers.get('Authorization').replace('Bearer', '').strip()

    data = request.json
    title = data.get('title')
    content = data.get('content')

    result = db_manager.update_note(note_id=id, user_token=token, title=title, content=content)

    if result is None or result == DatabaseManager.UNKNOWN_ERROR:
        return jsonify({'error': DatabaseManager.UNKNOWN_ERROR}), 500

    if result == DatabaseManager.TOKEN_EXPIRED or result == DatabaseManager.INVALID_TOKEN:
        return jsonify({'error': result}), 401

    if result == DatabaseManager.NOTE_NOT_FOUND:
        return jsonify({'error': result}), 404

    return jsonify({'message': DatabaseManager.OK}), 200


@api.route('/notes/<int:id>', methods=['DELETE'])
def delete_note(id):
    token = request.headers.get('Authorization').replace('Bearer', '').strip()

    result = db_manager.delete_note(note_id=id, user_token=token)

    if result is None or result == DatabaseManager.UNKNOWN_ERROR:
        return jsonify({'error': DatabaseManager.UNKNOWN_ERROR}), 500

    if result == DatabaseManager.TOKEN_EXPIRED or result == DatabaseManager.INVALID_TOKEN:
        return jsonify({'error': result}), 401

    if result == DatabaseManager.NOTE_NOT_FOUND:
        return jsonify({'error': result}), 404

    return jsonify({'message': DatabaseManager.OK}), 200

