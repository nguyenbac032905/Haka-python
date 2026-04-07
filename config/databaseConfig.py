import sqlite3

DB_NAME = "database/haka.db"

def get_connection():
    """Trả về đối tượng connection"""
    return sqlite3.connect(DB_NAME)