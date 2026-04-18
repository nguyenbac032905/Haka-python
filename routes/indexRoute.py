from routes.accountRoute import account_bp
from routes.cartItemRoute import cart_item_bp
from routes.cartRoute import cart_bp
from routes.orderItemRoute import order_item_bp
from routes.orderRoute import order_bp
from routes.productCategoryRoute import product_category_bp
from routes.productRoute import product_bp
from routes.userRoute import user_bp


def registerRoutes(app):
    app.register_blueprint(account_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(cart_bp)
    app.register_blueprint(cart_item_bp)
    app.register_blueprint(product_category_bp)
    app.register_blueprint(product_bp)
    app.register_blueprint(order_bp)
    app.register_blueprint(order_item_bp)
