from flask import Blueprint

from routes.productRoute import product_bp


def registerRoutes(app):
    app.register_blueprint(product_bp)