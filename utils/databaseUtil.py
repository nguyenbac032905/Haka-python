from config.databaseConfig import  get_connection

def execute_query(command, params=()):
    """Dùng cho INSERT, UPDATE, DELETE"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(command, params)
    conn.commit()
    last_id = cursor.lastrowid
    conn.close()
    return last_id

def fetch_query(command, params=()):
    """Dùng cho SELECT"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(command, params)
    data = cursor.fetchall()
    conn.close()
    return data