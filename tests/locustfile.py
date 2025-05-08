import json
import random
import string
from locust import HttpUser, TaskSet, task, between
from locust import events


def random_string(length):
    return ''.join(random.choice(string.ascii_letters) for i in range(length))


def random_email():
    return f"{random_string(10)}@{random_string(5)}.com"


class NotesAppTasks(TaskSet):

    def on_start(self):
        """
        Setup: Create a user and sign in to get a token.
        This method runs once for each user when they start.
        """
        self.username = random_string(10)
        self.password = random_string(10)
        self.email = random_email()

        signup_data = {
            "username": self.username,
            "password": self.password,
            "email": self.email
        }
        signup_response = self.client.post("/sign_up", json=signup_data)
        if signup_response.status_code != 200:
            print(f"Failed to sign up user: {signup_response.text}")
            events.request.fire(
                request_type="signup", name="/sign_up",
                response_time=signup_response.elapsed.total_seconds(),
                response_length=len(signup_response.content),
                exception=Exception(f"Sign-up failed: {signup_response.text}"))
            self.interrupt()
            return

        self.token = signup_response.json().get("token")
        if not self.token:
            print(f"Failed to get token after signup: {signup_response.text}")
            events.request.fire(
                request_type="signup", name="/sign_up",
                response_time=signup_response.elapsed.total_seconds(),
                response_length=len(signup_response.content),
                exception=Exception("Failed to get token after signup."))
            self.interrupt()
            return

    @task
    def get_notes(self):
        """
        Task: Get all notes for the user.
        """
        headers = {"Authorization": f"Bearer {self.token}"}
        self.client.get("/notes", headers=headers, name="/notes")

    @task
    def create_note(self):
        """
        Task: Create a new note.
        """
        headers = {"Authorization": f"Bearer {self.token}"}
        note_data = {
            "title": random_string(20),
            "content": random_string(100)
        }
        self.client.post("/notes", headers=headers,
                         json=note_data, name="/notes (POST)")

    @task
    def update_note(self):
        """
        Task: Update an existing note.
        This requires first creating a note to get its ID.
        """
        headers = {"Authorization": f"Bearer {self.token}"}
        note_data = {
            "title": random_string(20),
            "content": random_string(100)
        }
        create_response = self.client.post(
            "/notes", headers=headers, json=note_data)
        if create_response.status_code == 201:
            note_id = create_response.json().get("note_id")
            if note_id:
                update_data = {
                    "title": random_string(20) + " (updated)",
                    "content": random_string(100) + " (updated)"
                }
                self.client.patch(
                    f"/notes/{note_id}", headers=headers,
                    json=update_data, name="/notes/[id] (PATCH)")
            else:
                print("Failed to retrieve note_id after creating note.")
                events.request.fire(
                    request_type="create_note", name="/notes (POST)",
                    response_time=create_response.elapsed.total_seconds(),
                    response_length=len(create_response.content),
                    exception=Exception(
                        "Failed to retrieve note_id after creating note."))
        else:
            print(f"Failed to create note for update: {create_response.text}")
            events.request.fire(
                request_type="create_note", name="/notes (POST)",
                response_time=create_response.elapsed.total_seconds(),
                response_length=len(create_response.content),
                exception=Exception(
                    f"""Failed to create note for update:
                     {create_response.text}"""))

    @task
    def delete_note(self):
        """
        Task: Delete an existing note.
        This requires first creating a note to get its ID.
        """
        headers = {"Authorization": f"Bearer {self.token}"}
        note_data = {
            "title": random_string(20),
            "content": random_string(100)
        }
        create_response = self.client.post(
            "/notes", headers=headers, json=note_data)
        if create_response.status_code == 201:
            note_id = create_response.json().get("note_id")
            if note_id:
                self.client.delete(
                    f"/notes/{note_id}",
                    headers=headers, name="/notes/[id] (DELETE)")
            else:
                print("Failed to retrieve note_id after creating note.")
                events.request.fire(
                    request_type="create_note", name="/notes (POST)",
                    response_time=create_response.elapsed.total_seconds(),
                    response_length=len(create_response.content),
                    exception=Exception(
                        "Failed to retrieve note_id after creating note."))
        else:
            print(
                f"Failed to create note for deletion: {create_response.text}")
            events.request.fire(
                request_type="create_note", name="/notes (POST)",
                response_time=create_response.elapsed.total_seconds(),
                response_length=len(create_response.content),
                exception=Exception(
                    f"""Failed to create note for deletion:
                     {create_response.text}"""))

    @task
    def translate(self):
        """
        Task: Translate some text.
        """
        headers = {"Authorization": f"Bearer {self.token}"}
        translate_data = {"query": "Hello world!"}
        with self.client.post(
                "/translate", headers=headers,
                json=translate_data,
                name="/translate",
                catch_response=True) as response:
            if response.status_code != 200:
                response.failure(
                    f"""Translate failed with status code:
                     {response.status_code}. Response: {response.text}""")
            else:
                try:
                    response_json = response.json()
                    if "translation" not in response_json:
                        response.failure(
                            f"""Translation missing from response:
                             {response.text}""")

                except json.JSONDecodeError:
                    response.failure("Failed to decode JSON response")
                except KeyError as e:
                    response.failure(f"Missing key in JSON response: {e}")
                except Exception as e:
                    response.failure(f"An unexpected error occurred: {e}")


class NotesAppUser(HttpUser):
    """
    Represents a user of the Notes application.
    """
    wait_time = between(0.1, 0.5)
    host = "http://localhost:8080"
    tasks = [NotesAppTasks]

    def on_start(self):
        pass
