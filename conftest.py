import os
import sys
import tempfile

import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import my_app


@pytest.fixture()
def app():
    with tempfile.TemporaryDirectory() as temporary_directory:
        test_app = my_app.app
        test_app.config.update(
            TESTING=True,
            SECRET_KEY="test-secret",
            DATABASE=os.path.join(temporary_directory, "test.sqlite3"),
            UPLOAD_FOLDER=os.path.join(temporary_directory, "uploads"),
        )

        my_app._initialized_database_paths.clear()
        my_app.create_database()

        yield test_app

        my_app._initialized_database_paths.clear()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def auth(client):
    class AuthActions:
        def register(
            self,
            name="Emmy",
            email="emmy@example.com",
            password="Strong123!",
        ):
            return client.post(
                "/register",
                data={
                    "name": name,
                    "email": email,
                    "password": password,
                    "check_password": password,
                    "description": "Student building tools for her community.",
                    "clubs[]": ["Peace Forum"],
                },
                follow_redirects=True,
            )

        def login(self, email="emmy@example.com", password="Strong123!"):
            return client.post(
                "/login",
                data={"email": email, "password": password},
                follow_redirects=True,
            )

        def logout(self):
            return client.get("/logout", follow_redirects=True)

    return AuthActions()
