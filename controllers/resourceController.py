import sqlite3

from flask import jsonify, request

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


def normalize_aliases(aliases):
    return aliases or {}


def to_db_field(field_name, write_aliases):
    return normalize_aliases(write_aliases).get(field_name, field_name)


def serialize_record(record, read_aliases=None):
    if not record:
        return record

    serialized = dict(record)
    for db_field, api_field in normalize_aliases(read_aliases).items():
        if db_field in serialized:
            serialized[api_field] = serialized.pop(db_field)
    return serialized


def serialize_records(records, read_aliases=None):
    return [serialize_record(record, read_aliases) for record in records]


def list_records(table, read_aliases=None, write_aliases=None):
    table_name = normalize_table_name(table)
    if not table_name:
        return error_response("Bảng không hợp lệ", 404)

    column_map = get_column_map(table_name)
    query_args = request.args.to_dict(flat=True)
    where_clauses = []
    params = []

    for raw_key, value in query_args.items():
        if raw_key in RESERVED_QUERY_PARAMS:
            continue

        key = to_db_field(raw_key, write_aliases)
        if key not in column_map:
            continue

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
        db_sort_by = to_db_field(sort_by, write_aliases)
        if db_sort_by in column_map:
            if sort_order not in {"ASC", "DESC"}:
                sort_order = "ASC"
            sql += f" ORDER BY {db_sort_by} {sort_order}"
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
    return jsonify(serialize_records(records, read_aliases))


def get_record(table, item_id, read_aliases=None):
    table_name = normalize_table_name(table)
    if not table_name:
        return error_response("Bảng không hợp lệ", 404)

    record = get_record_by_id(table_name, item_id)
    if not record:
        return error_response("Không tìm thấy dữ liệu", 404)
    return jsonify(serialize_record(record, read_aliases))


def create_record(table, read_aliases=None, write_aliases=None):
    table_name = normalize_table_name(table)
    if not table_name:
        return error_response("Bảng không hợp lệ", 404)

    payload = request.get_json(silent=True)
    if payload is None:
        payload = {}
    if not isinstance(payload, dict):
        return error_response("Body phải là JSON object", 400)

    column_map = get_column_map(table_name)
    insert_data = {}

    for raw_key, value in payload.items():
        key = to_db_field(raw_key, write_aliases)
        if key == "id" or key not in column_map:
            continue
        insert_data[key] = cast_column_value(value, column_map[key]["type"])

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
    return jsonify(serialize_record(created_record, read_aliases)), 201


def patch_record(table, item_id, read_aliases=None, write_aliases=None):
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
    update_data = {}

    for raw_key, value in payload.items():
        key = to_db_field(raw_key, write_aliases)
        if key == "id" or key not in column_map:
            continue
        update_data[key] = cast_column_value(value, column_map[key]["type"])

    if not update_data:
        return error_response("Không có field hợp lệ để cập nhật", 400)

    assignments = [f"{field} = ?" for field in update_data]
    params = list(update_data.values())

    if "updatedAt" in column_map:
        assignments.append("updatedAt = CURRENT_TIMESTAMP")

    params.append(item_id)

    try:
        execute_non_query(
            f"UPDATE {table_name} SET {', '.join(assignments)} WHERE id = ?",
            tuple(params),
        )
    except sqlite3.IntegrityError as error:
        return error_response(f"Lỗi dữ liệu: {error}", 400)

    updated_record = get_record_by_id(table_name, item_id)
    return jsonify(serialize_record(updated_record, read_aliases))


def delete_record(table, item_id, read_aliases=None):
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
        deleted_record = get_record_by_id(table_name, item_id)
        return jsonify(serialize_record(deleted_record, read_aliases))

    execute_non_query(f"DELETE FROM {table_name} WHERE id = ?", (item_id,))
    return jsonify(serialize_record(existing_record, read_aliases))
