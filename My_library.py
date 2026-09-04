import sqlite3

from passlib.context import CryptContext


# Original CasHub password-hashing approach, preserved from the 2023 project.
pwd_config = CryptContext(
    schemes=["pbkdf2_sha256"],
    default="pbkdf2_sha256",
    pbkdf2_sha256__default_rounds=30000,
)


def encrypt_password(user_password):
    """Hash a plaintext password."""
    return pwd_config.hash(user_password)


def check_password(user_password, hashed):
    """Return True when a plaintext password matches the stored hash."""
    return pwd_config.verify(user_password, hashed)


class database_worker:
    """Small SQLite helper originally created for CasHub.

    The 2026 portfolio revision keeps the original abstraction while adding
    parameter support so SQL can be executed safely without string interpolation.
    """

    def __init__(self, name):
        self.connection = sqlite3.connect(name)
        self.connection.execute("PRAGMA foreign_keys = ON")
        self.cursor = self.connection.cursor()

    def search(self, query, params=()):
        return self.cursor.execute(query, params).fetchall()

    def get(self, query, params=()):
        return self.cursor.execute(query, params).fetchone()

    def run_save(self, query, params=()):
        self.cursor.execute(query, params)
        self.connection.commit()

    def close(self):
        self.connection.close()
