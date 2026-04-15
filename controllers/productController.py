import sqlite3

from flask import jsonify, request

from config.databaseConfig import get_connection
from utils.databaseUtil import (
    execute_non_query,
    execute_query,
    fetch_one,
    fetch_query,
    get_table_schema,
    normalize_table_name,
)

RESERVED_QUERY_PARAMS = {"_page", "_limit", "_sort", "_order", "_q"}


def error_response(message, status_code=400):
    return jsonify({"message": message}), status_code


def parse_positive_int(value, default=None, maximum=None):
    if value is None:
        return default

    try:
        parsed_value = int(value)
    except (TypeError, ValueError):
        return default

    if parsed_value <= 0:
        return default
    if maximum is not None:
        return min(parsed_value, maximum)
    return parsed_value


def parse_bool_like(value):
    if isinstance(value, bool):
        return 1 if value else 0

    if isinstance(value, (int, float)):
        return 1 if value else 0

    if isinstance(value, str):
        lowered_value = value.strip().lower()
        if lowered_value in {"true", "1", "yes", "on"}:
            return 1
        if lowered_value in {"false", "0", "no", "off"}:
            return 0

    return None


def cast_column_value(value, column_type):
    if value is None:
        return None

    if isinstance(value, str) and value.strip().lower() == "null":
        return None

    normalized_type = (column_type or "").upper()

    if "BOOL" in normalized_type:
        parsed_bool = parse_bool_like(value)
        return value if parsed_bool is None else parsed_bool

    if "INT" in normalized_type:
        parsed_bool = parse_bool_like(value)
        if parsed_bool is not None:
            return parsed_bool
        try:
            return int(value)
        except (TypeError, ValueError):
            return value

    if any(type_name in normalized_type for type_name in {"REAL", "FLOA", "DOUB", "NUMERIC", "DECIMAL"}):
        try:
            return float(value)
        except (TypeError, ValueError):
            return value

    return value


def get_column_map(table_name):
    return {column["name"]: column for column in get_table_schema(table_name)}


def get_record_by_id(table_name, item_id):
    return fetch_one(f"SELECT * FROM {table_name} WHERE id = ?", (item_id,))


def fetch_active_user(user_id):
    return fetch_one(
        "SELECT * FROM users WHERE id = ? AND COALESCE(deleted, 0) = 0",
        (user_id,),
    )


def fetch_active_product(product_id):
    return fetch_one(
        "SELECT * FROM products WHERE id = ? AND COALESCE(deleted, 0) = 0",
        (product_id,),
    )


def ensure_user_exists(user_id):
    user = fetch_active_user(user_id)
    if not user:
        return None, error_response("User không tồn tại hoặc đã bị xóa", 404)
    return user, None


def ensure_product_exists(product_id):
    product = fetch_active_product(product_id)
    if not product:
        return None, error_response("Sản phẩm không tồn tại hoặc đã bị xóa", 404)
    return product, None


def calculate_cart_summary(items):
    subtotal = 0.0
    grand_total = 0.0
    total_quantity = 0

    for item in items:
        price = float(item.get("price") or 0)
        final_price = float(item.get("finalPrice") or price)
        quantity = int(item.get("quantity") or 0)
        subtotal += price * quantity
        grand_total += final_price * quantity
        total_quantity += quantity

    return {
        "itemsCount": len(items),
        "totalQuantity": total_quantity,
        "subtotal": round(subtotal, 2),
        "discountAmount": round(subtotal - grand_total, 2),
        "grandTotal": round(grand_total, 2),
    }


def get_or_create_cart(user_id, conn=None):
    own_connection = False
    if conn is None:
        conn = get_connection()
        own_connection = True

    cursor = conn.cursor()
    cursor.execute("SELECT * FROM carts WHERE user_id = ? ORDER BY id DESC LIMIT 1", (user_id,))
    cart = cursor.fetchone()

    if not cart:
        cursor.execute("INSERT INTO carts (user_id) VALUES (?)", (user_id,))
        cursor.execute("SELECT * FROM carts WHERE id = ?", (cursor.lastrowid,))
        cart = cursor.fetchone()

    cart_data = dict(cart)

    if own_connection:
        conn.commit()
        conn.close()

    return cart_data


def build_cart_detail(user_id):
    cart = get_or_create_cart(user_id)
    items = fetch_query(
        """
        SELECT
            ci.*,
            p.title AS productTitle,
            p.slug AS productSlug,
            p.thumbnail AS productThumbnail,
            p.price,
            p.discountPercentage,
            p.stock,
            ROUND(p.price * (1 - COALESCE(p.discountPercentage, 0) / 100.0), 2) AS finalPrice,
            ROUND(ci.quantity * p.price * (1 - COALESCE(p.discountPercentage, 0) / 100.0), 2) AS lineTotal
        FROM cart_items ci
        INNER JOIN products p ON p.id = ci.product_id
        WHERE ci.cart_id = ?
        ORDER BY ci.id DESC
        """,
        (cart["id"],),
    )

    return {
        "cart": cart,
        "items": items,
        "summary": calculate_cart_summary(items),
    }


def build_order_detail(order_id):
    order = fetch_one(
        """
        SELECT
            o.*,
            u.email AS userEmail,
            u.avatar AS userAvatar
        FROM orders o
        LEFT JOIN users u ON u.id = o.user_id
        WHERE o.id = ?
        """,
        (order_id,),
    )
    if not order:
        return None

    items = fetch_query(
        """
        SELECT
            oi.*,
            p.title AS productTitle,
            p.slug AS productSlug,
            p.thumbnail AS productThumbnail,
            ROUND(oi.price * (1 - COALESCE(oi.discountPercentage, 0) / 100.0), 2) AS finalPrice,
            ROUND(oi.quantity * oi.price * (1 - COALESCE(oi.discountPercentage, 0) / 100.0), 2) AS lineTotal
        FROM order_items oi
        INNER JOIN products p ON p.id = oi.product_id
        WHERE oi.order_id = ?
        ORDER BY oi.id DESC
        """,
        (order_id,),
    )

    subtotal = sum(float(item.get("price") or 0) * int(item.get("quantity") or 0) for item in items)
    grand_total = sum(float(item.get("lineTotal") or 0) for item in items)

    return {
        "order": order,
        "items": items,
        "summary": {
            "itemsCount": len(items),
            "totalQuantity": sum(int(item.get("quantity") or 0) for item in items),
            "subtotal": round(subtotal, 2),
            "discountAmount": round(subtotal - grand_total, 2),
            "grandTotal": round(grand_total, 2),
        },
    }


def list_records(table):
    table_name = normalize_table_name(table)
    if not table_name:
        return error_response("Bảng không hợp lệ", 404)

    column_map = get_column_map(table_name)
    query_args = request.args.to_dict(flat=True)
    where_clauses = []
    params = []

    for key, value in query_args.items():
        if key in RESERVED_QUERY_PARAMS:
            continue
        if key not in column_map:
            return error_response(f"Field lọc không hợp lệ: {key}", 400)
        where_clauses.append(f"{key} = ?")
        params.append(cast_column_value(value, column_map[key]["type"]))

    keyword = query_args.get("_q")
    if keyword:
        text_columns = [
            column_name
            for column_name, metadata in column_map.items()
            if any(type_name in (metadata["type"] or "").upper() for type_name in {"CHAR", "TEXT", "CLOB"})
        ]
        if text_columns:
            where_clauses.append("(" + " OR ".join(f"{column} LIKE ?" for column in text_columns) + ")")
            params.extend([f"%{keyword}%"] * len(text_columns))

    sql = f"SELECT * FROM {table_name}"
    if where_clauses:
        sql += " WHERE " + " AND ".join(where_clauses)

    sort_by = query_args.get("_sort")
    sort_order = query_args.get("_order", "ASC").upper()
    if sort_by:
        if sort_by not in column_map:
            return error_response(f"Field sort không hợp lệ: {sort_by}", 400)
        if sort_order not in {"ASC", "DESC"}:
            sort_order = "ASC"
        sql += f" ORDER BY {sort_by} {sort_order}"
    elif "id" in column_map:
        sql += " ORDER BY id DESC"

    limit = parse_positive_int(query_args.get("_limit"), maximum=100)
    page = parse_positive_int(query_args.get("_page"))

    if page and not limit:
        limit = 10

    if limit:
        sql += " LIMIT ?"
        params.append(limit)
        if page:
            sql += " OFFSET ?"
            params.append((page - 1) * limit)

    records = fetch_query(sql, tuple(params))
    return jsonify(records)


def get_record(table, item_id):
    table_name = normalize_table_name(table)
    if not table_name:
        return error_response("Bảng không hợp lệ", 404)

    record = get_record_by_id(table_name, item_id)
    if not record:
        return error_response("Không tìm thấy dữ liệu", 404)
    return jsonify(record)


def create_record(table):
    table_name = normalize_table_name(table)
    if not table_name:
        return error_response("Bảng không hợp lệ", 404)

    payload = request.get_json(silent=True)
    if payload is None:
        payload = {}
    if not isinstance(payload, dict):
        return error_response("Body phải là JSON object", 400)

    column_map = get_column_map(table_name)
    invalid_fields = [key for key in payload if key not in column_map or key == "id"]
    if invalid_fields:
        return error_response(f"Field không hợp lệ: {', '.join(invalid_fields)}", 400)

    insert_data = {
        key: cast_column_value(value, column_map[key]["type"])
        for key, value in payload.items()
        if key != "id"
    }

    if (
        "status" in column_map
        and "status" not in insert_data
        and column_map["status"].get("default_value") is None
    ):
        insert_data["status"] = "active"
    if "deleted" in column_map and "deleted" not in insert_data:
        insert_data["deleted"] = 0

    try:
        if insert_data:
            columns_sql = ", ".join(insert_data.keys())
            placeholders = ", ".join(["?"] * len(insert_data))
            last_id = execute_query(
                f"INSERT INTO {table_name} ({columns_sql}) VALUES ({placeholders})",
                tuple(insert_data.values()),
            )
        else:
            last_id = execute_query(f"INSERT INTO {table_name} DEFAULT VALUES")
    except sqlite3.IntegrityError as error:
        return error_response(f"Lỗi dữ liệu: {error}", 400)

    created_record = get_record_by_id(table_name, last_id)
    return jsonify(created_record), 201


def patch_record(table, item_id):
    table_name = normalize_table_name(table)
    if not table_name:
        return error_response("Bảng không hợp lệ", 404)

    existing_record = get_record_by_id(table_name, item_id)
    if not existing_record:
        return error_response("Không tìm thấy dữ liệu", 404)

    payload = request.get_json(silent=True)
    if not isinstance(payload, dict) or not payload:
        return error_response("Body phải là JSON object và có ít nhất 1 field", 400)

    column_map = get_column_map(table_name)
    invalid_fields = [key for key in payload if key not in column_map or key == "id"]
    if invalid_fields:
        return error_response(f"Field không hợp lệ: {', '.join(invalid_fields)}", 400)

    update_data = {
        key: cast_column_value(value, column_map[key]["type"])
        for key, value in payload.items()
        if key != "id"
    }

    assignments = [f"{field} = ?" for field in update_data]
    params = list(update_data.values())

    if "updatedAt" in column_map:
        assignments.append("updatedAt = CURRENT_TIMESTAMP")

    if not assignments:
        return error_response("Không có field hợp lệ để cập nhật", 400)

    params.append(item_id)

    try:
        execute_non_query(
            f"UPDATE {table_name} SET {', '.join(assignments)} WHERE id = ?",
            tuple(params),
        )
    except sqlite3.IntegrityError as error:
        return error_response(f"Lỗi dữ liệu: {error}", 400)

    updated_record = get_record_by_id(table_name, item_id)
    return jsonify(updated_record)


def delete_record(table, item_id):
    table_name = normalize_table_name(table)
    if not table_name:
        return error_response("Bảng không hợp lệ", 404)

    existing_record = get_record_by_id(table_name, item_id)
    if not existing_record:
        return error_response("Không tìm thấy dữ liệu", 404)

    column_map = get_column_map(table_name)

    if "deleted" in column_map:
        assignments = ["deleted = 1"]
        if "deletedAt" in column_map:
            assignments.append("deletedAt = CURRENT_TIMESTAMP")
        if "updatedAt" in column_map:
            assignments.append("updatedAt = CURRENT_TIMESTAMP")

        execute_non_query(
            f"UPDATE {table_name} SET {', '.join(assignments)} WHERE id = ?",
            (item_id,),
        )
        return jsonify(get_record_by_id(table_name, item_id))

    execute_non_query(f"DELETE FROM {table_name} WHERE id = ?", (item_id,))
    return jsonify({"message": "Xóa dữ liệu thành công"})


def login_account():
    payload = request.get_json(silent=True) or {}
    email = payload.get("email")
    password = payload.get("password")

    if not email or not password:
        return error_response("Cần truyền email và password", 400)

    account = fetch_one(
        """
        SELECT *
        FROM accounts
        WHERE email = ? AND password = ? AND COALESCE(deleted, 0) = 0
        LIMIT 1
        """,
        (email, password),
    )

    if not account:
        return error_response("Email hoặc password không đúng", 401)

    return jsonify(account)


def login_user():
    payload = request.get_json(silent=True) or {}
    email = payload.get("email")
    password = payload.get("password")

    if not email or not password:
        return error_response("Cần truyền email và password", 400)

    user = fetch_one(
        """
        SELECT *
        FROM users
        WHERE email = ? AND password = ? AND COALESCE(deleted, 0) = 0
        LIMIT 1
        """,
        (email, password),
    )

    if not user:
        return error_response("Email hoặc password không đúng", 401)

    return jsonify(user)


def search_products():
    query_args = request.args
    where_clauses = ["COALESCE(p.deleted, 0) = 0"]
    params = []

    if query_args.get("status"):
        where_clauses.append("p.status = ?")
        params.append(query_args.get("status"))
    else:
        where_clauses.append("COALESCE(p.status, 'active') = 'active'")

    keyword = query_args.get("q")
    if keyword:
        where_clauses.append(
            "("
            "p.title LIKE ? OR "
            "COALESCE(p.description, '') LIKE ? OR "
            "COALESCE(p.content, '') LIKE ? OR "
            "COALESCE(p.slug, '') LIKE ?"
            ")"
        )
        params.extend([f"%{keyword}%"] * 4)

    category_id = query_args.get("categoryId")
    if category_id:
        where_clauses.append("p.product_category_id = ?")
        params.append(category_id)

    min_price = query_args.get("minPrice")
    if min_price is not None:
        try:
            params.append(float(min_price))
            where_clauses.append("p.price >= ?")
        except ValueError:
            return error_response("minPrice phải là số", 400)

    max_price = query_args.get("maxPrice")
    if max_price is not None:
        try:
            params.append(float(max_price))
            where_clauses.append("p.price <= ?")
        except ValueError:
            return error_response("maxPrice phải là số", 400)

    in_stock = parse_bool_like(query_args.get("inStock"))
    if in_stock == 1:
        where_clauses.append("COALESCE(p.stock, 0) > 0")

    sort_map = {
        "price": "p.price",
        "createdAt": "p.createdAt",
        "sold": "p.sold",
        "title": "p.title",
        "position": "p.position",
    }
    sort_by = sort_map.get(query_args.get("sort"), "p.id")
    sort_order = query_args.get("order", "DESC").upper()
    if sort_order not in {"ASC", "DESC"}:
        sort_order = "DESC"

    limit = parse_positive_int(query_args.get("limit"), default=20, maximum=100)
    page = parse_positive_int(query_args.get("page"), default=1)
    offset = (page - 1) * limit

    products = fetch_query(
        f"""
        SELECT
            p.*,
            pc.title AS categoryTitle,
            pc.slug AS categorySlug,
            ROUND(p.price * (1 - COALESCE(p.discountPercentage, 0) / 100.0), 2) AS finalPrice
        FROM products p
        LEFT JOIN product_categories pc ON pc.id = p.product_category_id
        WHERE {' AND '.join(where_clauses)}
        ORDER BY {sort_by} {sort_order}
        LIMIT ? OFFSET ?
        """,
        tuple(params + [limit, offset]),
    )

    return jsonify(products)


def get_product_by_slug(slug):
    product = fetch_one(
        """
        SELECT
            p.*,
            pc.title AS categoryTitle,
            pc.slug AS categorySlug,
            ROUND(p.price * (1 - COALESCE(p.discountPercentage, 0) / 100.0), 2) AS finalPrice,
            (
                SELECT COUNT(*)
                FROM comments c
                WHERE c.product_id = p.id AND COALESCE(c.deleted, 0) = 0
            ) AS commentsCount,
            (
                SELECT ROUND(AVG(c.rating), 1)
                FROM comments c
                WHERE c.product_id = p.id AND COALESCE(c.deleted, 0) = 0
            ) AS averageRating
        FROM products p
        LEFT JOIN product_categories pc ON pc.id = p.product_category_id
        WHERE p.slug = ? AND COALESCE(p.deleted, 0) = 0
        LIMIT 1
        """,
        (slug,),
    )

    if not product:
        return error_response("Không tìm thấy sản phẩm theo slug", 404)

    return jsonify(product)


def get_category_tree():
    categories = fetch_query(
        """
        SELECT *
        FROM product_categories
        WHERE COALESCE(deleted, 0) = 0
        ORDER BY COALESCE(position, 999999), id ASC
        """
    )

    lookup = {}
    roots = []

    for category in categories:
        category["children"] = []
        lookup[category["id"]] = category

    for category in categories:
        parent_id = category.get("parent_id")
        if parent_id and parent_id in lookup:
            lookup[parent_id]["children"].append(category)
        else:
            roots.append(category)

    return jsonify(roots)


def get_product_comments(product_id):
    product, error = ensure_product_exists(product_id)
    if error:
        return error

    comments = fetch_query(
        """
        SELECT
            c.*,
            u.fullName AS userFullName,
            u.avatar AS userAvatar
        FROM comments c
        INNER JOIN users u ON u.id = c.user_id
        WHERE c.product_id = ? AND COALESCE(c.deleted, 0) = 0
        ORDER BY c.updatedAt DESC, c.id DESC
        """,
        (product_id,),
    )

    average_rating = round(
        sum(int(comment.get("rating") or 0) for comment in comments) / len(comments),
        1,
    ) if comments else 0

    return jsonify(
        {
            "product": {
                "id": product["id"],
                "title": product["title"],
                "slug": product["slug"],
            },
            "summary": {
                "count": len(comments),
                "averageRating": average_rating,
            },
            "items": comments,
        }
    )


def upsert_product_comment(product_id):
    product, error = ensure_product_exists(product_id)
    if error:
        return error

    payload = request.get_json(silent=True) or {}
    user_id = payload.get("user_id")
    rating = payload.get("rating")

    if not user_id or rating is None:
        return error_response("Cần truyền user_id và rating", 400)

    user, error = ensure_user_exists(user_id)
    if error:
        return error

    try:
        rating = int(rating)
    except (TypeError, ValueError):
        return error_response("rating phải là số nguyên từ 1 đến 5", 400)

    if rating < 1 or rating > 5:
        return error_response("rating phải nằm trong khoảng 1 đến 5", 400)

    content = payload.get("content")
    image = payload.get("image")

    existing_comment = fetch_one(
        "SELECT * FROM comments WHERE user_id = ? AND product_id = ? LIMIT 1",
        (user_id, product_id),
    )

    if existing_comment:
        execute_non_query(
            """
            UPDATE comments
            SET rating = ?, content = ?, image = ?, deleted = 0, updatedAt = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (rating, content, image, existing_comment["id"]),
        )
        comment_id = existing_comment["id"]
    else:
        comment_id = execute_query(
            """
            INSERT INTO comments (user_id, product_id, rating, content, image, deleted)
            VALUES (?, ?, ?, ?, ?, 0)
            """,
            (user["id"], product["id"], rating, content, image),
        )

    comment = fetch_one(
        """
        SELECT
            c.*,
            u.fullName AS userFullName,
            u.avatar AS userAvatar
        FROM comments c
        INNER JOIN users u ON u.id = c.user_id
        WHERE c.id = ?
        """,
        (comment_id,),
    )

    return jsonify(comment), 201 if not existing_comment else 200


def get_user_cart(user_id):
    _, error = ensure_user_exists(user_id)
    if error:
        return error

    return jsonify(build_cart_detail(user_id))


def add_item_to_cart(user_id):
    _, error = ensure_user_exists(user_id)
    if error:
        return error

    payload = request.get_json(silent=True) or {}
    product_id = payload.get("product_id")
    quantity = payload.get("quantity", 1)

    if not product_id:
        return error_response("Cần truyền product_id", 400)

    try:
        quantity = int(quantity)
    except (TypeError, ValueError):
        return error_response("quantity phải là số nguyên dương", 400)

    if quantity <= 0:
        return error_response("quantity phải lớn hơn 0", 400)

    product, error = ensure_product_exists(product_id)
    if error:
        return error

    conn = get_connection()
    try:
        cart = get_or_create_cart(user_id, conn)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM cart_items WHERE cart_id = ? AND product_id = ? LIMIT 1",
            (cart["id"], product["id"]),
        )
        existing_item = cursor.fetchone()

        current_quantity = existing_item["quantity"] if existing_item else 0
        next_quantity = current_quantity + quantity

        if product.get("stock") is not None and next_quantity > int(product["stock"]):
            return error_response("Số lượng vượt quá tồn kho hiện tại", 400)

        if existing_item:
            cursor.execute(
                """
                UPDATE cart_items
                SET quantity = ?, updatedAt = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (next_quantity, existing_item["id"]),
            )
        else:
            cursor.execute(
                "INSERT INTO cart_items (cart_id, product_id, quantity) VALUES (?, ?, ?)",
                (cart["id"], product["id"], quantity),
            )

        cursor.execute("UPDATE carts SET updatedAt = CURRENT_TIMESTAMP WHERE id = ?", (cart["id"],))
        conn.commit()
    except sqlite3.Error as error:
        conn.rollback()
        return error_response(f"Không thể cập nhật giỏ hàng: {error}", 400)
    finally:
        conn.close()

    return jsonify(build_cart_detail(user_id)), 201


def update_cart_item(user_id, item_id):
    _, error = ensure_user_exists(user_id)
    if error:
        return error

    payload = request.get_json(silent=True) or {}
    quantity = payload.get("quantity")

    if quantity is None:
        return error_response("Cần truyền quantity", 400)

    try:
        quantity = int(quantity)
    except (TypeError, ValueError):
        return error_response("quantity phải là số nguyên", 400)

    conn = get_connection()
    try:
        cart = get_or_create_cart(user_id, conn)
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT
                ci.*,
                p.stock
            FROM cart_items ci
            INNER JOIN products p ON p.id = ci.product_id
            WHERE ci.id = ? AND ci.cart_id = ?
            LIMIT 1
            """,
            (item_id, cart["id"]),
        )
        item = cursor.fetchone()

        if not item:
            return error_response("Không tìm thấy item trong giỏ hàng", 404)

        if quantity <= 0:
            cursor.execute("DELETE FROM cart_items WHERE id = ?", (item_id,))
        else:
            if item["stock"] is not None and quantity > int(item["stock"]):
                return error_response("Số lượng vượt quá tồn kho hiện tại", 400)
            cursor.execute(
                """
                UPDATE cart_items
                SET quantity = ?, updatedAt = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (quantity, item_id),
            )

        cursor.execute("UPDATE carts SET updatedAt = CURRENT_TIMESTAMP WHERE id = ?", (cart["id"],))
        conn.commit()
    except sqlite3.Error as error:
        conn.rollback()
        return error_response(f"Không thể cập nhật item giỏ hàng: {error}", 400)
    finally:
        conn.close()

    return jsonify(build_cart_detail(user_id))


def delete_cart_item(user_id, item_id):
    _, error = ensure_user_exists(user_id)
    if error:
        return error

    conn = get_connection()
    try:
        cart = get_or_create_cart(user_id, conn)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM cart_items WHERE id = ? AND cart_id = ?", (item_id, cart["id"]))
        if cursor.rowcount == 0:
            return error_response("Không tìm thấy item trong giỏ hàng", 404)

        cursor.execute("UPDATE carts SET updatedAt = CURRENT_TIMESTAMP WHERE id = ?", (cart["id"],))
        conn.commit()
    except sqlite3.Error as error:
        conn.rollback()
        return error_response(f"Không thể xóa item khỏi giỏ hàng: {error}", 400)
    finally:
        conn.close()

    return jsonify(build_cart_detail(user_id))


def create_order_from_cart():
    payload = request.get_json(silent=True) or {}
    user_id = payload.get("user_id")
    full_name = payload.get("fullName")
    phone = payload.get("phone")
    address = payload.get("address")
    payment_method = payload.get("paymentMethod", "cod")

    if not user_id or not full_name or not phone or not address:
        return error_response("Cần truyền user_id, fullName, phone, address", 400)

    _, error = ensure_user_exists(user_id)
    if error:
        return error

    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM carts WHERE user_id = ? ORDER BY id DESC LIMIT 1", (user_id,))
        cart = cursor.fetchone()
        if not cart:
            return error_response("Người dùng chưa có giỏ hàng", 400)

        cursor.execute(
            """
            SELECT
                ci.*,
                p.title,
                p.price,
                p.discountPercentage,
                p.stock
            FROM cart_items ci
            INNER JOIN products p ON p.id = ci.product_id
            WHERE ci.cart_id = ?
            """,
            (cart["id"],),
        )
        cart_items = cursor.fetchall()

        if not cart_items:
            return error_response("Giỏ hàng đang trống", 400)

        for item in cart_items:
            if item["stock"] is not None and int(item["quantity"]) > int(item["stock"]):
                return error_response(
                    f"Sản phẩm '{item['title']}' không đủ tồn kho để tạo đơn hàng",
                    400,
                )

        cursor.execute(
            """
            INSERT INTO orders (user_id, fullName, phone, address, paymentMethod, status, paymentStatus, deleted)
            VALUES (?, ?, ?, ?, ?, 'initial', 'pending', 0)
            """,
            (user_id, full_name, phone, address, payment_method),
        )
        order_id = cursor.lastrowid

        for item in cart_items:
            cursor.execute(
                """
                INSERT INTO order_items (order_id, product_id, price, quantity, discountPercentage)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    order_id,
                    item["product_id"],
                    item["price"],
                    item["quantity"],
                    item["discountPercentage"] or 0,
                ),
            )
            cursor.execute(
                """
                UPDATE products
                SET
                    stock = CASE WHEN stock IS NULL THEN NULL ELSE stock - ? END,
                    sold = COALESCE(sold, 0) + ?,
                    updatedAt = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (item["quantity"], item["quantity"], item["product_id"]),
            )

        cursor.execute("DELETE FROM cart_items WHERE cart_id = ?", (cart["id"],))
        cursor.execute("UPDATE carts SET updatedAt = CURRENT_TIMESTAMP WHERE id = ?", (cart["id"],))
        conn.commit()
    except sqlite3.Error as error:
        conn.rollback()
        return error_response(f"Không thể tạo đơn hàng: {error}", 400)
    finally:
        conn.close()

    return jsonify(build_order_detail(order_id)), 201


def get_order_detail(order_id):
    order_detail = build_order_detail(order_id)
    if not order_detail:
        return error_response("Không tìm thấy đơn hàng", 404)
    return jsonify(order_detail)


def get_user_orders(user_id):
    _, error = ensure_user_exists(user_id)
    if error:
        return error

    orders = fetch_query(
        """
        SELECT
            o.*,
            (
                SELECT ROUND(
                    SUM(oi.quantity * oi.price * (1 - COALESCE(oi.discountPercentage, 0) / 100.0)),
                    2
                )
                FROM order_items oi
                WHERE oi.order_id = o.id
            ) AS grandTotal
        FROM orders o
        WHERE o.user_id = ? AND COALESCE(o.deleted, 0) = 0
        ORDER BY o.createdAt DESC, o.id DESC
        """,
        (user_id,),
    )
    return jsonify(orders)


def update_order_status(order_id):
    existing_order = fetch_one("SELECT * FROM orders WHERE id = ?", (order_id,))
    if not existing_order:
        return error_response("Không tìm thấy đơn hàng", 404)

    payload = request.get_json(silent=True) or {}
    allowed_fields = {"status", "paymentStatus", "paymentMethod", "phone", "address"}
    update_data = {key: value for key, value in payload.items() if key in allowed_fields}

    if not update_data:
        return error_response("Không có field hợp lệ để cập nhật đơn hàng", 400)

    assignments = [f"{field} = ?" for field in update_data]
    params = list(update_data.values()) + [order_id]

    execute_non_query(
        f"UPDATE orders SET {', '.join(assignments)}, updatedAt = CURRENT_TIMESTAMP WHERE id = ?",
        tuple(params),
    )

    return jsonify(build_order_detail(order_id))
