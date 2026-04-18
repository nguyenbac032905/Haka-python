from controllers.resourceController import (
    create_record,
    delete_record,
    get_record,
    list_records,
    patch_record,
)

RESOURCE_NAME = "product_categories"


def list_product_categories():
    return list_records(RESOURCE_NAME)


def create_product_category():
    return create_record(RESOURCE_NAME)


def get_product_category(item_id):
    return get_record(RESOURCE_NAME, item_id)


def patch_product_category(item_id):
    return patch_record(RESOURCE_NAME, item_id)


def delete_product_category(item_id):
    return delete_record(RESOURCE_NAME, item_id)
