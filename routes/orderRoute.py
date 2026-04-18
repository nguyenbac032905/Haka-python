from flask import Blueprint

from controllers.orderController import (
    create_order,
    delete_order,
    get_order,
    list_orders,
    patch_order,
)

order_bp = Blueprint("orders", __name__)


@order_bp.route("/orders", methods=["GET"])
def list_orders_route():
    return list_orders()


@order_bp.route("/orders", methods=["POST"])
def create_order_route():
    return create_order()


@order_bp.route("/orders/<int:item_id>", methods=["GET"])
def get_order_route(item_id):
    return get_order(item_id)


@order_bp.route("/orders/<int:item_id>", methods=["PATCH"])
def patch_order_route(item_id):
    return patch_order(item_id)


@order_bp.route("/orders/<int:item_id>", methods=["DELETE"])
def delete_order_route(item_id):
    return delete_order(item_id)
