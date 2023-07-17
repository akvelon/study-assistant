import os
import sqlite3
import hashlib, uuid
from pydantic import BaseModel


def get_pass_hash(password: str, salt: str):
    payload = password + salt
    return hashlib.sha512(payload.encode("utf-8")).hexdigest()


class AuthEntry(BaseModel):
    id: int
    email: str
    school_id: int
    password_hash: str
    salt: str
    token: str

    def __init__(self, id, email, school_id, password_hash, salt, token):
        super().__init__(
            id=id,
            email=email,
            school_id=school_id,
            password_hash=password_hash,
            salt=salt,
            token=token,
        )


class UsersDB:
    database_path = "data/db/api_db.sqlite"

    def __init__(self, db_path, db_name):
        os.makedirs(db_path, exist_ok=True)
        path = os.path.join(db_path, db_name)
        self.database_path = path
        try:
            self.connection = sqlite3.connect(self.database_path)
            self.cursor = self.connection.cursor()

            self.create_database_if_not_exists()
        except sqlite3.Error as e:
            print(f"Failed to establish connection to database\n{e}")

    # Gurauntees that the connection to the database is closed
    def __del__(self):
        self.connection.commit()
        self.connection.close()

    def create_database_if_not_exists(self):
        self.cursor.execute(
            """CREATE TABLE IF NOT EXISTS auth_users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email VARCHAR NOT NULL,
                    school_id INTEGER NOT NULL,
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

    def get_user(self, email):
        # TODO: Joins are extremely expensive, instead perform to queries
        # First quary to get user_id form auth_tokens table, then second quary
        # to get user data from auth_users table with user_id.
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
        # Insert token data
        insert_token_sql = """INSERT INTO auth_tokens (user_id, token) VALUES (?, ?)"""
        self.cursor.execute(insert_token_sql, [user_id, token])

        self.connection.commit()

    def add_user(self, user):
        # Hash password
        salt = uuid.uuid4().hex
        password_hash = get_pass_hash(user.password, salt)

        # Insert user data
        insert_user_sql = """INSERT INTO auth_users (email, school_id, password_hash, salt) VALUES (?, ?, ?, ?)"""
        self.cursor.execute(
            insert_user_sql, [user.email, user.schoolId, password_hash, salt]
        )

        # Get the last inserted user ID
        user_id = self.cursor.lastrowid

        # Finish
        self.connection.commit()

        return user_id


users_db = UsersDB("data/db/", "users.db")
