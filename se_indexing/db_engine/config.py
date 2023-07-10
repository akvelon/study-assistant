import sys

from .db import IndexDB

database = "sqlite3"
path = "se_indexing/index.sqlite"


def get_database():
    if database == "sqlite3":
        return IndexDB(path)
    else:
        raise NotImplementedError(f"Database type {database} is not implemented.")
