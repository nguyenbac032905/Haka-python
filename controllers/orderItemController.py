from controllers.resourceController import (
    create_record,
    delete_record,
    get_record,
    list_records,
    patch_record,
)

RESOURCE_NAME = "order_items"


def list_order_items():
    return list_records(RESOURCE_NAME)


def create_order_item():
    return create_record(RESOURCE_NAME)


def get_order_item(item_id):
    return get_record(RESOURCE_NAME, item_id)


def patch_order_item(item_id):
    return patch_record(RESOURCE_NAME, item_id)


def delete_order_item(item_id):
    return delete_record(RESOURCE_NAME, item_id)
