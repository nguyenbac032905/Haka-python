from functools import lru_cache

from config.databaseConfig import get_connection

TABLE_ALIASES = {
    "product-categories": "product_categories",
    "cart-items": "cart_items",
    "order-items": "order_items",
}

ALLOWED_TABLES = {
    "accounts",
    "users",
    "product_categories",
    "products",
    "orders",
    "order_items",
}


def execute_query(command, params=()):
    """Dùng cho INSERT, UPDATE, DELETE và trả về lastrowid."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(command, params)
    conn.commit()
    last_id = cursor.lastrowid
    conn.close()
    return last_id


def execute_non_query(command, params=()):
    """Dùng cho UPDATE, DELETE và trả về số dòng bị ảnh hưởng."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(command, params)
    conn.commit()
    row_count = cursor.rowcount
    conn.close()
    return row_count


def fetch_query(command, params=()):
    """Dùng cho SELECT và trả về list[dict]."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(command, params)
    data = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return data


def fetch_one(command, params=()):
    """Dùng cho SELECT 1 bản ghi và trả về dict hoặc None."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(command, params)
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


@lru_cache(maxsize=1)
def get_database_tables():
    """Lấy danh sách bảng thật sự tồn tại trong database."""
    rows = fetch_query(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'"
    )
    return {row["name"] for row in rows}


def normalize_table_name(table_name):
    """Map tên bảng từ URL sang tên bảng thật trong SQLite."""
    normalized_name = TABLE_ALIASES.get(table_name, table_name.replace("-", "_"))
    if normalized_name in ALLOWED_TABLES and normalized_name in get_database_tables():
        return normalized_name
    return None


@lru_cache(maxsize=None)
def get_table_schema(table_name):
    """Lấy schema của một bảng theo PRAGMA table_info."""
    normalized_name = normalize_table_name(table_name)
    if not normalized_name:
        return []

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({normalized_name})")
    schema = [
        {
            "cid": row["cid"],
            "name": row["name"],
            "type": row["type"],
            "notnull": row["notnull"],
            "default_value": row["dflt_value"],
            "pk": row["pk"],
        }
        for row in cursor.fetchall()
    ]
    conn.close()
    return schema


@lru_cache(maxsize=None)
def get_table_columns(table_name):
    """Trả về danh sách cột của bảng."""
    return [column["name"] for column in get_table_schema(table_name)]
