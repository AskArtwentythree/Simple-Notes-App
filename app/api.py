import json
import os
import requests
from flask import Flask, request, jsonify
from app.db import DatabaseManager


api = Flask(__name__)
db_manager = DatabaseManager()


@api.route("/sign_in", methods=["POST"])
def sign_in():
    """
    Authenticates an existing user.
    Receives user credentials (username and password)
    from the request body and attempts
    to verify them against the database.
    """

    try:
        data = request.json
        username = data.get("username")
        password = data.get("password")

        result = db_manager.verify_user(username=username, password=password)

        if result is None or result == DatabaseManager.UNKNOWN_ERROR:
            return jsonify({"error": DatabaseManager.UNKNOWN_ERROR}), 500

        if (
            result == DatabaseManager.INVALID_PASSWORD
            or result == DatabaseManager.USER_NOT_FOUND
        ):
            return jsonify({"error": result}), 404

        (_, token) = result
        return jsonify({"token": token}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api.route("/sign_up", methods=["POST"])
def sign_up():
    """
    Registers a new user.
    Receives user details (email, username, password)
    from the request body and attempts
    to create a new user in the database.
    """

    try:
        data = request.json
        email = data.get("email")
        username = data.get("username")
        password = data.get("password")

        result = db_manager.create_user(
            username=username, password=password, email=email
        )

        if result is None or result == DatabaseManager.UNKNOWN_ERROR:
            return jsonify({"error": DatabaseManager.UNKNOWN_ERROR}), 500

        if result == DatabaseManager.USER_ALREADY_EXISTS:
            return jsonify({"error": result}), 400

        (_, token) = result
        return jsonify({"token": token}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api.route("/notes", methods=["GET"])
def get_notes():
    """
    Retrieves all notes associated with
    the authenticated user,
    with optional search functionality.
    """

    try:
        token = request.headers.get("Authorization")
        token = token.replace("Bearer", "").strip()
        search_query = request.args.get("query", "")

        result = db_manager.get_all_notes(
            user_token=token,
            search_query=search_query,
        )

        if result is None or result == DatabaseManager.UNKNOWN_ERROR:
            return jsonify({"error": DatabaseManager.UNKNOWN_ERROR}), 500

        if (
            result == DatabaseManager.TOKEN_EXPIRED
            or result == DatabaseManager.INVALID_TOKEN
        ):
            return jsonify({"error": result}), 401

        return jsonify([x.to_dict() for x in result]), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api.route("/notes/<int:id>", methods=["GET"])
def get_note_by_id(id):
    """
    Retrieves a specific note based on its ID.

    Args:
        id (int): The unique identifier of the note to retrieve.
    """

    try:
        token = request.headers.get("Authorization")
        token = token.replace("Bearer", "").strip()

        result = db_manager.get_note(note_id=id, user_token=token)

        if result is None or result == DatabaseManager.UNKNOWN_ERROR:
            return jsonify({"error": DatabaseManager.UNKNOWN_ERROR}), 500

        if (
            result == DatabaseManager.TOKEN_EXPIRED
            or result == DatabaseManager.INVALID_TOKEN
        ):
            return jsonify({"error": result}), 401

        if result == DatabaseManager.NOTE_NOT_FOUND:
            return jsonify({"error": result}), 404

        return json.dumps(result.to_dict()), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api.route("/notes", methods=["POST"])
def create_note():
    """
    Handles the POST request to create a new note.
    The user must be authenticated via
    a Bearer token in the Authorization header.
    The request body must contain the
    'title' and 'content' for the new note.
    """

    try:
        token = request.headers.get("Authorization")
        token = token.replace("Bearer", "").strip()

        data = request.json
        title = data.get("title")
        content = data.get("content")

        result = db_manager.create_note(
            user_token=token,
            title=title,
            content=content,
        )

        if result is None or result == DatabaseManager.UNKNOWN_ERROR:
            return jsonify({"error": DatabaseManager.UNKNOWN_ERROR}), 500

        if (
            result == DatabaseManager.TOKEN_EXPIRED
            or result == DatabaseManager.INVALID_TOKEN
        ):
            return jsonify({"error": result}), 401

        return jsonify({"note_id": result}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api.route("/notes/<int:id>", methods=["PATCH"])
def update_note(id):
    """
    Handles the PATCH request to
    update an existing note identified by its ID.
    Allows partial updates to the
    note's title and/or content.
    The user must provide a valid
    Bearer token for authorization.
    """

    try:
        token = request.headers.get("Authorization")
        token = token.replace("Bearer", "").strip()

        data = request.json
        title = data.get("title")
        content = data.get("content")

        result = db_manager.update_note(
            note_id=id, user_token=token, title=title, content=content
        )

        if result is None or result == DatabaseManager.UNKNOWN_ERROR:
            return jsonify({"error": DatabaseManager.UNKNOWN_ERROR}), 500

        if (
            result == DatabaseManager.TOKEN_EXPIRED
            or result == DatabaseManager.INVALID_TOKEN
        ):
            return jsonify({"error": result}), 401

        if result == DatabaseManager.NOTE_NOT_FOUND:
            return jsonify({"error": result}), 404

        return jsonify({"message": DatabaseManager.OK}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api.route("/notes/<int:id>", methods=["DELETE"])
def delete_note(id):
    """
    Deletes a specific note identified by its ID.

    The user must be authenticated
    via a Bearer token in the Authorization header.

    Path Parameters:
        id (int): The unique identifier
        of the note to be deleted.

    Request Headers:
        Authorization (str): Bearer token for authentication.
        Example: "Bearer <your_jwt_token>"
    """

    try:
        token = request.headers.get("Authorization")
        token = token.replace("Bearer", "").strip()

        result = db_manager.delete_note(note_id=id, user_token=token)

        if result is None or result == DatabaseManager.UNKNOWN_ERROR:
            return jsonify({"error": DatabaseManager.UNKNOWN_ERROR}), 500

        if (
            result == DatabaseManager.TOKEN_EXPIRED
            or result == DatabaseManager.INVALID_TOKEN
        ):
            return jsonify({"error": result}), 401

        if result == DatabaseManager.NOTE_NOT_FOUND:
            return jsonify({"error": result}), 404

        return jsonify({"message": DatabaseManager.OK}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api.route("/translate", methods=["POST"])
def translate():
    """
    Translates given text from
    English to Russian using Deep Translate API.

    Request Body:
    {
        "query": "Text to translate"
    }

    Response Format:
    {
        "translation": "Translated Text"
    }
    """

    token = request.headers.get("Authorization").replace("Bearer", "").strip()
    result = db_manager.get_user_id_from_token(token)

    if (
        result == DatabaseManager.TOKEN_EXPIRED
        or result == DatabaseManager.INVALID_TOKEN
    ):
        return jsonify({"error": result}), 401

    try:
        data = request.json
        query = data.get("query")

        if not query:
            return jsonify({"error": "No text to translate"}), 400

        query = query.strip()

        headers = {
            "Content-Type": "application/json",
            "X-RapidAPI-Host": "deep-translate1.p.rapidapi.com",
            "X-RapidAPI-Key": os.getenv("DEEP_TRANSLATE_API_KEY"),
        }

        payload = {
            "q": query,
            "source": "ru",
            "target": "en"
        }

        response = requests.post(
            "https://deep-translate1.p.rapidapi.com/language/translate/v2",
            headers=headers,
            json=payload,
            timeout=10
        )

        if response.status_code != 200:
            error_message = f"Translation API Error ({response.status_code})"
            return jsonify({"error": error_message}), 500

        translated_data = response.json()
        translated_text = translated_data["data"]
        translated_text = translated_text["translations"]
        translated_text = translated_text["translatedText"][0]

        return jsonify({"translation": translated_text}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
