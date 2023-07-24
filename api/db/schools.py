"""
    schools database
"""
import os
import sqlite3


class SchoolsDB:
    """schools.db wrapper"""

    database_path = "data/db/schools.db"

    def __init__(self, db_path, db_name):
        os.makedirs(db_path, exist_ok=True)
        path = os.path.join(db_path, db_name)
        self.database_path = path
        try:
            self.connection = sqlite3.connect(self.database_path)
            self.cursor = self.connection.cursor()

            self.create_database_if_not_exists()
        except sqlite3.Error as error:
            print(f"Failed to establish connection to database\n{error}")

    def __del__(self):
        self.connection.commit()
        self.connection.close()

    def create_database_if_not_exists(self):
        """Creates schools table if needed"""
        self.cursor.execute(
            """CREATE TABLE IF NOT EXISTS schools (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title VARCHAR NOT NULL,
                    short_name VARCHAR NOT NULL
            )"""
        )
        self.connection.commit()

    def get_schools(self):
        """Returns a list of all schools in database"""
        self.cursor.execute("SELECT id, title, short_name FROM schools")
        rows = self.cursor.fetchall()

        # Create a list to store the results
        result = []

        # Iterate through the fetched rows and append them to the result list
        for row in rows:
            id_value, title, short_name = row
            result.append((id_value, title, short_name))

        return result


schools_db = SchoolsDB("data/db/", "schools.db")
