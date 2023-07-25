"""
    Users database 
"""
import os
import sqlite3
import hashlib
import uuid
from pydantic import BaseModel

from settings import settings


def get_pass_hash(password: str, salt: str):
    """Hash password with given salt using sha512 hash"""
    payload = password + salt
    return hashlib.sha512(payload.encode("utf-8")).hexdigest()


class AuthEntry(BaseModel):
    """Auth database model"""

    id: int
    email: str
    school_id: int
    password_hash: str
    salt: str
    token: str

    def __init__(self, user_id, email, school_id, password_hash, salt, token):
        super().__init__(
            id=user_id,
            email=email,
            school_id=school_id,
            password_hash=password_hash,
            salt=salt,
            token=token,
        )


class UsersDB:
    """users.db wrapper"""

    db_path = "data/db/users.db"

    def __init__(self, db_path):
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.db_path = db_path
        try:
            self.connection = sqlite3.connect(self.db_path)
            self.cursor = self.connection.cursor()

            self.create_database_if_not_exists()
        except sqlite3.Error as ex:
            print(f"Failed to establish connection to database\n{ex}")

    def __del__(self):
        self.connection.commit()
        self.connection.close()

    def create_database_if_not_exists(self):
        """Creates auth_* tables if needed"""
        self.cursor.execute(
            """CREATE TABLE IF NOT EXISTS auth_users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email VARCHAR NOT NULL,
                    school_id INTEGER NOT NULL REFERENCES schools(id),
                    password_hash BLOB NOT NULL,
                    salt BLOB NOT NULL
            )"""
        )

        self.cursor.execute(
            """CREATE TABLE IF NOT EXISTS auth_tokens (
                    user_id INTEGER PRIMARY KEY,
                    token TEXT,
                    FOREIGN KEY (user_id) REFERENCES auth_users(id)
            )"""
        )

        self.connection.commit()

    # TODO: Use user id instead of email for most of the cases except register.
    # As auth_users and auth_tokens contain the same user id, we should be
    # able to fetch user entry in a single query
    def get_user(self, email):
        """Get user from by email given"""
        # TODO: Check joins perf as they may still be expensive,
        # instead perform two queries:
        # First quary to get user_id form auth_tokens table, then second quary
        # to get user data from auth_users table with user_id.
        # Might not be needed after get_user recieves id instead of email
        self.cursor.execute(
            """
            SELECT
                auth_users.id,
                auth_users.email,
                auth_users.school_id,
                auth_users.password_hash,
                auth_users.salt,
                auth_tokens.token
            FROM
                auth_users
            INNER JOIN
                auth_tokens
            ON
                auth_users.id = auth_tokens.user_id
            WHERE
                auth_users.email = ?
        """,
            (email,),
        )
        row = self.cursor.fetchone()

        if not row:
            return None

        return AuthEntry(*row)

    def add_token(self, user_id, token):
        """Add token for the user id specified"""
        insert_token_sql = """INSERT INTO auth_tokens (user_id, token) VALUES (?, ?)"""
        self.cursor.execute(insert_token_sql, [user_id, token])

        self.connection.commit()

    def add_user(self, user):
        """Add a user entry to database"""
        # Hash password
        salt = uuid.uuid4().hex
        password_hash = get_pass_hash(user.password, salt)

        # Insert user data
        insert_user_sql = """INSERT INTO auth_users
                            (email, school_id, password_hash, salt) 
                            VALUES (?, ?, ?, ?)
                        """
        self.cursor.execute(
            insert_user_sql, [user.email, user.schoolId, password_hash, salt]
        )

        # Get the last inserted user ID
        user_id = self.cursor.lastrowid

        # Finish
        self.connection.commit()
        return user_id

    def change_school_id(self, user, new_id):
        """Replace school id of a user with the given id"""
        update_query = """UPDATE auth_users SET school_id = ? WHERE id = ?"""
        self.cursor.execute(update_query, (new_id, user.id))

        self.connection.commit()


users_db = UsersDB(settings.db_path)
