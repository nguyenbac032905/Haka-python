from flask import Blueprint

from controllers.productController import (
    add_item_to_cart,
    create_order_from_cart,
    create_record,
    delete_cart_item,
    delete_record,
    get_category_tree,
    get_order_detail,
    get_product_by_slug,
    get_product_comments,
    get_record,
    get_user_cart,
    get_user_orders,
    list_records,
    login_account,
    login_user,
    patch_record,
    search_products,
    update_cart_item,
    update_order_status,
    upsert_product_comment,
)

product_bp = Blueprint("product", __name__)


# Endpoint đăng nhập tài khoản admin/account theo email và password.
@product_bp.route("/accounts/login", methods=["POST"])
def account_login_route():
    return login_account()


# Endpoint đăng nhập người dùng web/mobile theo email và password.
@product_bp.route("/users/login", methods=["POST"])
def user_login_route():
    return login_user()


# Endpoint tìm kiếm sản phẩm nâng cao theo từ khóa, giá, danh mục, tồn kho, sắp xếp.
@product_bp.route("/products/search", methods=["GET"])
def product_search_route():
    return search_products()


# Endpoint lấy chi tiết sản phẩm theo slug để render trang chi tiết SEO-friendly.
@product_bp.route("/products/slug/<string:slug>", methods=["GET"])
def product_by_slug_route(slug):
    return get_product_by_slug(slug)


# Endpoint lấy cây danh mục sản phẩm để dựng menu nhiều cấp.
@product_bp.route("/product-categories/tree", methods=["GET"])
def category_tree_route():
    return get_category_tree()


# Endpoint lấy danh sách comment/review của một sản phẩm kèm thông tin người dùng.
@product_bp.route("/products/<int:product_id>/comments", methods=["GET"])
def product_comments_route(product_id):
    return get_product_comments(product_id)


# Endpoint tạo mới hoặc cập nhật review của user cho một sản phẩm.
@product_bp.route("/products/<int:product_id>/comments", methods=["POST"])
def product_comment_upsert_route(product_id):
    return upsert_product_comment(product_id)


# Endpoint lấy giỏ hàng hiện tại của user, tự tạo cart nếu chưa có.
@product_bp.route("/users/<int:user_id>/cart", methods=["GET"])
def user_cart_route(user_id):
    return get_user_cart(user_id)


# Endpoint thêm sản phẩm vào giỏ hàng của user.
@product_bp.route("/users/<int:user_id>/cart/items", methods=["POST"])
def add_cart_item_route(user_id):
    return add_item_to_cart(user_id)


# Endpoint cập nhật số lượng một item trong giỏ hàng của user.
@product_bp.route("/users/<int:user_id>/cart/items/<int:item_id>", methods=["PATCH"])
def update_cart_item_route(user_id, item_id):
    return update_cart_item(user_id, item_id)


# Endpoint xóa một item khỏi giỏ hàng của user.
@product_bp.route("/users/<int:user_id>/cart/items/<int:item_id>", methods=["DELETE"])
def delete_cart_item_route(user_id, item_id):
    return delete_cart_item(user_id, item_id)


# Endpoint tạo đơn hàng từ toàn bộ sản phẩm hiện có trong giỏ hàng.
@product_bp.route("/orders/from-cart", methods=["POST"])
def create_order_from_cart_route():
    return create_order_from_cart()


# Endpoint lấy chi tiết đơn hàng kèm danh sách sản phẩm trong đơn.
@product_bp.route("/orders/<int:order_id>/detail", methods=["GET"])
def order_detail_route(order_id):
    return get_order_detail(order_id)


# Endpoint lấy lịch sử đơn hàng của một user.
@product_bp.route("/users/<int:user_id>/orders", methods=["GET"])
def user_orders_route(user_id):
    return get_user_orders(user_id)


# Endpoint cập nhật trạng thái đơn hàng hoặc thanh toán.
@product_bp.route("/orders/<int:order_id>/status", methods=["PATCH"])
def update_order_status_route(order_id):
    return update_order_status(order_id)


# Endpoint lấy toàn bộ dữ liệu của một bảng, hỗ trợ filter query, search, sort, phân trang.
@product_bp.route("/<string:table>", methods=["GET"])
def list_records_route(table):
    return list_records(table)


# Endpoint tạo mới một bản ghi trong bảng bất kỳ được whitelist.
@product_bp.route("/<string:table>", methods=["POST"])
def create_record_route(table):
    return create_record(table)


# Endpoint lấy chi tiết một bản ghi theo id trong bảng bất kỳ được whitelist.
@product_bp.route("/<string:table>/<int:item_id>", methods=["GET"])
def get_record_route(table, item_id):
    return get_record(table, item_id)


# Endpoint cập nhật một phần dữ liệu theo id, chỉ update các field được gửi lên.
@product_bp.route("/<string:table>/<int:item_id>", methods=["PATCH"])
def patch_record_route(table, item_id):
    return patch_record(table, item_id)


# Endpoint xóa dữ liệu theo id, ưu tiên soft delete nếu bảng có cột deleted.
@product_bp.route("/<string:table>/<int:item_id>", methods=["DELETE"])
def delete_record_route(table, item_id):
    return delete_record(table, item_id)
