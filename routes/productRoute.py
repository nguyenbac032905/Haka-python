from flask import Blueprint

from controllers.productController import (
    create_product,
    delete_product,
    get_product,
    list_products,
    patch_product,
)

product_bp = Blueprint("products", __name__)


@product_bp.route("/products", methods=["GET"])
def list_products_route():
    return list_products()


@product_bp.route("/products", methods=["POST"])
def create_product_route():
    return create_product()


@product_bp.route("/products/<int:item_id>", methods=["GET"])
def get_product_route(item_id):
    return get_product(item_id)


@product_bp.route("/products/<int:item_id>", methods=["PATCH"])
def patch_product_route(item_id):
    return patch_product(item_id)


@product_bp.route("/products/<int:item_id>", methods=["DELETE"])
def delete_product_route(item_id):
    return delete_product(item_id)
