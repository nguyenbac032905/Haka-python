from flask import Blueprint

from controllers.cartController import (
    create_cart,
    delete_cart,
    get_cart,
    list_carts,
    patch_cart,
)

cart_bp = Blueprint("carts", __name__)


@cart_bp.route("/carts", methods=["GET"])
def list_carts_route():
    return list_carts()


@cart_bp.route("/carts", methods=["POST"])
def create_cart_route():
    return create_cart()


@cart_bp.route("/carts/<int:item_id>", methods=["GET"])
def get_cart_route(item_id):
    return get_cart(item_id)


@cart_bp.route("/carts/<int:item_id>", methods=["PATCH"])
def patch_cart_route(item_id):
    return patch_cart(item_id)


@cart_bp.route("/carts/<int:item_id>", methods=["DELETE"])
def delete_cart_route(item_id):
    return delete_cart(item_id)
