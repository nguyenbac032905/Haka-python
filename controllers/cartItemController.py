from controllers.resourceController import (
    create_record,
    delete_record,
    get_record,
    list_records,
    patch_record,
)

RESOURCE_NAME = "cart_items"


def list_cart_items():
    return list_records(RESOURCE_NAME)


def create_cart_item():
    return create_record(RESOURCE_NAME)


def get_cart_item(item_id):
    return get_record(RESOURCE_NAME, item_id)


def patch_cart_item(item_id):
    return patch_record(RESOURCE_NAME, item_id)


def delete_cart_item(item_id):
    return delete_record(RESOURCE_NAME, item_id)
