from flask import Blueprint

from controllers.orderItemController import (
    create_order_item,
    delete_order_item,
    get_order_item,
    list_order_items,
    patch_order_item,
)

order_item_bp = Blueprint("order_items", __name__)


@order_item_bp.route("/order_items", methods=["GET"])
def list_order_items_route():
    return list_order_items()


@order_item_bp.route("/order_items", methods=["POST"])
def create_order_items_route():
    return create_order_item()


@order_item_bp.route("/order_items/<int:item_id>", methods=["GET"])
def get_order_items_route(item_id):
    return get_order_item(item_id)


@order_item_bp.route("/order_items/<int:item_id>", methods=["PATCH"])
def patch_order_items_route(item_id):
    return patch_order_item(item_id)


@order_item_bp.route("/order_items/<int:item_id>", methods=["DELETE"])
def delete_order_items_route(item_id):
    return delete_order_item(item_id)
