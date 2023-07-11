import os
import sqlite3
import hashlib, uuid
from pydantic import BaseModel

def get_pass_hash(password: str, salt: str):
    payload = password + salt
    return hashlib.sha512(payload.encode('utf-8')).hexdigest()

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
            token=token
        )

class UsersDB:
    database_path = "data/db/users.db"

    def __init__(self, db_path, db_name):
        os.makedirs(db_path, exist_ok=True)
        path = os.path.join(db_path, db_name)
        self.database_path = path
        try:
            # Making a connection between sqlite3 database and Python Program
            sqliteConnection = sqlite3.connect(self.database_path)

            cursor = sqliteConnection.cursor()

            cursor.execute(
                """CREATE TABLE IF NOT EXISTS auth_users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email VARCHAR NOT NULL,
                    school_id INTEGER NOT NULL,
                    password_hash BLOB NOT NULL,
                    salt BLOB NOT NULL
                )"""
            )

            cursor.execute(
                """CREATE TABLE IF NOT EXISTS auth_tokens (
                    user_id INTEGER PRIMARY KEY,
                    token TEXT,
                    FOREIGN KEY (user_id) REFERENCES auth_users(id)
                )"""
            )

            sqliteConnection.commit()
            sqliteConnection.close()

        except sqlite3.Error as error:
            print("Failed to connect to sqlite3 database, error: ", error)

    def get_user(self, email):
        connection = sqlite3.connect(self.database_path)
        cursor = connection.cursor()

        cursor.execute("""
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
        """, (email,))
        row = cursor.fetchone()

        if not row:
            return None

        cursor.close()
        connection.close()
        return AuthEntry(*row)

    def add_token(self, user_id, token):
        # TODO: improve DB connection lifecycle
        connection = sqlite3.connect(self.database_path)
        cursor = connection.cursor()

        # Insert token data
        insert_token_sql = """INSERT INTO auth_tokens (user_id, token) VALUES (?, ?)"""
        cursor.execute(insert_token_sql, [user_id, token])

        connection.commit()  
        connection.close()

    def add_user(self, user):
        # TODO: improve DB connection lifecycle
        connection = sqlite3.connect(self.database_path)
        cursor = connection.cursor()

        # Hash password
        salt = uuid.uuid4().hex
        password_hash = get_pass_hash(user.password, salt)

        # Insert user data
        insert_user_sql = """INSERT INTO auth_users (email, school_id, password_hash, salt) VALUES (?, ?, ?, ?)"""
        cursor.execute(insert_user_sql, [user.email, user.schoolId, password_hash, salt])

        # Get the last inserted user ID
        user_id = cursor.lastrowid

        # Finish
        connection.commit()  
        connection.close()
        return user_id

users_db = UsersDB("data/db/", "users.db")
