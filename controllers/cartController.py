from controllers.resourceController import (
    create_record,
    delete_record,
    get_record,
    list_records,
    patch_record,
)

RESOURCE_NAME = "carts"


def list_carts():
    return list_records(RESOURCE_NAME)


def create_cart():
    return create_record(RESOURCE_NAME)


def get_cart(item_id):
    return get_record(RESOURCE_NAME, item_id)


def patch_cart(item_id):
    return patch_record(RESOURCE_NAME, item_id)


def delete_cart(item_id):
    return delete_record(RESOURCE_NAME, item_id)
