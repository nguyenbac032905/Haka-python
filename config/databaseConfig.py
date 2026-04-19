import sqlite3

DB_NAME = "database/haka.db"

def get_connection():
    conn = sqlite3.connect(
        DB_NAME,
        timeout=10,
        check_same_thread=False
    )

    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")

    return conn