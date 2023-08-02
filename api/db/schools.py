"""
    schools database
"""
import os
import sqlite3
from contextlib import closing

from settings import settings


class SchoolsDB:
    """schools.db wrapper"""

    db_path = "data/db/schools.db"

    def __init__(self, db_path):
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.db_path = db_path
        try:
            self.connection = sqlite3.connect(self.db_path)

            self.create_database_if_not_exists()
        except sqlite3.Error as error:
            print(f"Failed to establish connection to database\n{error}")

    def __del__(self):
        self.connection.commit()
        self.connection.close()

    def create_database_if_not_exists(self):
        """Creates schools table if needed"""

        with closing(self.connection.cursor()) as cursor:
            cursor.execute(
                """CREATE TABLE IF NOT EXISTS schools (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        title VARCHAR NOT NULL,
                        short_name VARCHAR NOT NULL,
                        url VARCHAR NOT NULL
                )"""
            )
            (rows,) = cursor.execute("SELECT COUNT(id) from schools").fetchone()
            if rows == 0:
                cursor.executemany(
                    """INSERT INTO schools (title, short_name, url) VALUES (?, ?, ?)""",
                    [
                        (
                            "University of Washington",
                            "UW",
                            "https://www.cs.washington.edu",
                        ),
                        ("Bellevue high school", "BHS", "https://bsd405.org/bhs"),
                        ("Sammamish high school", "SHS", "https://bsd405.org/sammamish"),
                        ("Interlake high school", "IHS", "https://bsd405.org/interlake"),
                        ("Newport high school", "NHS", "https://bsd405.org/nhs"),
                        ("Bellevue college", "BC", "https://www.bellevuecollege.edu"),
                    ],
                )

        self.connection.commit()

    def get_schools(self):
        """Returns a list of all schools in database"""
        with closing(self.connection.cursor()) as cursor:
            cursor.execute("SELECT id, title, short_name, url FROM schools")
            rows = cursor.fetchall()

            return rows


schools_db = SchoolsDB(settings.db_path)
