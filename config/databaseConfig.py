import sqlite3

DB_NAME = "database/haka.db"

def get_connection():
    """Trả về đối tượng connection"""
    connection = sqlite3.connect(DB_NAME)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection
