"""history.py implement HistoryDB that handles all database interactions."""

import sqlite3
import pickle
import zlib
from contextlib import closing

from settings import settings
from api.endpoints.schemas import Message, History, Chat


class HistoryDB:
    """HistoryDB is a singleton class that handles all database interactions"""

    def __init__(self):
        try:
            self.connection = sqlite3.connect(settings.db_path)

            self.create_if_not_exists()
        except sqlite3.Error as error:
            print("Failed to connect to HistoryDB.")
            print(error)
            print(error.sqlite_errorcode)
            print(error.sqlite_errorname)

    def __del__(self):
        if self.connection:
            self.connection = self.connection.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self.connection:
            self.connection = self.connection.close()

    def create_if_not_exists(self):
        """Create History table if it doesn't exist."""
        sql_create_history_table = """
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            openai_id TEXT,
            user_id INTEGER REFERENCES auth_users(id),
            summary TEXT,
            messages BLOB
        );"""
        with closing(self.connection.cursor()) as cursor:
            cursor.execute(sql_create_history_table)
        self.connection.commit()

    def delete(self):
        """Delete History table."""
        with closing(self.connection.cursor()) as cursor:
            cursor.execute("DROP TABLE IF EXISTS chat_history")
        self.connection.commit()

    def get_history(self, chat_id: int) -> History | None:
        """Grab singular history by id and return it."""
        sql_select_history = """
        SELECT * FROM chat_history WHERE id = ?;"""

        try:
            with closing(self.connection.cursor()) as cursor:
                cursor.execute(
                    sql_select_history,
                    (chat_id,),
                )
                history_raw = cursor.fetchone()

                if history_raw is None:
                    return None

                return History(
                    user_id=history_raw[2],
                    chat=Chat(id=history_raw[0], summary=history_raw[3]),
                    messages=uncompress_messages(history_raw[4]),
                )
        except sqlite3.Error as error:
            print(f"Failed query: {sql_select_history}\n{error}")
            raise HistoryDbException from error

    def get_history_by_ids(self, openai_id: str, user_id: int) -> History | None:
        """Grab singular history by openai_id and user_id and return it."""

        sql_select_history = """
        SELECT * FROM chat_history WHERE openai_id = ? AND user_id = ?;"""

        try:
            with closing(self.connection.cursor()) as cursor:
                cursor.execute(
                    sql_select_history,
                    (
                        openai_id,
                        user_id,
                    ),
                )
                history_raw = cursor.fetchone()

                if history_raw is None:
                    return None

                return History(
                    user_id=history_raw[2],
                    chat=Chat(id=history_raw[0], summary=history_raw[3]),
                    messages=uncompress_messages(history_raw[4]),
                )
        except sqlite3.Error as error:
            print(f"Failed query: {sql_select_history}\n{error}")
            raise HistoryDbException from error

    def get_all_history_by_user_id(self, user_id: int) -> list[History] | None:
        """Grab all history for user and return"""
        sql_select_all_history = """
        SELECT * FROM chat_history WHERE user_id = ?;"""

        # Grab all chat_history for user
        history_raw = None
        with closing(self.connection.cursor()) as cursor:
            cursor.execute(sql_select_all_history, (user_id,))
            history_raw = cursor.fetchall()

        # Check if SELECT failed to find user_id
        if history_raw is None:
            raise InvalidUserIdException

        # Convert raw data to History objects
        history: list[History] = []
        for row in history_raw:
            history.append(
                History(
                    user_id=row[2],
                    chat=Chat(id=row[0], summary=row[3]),
                    messages=uncompress_messages(row[4]),
                )
            )

        # Return History
        return history

    def create_new_history_ids(
        self, openai_id: str, user_id: int, summary: str | None
    ) -> int:
        """Create new history and return id."""
        sql_query = """
        INSERT INTO chat_history (openai_id, user_id, summary, messages)
        VALUES (?, ?, ?, NULL);"""
        with closing(self.connection.cursor()) as cursor:
            cursor.execute(
                sql_query,
                (
                    openai_id,
                    user_id,
                    summary,
                ),
            )
            self.connection.commit()
            return cursor.lastrowid

    def get_messages(self, chat_id: int) -> list[Message]:
        """Return json data from column messages in History table."""
        sql_query = """
        SELECT messages FROM chat_history WHERE id = ?;"""

        # Get messages blob from history
        message_blob = None
        with closing(self.connection.cursor()) as cursor:
            cursor.execute(
                sql_query,
                (chat_id,),
            )
            message_blob = cursor.fetchone()

        # Check if SELECT failed to find by history_id
        if message_blob is None:
            raise InvalidChatIdException

        # We only want the first element
        message_blob = message_blob[0]

        messages = []
        # Check if blob contains any data (could be newly created History)
        if message_blob:
            # Uncompress and unpickle the blob
            messages = uncompress_messages(message_blob)

        return messages

    def get_messages_by_ids(self, openai_id: str, user_id: int) -> list[Message]:
        """Return json data from column messages in History table."""
        sql_query = """
        SELECT messages FROM chat_history WHERE openai_id = ? AND user_id = ?;"""

        # Get messages blob from history
        message_blob = None
        with closing(self.connection.cursor()) as cursor:
            cursor.execute(
                sql_query,
                (
                    openai_id,
                    user_id,
                ),
            )
            message_blob = cursor.fetchone()

        # Check if SELECT failed to find by history_id
        if message_blob is None:
            raise InvalidHistoryException

        # We only want the first element
        message_blob = message_blob[0]

        messages = []
        # Check if blob contains any data (could be newly created History)
        if message_blob:
            # Uncompress and unpickle the blob
            messages = uncompress_messages(message_blob)

        return messages

    def update_messages(self, chat_id: int, messages: list[Message]):
        """Update messages column for row with matching id"""
        try:
            sql_query = """
            UPDATE chat_history SET messages = ? WHERE id = ?;"""

            # Compress and pickle messages
            blob = compress_messages(messages)

            # Update database
            with closing(self.connection.cursor()) as cursor:
                cursor.execute(
                    sql_query,
                    (
                        sqlite3.Binary(blob),
                        chat_id,
                    ),
                )

            self.connection.commit()
        except sqlite3.Error as error:
            print(f"Error while updating history messages with id = {chat_id}: {error}")
            raise InvalidChatIdException from error

    def update_messages_by_ids(
        self, openai_id: str, user_id: int, messages: list[Message]
    ):
        """Update messages column for row with matching ids"""
        try:
            sql_query = """
            UPDATE chat_history SET messages = ? WHERE openai_id = ? AND user_id = ?;"""

            # Compress and pickle messages
            blob = compress_messages(messages)

            # Update database
            with closing(self.connection.cursor()) as cursor:
                cursor.execute(
                    sql_query,
                    (
                        sqlite3.Binary(blob),
                        openai_id,
                        user_id,
                    ),
                )

            self.connection.commit()
        except sqlite3.Error as error:
            print(f"Error while updating history messages with id = {openai_id}: {error}")
            raise InvalidHistoryException from error


# HistoryDB singleton
history_db = HistoryDB()


class InvalidUserIdException(Exception):
    """InvalidUserIdException is raised when a user_id is not found in the database."""


class InvalidChatIdException(Exception):
    """InvalidChatIdException is raised when a chat_id is not found in the database."""


class InvalidHistoryException(Exception):
    """InvalidHistoryException is raised when a history is not found in the database."""


class HistoryDbException(Exception):
    """HistoryDbException is raised when there is an error with the database."""


def compress_messages(messages: list[Message]):
    """Compress and pickle messages"""
    return zlib.compress(pickle.dumps(messages, pickle.HIGHEST_PROTOCOL))


def uncompress_messages(blob) -> list[Message]:
    """Uncompress and unpickle messages"""
    return pickle.loads(zlib.decompress(blob))
