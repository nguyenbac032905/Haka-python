from flask import Blueprint

from controllers.userController import (
    create_user,
    delete_user,
    get_user,
    list_users,
    patch_user,
)

user_bp = Blueprint("users", __name__)


@user_bp.route("/users", methods=["GET"])
def list_users_route():
    return list_users()


@user_bp.route("/users", methods=["POST"])
def create_user_route():
    return create_user()


@user_bp.route("/users/<int:item_id>", methods=["GET"])
def get_user_route(item_id):
    return get_user(item_id)


@user_bp.route("/users/<int:item_id>", methods=["PATCH"])
def patch_user_route(item_id):
    return patch_user(item_id)


@user_bp.route("/users/<int:item_id>", methods=["DELETE"])
def delete_user_route(item_id):
    return delete_user(item_id)
