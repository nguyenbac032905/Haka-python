from controllers.resourceController import (
    create_record,
    delete_record,
    get_record,
    list_records,
    patch_record,
)

RESOURCE_NAME = "users"
READ_ALIASES = {"tokenUser": "token"}
WRITE_ALIASES = {"token": "tokenUser"}


def list_users():
    return list_records(RESOURCE_NAME, read_aliases=READ_ALIASES, write_aliases=WRITE_ALIASES)


def create_user():
    return create_record(RESOURCE_NAME, read_aliases=READ_ALIASES, write_aliases=WRITE_ALIASES)


def get_user(item_id):
    return get_record(RESOURCE_NAME, item_id, read_aliases=READ_ALIASES)


def patch_user(item_id):
    return patch_record(RESOURCE_NAME, item_id, read_aliases=READ_ALIASES, write_aliases=WRITE_ALIASES)


def delete_user(item_id):
    return delete_record(RESOURCE_NAME, item_id, read_aliases=READ_ALIASES)
