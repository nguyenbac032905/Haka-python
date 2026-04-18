from flask import Blueprint

from controllers.cartItemController import (
    create_cart_item,
    delete_cart_item,
    get_cart_item,
    list_cart_items,
    patch_cart_item,
)

cart_item_bp = Blueprint("cart_items", __name__)


@cart_item_bp.route("/cart_items", methods=["GET"])
def list_cart_items_route():
    return list_cart_items()


@cart_item_bp.route("/cart_items", methods=["POST"])
def create_cart_items_route():
    return create_cart_item()


@cart_item_bp.route("/cart_items/<int:item_id>", methods=["GET"])
def get_cart_items_route(item_id):
    return get_cart_item(item_id)


@cart_item_bp.route("/cart_items/<int:item_id>", methods=["PATCH"])
def patch_cart_items_route(item_id):
    return patch_cart_item(item_id)


@cart_item_bp.route("/cart_items/<int:item_id>", methods=["DELETE"])
def delete_cart_items_route(item_id):
    return delete_cart_item(item_id)
