from flask import Blueprint

from controllers.productCategoryController import (
    create_product_category,
    delete_product_category,
    get_product_category,
    list_product_categories,
    patch_product_category,
)

product_category_bp = Blueprint("product_categories", __name__)


@product_category_bp.route("/product_categories", methods=["GET"])
def list_product_categories_route():
    return list_product_categories()


@product_category_bp.route("/product_categories", methods=["POST"])
def create_product_categories_route():
    return create_product_category()


@product_category_bp.route("/product_categories/<int:item_id>", methods=["GET"])
def get_product_categories_route(item_id):
    return get_product_category(item_id)


@product_category_bp.route("/product_categories/<int:item_id>", methods=["PATCH"])
def patch_product_categories_route(item_id):
    return patch_product_category(item_id)


@product_category_bp.route("/product_categories/<int:item_id>", methods=["DELETE"])
def delete_product_categories_route(item_id):
    return delete_product_category(item_id)
