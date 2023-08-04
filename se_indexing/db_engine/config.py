"""Configuration for database engine"""
from .db import IndexDB

database = "sqlite3"
path = "se_indexing/index.sqlite"


def get_database():
    """Gets the database connection according to configuration provided"""
    if database == "sqlite3":
        return IndexDB(path)
    raise NotImplementedError(f"Database type {database} is not implemented.")
