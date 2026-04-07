from flask import Blueprint

from controllers.productController import getListProducts

product_bp = Blueprint("product",__name__)
@product_bp.route("/products")
def products():
    return getListProducts()
